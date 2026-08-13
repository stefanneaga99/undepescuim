/* eslint-disable no-console */
/**
 * Mobile-branch e2e for t_7a7192ea (Bug 1: association selection on mobile).
 *
 * Uses page.setViewportSize({390,844}) which DOES apply on this browserless
 * instance (innerWidth becomes 390 — the real mobile branch: icon button,
 * useMediaQuery('(max-width: 767px)') → true, vaul bottom sheet).
 *
 * Flow: tap icon → fullscreen overlay → type → tap association → expect
 * store updated + overlay closed + map highlights green.
 *
 * Run: PLAYWRIGHT_CDP=http://localhost:3000 node scripts/_e2e_assoc_mobile.mjs http://172.25.236.246:3100
 */
import { chromium } from 'playwright';

const BASE = process.argv[2] || process.env.BASE_URL || 'http://localhost:3000';
const CDP = process.env.PLAYWRIGHT_CDP;

const browser = CDP ? await chromium.connectOverCDP(CDP) : await chromium.launch();
// Close leftover pages from crashed runs — they share the single browserless
// window, so a stale 800px page pins the window width (viewport resizes on a
// fresh page get overridden by the shared window).
for (const ctx of browser.contexts()) {
  for (const p of ctx.pages()) {
    if (p.url() !== 'about:blank') await p.close().catch(() => {});
  }
}
const page = await browser.newPage();
await page.setViewportSize({ width: 390, height: 844 });

let failures = 0;
const check = (cond, label) => {
  if (cond) console.log(`  PASS  ${label}`);
  else { console.log(`  FAIL  ${label}`); failures += 1; }
};
const COVERED = '#22c55e';
const countStroke = (color) =>
  page.evaluate((c) => {
    let n = 0;
    document.querySelectorAll('.leaflet-overlay-pane path').forEach((p) => {
      if ((p.getAttribute('stroke') || '').toLowerCase() === c) n += 1;
    });
    return n;
  }, color);

console.log(`== load ${BASE} @390px (real mobile branch) ==`);
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
console.log('  innerWidth:', await page.evaluate(() => window.innerWidth));
await page.waitForSelector('button:visible[aria-pressed]', { timeout: 90000 });
await page.waitForFunction(
  () => document.querySelectorAll('.leaflet-overlay-pane path').length > 0,
  { timeout: 60000 },
).catch(() => console.log('  warn: no overlay paths after load wait'));
await page.waitForTimeout(1500);

console.log('== mobile icon visible? ==');
const icon = page.locator('[aria-label="Caută asociația"]');
const iconVisible = await icon.isVisible().catch(() => false);
console.log(`  icon visible: ${iconVisible}`);
check(iconVisible, 'mobile search icon visible');

console.log('== tap icon → overlay opens ==');
await icon.click();
await page.waitForTimeout(700);
// Overlay marker: its own back button (the desktop trigger also has the text
// 'Caută asociația…', so text-match alone is ambiguous).
const overlayBack = page.locator('[aria-label="Înapoi"]');
const overlayVisible = await overlayBack.isVisible().catch(() => false);
console.log(`  overlay back visible: ${overlayVisible}`);
check(overlayVisible, 'fullscreen overlay opened');

const items = page.locator('[data-slot="command-item"]');
const itemCount = await items.count();
console.log(`  command items: ${itemCount}`);
check(itemCount > 0, `association list rendered (${itemCount} items)`);
await page.screenshot({ path: '.e2e/mobile_overlay.png' });

console.log('== type "covasna" + tap AJVPS Covasna ==');
const input = page.locator('[data-slot="command-input"]');
await input.fill('covasna');
await page.waitForTimeout(600);
const filteredItems = page.locator('[data-slot="command-item"]');
const fCount = await filteredItems.count();
console.log(`  filtered items: ${fCount}`);
let clickedItem = false;
for (let i = 0; i < fCount; i += 1) {
  const txt = (await filteredItems.nth(i).textContent()) || '';
  if (txt.includes('AJVPS Covasna')) {
    await filteredItems.nth(i).click();
    clickedItem = true;
    break;
  }
}
check(clickedItem, 'tapped AJVPS Covasna item');
await page.waitForTimeout(1200);

const headerText = (await page.locator('header').textContent()) || '';
console.log(`  header: ${headerText.replace(/\s+/g, ' ').slice(0, 60)}`);
check(headerText.includes('AJVPS Covasna'), 'trigger shows selected association');

const overlayClosed = !(await page
  .locator('[aria-label="Înapoi"]')
  .isVisible()
  .catch(() => false));
check(overlayClosed, 'overlay closed after selection');

const green = await countStroke(COVERED);
console.log(`  green paths: ${green}`);
check(green > 0, 'map highlighted association waters green');
await page.screenshot({ path: '.e2e/mobile_select.png' });

await browser.close();
console.log(failures === 0 ? 'MOBILE E2E PASSED' : `MOBILE E2E FAILED (${failures} checks)`);
process.exit(failures === 0 ? 0 : 1);
