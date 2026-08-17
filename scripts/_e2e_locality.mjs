/* eslint-disable no-console */
/**
 * E2E smoke test for the county→locality filter cascade (t_dd918db7).
 *
 * 1. Served data: waters.json / uncontracted_rivers.json / uncontracted_lakes.json
 *    carry `locality`; spot-checks a text-fallback resolution (Mihoești →
 *    Câmpeni) and the overall coverage floor.
 * 2. UI: no locality control before a county is selected; selecting Bihor
 *    reveals it; the dropdown is county-scoped (contains Oradea, NOT
 *    Cluj-Napoca); searching nonsense shows 'Fără localități'.
 * 3. Selecting Oradea filters the map (rendered path count drops vs
 *    county-only) and the pill reflects the selection.
 * 4. Cascade: adding a second county resets the locality selection
 *    ('Toate localitățile' pill returns).
 * 5. Uncontracted pool participates: an Oradea uncontracted river exists in
 *    the served data and the locality filter still renders uncontracted.
 *
 * Run: node scripts/_e2e_locality.mjs (dev server must be on :3000)
 */
import { chromium } from 'playwright';

const BASE = process.env.BASE_URL || 'http://localhost:3000';
const OUT_DIR = new URL('../.e2e/', import.meta.url);

const errors = [];

const CDP = process.env.PLAYWRIGHT_CDP;
const browser = CDP
  ? await chromium.connectOverCDP(CDP)
  : await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });

page.on('console', (msg) => {
  if (msg.type() === 'error') errors.push(`console.error: ${msg.text()}`);
});
page.on('pageerror', (err) => errors.push(`pageerror: ${err.message}`));

let failures = 0;
const check = (cond, label) => {
  if (cond) {
    console.log(`  PASS  ${label}`);
  } else {
    console.log(`  FAIL  ${label}`);
    failures += 1;
  }
};

console.log('== 1. served data carries locality ==');
const wres = await fetch(`${BASE}/data/waters.json`);
const ures = await fetch(`${BASE}/data/uncontracted_rivers.json`);
const lres = await fetch(`${BASE}/data/uncontracted_lakes.json`);
check(wres.ok && ures.ok && lres.ok, 'all three data files served 200');
const servedWaters = await wres.json();
const servedUnc = await ures.json();
const servedLakes = await lres.json();
check(servedWaters.length === 1013, `waters.json parses (${servedWaters.length} waters)`);
const withLoc = servedWaters.filter((w) => typeof w.locality === 'string');
check(withLoc.length >= 850, `contracted coverage >= 84% (${withLoc.length}/1013)`);
const mihoesti = servedWaters.find((w) => w.slug === 'anpa-anpa-0008');
check(mihoesti?.locality === 'Câmpeni', 'limite-text fallback: Mihoești → Câmpeni');
// NOTE (t_5ebd076b): uncontracted RIVERS now carry locality again — the A1
// rebuild (t_45a0beae) had silently wiped the field; build_locality_assignment.py
// was re-run (3936/4140, 95.1%) and the builder preserves enrichment keys now.
// Both uncontracted pools participate in the locality filter.
check(
  servedLakes.some((w) => w.judet === 'Bihor' && w.locality === 'Oradea'),
  'uncontracted lake pool carries locality (Bihor/Oradea)',
);
check(
  servedUnc.some((w) => w.judet === 'Bihor' && w.locality === 'Oradea'),
  'uncontracted RIVER pool carries locality (Bihor/Oradea)',
);
const riverLocalityCoverage = (servedUnc.filter((w) => typeof w.locality === 'string').length / servedUnc.length) * 100;
check(riverLocalityCoverage >= 90, `uncontracted river locality coverage >= 90% (${riverLocalityCoverage.toFixed(1)}%)`);
check(!errors.length, `no console errors while loading (${errors.length})`);

