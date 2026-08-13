/* eslint-disable no-console */
/**
 * E2E smoke test for the uncontracted lakes/ponds overlay (t_51e028c4).
 *
 * 1. Asserts /data/uncontracted_lakes.json is served, parses, and carries the
 *    10 Dumbrăvița (Hălchiu, Brașov) ponds with 'Privat / Necontractat' status.
 * 2. Loads the map, filters to Brașov + Lacuri, zooms to the Hălchiu ponds and
 *    clicks one — the detail card must show 'Privat / Necontractat'.
 * 3. Asserts no console/page errors along the way.
 *
 * Run: node scripts/_e2e_lakes.mjs (dev server must be on :3000)
 */
import { chromium } from 'playwright';

const BASE = process.env.BASE_URL || 'http://localhost:3000';

const errors = [];
const lakesResp = {};

const CDP = process.env.PLAYWRIGHT_CDP;
const browser = CDP
  ? await chromium.connectOverCDP(CDP)
  : await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });

page.on('console', (msg) => {
  if (msg.type() === 'error') errors.push(`console.error: ${msg.text()}`);
});
page.on('pageerror', (err) => errors.push(`pageerror: ${err.message}`));
page.on('response', async (res) => {
  if (res.url().includes('/data/uncontracted_lakes.json')) {
    lakesResp.ok = res.ok();
    lakesResp.status = res.status();
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
await page.waitForSelector('button:visible[aria-pressed]', { timeout: 60000 });
await page.waitForTimeout(2000);

const lres = await fetch(`${BASE}/data/uncontracted_lakes.json`);
check(lakesResp.ok && lres.ok, 'uncontracted_lakes.json served 200');
const lakes = await lres.json();
check(Array.isArray(lakes) && lakes.length > 5000, `parses, ${lakes.length} lakes`);
const dumbravita = lakes.filter(
  (w) =>
    w.name === 'Dumbrăvița' &&
    w.judet === 'Brașov' &&
    w.coordinates[0] > 25.3 &&
    w.coordinates[0] < 25.6,
);
check(dumbravita.length === 10, `Dumbrăvița Hălchiu: ${dumbravita.length} ponds`);
check(
  dumbravita.every((w) => w.uncontracted === true && w.subtype === 'lac' && w.areaHa > 0),
  'all ponds uncontracted lac with areaHa',
);
const vidraru = lakes.find((w) => w.name.includes('Vidraru'));
check(!vidraru, 'contracted Vidraru excluded');
const snagov = lakes.find((w) => w.name.includes('Snagov'));
check(!!snagov, 'uncontracted Lacul Snagov present');

console.log('== 2. click a pond → card shows Privat / Necontractat ==');
// filter: Lacuri + Brașov to keep the map light
await page.locator('button:visible', { hasText: 'Lacuri' }).first().click();
await page.locator('button:visible', { hasText: /^Brașov$/ }).first().click();
await page.waitForTimeout(1500);

// zoom in a couple of steps so the ponds are big enough to click (z10: the
// Hălchiu ponds sit just east of the default Romania center)
for (let i = 0; i < 3; i += 1) {
  await page.locator('.leaflet-control-zoom-in').click();
  await page.waitForTimeout(250);
}
await page.waitForTimeout(800);

// The biggest Dumbrăvița pond (109 ha) from the served data — click its exact
// screen position, derived from the OSM tile math (no map-instance access
// needed): read z/x/y from any loaded tile's src, compute world pixels, and
// derive the pane offset from the tile's rendered bounding rect.
const target = dumbravita.reduce((a, b) => (a.areaHa > b.areaHa ? a : b));
const computePos = (lon, lat) =>
  page.evaluate(
    ([lon, lat]) => {
      const img = document.querySelector('.leaflet-tile-container img.leaflet-tile');
      if (!img) return null;
      const parts = img.src.split('/');
      const z = Number(parts[parts.length - 3]);
      const tx = Number(parts[parts.length - 2]);
      const ty = Number(parts[parts.length - 1].replace('.png', ''));
      const rect = img.getBoundingClientRect();
      // screen = paneOffset + worldPx, so paneOffset = tileRect.topLeft - tileWorldPx
      const paneX = rect.left - tx * 256;
      const paneY = rect.top - ty * 256;
      const s = 256 * Math.pow(2, z);
      const px = ((lon + 180) / 360) * s;
      const latRad = (lat * Math.PI) / 180;
      const py = ((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2) * s;
      return { x: paneX + px, y: paneY + py, z };
    },
    [lon, lat],
  );

let pos = await computePos(target.coordinates[0], target.coordinates[1]);
console.log(`  target ${target.name} ${target.areaHa}ha at ${target.coordinates} -> screen ${JSON.stringify(pos)}`);
check(!!pos, 'computed target screen position from tiles');

// Pan the target to the viewport center with in-bounds multi-step drags.
let guard = 0;
while (pos && (pos.x < 200 || pos.x > 1080 || pos.y < 120 || pos.y > 680) && guard < 8) {
  const dx = Math.max(-250, Math.min(250, 640 - pos.x));
  const dy = Math.max(-250, Math.min(250, 400 - pos.y));
  await page.mouse.move(640, 400);
  await page.mouse.down();
  await page.mouse.move(640 + dx, 400 + dy, { steps: 6 });
  await page.mouse.up();
  await page.waitForTimeout(400);
  pos = await computePos(target.coordinates[0], target.coordinates[1]);
  guard += 1;
}
check(!!pos && pos.x >= 200 && pos.x <= 1080 && pos.y >= 120 && pos.y <= 680,
  `target inside viewport after pan (${JSON.stringify(pos)})`);

// click the polygon fill
await page.mouse.click(pos.x, pos.y);
await page.waitForTimeout(1500);

const cardVisible = await page
  .locator('text=Privat / Necontractat')
  .first()
  .isVisible()
  .catch(() => false);
check(cardVisible, 'detail card shows "Privat / Necontractat"');

const cardText = await page
  .locator('aside, [role="dialog"], [data-vaul-drawer]')
  .first()
  .innerText()
  .catch(() => '');
const hasDumbravita = cardText.includes('Dumbrăvița');
check(hasDumbravita, `card names the pond (got: ${cardText.split('\n')[0] || 'empty'})`);

await page.screenshot({ path: '.e2e/lakes_halchiu.png', fullPage: false });
check(!errors.length, `no console/page errors (${errors.length})`);

console.log('== 3. summary ==');
if (errors.length) {
  console.log('console errors seen:');
  for (const e of errors.slice(0, 10)) console.log('  -', e);
}
await browser.close();
console.log(failures === 0 ? 'E2E PASSED' : `E2E FAILED (${failures} checks)`);
process.exit(failures === 0 ? 0 : 1);
