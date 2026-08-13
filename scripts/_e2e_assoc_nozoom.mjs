/* eslint-disable no-console */
/**
 * t_abccfd6c e2e: clicking a river of the SELECTED association must NOT
 * zoom the map out — the map stays put and the detail card opens; the
 * association filter stays active (coverage keeps highlighting its waters).
 * Clicking a water OUTSIDE the association still clears the filter
 * (t_7a7192ea behavior) and may zoom out — acceptable there.
 *
 * Runs BOTH viewports (desktop 1280px and mobile 390px) through the same
 * assertions, using setViewportSize (the browserless CDP window honours it).
 *
 * Known environment flake (t_abccfd6c): the browserless container shares ONE
 * window, and concurrent consumers can resize it mid-run (innerWidth jumps
 * 800→1280), which makes Playwright click against a stale layout ("html
 * intercepts pointer events"). Every pass therefore FORCES the viewport back
 * with settleViewport() before loading and before each interaction.
 *
 * Checks per pass:
 *  1. select AJVPS BUZĂU → flyTo bbox (zoom 9) + green/grey highlight
 *  2. click a GREEN river → map zoom UNCHANGED (no zoom-out), association
 *     kept (green stays), orange click-focus appears, card opens
 *  3. select AJVPS Covasna → click an UNCONTRACTED teal river → association
 *     clears (green gone), card shows 'Apă necontractată'
 *
 * Run: PLAYWRIGHT_CDP=http://localhost:3000 node scripts/_e2e_assoc_nozoom.mjs http://172.25.236.246:3100
 */
import { chromium } from 'playwright';

const BASE = process.argv[2] || process.env.BASE_URL || 'http://localhost:3000';
const CDP = process.env.PLAYWRIGHT_CDP;

const browser = CDP ? await chromium.connectOverCDP(CDP) : await chromium.launch();
// The page is swapped per pass (fresh page at the pass's viewport — the
// established recipe for the shared browserless window).
let page = await browser.newPage();

let failures = 0;
const check = (cond, label) => {
  if (cond) console.log(`  PASS  ${label}`);
  else { console.log(`  FAIL  ${label}`); failures += 1; }
};
const COVERED = '#22c55e';
const ORANGE = '#f97316';
const TEAL = '#14b8a6';

// Force the shared browserless window back to the pass's viewport. The window
// is shared with concurrent consumers that can resize it mid-run, so verify
// innerWidth actually stuck before proceeding.
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

const countStroke = (color) =>
  page.evaluate((c) => {
    let n = 0;
    document.querySelectorAll('.leaflet-overlay-pane path').forEach((p) => {
      if ((p.getAttribute('stroke') || '').toLowerCase() === c) n += 1;
    });
    return n;
  }, color);

const waitForStrokeCount = async (color, min, timeout = 20000) => {
  try {
    await page.waitForFunction(
      ({ c, m }) =>
        [...document.querySelectorAll('.leaflet-overlay-pane path')].filter(
          (p) => (p.getAttribute('stroke') || '').toLowerCase() === c,
        ).length >= m,
      { c: color, m: min },
      { timeout },
    );
    return true;
  } catch {
    return false;
  }
};

// Current map zoom, read from the tile URLs (z/x/y in the src). DPR-agnostic
// for COMPARISONS (before vs after a click at the same view) — the tile z
// moves with the map zoom, so equality means the map did not zoom.
const mapZoom = () =>
  page.evaluate(() => {
    const zs = [...document.querySelectorAll('.leaflet-tile')]
      .map((t) => (t.getAttribute('src') || '').match(/\/(\d+)\/\d+\/\d+(?:@2x)?\.png/)?.[1])
      .filter(Boolean)
      .map(Number);
    if (!zs.length) return null;
    // mode: at rest all tiles share one z (animation leftovers are fewer)
    const counts = new Map();
    zs.forEach((z) => counts.set(z, (counts.get(z) || 0) + 1));
    return [...counts.entries()].sort((a, b) => b[1] - a[1])[0][0];
  });

