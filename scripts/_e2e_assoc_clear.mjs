/* eslint-disable no-console */
/**
 * t_7a7192ea Bug 2 e2e: clicking a river/lake while an association filter is
 * active must CLEAR the association (and any county/type filter that would
 * hide the clicked water), then select + orange-highlight the clicked water
 * and show its detail card with the sector's association.
 *
 * Checks:
 *  1. select AJVPS BUZĂU → green highlight + grey dim appear
 *  2. click a green river (e.g. Râul Buzău sector) →
 *       - association cleared (no green left, trigger label back to
 *         'Caută asociația…')
 *       - orange click-focus appears
 *       - detail card shows the clicked water + its association
 *  3. select AJVPS Covasna → click an UNCONTRACTED teal river →
 *       - association cleared, teal water selected, orange focus on it,
 *         card shows 'Apă necontractată'
 *  4. county filter + association: county stays when the clicked water is
 *     inside it (only the association clears)
 *
 * Run: PLAYWRIGHT_CDP=http://localhost:3000 node scripts/_e2e_assoc_clear.mjs http://172.25.236.246:3100
 */
import { chromium } from 'playwright';

const BASE = process.argv[2] || process.env.BASE_URL || 'http://localhost:3000';
const CDP = process.env.PLAYWRIGHT_CDP;

const browser = CDP ? await chromium.connectOverCDP(CDP) : await chromium.launch();
// Close leftover pages from crashed runs (shared browserless window).
for (const ctx of browser.contexts()) {
  for (const p of ctx.pages()) {
    if (p.url() !== 'about:blank') await p.close().catch(() => {});
  }
}
const page = await browser.newPage();

let failures = 0;
const check = (cond, label) => {
  if (cond) console.log(`  PASS  ${label}`);
  else { console.log(`  FAIL  ${label}`); failures += 1; }
};
const COVERED = '#22c55e';
const UNCOVERED = '#9ca3af';
const ORANGE = '#f97316';
const TEAL = '#14b8a6';

const countStroke = (color) =>
  page.evaluate((c) => {
    let n = 0;
    document.querySelectorAll('.leaflet-overlay-pane path').forEach((p) => {
      if ((p.getAttribute('stroke') || '').toLowerCase() === c) n += 1;
    });
    return n;
  }, color);

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

const triggerText = () =>
  page.evaluate(() => {
    const t = document.querySelector('header button span.flex-1.truncate');
    return t ? t.textContent.trim() : '';
  });

const cardText = () =>
  page.evaluate(() => {
    const aside = document.querySelector('aside:has(h2)');
    const drawer = document.querySelector('[data-vaul-drawer]');
    const el = aside || drawer;
    return el ? (el.textContent || '').replace(/\s+/g, ' ').trim() : '';
  });

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

console.log(`== load ${BASE} ==`);
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('button:visible[aria-pressed]', { timeout: 90000 });
await page.waitForFunction(
  () => document.querySelectorAll('.leaflet-overlay-pane path').length > 0,
  { timeout: 60000 },
).catch(() => console.log('  warn: no overlay paths after load wait'));
await page.waitForTimeout(1500);

console.log('== 1. select AJVPS BUZĂU → green + grey ==');
check(await selectAssociation('buzau', 'AJVPS BUZĂU'), 'selected AJVPS BUZĂU');
check(await waitForStrokeCount(COVERED, 4), 'green paths appeared');
const greenBefore = await countStroke(COVERED);
const greyBefore = await countStroke(UNCOVERED);
console.log(`  green=${greenBefore} grey=${greyBefore}`);
check(greyBefore > 0, 'other waters dimmed grey');

console.log('== 2. click a green river → association filter clears ==');
check(await clickStroke(COVERED), 'clicked a green river');
const greenAfter = await countStroke(COVERED);
const greyAfter = await countStroke(UNCOVERED);
const orangeAfter = await countStroke(ORANGE);
console.log(`  green=${greenAfter} grey=${greyAfter} orange=${orangeAfter}`);
check(greenAfter === 0, `association cleared (no green left, got ${greenAfter})`);
check(greyAfter === 0, `no more dimmed waters (got ${greyAfter})`);
check(orangeAfter > 0, `orange click-focus appeared (got ${orangeAfter})`);
const trig = await triggerText();
console.log(`  trigger: "${trig}"`);
check(!trig.includes('AJVPS'), 'trigger back to placeholder (association deselected)');
const card = await cardText();
console.log(`  card: ${card.slice(0, 110)}`);
check(card.includes('Asociație'), 'detail card shows the association section');
await page.screenshot({ path: '.e2e/b2_cleared.png' });

console.log('== 3. select AJVPS Covasna → click an UNCONTRACTED teal river ==');
check(await selectAssociation('covasna', 'AJVPS Covasna'), 'selected AJVPS Covasna');
check(await waitForStrokeCount(COVERED, 1), 'green paths appeared');
check(await clickStroke(TEAL), 'clicked a teal uncontracted river');
const green3 = await countStroke(COVERED);
const orange3 = await countStroke(ORANGE);
const teal3 = await countStroke(TEAL);
console.log(`  green=${green3} orange=${orange3} teal=${teal3}`);
check(green3 === 0, `association cleared after teal click (got ${green3})`);
check(orange3 > 0, `orange focus on the uncontracted water (got ${orange3})`);
const card3 = await cardText();
console.log(`  card: ${card3.slice(0, 110)}`);
check(card3.includes('Apă necontractată'), 'card shows the uncontracted notice');
await page.screenshot({ path: '.e2e/b2_uncontracted.png' });

console.log('== 4. county filter preserved when clicked water is inside it ==');
// toggle a county chip (Buzău) — chips are in the filter bar
const countyChip = page.locator('button:visible[aria-pressed]').filter({ hasText: /^Buzău$/ });
if (await countyChip.count().catch(() => 0) > 0) {
  await countyChip.first().click();
  await page.waitForTimeout(800);
  const pressed = await page.evaluate(() => {
    const btn = [...document.querySelectorAll('button[aria-pressed]')].find((b) => (b.textContent || '').trim() === 'Buzău');
    return btn ? btn.getAttribute('aria-pressed') : null;
  });
  console.log(`  county chip pressed: ${pressed}`);
  check(pressed === 'true', 'county filter Buzău active');
  check(await selectAssociation('buzau', 'AJVPS BUZĂU'), 'selected AJVPS BUZĂU');
  check(await waitForStrokeCount(COVERED, 1), 'green paths under county filter');
  check(await clickStroke(COVERED), 'clicked a green river (in Buzău)');
  const green4 = await countStroke(COVERED);
  const pressedAfter = await page.evaluate(() => {
    const btn = [...document.querySelectorAll('button[aria-pressed]')].find((b) => (b.textContent || '').trim() === 'Buzău');
    return btn ? btn.getAttribute('aria-pressed') : null;
  });
  console.log(`  green=${green4} county still pressed: ${pressedAfter}`);
  check(green4 === 0, 'association cleared');
  check(pressedAfter === 'true', 'county filter preserved (clicked water inside it)');
} else {
  console.log('  skip: county chip not found');
}

await browser.close();
console.log(failures === 0 ? 'ASSOC-CLEAR E2E PASSED' : `ASSOC-CLEAR E2E FAILED (${failures} checks)`);
process.exit(failures === 0 ? 0 : 1);
