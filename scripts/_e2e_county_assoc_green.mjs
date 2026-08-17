/* eslint-disable no-console */
/**
 * Regression for t_e66e5898 — county filter must keep visual emphasis on the
 * county's waters, and association highlight must still work on top.
 *
 * Reported: filtering by county made the county's waters lose their blue
 * emphasis (grey instead). Root cause (found on investigation): under a county
 * filter a COVERED multi-contract member WITH geometry (e.g. Râul Jiu / AJVPS
 * GORJ, or Râul Olt / AVPS RUPEA Brașov) rendered GREY instead of GREEN — the
 * t_5f5f2cce multi-contract-member guard neutralized its color even though the
 * rendered geometry is already the per-county clip (which is exactly the
 * county's sector), and the green covered-slices layer is skipped under a
 * county filter. The guard now only applies in the unfiltered (national)
 * view where the full shared course would leak into other counties.
 *
 * Flow (desktop): select association → county → the covered member's clip must
 * render green; changing locality keeps it green; blue others stay blue.
 */
import { chromium } from 'playwright';

const BASE = process.env.BASE_URL || process.argv[2] || 'http://localhost:3100';
const CDP = process.env.PLAYWRIGHT_CDP;

const browser = CDP
  ? await chromium.connectOverCDP(CDP)
  : await chromium.launch({ args: ['--no-sandbox'] });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function freshPage(browser, width) {
  return browser.newPage({ viewport: { width, height: 800 } });
}

let failures = 0;
const check = (cond, label, extra = '') => {
  console.log(`  ${cond ? 'PASS' : 'FAIL'}  ${label}${extra ? `  [${extra}]` : ''}`);
  if (!cond) failures += 1;
};

const overlayStats = (page) =>
  page.evaluate(() => {
    const paths = Array.from(document.querySelectorAll('.leaflet-overlay-pane path'));
    const strokes = paths.map((p) => p.getAttribute('stroke') || '').filter(Boolean);
    const count = (c) => strokes.filter((s) => s === c).length;
    return {
      total: paths.length,
      blue: count('#3b82f6'),
      green: count('#22c55e') + count('#22c55e') * 0, // green = #22c55e (all weights)
      grey: count('#9ca3af'),
    };
  });

// probe a specific slug's visible layer color via the map bridge
const probeSlug = (page, slug) =>
  page.evaluate((s) => {
    const map = window.__UNDEPESCUIM_MAP__;
    if (!map) return null;
    const out = [];
    for (const id in map._layers) {
      const ly = map._layers[id];
      if (ly.feature && ly.feature.properties?.slug === s && ly.options?.opacity !== 0) {
        out.push({ color: ly.options?.color, weight: ly.options?.weight });
      }
    }
    return out;
  }, slug);

async function selectAssociation(page, term) {
  const searchBtn = page.locator('[data-testid="assoc-search"]').first();
  await searchBtn.click();
  await sleep(600);
  await page
    .locator('[data-testid="assoc-search"] input, [data-slot="command-input"], input[placeholder*="Caută"]')
    .first()
    .fill(term);
  await sleep(800);
  const opt = page.locator('[data-testid="assoc-option"]').filter({ hasText: new RegExp(term, 'i') }).first();
  if (await opt.isVisible().catch(() => false)) {
    await opt.click();
    await sleep(2000);
    return true;
  }
  return false;
}

async function toggleCounty(page, county) {
  const chip = page
    .locator('[data-testid="county-chip"]')
    .filter({ hasText: new RegExp(`^${county}$`) })
    .filter({ visible: true })
    .first();
  await chip.click();
  await sleep(2000);
}

// ── Pass A: county=Gorj + assoc=AJVPS GORJ → covered Jiu owner (qrjybswm) green ──
{
  for (const p of browser.contexts().flatMap((c) => c.pages())) {
    if (p.url() !== 'about:blank') await p.close();
  }
  const page = await freshPage(browser, 1280);
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await page.waitForSelector('[data-testid="waters-drawn"]', { state: 'attached', timeout: 90000 });
  await sleep(3000);

  console.log('== A. county=Gorj + assoc=AJVPS GORJ (Râul Jiu owner must be GREEN) ==');
  const ok = await selectAssociation(page, 'GORJ');
  check(ok, 'select association AJVPS GORJ');
  await toggleCounty(page, 'Gorj');
  const st = await overlayStats(page);
  console.log('  colors:', JSON.stringify(st));
  const jiu = await probeSlug(page, 'qrjybswm');
  console.log('  Râul Jiu (qrjybswm) layers:', JSON.stringify(jiu));
  const jiuGreen = jiu ? jiu.some((l) => l.color === '#22c55e') : false;
  check(jiuGreen, 'covered Râul Jiu renders GREEN under county+assoc', JSON.stringify(jiu));
  await page.close();
}

// ── Pass B: county=Brașov alone → waters BLUE (county emphasis) ──
{
  for (const p of browser.contexts().flatMap((c) => c.pages())) {
    if (p.url() !== 'about:blank') await p.close();
  }
  const page = await freshPage(browser, 1280);
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await page.waitForSelector('[data-testid="waters-drawn"]', { state: 'attached', timeout: 90000 });
  await sleep(3000);

  console.log('== B. county=Brașov alone → blue emphasis ==');
  await toggleCounty(page, 'Brașov');
  const st = await overlayStats(page);
  console.log('  colors:', JSON.stringify(st));
  check(st.blue > 0, `county waters are BLUE (${st.blue})`);
  check(st.grey <= st.blue, `no grey overriding blue (grey ${st.grey} vs blue ${st.blue})`);
  await page.close();
}

// ── Pass C: county=Brașov + assoc=AVPS RUPEA (covered Olt member with geometry) green ──
{
  for (const p of browser.contexts().flatMap((c) => c.pages())) {
    if (p.url() !== 'about:blank') await p.close();
  }
  const page = await freshPage(browser, 1280);
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await page.waitForSelector('[data-testid="waters-drawn"]', { state: 'attached', timeout: 90000 });
  await sleep(3000);

  console.log('== C. county=Brașov + assoc=AVPS RUPEA (covered Olt member ehwpvgwh) ==');
  const ok = await selectAssociation(page, 'RUPEA');
  check(ok, 'select association AVPS RUPEA');
  await toggleCounty(page, 'Brașov');
  const st = await overlayStats(page);
  console.log('  colors:', JSON.stringify(st));
  const olt = await probeSlug(page, 'ehwpvgwh');
  console.log('  Râul Olt RUPEA (ehwpvgwh) layers:', JSON.stringify(olt));
  const oltGreen = olt ? olt.some((l) => l.color === '#22c55e') : false;
  check(oltGreen, 'covered Râul Olt (RUPEA) renders GREEN under county+assoc', JSON.stringify(olt));
  await page.close();
}

await browser.close();
console.log(failures === 0 ? '\nALL CHECKS PASSED' : `\n${failures} CHECKS FAILED`);
process.exit(failures === 0 ? 0 : 1);