const openSearch = async (expectedWidth) => {
  // Shared-window flake guard: re-force the viewport if it drifted.
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

const selectAssociation = async (searchText, expectName, expectedWidth) => {
  await openSearch(expectedWidth);
  await page.waitForTimeout(400);
  const input = page.locator('[data-slot="command-input"]');
  await input.fill(searchText);
  await page.waitForTimeout(500);
  const items = page.locator('[data-slot="command-item"]');
  const count = await items.count();
  for (let i = 0; i < count; i += 1) {
    const txt = (await items.nth(i).textContent()) || '';
    if (txt.includes(expectName)) {
      await items.nth(i).click();
      // flyTo animation (0.8s) + overlay close — let it settle
      await page.waitForTimeout(1400);
      return true;
    }
  }
  return false;
};

/** Click the midpoint of an on-screen path of `stroke` (best-effort). */
const clickStroke = async (stroke) => {
  const r = await page.evaluate((c) => {
    const paths = [...document.querySelectorAll('.leaflet-overlay-pane path')].filter((p) => {
      if ((p.getAttribute('stroke') || '').toLowerCase() !== c) return false;
      const b = p.getBoundingClientRect();
      return b.right > 0 && b.bottom > 0 && b.left < window.innerWidth && b.top < window.innerHeight && b.width * b.height > 0;
    });
    for (const p of paths) {
      const len = p.getTotalLength();
      for (const frac of [0.3, 0.5, 0.7]) {
        const pt = p.getPointAtLength(len * frac);
        const m = p.ownerSVGElement.getScreenCTM();
        const sp = new DOMPoint(pt.x, pt.y).matrixTransform(m);
        if (sp.x < 0 || sp.x > window.innerWidth || sp.y < 0 || sp.y > window.innerHeight) continue;
        const top = document.elementFromPoint(sp.x, sp.y);
        if (top === p || (top && top.getAttribute('stroke') === p.getAttribute('stroke'))) {
          return { x: sp.x, y: sp.y };
        }
      }
    }
    return null;
  }, stroke);
  if (!r) return false;
  await page.mouse.click(r.x, r.y);
  await page.waitForTimeout(1200);
  return true;
};

const cardText = () =>
  page.evaluate(() => {
    const aside = document.querySelector('aside:has(h2)');
    const drawer = document.querySelector('[data-vaul-drawer]');
    const el = aside || drawer;
    return el ? (el.textContent || '').replace(/\s+/g, ' ').trim() : '';
  });

const waitForCardText = async (timeout = 12000) => {
  try {
    await page.waitForFunction(
      () => {
        const aside = document.querySelector('aside:has(h2)');
        const drawer = document.querySelector('[data-vaul-drawer]');
        const el = aside || drawer;
        return !!el && (el.textContent || '').trim().length > 10;
      },
      { timeout },
    );
    return true;
  } catch {
    return false;
  }
};

// Close any open detail card first: the vaul bottom sheet sets
// pointer-events:none on body and its full-height container covers the
// header, so the search icon/trigger is untappable while a card is open
// (a real mobile user closes the card before switching association).
const closeCardIfOpen = async () => {
  const open = await page.evaluate(
    () => !!document.querySelector('[data-vaul-drawer]') || !!document.querySelector('aside:has(h2)'),
  );
  if (open) {
    await page.keyboard.press('Escape');
    await page.waitForTimeout(500);
  }
};

// Whether the SELECTED uncontracted water should be rendered at zoom `z`
// (LOD: z<8 → ≥30km rivers / ≥100ha lakes, z<10 → ≥10km / ≥10ha, else all).
// After a non-association click the map may zoom OUT to the national view
// (accepted t_abccfd6c behavior), which culls short rivers — the orange
// focus then legitimately cannot render. Returns the river name + flag.
const selectedWaterRenderable = (z) =>
  page.evaluate(async (zoom) => {
    const aside = document.querySelector('aside:has(h2)');
    const drawer = document.querySelector('[data-vaul-drawer]');
    const el = aside || drawer;
    // The water name is the bold h2 in WaterDetailCard (the aside's own
    // header h2 is 'Detalii apă').
    const name = (
      el?.querySelector('h2.font-bold')?.textContent ||
      el?.querySelector('h2')?.textContent ||
      ''
    ).trim();
    if (!name) return { name, renderable: false, lenKm: null };
    const [rivers, lakes] = await Promise.all([
      fetch('/data/uncontracted_rivers.json').then((r) => r.json()),
      fetch('/data/uncontracted_lakes.json').then((r) => r.json()),
    ]);
    const w = rivers.find((x) => x.name === name) || lakes.find((x) => x.name === name);
    const len = w ? w.lengthKm ?? 0 : 0;
    const area = w ? w.areaHa ?? 0 : 0;
    const minLen = zoom < 8 ? 30 : zoom < 10 ? 10 : 0;
    const minArea = zoom < 8 ? 100 : zoom < 10 ? 10 : 0;
    const renderable = !!w && (len >= minLen || area >= minArea);
    return { name, renderable, lenKm: len };
  }, z);

async function runPass(label, isMobile, expectedWidth) {
  console.log(`\n========== ${label} (innerWidth=${await page.evaluate(() => window.innerWidth)}) ==========`);

  console.log('== 1. select AJVPS BUZĂU → flyTo + green/grey highlight ==');
  check(await selectAssociation('buzau', 'AJVPS BUZĂU', expectedWidth), 'selected AJVPS BUZĂU');
  check(await waitForStrokeCount(COVERED, isMobile ? 1 : 4), 'green paths appeared');
  const greenBefore = await countStroke(COVERED);
  const zoomAfterSelect = await mapZoom();
  console.log(`  green=${greenBefore} zoom after select=${zoomAfterSelect}`);
  check(zoomAfterSelect !== null && zoomAfterSelect >= 8, `map flew to the association view (zoom ${zoomAfterSelect})`);

  console.log('== 2. click a GREEN river → no zoom-out, association kept, card opens ==');
  const zoomBeforeClick = await mapZoom();
  check(await clickStroke(COVERED), 'clicked a green river');
  check(await waitForCardText(), 'detail card opened');
  const greenAfter = await countStroke(COVERED);
  const orangeAfter = await countStroke(ORANGE);
  const zoomAfterClick = await mapZoom();
  console.log(`  green=${greenAfter} orange=${orangeAfter} zoom ${zoomBeforeClick} → ${zoomAfterClick}`);
  check(greenAfter > 0, `association kept (green still highlighted, got ${greenAfter})`);
  check(orangeAfter > 0, `orange click-focus appeared (got ${orangeAfter})`);
  check(zoomAfterClick === zoomBeforeClick, `map zoom UNCHANGED after covered click (${zoomBeforeClick} → ${zoomAfterClick})`);
  const card = await cardText();
  console.log(`  card: ${card.slice(0, 110)}`);
  check(card.includes('Asociație'), 'card shows the association section');
  await page.screenshot({ path: `.e2e/nozoom_${isMobile ? 'mobile' : 'desktop'}_kept.png` });

  console.log('== 3. select AJVPS Covasna → click UNCONTRACTED teal → association clears ==');
  await closeCardIfOpen();
  check(await selectAssociation('covasna', 'AJVPS Covasna', expectedWidth), 'selected AJVPS Covasna');
  check(await waitForStrokeCount(COVERED, 1), 'green paths appeared (Covasna)');
  const zoomBeforeTeal = await mapZoom();
  check(await clickStroke(TEAL), 'clicked a teal uncontracted river');
  await page.waitForTimeout(600); // let the clear + optional flyTo settle
  const green3 = await countStroke(COVERED);
  const orange3 = await countStroke(ORANGE);
  const zoomAfterTeal = await mapZoom();
  const sel3 = await selectedWaterRenderable(zoomAfterTeal);
  console.log(`  green=${green3} orange=${orange3} zoom ${zoomBeforeTeal} → ${zoomAfterTeal} sel=${sel3.name} (${sel3.lenKm ?? '?'}km, renderable@z${zoomAfterTeal}=${sel3.renderable})`);
  check(green3 === 0, `association cleared after teal click (got ${green3})`);
  // Orange focus only when the clicked water survives the post-clear LOD cull
  // (the map zooms to the national view on clear — accepted for non-association
  // clicks); when it SHOULD render, orange is mandatory.
  check(!sel3.renderable || orange3 > 0, `orange focus on the uncontracted water (got ${orange3})`);
  const card3 = await cardText();
  console.log(`  card: ${card3.slice(0, 110)}`);
  check(card3.includes('Apă necontractată'), 'card shows the uncontracted notice');
  await page.screenshot({ path: `.e2e/nozoom_${isMobile ? 'mobile' : 'desktop'}_cleared.png` });
}

async function loadApp() {
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('button:visible[aria-pressed]', { timeout: 90000 });
  await page.waitForFunction(
    () => document.querySelectorAll('.leaflet-overlay-pane path').length > 0,
    { timeout: 60000 },
  ).catch(() => console.log('  warn: no overlay paths after load wait'));
  await page.waitForTimeout(1500);
}

// Fresh page at the pass's viewport, then load the app. Closing leftovers
// first: the browserless container shares ONE window, so a leftover page from
// a crashed run pins the window width and a reused page keeps stale layout.
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
    console.log(`  warn: viewport ${w}x${h} not honored (got ${iw}) — retry with fresh page`);
    await page.close().catch(() => {});
    page = null;
    return freshPage(w, h);
  }
  return page;
}

// ---- desktop pass (1280px: true desktop branch — right aside panel) ----
await freshPage(1280, 800);
await runPass('DESKTOP PASS', false, 1280);

// ---- mobile pass (390px: real mobile branch — vaul bottom sheet) ----
await freshPage(390, 844);
await runPass('MOBILE PASS', true, 390);

await browser.close();
console.log(failures === 0 ? '\nASSOC-NOZOOM E2E PASSED' : `\nASSOC-NOZOOM E2E FAILED (${failures} checks)`);
process.exit(failures === 0 ? 0 : 1);