console.log('== 2. UI: locality gated behind county selection ==');
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
// wait for county chips (data loaded)
await page.waitForSelector('button:visible[aria-pressed]', { timeout: 60000 });
await page.waitForTimeout(2000);
const localityLabelBefore = await page.locator('text=Localitate').first().isVisible().catch(() => false);
check(!localityLabelBefore, 'no locality control before any county is selected');

const bihor = page.locator('button:visible', { hasText: /^Bihor$/ }).first();
await bihor.click();
await page.waitForTimeout(1500);
check(await bihor.getAttribute('aria-pressed') === 'true', 'Bihor chip toggled active');
const localityLabelAfter = page.locator('text=Localitate');
try {
  await localityLabelAfter.first().waitFor({ state: 'attached', timeout: 8000 });
  // FilterBar content renders twice (hidden mobile bar + desktop panel) —
  // any visible instance proves the control is shown.
  const anyVisible = await localityLabelAfter.evaluateAll((els) =>
    els.some((el) => el.offsetParent !== null),
  );
  check(anyVisible, 'locality control appears after Bihor selected');
} catch {
  check(false, 'locality control appears after Bihor selected');
}

console.log('== 3. dropdown is county-scoped + searchable ==');
const trigger = page.locator('button:visible', { hasText: /^Toate localitățile$/ }).first();
await trigger.click();
await page.waitForSelector('[data-slot="command-input"]', { timeout: 5000 });
const items = page.locator('[data-slot="command-item"]');
const texts = await items.allTextContents();
check(texts.some((t) => t.includes('Oradea')), 'dropdown lists Oradea (Bihor UAT)');
check(!texts.some((t) => t.includes('Cluj-Napoca')), 'dropdown excludes Cluj-Napoca (county-scoped)');
// search: nonsense → empty state
const search = page.locator('[data-slot="command-input"]');
await search.fill('zzzzz');
await page.waitForTimeout(300);
check(await page.locator('text=Fără localități').first().isVisible(), "search nonsense shows 'Fără localități'");
// search: Oradea → selectable item
await search.fill('Oradea');
await page.waitForTimeout(300);
const oradeaItem = page.locator('[data-slot="command-item"]', { hasText: 'Oradea' }).first();
await oradeaItem.click();
await page.waitForTimeout(1200);
check(await page.locator('button:visible', { hasText: /^Oradea$/ }).first().isVisible(), "pill shows 'Oradea' after selection");
check(!errors.length, 'no console errors after locality selection');

console.log('== 4. locality filters the map (fewer rendered features) ==');
const countPaths = async () => page.locator('.leaflet-overlay-pane path').count();
// The popover stays open after a multi-select toggle; close it before each
// interaction so a subsequent trigger click re-opens (not closes) it.
await page.keyboard.press('Escape');
await page.waitForTimeout(300);
// Deselect Oradea → county-only baseline.
const trigger2 = page.locator('button:visible', { hasText: /^Oradea$/ }).first();
await trigger2.click();
await page.locator('[data-slot="command-input"]').fill('Oradea');
await page.waitForTimeout(300);
await page.locator('[data-slot="command-item"]', { hasText: 'Oradea' }).first().click(); // deselect
await page.keyboard.press('Escape');
await page.waitForTimeout(1200);
const countyOnly = await countPaths();
await page.screenshot({ path: new URL('locality_bihor_all.png', OUT_DIR).pathname, fullPage: false });

// Re-select Oradea → locality-filtered count.
const trigger3 = page.locator('button:visible', { hasText: /^Toate localitățile$/ }).first();
await trigger3.click();
await page.locator('[data-slot="command-input"]').fill('Oradea');
await page.waitForTimeout(300);
await page.locator('[data-slot="command-item"]', { hasText: 'Oradea' }).first().click();
await page.keyboard.press('Escape');
await page.waitForTimeout(1200);
const oradeaCount = await countPaths();
check(oradeaCount > 0 && oradeaCount < countyOnly, `Oradea renders fewer features than Bihor (${oradeaCount} < ${countyOnly})`);
await page.screenshot({ path: new URL('locality_oradea.png', OUT_DIR).pathname, fullPage: false });

