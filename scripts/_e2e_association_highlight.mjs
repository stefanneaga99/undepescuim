/* eslint-disable no-console */
/**
 * t_b6a0e2fe association-highlight e2e. Selecting an association in the
 * search must:
 *   1. turn ALL its contracted waters bold bright-green (#22c55e) — rivers,
 *      lakes AND geometry-less sector slices (Pârâu Buzăul Mijlociu /
 *      Râul Buzăul superior);
 *   2. dim every other water to thin grey (#9ca3af);
 *   3. keep the click-focus orange working on top.
 * Tested associations: AJVPS Covasna, AJVPS BUZĂU (slug fix: 12 waters now),
 * Direcția Silvică Brașov (Buzăul superior sector slice), AJVPS TIMIȘ
 * (Lacul Dumbrăvița green polygon).
 *
 * Run: node scripts/_e2e_association_highlight.mjs [BASE_URL]
 */
import { chromium } from 'playwright';

const BASE = process.argv[2] || process.env.BASE_URL || 'http://localhost:3000';
const CDP = process.env.PLAYWRIGHT_CDP;

const browser = CDP
  ? await chromium.connectOverCDP(CDP)
  : await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });

let failures = 0;
const check = (cond, label) => {
  if (cond) console.log(`  PASS  ${label}`);
  else { console.log(`  FAIL  ${label}`); failures += 1; }
};

const COVERED = '#22c55e';
const UNCOVERED = '#9ca3af';
const NEUTRAL = '#3b82f6';
const ORANGE = '#f97316';

const countStroke = (color) =>
  page.evaluate((c) => {
    let n = 0;
    document.querySelectorAll('.leaflet-overlay-pane path').forEach((p) => {
      if ((p.getAttribute('stroke') || '').toLowerCase() === c) n += 1;
    });
    return n;
  }, color);

const countGreenPolygons = () =>
  page.evaluate(() => {
    let n = 0;
    document.querySelectorAll('.leaflet-overlay-pane path').forEach((p) => {
      if (
        (p.getAttribute('stroke') || '').toLowerCase() === '#22c55e' &&
        (p.getAttribute('d') || '').trim().endsWith('z')
      ) n += 1;
    });
    return n;
  });

/** Open the association search UI (mobile fullscreen icon or desktop inline
 * trigger — only ONE is visible depending on the breakpoint). */
const openSearch = async () => {
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

/** Select an association from the search UI. */
const selectAssociation = async (searchText, expectName) => {
  await openSearch();
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
      await page.waitForTimeout(900);
      return true;
    }
  }
  return false;
};

const clearAssociation = async () => {
  await openSearch();
  await page.waitForTimeout(400);
  const items = page.locator('[data-slot="command-item"]');
  const count = await items.count();
  for (let i = 0; i < count; i += 1) {
    const txt = (await items.nth(i).textContent()) || '';
    if (txt.includes('Toate asociațiile')) {
      await items.nth(i).click();
      await page.waitForTimeout(900);
      return true;
    }
  }
  return false;
};

/** Wait until at least `min` overlay paths carry the given stroke color. */
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

/** Click the midpoint of an on-screen path of `stroke` (best-effort; skips
 * paths outside the viewport). Returns true when a click landed. */
