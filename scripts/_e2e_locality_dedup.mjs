/**
 * Regression for t_f6445fda (user report 2026-08-17):
 *   1. The LOCALITATE dropdown must show 'Brașov' exactly ONCE (no visually
 *      identical duplicates — whitespace/case/diacritic variants collapse).
 *   2. Selecting Brașov locality must visibly filter the map (path count +
 *      zoom change); clearing restores the pre-locality view.
 *
 * Runs against any BASE (default producción). Local-chromium launch with
 * --no-sandbox (this WSL host), or connectOverCDP when PLAYWRIGHT_CDP is set.
 * Usage:
 *   /tmp/asound-run.sh node scripts/_e2e_locality_dedup.mjs http://localhost:3101
 *   PLAYWRIGHT_CDP=http://localhost:3000 node scripts/_e2e_locality_dedup.mjs http://172.25.236.246:3100
 */
import { chromium } from 'playwright';

const BASE = process.argv[2] || 'https://undepescuim.vercel.app';
const CDP = process.env.PLAYWRIGHT_CDP;

const browser = CDP
  ? await chromium.connectOverCDP(CDP)
  : await chromium.launch({ args: ['--no-sandbox'] });
if (CDP) {
  for (const ctx of browser.contexts()) {
    for (const p of ctx.pages()) {
      if (p.url() !== 'about:blank') await p.close();
    }
  }
}
const page = await browser.newPage();
await page.setViewportSize({ width: 390, height: 844 }); // mobile

const errors = [];
page.on('console', (m) => {
  if (m.type() === 'error') errors.push(m.text());
});
page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));

let failures = 0;
const check = (cond, label, extra = '') => {
  console.log(`  ${cond ? 'PASS' : 'FAIL'}  ${label}${extra ? `  [${extra}]` : ''}`);
  if (!cond) failures += 1;
};

/** Read the visible locality options (any copy of the popover, deduped by DOM order). */
const readOptions = async () => {
  const items = page.locator('[data-testid="locality-option"]');
  const n = await items.count();
  const texts = [];
  for (let i = 0; i < n; i++) {
    const t = ((await items.nth(i).textContent().catch(() => '')) || '');
    // only rows that are actually displayed
    const vis = await items
      .nth(i)
      .evaluate((el) => el.offsetParent !== null)
      .catch(() => true);
    if (vis) texts.push(t.trim());
  }
  return texts;
};

const normKey = (s) =>
  s
    .normalize('NFC')
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');

console.log(`== load ${BASE} (mobile 390px) ==`);
await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 60000 });
await page
  .waitForFunction(() => {
    const el = document.querySelector('.leaflet-container');
    return !!el && el.getBoundingClientRect().height > 100;
  }, { timeout: 60000 })
  .catch(() => {});
await page.waitForTimeout(2000);
console.log('  innerWidth:', await page.evaluate(() => window.innerWidth));

// --- 1. county Brașov ---
console.log('== select county Brașov ==');
const chips = page.locator('[data-testid="county-chip"]');
const nChips = await chips.count();
check(nChips > 40, `county chips rendered (${nChips})`);
let clickedCounty = false;
for (let i = 0; i < nChips; i++) {
  const t = ((await chips.nth(i).textContent().catch(() => '')) || '').trim();
  if (t === 'Brașov') {
    await chips.nth(i).click();
    clickedCounty = true;
    break;
  }
}
check(clickedCounty, 'clicked county chip Brașov');
await page.waitForTimeout(1000);

// --- 2. LOCALITATE dropdown: exactly ONE 'Brașov' ---
console.log('== open LOCALITATE dropdown (dup check) ==');
const triggers = page.locator('[data-testid="locality-filter"]');
check(await triggers.count() > 0, 'locality filter trigger exists after county pick');
const trigger = triggers.first();
const triggerVisible = await trigger
  .evaluateAll((els) => els.some((el) => el.offsetParent !== null))
  .catch(() => false);
check(triggerVisible, 'locality filter trigger is visible');
await trigger.click();
await page.waitForTimeout(800);

