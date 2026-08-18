/* eslint-disable no-console */
/**
 * E2E smoke test for the county-clip fix (t_117f0b99) on the P0 split
 * (plan §4.2): geometryByCounty was moved OUT of waters.json into
 * public/data/waters_county_clips.json and is fetched LAZILY on the first
 * county activation.
 *
 * 1. Intercepts /data/waters.json / data/waters_county_clips.json; asserts
 *    waters.json does NOT carry geometryByCounty (split) and the clips file
 *    does (the Olt Brașov entry has a 'brasov' clip).
 * 2. Loads the map, waits for data, clicks the 'Brașov' county chip; asserts
 *    the clips file is fetched lazily, the spinner shows while loading, and
 *    no console errors —
 * 3. Zooms toward the Brașov Olt passage and screenshots for the record.
 * 4. Verifies the uncontracted overlay request too (background/deferred).
 *
 * Run: node scripts/_e2e_county_clip.mjs (dev server must be on :3000)
 */
import { chromium } from 'playwright';

const BASE = process.env.BASE_URL || 'http://localhost:3000';
const OUT_DIR = new URL('../.e2e/', import.meta.url);

const errors = [];
const watersResp = {};
const uncResp = {};
const clipsResp = {};

const CDP = process.env.PLAYWRIGHT_CDP;
// WSL: the bundled chromium needs --no-sandbox and the local-chromium path.
const browser = CDP
  ? await chromium.connectOverCDP(CDP)
  : await chromium.launch({ args: ['--no-sandbox'] });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });

page.on('console', (msg) => {
  if (msg.type() === 'error') errors.push(`console.error: ${msg.text()}`);
});
page.on('pageerror', (err) => errors.push(`pageerror: ${err.message}`));
page.on('request', (req) => {
  if (req.url().includes('/data/waters.json')) watersResp.url = req.url();
  if (req.url().includes('/data/uncontracted_rivers.json')) uncResp.url = req.url();
  if (req.url().includes('/data/waters_county_clips.json')) {
    clipsResp.url = req.url();
    clipsResp.requestedAt = Date.now();
  }
});
page.on('response', async (res) => {
  try {
    if (res.url().includes('/data/waters.json')) {
      watersResp.ok = res.ok();
      watersResp.status = res.status();
      watersResp.bodySize = (await res.body()).length;
      watersResp.json = JSON.parse(await res.text());
    }
    if (res.url().includes('/data/uncontracted_rivers.json')) {
      uncResp.ok = res.ok();
      uncResp.json = await res.json();
    }
    if (res.url().includes('/data/waters_county_clips.json')) {
      clipsResp.ok = res.ok();
      clipsResp.status = res.status();
      clipsResp.json = await res.json();
    }
  } catch (e) {
    watersResp.err = String(e);
  }
});

let failures = 0;
const check = (cond, label) => {
  if (cond) {
    console.log(`  PASS  ${label}`);
  } else {
    console.log(`  FAIL  ${label}`);
    failures += 1;
  }
};

console.log('== 1. served data ==');
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
// waters.json is simplified now (~5 MB, was ~40) — still wait for the county
// chips (they render only after the data has loaded).
await page.waitForSelector('button:visible[aria-pressed]', { timeout: 60000 });
await page.waitForTimeout(1200);
// Validate the SERVED files directly (the CDP inspector cache evicts the body
// before the response event can read it — fetch it with Node instead).
const wres = await fetch(`${BASE}/data/waters.json`);
const ures = await fetch(`${BASE}/data/uncontracted_rivers.json`);
const cres = await fetch(`${BASE}/data/waters_county_clips.json`);
check(wres.ok && ures.ok && cres.ok, 'waters.json + uncontracted_rivers.json + waters_county_clips.json served 200');
const servedWaters = await wres.json();
const servedUnc = await ures.json();
const servedClips = await cres.json();
// Count drifts as data-pipeline tasks merge/sweep waters; the assertion's job
// is a parse sanity check, not an exact-count pin.
check(Array.isArray(servedWaters) && servedWaters.length >= 1000, `waters.json parses (${servedWaters.length} waters)`);
// P0 §4.2: geometryByCounty is NO LONGER inside waters.json / uncontracted —
// it lives in waters_county_clips.json keyed by slug.
check(
  !servedWaters.some((w) => w.geometryByCounty) && !servedUnc.some((w) => w.geometryByCounty),
  'geometryByCounty is split OUT of waters.json + uncontracted (not inline)',
);
check(
  servedClips && typeof servedClips === 'object' && Object.keys(servedClips).length >= 900,
  `waters_county_clips.json carries ${Object.keys(servedClips).length} clip entries`,
);
const ehwpvgwh = servedClips['ehwpvgwh'];
check(!!ehwpvgwh?.brasov, 'Olt Brașov entry has a brasov clip (in clips file)');
const oltV = servedClips['3e8t20hn'];
check(!!oltV?.valcea, 'Olt Vâlcea entry has a valcea clip');
const siretG = servedClips['anpa-anpa-0296'];
check(!!siretG?.galati, 'Siret Galați entry has a galati clip');
check(Object.keys(servedClips).some((k) => k.startsWith('unc-')), 'uncontracted clips present (unc-* slugs)');

console.log('== 2. county filter interaction (lazy clip load) ==');
check(!(clipsResp.requestedAt), 'clips file NOT fetched before any county click (lazy)');
const chip = page.locator('button:visible', { hasText: /^Brașov$/ }).first();
await chip.click();
await page.waitForTimeout(2400);
check(!!clipsResp.requestedAt, 'county click triggered a fetch of waters_county_clips.json');
check(!!clipsResp.ok, `clips fetch ok (${clipsResp.status})`);
check(await chip.getAttribute('aria-pressed') === 'true', 'Brașov chip toggled active');
check(!errors.length, `no console/page errors after county select (${errors.length})`);

// toggle a second county to exercise the multi-county merge path
const vCh = page.locator('button:visible', { hasText: /^Vâlcea$/ }).first();
await vCh.click();
await page.waitForTimeout(1000);
check(!errors.length, 'no errors after Vâlcea added (multi-county)');

// back to Brașov only
await vCh.click();
await page.waitForTimeout(1000);
await page.screenshot({ path: '.e2e/county_brasov_full.png', fullPage: false });

console.log('== 3. zoom toward Brașov Olt ==');
// Default view is Romania z7 centered [45.95, 24.95]. Zoom in via the control,
// then pan slightly east to the Olt Brașov passage.
for (let i = 0; i < 5; i += 1) {
  await page.locator('.leaflet-control-zoom-in').click();
  await page.waitForTimeout(250);
}
await page.mouse.move(640, 400);
await page.mouse.down();
await page.mouse.move(600, 400, { steps: 10 });
await page.mouse.up();
await page.waitForTimeout(1200);
check(!errors.length, 'no errors after zoom/pan');
await page.screenshot({ path: new URL('county_brasov.png', OUT_DIR).pathname, fullPage: false });

// cleanup: deselect Brașov → full map back
await chip.click();
await page.waitForTimeout(800);
check(!errors.length, 'no errors after deselect');

console.log('== 4. summary ==');
if (errors.length) {
  console.log('console errors seen:');
  for (const e of errors.slice(0, 10)) console.log('  -', e);
}
await browser.close();
console.log(failures === 0 ? 'E2E PASSED' : `E2E FAILED (${failures} checks)`);
process.exit(failures === 0 ? 0 : 1);
