/* eslint-disable no-console */
/**
 * t_f930e4f3 e2e: mobile hamburger menu. On a ~390px viewport the header
 * shows a hamburger button (no inline links); tapping it opens a right-side
 * Sheet with the info-page links (Specii, Permis 2026). Selecting a link
 * closes the sheet and navigates. On desktop (1280px) the hamburger is
 * hidden and the inline links stay visible as before.
 *
 * Run: PLAYWRIGHT_CDP=http://localhost:3000 node scripts/_e2e_menu_mobile.mjs http://172.25.236.246:3100
 */
import { chromium } from 'playwright';

const BASE = process.argv[2] || process.env.BASE_URL || 'http://localhost:3000';
const CDP = process.env.PLAYWRIGHT_CDP;

const browser = CDP ? await chromium.connectOverCDP(CDP) : await chromium.launch();
let page = await browser.newPage();

let failures = 0;
const check = (cond, label) => {
  if (cond) console.log(`  PASS  ${label}`);
  else { console.log(`  FAIL  ${label}`); failures += 1; }
};

// Force the shared browserless window back to the pass's viewport (the
// window is shared with concurrent consumers that can resize it mid-run).
const settleViewport = async (w, h) => {
  for (let i = 0; i < 8; i += 1) {
    await page.setViewportSize({ width: w, height: h }).catch(() => {});
    await page.waitForTimeout(200);
    const iw = await page.evaluate(() => window.innerWidth).catch(() => 0);
    const ih = await page.evaluate(() => window.innerHeight).catch(() => 0);
    if (iw === w && ih === h) return true;
  }
  console.log(`  warn: viewport did not settle at ${w}x${h}`);
  return false;
};

async function loadApp() {
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('header', { timeout: 30000 });
  await page.waitForTimeout(1200);
}

async function freshPage(w, h) {
  // Close ALL non-blank pages — the browserless container shares ONE window
  // and a leftover page pins its width (skill: close leftovers first).
  for (const ctx of browser.contexts()) {
    for (const p of ctx.pages()) {
      if (p.url() !== 'about:blank') await p.close().catch(() => {});
    }
  }
  const pg = await browser.newPage();
  await pg.setViewportSize({ width: w, height: h });
  page = pg;
  await loadApp();
  const iw = await page.evaluate(() => window.innerWidth).catch(() => 0);
  if (iw !== w) {
    await page.close().catch(() => {});
    return freshPage(w, h);
  }
  return page;
}

// ---- mobile pass (390px: hamburger visible, inline links hidden) ----
await freshPage(390, 844);

console.log('\n========== MOBILE PASS (390px) ==========');
// Locators bind to the page object at creation — create them fresh here
// because freshPage() swaps `page` for a new page per pass.
const burger = page.locator('header button[aria-label="Meniu"]');
const inlinePermis = page.locator('header nav a:has-text("Permis 2026")');
const inlineSpecii = page.locator('header nav a:has-text("Specii")');
check(await burger.isVisible().catch(() => false), 'hamburger button visible');
check(!(await inlinePermis.isVisible().catch(() => false)), 'inline Permis link hidden on mobile');
check(!(await inlineSpecii.isVisible().catch(() => false)), 'inline Specii link hidden on mobile');

await burger.click();
await page.waitForTimeout(700); // sheet slide-in animation
const sheet = page.locator('[data-slot="sheet-content"]');
check(await sheet.isVisible().catch(() => false), 'sheet opened after hamburger tap');

const sheetText = ((await sheet.textContent().catch(() => '')) || '').replace(/\s+/g, ' ');
check(sheetText.includes('Specii') && sheetText.includes('Dimensiuni de reținere'), 'sheet lists Specii + size hint');
check(sheetText.includes('Permis 2026'), 'sheet lists Permis 2026');

// z-index above the map filter overlay (z-1000) — sheet must be z-1200
const sheetZ = await sheet.evaluate((el) => getComputedStyle(el).zIndex);
check(Number(sheetZ) >= 1100, `sheet z-index above map overlays (got ${sheetZ})`);

// Selecting a link closes the sheet and navigates
await page.locator('[data-slot="sheet-content"] a[href="/specii"]').click();
await page.waitForURL('**/specii', { timeout: 10000 });
await page.waitForTimeout(500);
check(!(await page.locator('[data-slot="sheet-content"]').isVisible().catch(() => false)), 'sheet closed on selection');
check(page.url().includes('/specii'), `navigated to /specii (${page.url()})`);
await page.screenshot({ path: '.e2e/menu_mobile_specii.png' }).catch(() => {});

// Reopen → Permis 2026 link works
await page.goBack({ waitUntil: 'domcontentloaded' });
await page.waitForTimeout(800);
check(await burger.isVisible().catch(() => false), 'hamburger visible again after back');
await burger.click();
await page.waitForTimeout(700);
await page.locator('[data-slot="sheet-content"] a[href="/permis"]').click();
await page.waitForURL('**/permis', { timeout: 10000 });
check(page.url().includes('/permis'), `navigated to /permis (${page.url()})`);

// Reopen → overlay tap closes the sheet without navigating
await page.goBack({ waitUntil: 'domcontentloaded' });
await page.waitForTimeout(800);
await burger.click();
await page.waitForTimeout(700);
const overlay = page.locator('[data-slot="sheet-overlay"]');
await overlay.click({ position: { x: 30, y: 400 } }).catch(async () => {
  await page.mouse.click(20, 400);
});
await page.waitForTimeout(500);
check(!(await page.locator('[data-slot="sheet-content"]').isVisible().catch(() => false)), 'overlay tap closes the sheet');

// ---- desktop pass (1280px: hamburger hidden, inline links unchanged) ----
await freshPage(1280, 800);

console.log('\n========== DESKTOP PASS (1280px) ==========');
console.log(`  innerWidth=${await page.evaluate(() => window.innerWidth)}`);
// Re-create locators — freshPage() swapped `page`, the old ones point at
// the closed mobile page.
const dBurger = page.locator('header button[aria-label="Meniu"]');
const dPermis = page.locator('header nav a:has-text("Permis 2026")');
const dSpecii = page.locator('header nav a:has-text("Specii")');
const desktopPermisVisible = await dPermis.isVisible().catch(() => false);
const desktopSpeciiVisible = await dSpecii.isVisible().catch(() => false);
const desktopBurgerVisible = await dBurger.isVisible().catch(() => false);
console.log(`  inlinePermis=${desktopPermisVisible} inlineSpecii=${desktopSpeciiVisible} burger=${desktopBurgerVisible}`);
check(!desktopBurgerVisible, 'hamburger hidden on desktop');
check(desktopPermisVisible, 'inline Permis 2026 link visible on desktop');
check(desktopSpeciiVisible, 'inline Specii link visible on desktop');
check(!(await page.locator('[data-slot="sheet-content"]').isVisible().catch(() => false)), 'no sheet on desktop');

// desktop inline link still navigates
await dSpecii.click();
await page.waitForURL('**/specii', { timeout: 10000 });
check(page.url().includes('/specii'), `desktop inline Specii navigates (${page.url()})`);

await browser.close();
console.log(failures === 0 ? '\nMENU-MOBILE E2E PASSED' : `\nMENU-MOBILE E2E FAILED (${failures} checks)`);
process.exit(failures === 0 ? 0 : 1);