const options = await readOptions();
console.log(`  ${options.length} locality options`);
const brasovExact = options.filter((t) => t === 'Brașov').length;
check(brasovExact === 1, `exactly ONE 'Brașov' option`, `count=${brasovExact}`);

// no two options may look identical under the normalization the app applies
const byKey = new Map();
for (const t of options) {
  const k = normKey(t);
  byKey.set(k, (byKey.get(k) || 0) + 1);
}
const dups = [...byKey.entries()].filter(([, c]) => c > 1);
check(dups.length === 0, 'no visually-identical duplicate options', JSON.stringify(dups));
check(options.every((t) => t.length > 0), 'no blank/whitespace-only options');

// --- 3. select Brașov → map must visibly change ---
console.log('== select Brașov locality ==');
const pathsBefore = await page.evaluate(
  () => document.querySelectorAll('.leaflet-overlay-pane path').length,
);
const zoomInfo = async () => {
  const src = await page.evaluate(
    () => document.querySelector('.leaflet-tile')?.getAttribute('src') ?? '',
  );
  const m = src.match(/\/(\d+)\/\d+\/\d+/);
  return m ? Number(m[1]) : null;
};
const zoomBefore = await zoomInfo();

const items = page.locator('[data-testid="locality-option"]');
const nItems = await items.count();
let selected = false;
for (let i = 0; i < nItems; i++) {
  const t = ((await items.nth(i).textContent().catch(() => '')) || '').trim();
  if (t === 'Brașov') {
    await items.nth(i).click();
    selected = true;
    break;
  }
}
check(selected, 'clicked Brașov option');
await page.keyboard.press('Escape').catch(() => {});
await page.waitForTimeout(2500); // locality flyTo animates

const pathsAfter = await page.evaluate(
  () => document.querySelectorAll('.leaflet-overlay-pane path').length,
);
const zoomAfter = await zoomInfo();
const pill = (
  (await page.locator('[data-testid="locality-filter"]').first().textContent().catch(() => '')) || ''
).trim();
console.log(`  paths ${pathsBefore} -> ${pathsAfter}; zoom ${zoomBefore} -> ${zoomAfter}; pill='${pill}'`);
check(pill.includes('Brașov'), "pill shows 'Brașov' after selection");
check(pathsAfter !== pathsBefore, 'map path count CHANGED after locality selection', `${pathsBefore} -> ${pathsAfter}`);
check(zoomAfter !== null && (zoomBefore === null || zoomAfter > zoomBefore), 'map zoomed toward the locality', `zoom ${zoomBefore} -> ${zoomAfter}`);

// --- 4. clear → restores the pre-locality view ---
console.log('== clear locality ==');
const clearTrig = page.locator('[data-testid="locality-filter"]').first();
await clearTrig.click();
await page.waitForTimeout(600);
// reset row (data-testid locality-reset) appears only when something is selected
const reset = page.locator('[data-testid="locality-reset"]');
if ((await reset.count()) > 0) {
  await reset.first().click();
} else {
  // fallback: reopen and toggle Brașov off
  await page.locator('[data-testid="locality-option"]', { hasText: /^Brașov$/ }).first().click();
}
await page.keyboard.press('Escape').catch(() => {});
await page.waitForTimeout(2000);
const pillAfter = (
  (await page.locator('[data-testid="locality-filter"]').first().textContent().catch(() => '')) || ''
).trim();
const zoomCleared = await zoomInfo();
check(!pillAfter.includes('Brașov'), 'pill cleared');
check(zoomCleared !== null && zoomCleared === 7, 'clearing restores the national zoom (z7)', `zoom=${zoomCleared}`);

// ---- console errors (log, but don't fail on the known deployed i18n #418) ----
const interesting = errors.filter(
  (e) => !/favicon|Failed to load resource|net::|#418/.test(e),
);
console.log('== console errors (excluding known i18n hydration #418) ==');
(interesting.length ? interesting : ['(none)']).forEach((e) => console.log('  ', e.slice(0, 200)));

await browser.close();
console.log(failures === 0 ? 'ALL CHECKS PASSED' : `${failures} CHECKS FAILED`);
process.exit(failures === 0 ? 0 : 1);