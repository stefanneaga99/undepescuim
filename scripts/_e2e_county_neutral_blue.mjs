/* eslint-disable no-console */
/**
 * Regression for t_14463aec — county-filter-only must visibly BLUE-emphasize
 * the county's waters (heavier neutral-blue), distinct from the unfiltered
 * default; association green, locality emphasis and click-focus orange must
 * still layer on top.
 *
 * Flows (desktop, county=Brașov):
 *  A. no filters   → neutral blue weight 2 (default)
 *  B. county only  → county waters are blue #3b82f6 with weight 4 (emphasized)
 *  C. county+assoc → covered member green; uncovered grey; else emphasized blue
 *  D. county+locality → still blue-emphasized
 *  E. county+click → clicked water orange (focus layered on top)
 */
import { chromium } from 'playwright';

const BASE = process.env.BASE_URL || process.argv[2] || 'http://localhost:3100';
const CDP = process.env.PLAYWRIGHT_CDP;

const browser = CDP
  ? await chromium.connectOverCDP(CDP)
  : await chromium.launch({ args: ['--no-sandbox'] });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

let failures = 0;
const check = (cond, label, extra = '') => {
  console.log(`  ${cond ? 'PASS' : 'FAIL'}  ${label}${extra ? `  [${extra}]` : ''}`);
  if (!cond) failures += 1;
};

// DOM-level color census (stroke attribute on rendered paths)
const overlayStats = (page) =>
  page.evaluate(() => {
    const paths = Array.from(document.querySelectorAll('.leaflet-overlay-pane path'));
    const strokes = paths.map((p) => p.getAttribute('stroke') || '').filter(Boolean);
    const count = (c) => strokes.filter((s) => s === c).length;
    return { total: paths.length, blue: count('#3b82f6'), green: count('#22c55e'), grey: count('#9ca3af'), orange: count('#f97316') };
  });

// Layer-level: all visible (opacity!==0) layers with color+weight for a given color
const layerColorCount = (page) =>
  page.evaluate(() => {
    const map = window.__UNDEPESCUIM_MAP__;
    if (!map) return { count: 0, weights: [] };
    const weights = [];
    for (const id in map._layers) {
      const ly = map._layers[id];
      if (ly.options?.opacity === 0) continue;
      if (ly.options?.color === '#3b82f6' && !ly.feature?.properties?._bboxFallback) {
        weights.push(ly.options?.weight);
      }
    }
    return { count: weights.length, weights };
  });

// probe a specific slug's visible layer colors
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

async function clearAssociation(page) {
  const searchBtn = page.locator('[data-testid="assoc-search"]').first();
  await searchBtn.click();
  await sleep(600);
  const clear = page.getByText('Toate asociațiile').first();
  if (await clear.isVisible().catch(() => false)) {
    await clear.click();
    await sleep(1500);
  }
}

async function toggleCounty(page, county) {
  const chip = page
    .locator('[data-testid="county-chip"]')
    .filter({ hasText: new RegExp(`^${county}$`) })
    .filter({ visible: true })
    .first();
  await chip.click();
  await sleep(2200);
}

async function pickLocality(page, locality) {
  // open locality popover, pick an item, close with Escape
  const btn = page
    .locator('[data-testid="locality-filter"]')
    .filter({ visible: true })
    .first();
  await btn.click();
  await sleep(800);
  const item = page.getByText(locality, { exact: true }).first();
  if (await item.isVisible().catch(() => false)) {
    await item.click();
    await sleep(1500);
  }
  await page.keyboard.press('Escape');
  await sleep(800);
}

const freshPage = async (w) => {
  for (const p of browser.contexts().flatMap((c) => c.pages())) {
    if (p.url() !== 'about:blank') await p.close();
  }
  const page = await browser.newPage({ viewport: { width: w, height: 800 } });
  await page.setViewportSize({ width: w, height: 800 });
  await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await page.waitForSelector('[data-testid="waters-drawn"]', { state: 'attached', timeout: 90000 });
  await sleep(3000);
  return page;
};

// ── A. no filters → default neutral blue weight 2 ──
{
  const page = await freshPage(1280);
  console.log('== A. no filters → neutral default (weight 2) ==');
  const { count, weights } = await layerColorCount(page);
  console.log('  neutral-blue layers (non-fallback):', count, 'weights:', JSON.stringify([...new Set(weights)]));
  check(count > 0, `neutral blue layers present (${count})`);
  check(weights.every((w) => w === 2), 'all neutral blue at default weight 2', JSON.stringify(weights));
  await page.close();
}

