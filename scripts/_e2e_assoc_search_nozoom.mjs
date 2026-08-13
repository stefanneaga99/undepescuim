/* eslint-disable no-console */
/**
 * t_d987cdb7 e2e: association SEARCH must not zoom the map on focus/typing
 * (mobile), and a CONFIRMED selection must fly at a SANE zoom (fitBounds +
 * padding, capped at 12) — never an over-zoomed landing.
 *
 * Root cause of the iPhone report: iOS Safari auto-zooms the WHOLE PAGE on
 * focus of any input with font-size < 16px. The association CommandInput was
 * text-sm (14px) → tapping the search field page-zoomed the map ~2x and it
 * stayed zoomed after searching. Guard: the input must render at 16px.
 *
 * Checks per pass (mobile 390px + desktop 1280px):
 *  1. command-input computed font-size === 16px (iOS auto-zoom guard)
 *  2. open search (tap icon / click trigger) → map zoom UNCHANGED
 *  3. type "buzau" → map zoom UNCHANGED (typing must never zoom)
 *  4. select AJVPS BUZĂU (confirmed tap) → map zoom CHANGED to a moderate
 *     value 7..12 (fitBounds with padding; bbox:null assocs don't move) +
 *     green coverage appears
 *
 * Run: PLAYWRIGHT_CDP=http://localhost:3000 node scripts/_e2e_assoc_search_nozoom.mjs http://172.25.236.246:3100
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
const COVERED = '#22c55e';

// Force the shared browserless window back to the pass's viewport (the
// window is shared with concurrent consumers that can resize it mid-run).
const settleViewport = async (w, h) => {
  for (let i = 0; i < 8; i += 1) {
    await page.setViewportSize({ width: w, height: h }).catch(() => {});
    await page.waitForTimeout(200);
    const iw = await page.evaluate(() => window.innerWidth).catch(() => 0);
    if (iw === w) return true;
  }
  return false;
};

const countStroke = (color) =>
  page.evaluate((c) => {
    let n = 0;
    document.querySelectorAll('.leaflet-overlay-pane path').forEach((p) => {
      if ((p.getAttribute('stroke') || '').toLowerCase() === c) n += 1;
    });
    return n;
  }, color);

// Current map zoom from the tile URLs (z/x/y). Mode of all tiles — at rest
// they share one z, so equality means the map did NOT zoom.
const mapZoom = () =>
  page.evaluate(() => {
    const zs = [...document.querySelectorAll('.leaflet-tile')]
      .map((t) => (t.getAttribute('src') || '').match(/\/(\d+)\/\d+\/\d+(?:@2x)?\.png/)?.[1])
      .filter(Boolean)
      .map(Number);
    if (!zs.length) return null;
    const counts = new Map();
    zs.forEach((z) => counts.set(z, (counts.get(z) || 0) + 1));
    return [...counts.entries()].sort((a, b) => b[1] - a[1])[0][0];
  });

// The association search input's computed font-size. iOS Safari auto-zooms
// the page on focus of any input < 16px — this is the regression guard.
const inputFontSize = () =>
  page.evaluate(() => {
    const el = document.querySelector('[data-slot="command-input"]');
    return el ? getComputedStyle(el).fontSize : null;
  });

const openSearch = async (expectedWidth) => {
  const iw = await page.evaluate(() => window.innerWidth).catch(() => 0);
  if (iw !== expectedWidth) {
    await settleViewport(expectedWidth, expectedWidth === 390 ? 844 : 800);
    await page.waitForTimeout(300);
  }
  const icon = page.locator('[aria-label="Caută asociația"]');
  if (await icon.isVisible().catch(() => false)) {
    await icon.click();
    return;
  }
  await page
    .locator('header button:visible')
    .filter({ has: page.locator('svg.lucide-search') })
    .first()
    .click();
};

const selectAssociation = async (searchText, expectName) => {
  const input = page.locator('[data-slot="command-input"]');
  await input.fill(searchText);
  await page.waitForTimeout(500);
  const items = page.locator('[data-slot="command-item"]');
  const count = await items.count();
  for (let i = 0; i < count; i += 1) {
    const txt = (await items.nth(i).textContent()) || '';
    if (txt.includes(expectName)) {
      await items.nth(i).click();
      // fitBounds animation (0.8s) + overlay close + tile reload — let settle
      await page.waitForTimeout(2000);
      return true;
    }
  }
  return false;
};

async function loadApp() {
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('button:visible[aria-pressed]', { timeout: 90000 });
  await page.waitForFunction(
    () => document.querySelectorAll('.leaflet-overlay-pane path').length > 0,
    { timeout: 60000 },
  ).catch(() => console.log('  warn: no overlay paths after load wait'));
  await page.waitForTimeout(1500);
}

async function freshPage(w, h) {
  for (const ctx of browser.contexts()) {
    for (const p of ctx.pages()) {
      if (p !== page && p.url() !== 'about:blank') await p.close().catch(() => {});
    }
  }
  const pg = await browser.newPage();
  await pg.setViewportSize({ width: w, height: h });
  page = pg;
  await loadApp();
  const iw = await page.evaluate(() => window.innerWidth).catch(() => 0);
  if (iw !== w) {
    console.log(`  warn: viewport ${w}x${h} not honored (got ${iw}) — retry`);
    await page.close().catch(() => {});
    page = null;
    return freshPage(w, h);
  }
  return page;
}

async function runPass(label, expectedWidth) {
  console.log(`\n========== ${label} (innerWidth=${await page.evaluate(() => window.innerWidth)}) ==========`);

  const zoomBeforeOpen = await mapZoom();
  console.log(`  initial map zoom=${zoomBeforeOpen}`);

  console.log('== 1. iOS auto-zoom guard: search input font-size >= 16px ==');
  await openSearch(expectedWidth);
  await page.waitForTimeout(500);
  const fs = await inputFontSize();
  console.log(`  command-input font-size: ${fs}`);
  check(fs === '16px' || (fs !== null && parseFloat(fs) >= 16), `search input renders >= 16px (got ${fs})`);

  console.log('== 2. opening search must NOT zoom the map ==');
  const zoomAfterOpen = await mapZoom();
  console.log(`  zoom ${zoomBeforeOpen} → ${zoomAfterOpen}`);
  check(zoomAfterOpen === zoomBeforeOpen, `map zoom UNCHANGED after opening search (${zoomBeforeOpen} → ${zoomAfterOpen})`);

  console.log('== 3. typing must NOT zoom the map ==');
  const input = page.locator('[data-slot="command-input"]');
  await input.fill('buzau');
  await page.waitForTimeout(700);
  const zoomAfterType = await mapZoom();
  console.log(`  zoom ${zoomAfterOpen} → ${zoomAfterType}`);
  check(zoomAfterType === zoomAfterOpen, `map zoom UNCHANGED while typing (${zoomAfterOpen} → ${zoomAfterType})`);

  console.log('== 4. confirmed selection flies at a sane zoom (fitBounds, <= 12) ==');
  check(await selectAssociation('buzau', 'AJVPS BUZĂU'), 'selected AJVPS BUZĂU');
  const zoomAfterSelect = await mapZoom();
  const green = await countStroke(COVERED);
  console.log(`  zoom after select=${zoomAfterSelect} green=${green}`);
  check(zoomAfterSelect !== null && zoomAfterSelect >= 7 && zoomAfterSelect <= 12,
    `selection flew to moderate zoom ${zoomAfterSelect} (7..12, capped)`);
  check(zoomAfterSelect !== zoomAfterType, `selection changed the zoom (${zoomAfterType} → ${zoomAfterSelect})`);
  check(green > 0, `map highlighted association waters green (got ${green})`);
  await page.screenshot({ path: `.e2e/search_nozoom_${expectedWidth === 390 ? 'mobile' : 'desktop'}.png` });

  // Close the search if still open (it should have closed on selection).
}

// ---- mobile pass (390px: real mobile branch — icon + fullscreen overlay) ----
await freshPage(390, 844);
await runPass('MOBILE PASS', 390);

// ---- desktop pass (1280px: inline trigger + dropdown) ----
await freshPage(1280, 800);
await runPass('DESKTOP PASS', 1280);

await browser.close();
console.log(failures === 0 ? '\nASSOC-SEARCH-NOZOOM E2E PASSED' : `\nASSOC-SEARCH-NOZOOM E2E FAILED (${failures} checks)`);
process.exit(failures === 0 ? 0 : 1);