console.log('== 5. cascade: county change resets locality ==');
await page.keyboard.press('Escape');
await page.waitForTimeout(300);
const cluj = page.locator('button:visible', { hasText: /^Cluj$/ }).first();
await cluj.click();
await page.waitForTimeout(1000);
check(
  await page.locator('button:visible', { hasText: /^Toate localitățile$/ }).first().isVisible().catch(() => false),
  'adding a second county resets locality to "Toate localitățile"',
);
check(!errors.length, 'no console errors after cascade');

// cleanup: deselect both counties
await bihor.click();
await cluj.click();
await page.waitForTimeout(800);

console.log('== 7. Brașov regression (t_9529e678 — user report) ==');
// User flow: județ Brașov → localitate Brașov — the map MUST visibly change
// (previously it rendered 0 paths at national zoom: the only contracted water
// with locality 'Brașov' is bbox-fallback (geometry: null → dropped by the
// county clip) and the 4 city lakes are < 100 ha → LOD-culled at z7).
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('button:visible[aria-pressed]', { timeout: 60000 });
await page.waitForTimeout(2000);
const brasov = page.locator('button:visible', { hasText: /^Brașov$/ }).first();
await brasov.click();
await page.waitForTimeout(1500);
const trig = page.locator('button:visible', { hasText: /^Toate localitățile$/ }).first();
await trig.click();
await page.waitForSelector('[data-slot="command-input"]', { timeout: 5000 });
await page.locator('[data-slot="command-input"]').fill('Brașov');
await page.waitForTimeout(300);
const brasovOption = page.locator('[data-slot="command-item"]', { hasText: /^Brașov/ }).first();
await brasovOption.click();
await page.waitForTimeout(2500); // locality flyTo animates
const tileZ = await page.evaluate(() => {
  const src = document.querySelector('.leaflet-tile')?.getAttribute('src') ?? '';
  const m = src.match(/\/(\d+)\/\d+\/\d+/);
  return m ? Number(m[1]) : null;
});
const lipsCount = await page.locator('.leaflet-overlay-pane path').count();
check(tileZ !== null && tileZ > 7, `map zoomed to the locality (tile z=${tileZ})`);
check(lipsCount > 0, `Brașov locality renders its waters (${lipsCount} paths)`);
// t_e70099a9: the dropdown surfaces a per-locality count so the user SEES the
// filter matched even when the rendered streams are faint — the Brașov option
// must carry a positive water count (1 contracted + 44 uncontracted rivers).
const brasovCount = await brasovOption.getAttribute('data-count');
check(brasovCount !== null && Number(brasovCount) > 0, `Brașov locality shows a count (${brasovCount})`);
await page.screenshot({ path: new URL('locality_brasov_city.png', OUT_DIR).pathname, fullPage: false });
await page.keyboard.press('Escape');
// clear the locality → the view is restored (no longer zoomed at the city)
await page.waitForTimeout(600);
const clearTrig = page.locator('[data-testid="locality-filter"]').filter({ visible: true }).first();
await clearTrig.click();
await page.locator('[data-slot="command-input"]').fill('Brașov');
await page.waitForTimeout(300);
await page.locator('[data-slot="command-item"]', { hasText: /^Brașov/ }).first().click();
await page.keyboard.press('Escape');
await page.waitForTimeout(1500);
const tileZAfter = await page.evaluate(() => {
  const src = document.querySelector('.leaflet-tile')?.getAttribute('src') ?? '';
  const m = src.match(/\/(\d+)\/\d+\/\d+/);
  return m ? Number(m[1]) : null;
});
check(tileZAfter !== null && tileZAfter === 7, `clearing the locality restores the national view (tile z=${tileZAfter})`);

console.log('== 8. summary ==');
if (errors.length) {
  console.log('console errors seen:');
  for (const e of errors.slice(0, 10)) console.log('  -', e);
}
await browser.close();
console.log(failures === 0 ? 'E2E PASSED' : `E2E FAILED (${failures} checks)`);
process.exit(failures === 0 ? 0 : 1);