const clickGreen = async () => {
  const r = await page.evaluate(() => {
    const paths = [...document.querySelectorAll('.leaflet-overlay-pane path')].filter((p) => {
      if ((p.getAttribute('stroke') || '').toLowerCase() !== '#22c55e') return false;
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
  });
  if (!r) return false;
  await page.mouse.click(r.x, r.y);
  await page.waitForTimeout(1200);
  return true;
};

console.log(`== load ${BASE} ==`);
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('button:visible[aria-pressed]', { timeout: 90000 });
// waters.json is ~40 MB — wait for the overlay to actually render paths.
await page.waitForFunction(
  () => document.querySelectorAll('.leaflet-overlay-pane path').length > 0,
  { timeout: 60000 },
).catch(() => console.log('  warn: no overlay paths after load wait'));
await page.waitForTimeout(1500);

console.log('== baseline: no association selected ==');
const green0 = await countStroke(COVERED);
const blue0 = await countStroke(NEUTRAL);
console.log(`  green=${green0} blue=${blue0}`);
check(green0 === 0, `no green before selection (got ${green0})`);
check(blue0 > 0, `neutral blue rivers visible (got ${blue0})`);

console.log('== AJVPS Covasna → green rivers + dimmed others ==');
check(await selectAssociation('covasna', 'AJVPS Covasna'), 'selected AJVPS Covasna');
check(await waitForStrokeCount(COVERED, 1), 'green paths appeared after selection');
const greenC = await countStroke(COVERED);
const greyC = await countStroke(UNCOVERED);
console.log(`  green=${greenC} grey=${greyC}`);
check(greenC > 0, `Covasna waters highlighted green (got ${greenC})`);
check(greyC > 0, `other waters dimmed grey (got ${greyC})`);
await page.screenshot({ path: '.e2e/a_covasna.png' });

console.log('== click a green river → orange focus still works ==');
const clicked = await clickGreen();
console.log(`  clicked green: ${clicked}`);
if (clicked) {
  const orange = await countStroke(ORANGE);
  console.log(`  orange=${orange}`);
  check(orange > 0, `click focus orange appears over association green (got ${orange})`);
  await page.screenshot({ path: '.e2e/a_covasna_focus.png' });
}

console.log('== AJVPS BUZĂU → slug fix: 12 waters highlight, incl. Siriu lake ==');
check(await selectAssociation('buzau', 'AJVPS BUZĂU'), 'selected AJVPS BUZĂU');
check(await waitForStrokeCount(COVERED, 4), 'green paths appeared after selection');
const greenB = await countStroke(COVERED);
const greyB = await countStroke(UNCOVERED);
const greenPolyB = await countGreenPolygons();
console.log(`  green=${greenB} grey=${greyB} greenPolygons=${greenPolyB}`);
check(greenB >= 4, `Buzău rivers/sectors highlighted green (got ${greenB})`);
check(greenPolyB >= 1, `Lac acumulare Siriu green polygon present (got ${greenPolyB})`);
await page.screenshot({ path: '.e2e/a_buzau.png' });

console.log('== Direcția Silvică Brașov → Buzăul superior sector slice ==');
check(await selectAssociation('brasov', 'Direcția Silvică Brașov'), 'selected Direcția Silvică Brașov');
check(await waitForStrokeCount(COVERED, 3), 'green paths appeared after selection');
const greenBr = await countStroke(COVERED);
console.log(`  green=${greenBr}`);
check(greenBr >= 3, `D.S. Brașov waters + Buzăul superior sector green (got ${greenBr})`);
await page.screenshot({ path: '.e2e/a_brasov.png' });

console.log('== AJVPS TIMIȘ → Lacul Dumbrăvița green polygon ==');
check(await selectAssociation('timis', 'AJVPS TIMIȘ'), 'selected AJVPS TIMIȘ');
check(await waitForStrokeCount(COVERED, 1), 'green paths appeared after selection');
const greenT = await countStroke(COVERED);
const greenPolyT = await countGreenPolygons();
console.log(`  green=${greenT} greenPolygons=${greenPolyT}`);
check(greenT > 0, `Timiș waters highlighted green (got ${greenT})`);
check(greenPolyT >= 1, `Lacul Dumbrăvița green polygon present (got ${greenPolyT})`);
await page.screenshot({ path: '.e2e/a_timis.png' });

console.log('== clear selection → back to neutral ==');
check(await clearAssociation(), 'cleared association');
const greenEnd = await countStroke(COVERED);
console.log(`  green=${greenEnd}`);
check(greenEnd === 0, `no green after clearing (got ${greenEnd})`);

await browser.close();
console.log(failures === 0 ? 'E2E PASSED' : `E2E FAILED (${failures} checks)`);
process.exit(failures === 0 ? 0 : 1);