// ── B. county=Brașov only → emphasized blue weight 4 ──
{
  const page = await freshPage(1280);
  console.log('== B. county=Brașov only → emphasized blue (weight 4) ==');
  await toggleCounty(page, 'Brașov');
  const st = await overlayStats(page);
  console.log('  DOM:', JSON.stringify(st));
  check(st.blue > 0, `county waters BLUE (#3b82f6) → ${st.blue}`, `grey ${st.grey}`);
  check(st.grey === 0, 'no grey overriding (no association)', `grey ${st.grey}`);
  const { count, weights } = await layerColorCount(page);
  console.log('  neutral-blue layers:', count, 'weights:', JSON.stringify([...new Set(weights)]));
  check(count > 0, `emphasized blue layers present (${count})`);
  check(weights.length > 0 && weights.every((w) => w === 4), 'county water weight is 4 (emphasized, distinct from default 2)', JSON.stringify([...new Set(weights)]));
  await page.close();
}

// ── C. county + association → covered green on top; blue stays emphasized for others ──
{
  const page = await freshPage(1280);
  console.log('== C. county=Brașov + assoc=AVPS RUPEA → green covered, blue emphasized rest ==');
  await toggleCounty(page, 'Brașov');
  const ok = await selectAssociation(page, 'RUPEA');
  check(ok, 'select association AVPS RUPEA');
  const st = await overlayStats(page);
  console.log('  DOM:', JSON.stringify(st));
  check(st.green > 0, `covered waters GREEN (${st.green})`);
  const olt = await probeSlug(page, 'ehwpvgwh');
  console.log('  Râul Olt RUPEA (ehwpvgwh):', JSON.stringify(olt));
  check(olt && olt.some((l) => l.color === '#22c55e'), 'covered Râul Olt renders GREEN on top of county filter', JSON.stringify(olt));
  // blue emphasis should disappear once an association is active (uncovered grey)
  check(st.blue === 0, 'no emphasized blue when association active (uncovered → grey instead)', `blue ${st.blue}`);
  await page.close();
}

// ── D. county + locality → still blue-emphasized ──
{
  const page = await freshPage(1280);
  console.log('== D. county=Brașov + locality → still emphasized blue ==');
  await toggleCounty(page, 'Brașov');
  // pick any locality available in Brașov; try a likely one, tolerate absence
  await pickLocality(page, 'Brașov');
  const { count, weights } = await layerColorCount(page);
  const st = await overlayStats(page);
  console.log('  DOM:', JSON.stringify(st));
  console.log('  emphasized blue layers:', count, 'weights:', JSON.stringify([...new Set(weights)]));
  check(st.blue > 0, `blue emphasis persists under locality (${st.blue})`);
  check(weights.length > 0 && weights.every((w) => w === 4), 'locality-filtered county water still weight 4', JSON.stringify([...new Set(weights)]));
  await page.close();
}

// ── E. county + click → orange focus layered on top ──
{
  const page = await freshPage(1280);
  console.log('== E. county=Brașov + click a water → orange focus ==');
  await toggleCounty(page, 'Brașov');
  // Click a visible blue lake polygon near the map center & verify orange appears.
  const clickedSlug = await page.evaluate(() => {
    const map = window.__UNDEPESCUIM_MAP__;
    if (!map) return null;
    // find a visible blue lake polygon layer with real geometry
    for (const id in map._layers) {
      const ly = map._layers[id];
      if (ly.options?.opacity === 0) continue;
      const p = ly.feature?.properties;
      const g = ly.feature?.geometry;
      if (ly.options?.color === '#3b82f6' && p?.slug && g && g.type === 'Polygon') return p.slug;
    }
    return null;
  });
  console.log('  candidate lake slug:', clickedSlug);
  if (clickedSlug) {
    await page.evaluate((slug) => {
      const map = window.__UNDEPESCUIM_MAP__;
      for (const id in map._layers) {
        const ly = map._layers[id];
        if (ly.feature?.properties?.slug === slug && ly.options?.opacity !== 0) {
          const rr = ly.getBounds ? ly.getBounds() : null;
          if (rr) {
            const c = rr.getCenter();
            const pt = map.latLngToContainerPoint(c);
            const rect = document.querySelector('.leaflet-container').getBoundingClientRect();
            const el = document.elementFromPoint(rect.left + pt.x, rect.top + pt.y);
            if (el) {
              const target = el.closest('path, circle, rect');
              if (target) target.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: rect.left + pt.x, clientY: rect.top + pt.y }));
            }
          }
          return;
        }
      }
    }, clickedSlug);
    await sleep(2000);
  } else {
    console.log('  no blue lake polygon found to click — asserting only qualifiers');
  }
  const st = await overlayStats(page);
  console.log('  DOM after click:', JSON.stringify(st));
  // A click arms the orange click-focus on the selected water; assert the
  // orange emphasis appears (layered on top of the blue), and the other
  // county waters keep their blue emphasis.
  check(st.orange > 0, 'click produces ORANGE focus layered on top', `orange ${st.orange}`);
  check(st.blue > 0, 'non-clicked county waters stay blue-emphasized', `blue ${st.blue}`);
  await page.close();
}

await browser.close();
console.log(failures === 0 ? '\nALL CHECKS PASSED' : `\n${failures} CHECKS FAILED`);
process.exit(failures === 0 ? 0 : 1);
