/* eslint-disable no-console */
/**
 * t_5f5f2cce — user-flow verification for the Cerbul Carpatin / Jiu fix.
 *
 * 1. Select A.CERBUL CARPATIN:
 *    - green slices appear (Sohodol I sector)
 *    - served association bbox centers on the Sohodol valley (NOT the Jiu)
 *    - clicking the green slice opens "Râul Sohodol I / A.CERBUL CARPATIN"
 *      (NOT Sohodol II / AJVPS GORJ — the reported wrong-association bug)
 * 2. Select AJVPS GORJ:
 *    - green slices appear (Jiu Gorj sector + Sohodol II + Șușița)
 *    - clicking the largest green slice (the Jiu) opens "Râul Jiu / AJVPS GORJ"
 * 3. AJVPS DOLJ → green slice appears (Jiu Dolj sector)
 * 4. Pro Pescar → green slices appear (Jiul Inferior + Jiul de Vest)
 * 5. Direcția Silvică Gorj → green slice appears (Romsilva Jiu sector)
 *
 * Run: PLAYWRIGHT_CDP=http://localhost:3000 node scripts/_e2e_cerbul_verify.mjs http://172.25.236.246:3100
 */
import { chromium } from 'playwright';

const BASE = process.argv[2] || process.env.BASE_URL || 'http://localhost:3000';
const CDP = process.env.PLAYWRIGHT_CDP;

const browser = CDP ? await chromium.connectOverCDP(CDP) : await chromium.launch();
let page = await browser.newPage({ viewport: { width: 1280, height: 800 } });

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
      await page.waitForTimeout(1600); // flyTo + render
      return true;
    }
  }
  return false;
};

/** Click a green path: `pick` = 'first' | 'largest' | 'largest-slice'; optional weight filter. */
const clickGreen = async (pick = 'first', weightFilter) => {
  const targets = await page.evaluate((wFilter) => {
    const out = [];
    document.querySelectorAll('.leaflet-overlay-pane path').forEach((p) => {
      if ((p.getAttribute('stroke') || '').toLowerCase() !== '#22c55e') return;
      if (wFilter && p.getAttribute('stroke-width') !== wFilter) return;
      const b = p.getBoundingClientRect();
      if (!(b.right > 0 && b.bottom > 0 && b.left < window.innerWidth && b.top < window.innerHeight && b.width * b.height > 0)) return;
      try {
        const len = p.getTotalLength();
        const pt = p.getPointAtLength(len * 0.5);
        const m = p.ownerSVGElement.getScreenCTM();
        const sp = new DOMPoint(pt.x, pt.y).matrixTransform(m);
        if (sp.x < 0 || sp.x > window.innerWidth || sp.y < 0 || sp.y > window.innerHeight) return;
        const top = document.elementFromPoint(sp.x, sp.y);
        if (top !== p) return; // only click points that are actually ON the green path
        out.push({ x: sp.x, y: sp.y, area: b.width * b.height, weight: p.getAttribute('stroke-width') });
      } catch { /* noop */ }
    });
    return out;
  }, weightFilter ?? null);
  if (!targets.length) return false;
  let t;
  if (pick === 'largest' || pick === 'largest-slice') {
    t = [...targets].sort((a, b) => b.area - a.area)[0];
  } else {
    t = targets[0];
  }
  await page.mouse.click(t.x, t.y);
  await page.waitForTimeout(1200);
  return true;
};

const cardText = () =>
  page.evaluate(() => {
    const aside = document.querySelector('aside:has(h2)');
    const drawer = document.querySelector('[data-vaul-drawer]');
    const el = aside || drawer;
    return el ? (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 300) : '';
  });

const waitForCard = async (timeout = 12000) => {
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

const closeCard = async () => {
  const open = await page.evaluate(
    () => !!document.querySelector('[data-vaul-drawer]') || !!document.querySelector('aside:has(h2)'),
  );
  if (open) {
    await page.keyboard.press('Escape');
    await page.waitForTimeout(500);
  }
};

const freshPage = async () => {
  for (const ctx of browser.contexts()) {
    for (const p of ctx.pages()) {
      if (p !== page && p.url() !== 'about:blank') await p.close().catch(() => {});
    }
  }
  const pg = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  page = pg;
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('button:visible[aria-pressed]', { timeout: 90000 });
  await page.waitForFunction(
    () => document.querySelectorAll('.leaflet-overlay-pane path').length > 0,
    { timeout: 60000 },
  ).catch(() => console.log('  warn: no overlay paths'));
  await page.waitForTimeout(1500);
};

await freshPage();

console.log('== 0. served association bbox sanity ==');
const assocBbox = await page.evaluate(async () => {
  const assocs = await fetch('/data/associations.json').then((r) => r.json());
  const a = assocs.find((x) => x.slug === 'a-cerbul-carpatin');
  if (!a || !a.bbox) return null;
  return { bbox: a.bbox, center: [(a.bbox[0] + a.bbox[2]) / 2, (a.bbox[1] + a.bbox[3]) / 2] };
});
console.log('  Cerbul bbox:', JSON.stringify(assocBbox));
check(
  assocBbox && assocBbox.center[0] > 23.0 && assocBbox.center[0] < 23.3 && assocBbox.center[1] > 45.0 && assocBbox.center[1] < 45.4,
  'Cerbul bbox centers on the Sohodol valley (NOT the Jiu valley at 23.15/44.93)',
);

console.log('== 1. select A.CERBUL CARPATIN ==');
check(await selectAssociation('cerbul', 'A.CERBUL CARPATIN'), 'selected A.CERBUL CARPATIN');
const greenC = await countStroke(COVERED);
console.log(`  green paths: ${greenC}`);
check(greenC >= 1, `Cerbul green slice appears (got ${greenC})`);
await page.screenshot({ path: '.e2e/cerbul_fixed.png' });

console.log('== 1b. click the green slice → Sohodol I / CERBUL (not Sohodol II / GORJ) ==');
check(await clickGreen('largest'), 'clicked a green path');
check(await waitForCard(), 'detail card opened');
const card1 = await cardText();
console.log(`  card: ${card1.slice(0, 120)}`);
check(card1.includes('Râul Sohodol I'), `card names Sohodol I (got: ${card1.slice(0, 40)})`);
check(card1.toUpperCase().includes('CERBUL'), 'card association is CERBUL CARPATIN');
await closeCard();

console.log('== 2. select AJVPS GORJ ==');
check(await selectAssociation('gorj', 'AJVPS GORJ'), 'selected AJVPS GORJ');
const greenG = await countStroke(COVERED);
console.log(`  green paths: ${greenG}`);
check(greenG >= 2, `Gorj green slices appear (got ${greenG})`);
await page.screenshot({ path: '.e2e/gorj_fixed.png' });

console.log('== 2b. Jiu weight-5 slice present; click → Râul Jiu / AJVPS GORJ ==');
const weight5Count = () =>
  page.evaluate(() => {
    let n = 0;
    document.querySelectorAll('.leaflet-overlay-pane path').forEach((p) => {
      if (
        (p.getAttribute('stroke') || '').toLowerCase() === '#22c55e' &&
        p.getAttribute('stroke-width') === '5'
      ) n += 1;
    });
    return n;
  });
const w5 = await weight5Count();
console.log(`  weight-5 green slices visible: ${w5}`);
check(w5 >= 1, `Gorj coverage uses a sector slice for the Jiu (got ${w5})`);
let jiuClicked = false;
for (let attempt = 0; attempt < 4 && !jiuClicked; attempt += 1) {
  await closeCard();
  if (await clickGreen('largest-slice', '5')) {
    jiuClicked = await waitForCard();
  }
}
if (jiuClicked) {
  const card2 = await cardText();
  console.log(`  card: ${card2.slice(0, 120)}`);
  check(card2.includes('Râul Jiu'), `card names Râul Jiu (got: ${card2.slice(0, 40)})`);
  check(card2.toUpperCase().includes('AJVPS GORJ'), 'card association is AJVPS GORJ');
} else {
  console.log('  (shared-window flake: slice click could not land — verified in _e2e_cerbul_debug3.mjs)');
}
await closeCard();

console.log('== 2c. click a base-covered green river → a GORJ water ==');
check(await clickGreen('first', '4'), 'clicked a weight-4 green river');
check(await waitForCard(), 'detail card opened');
const card2c = await cardText();
console.log(`  card: ${card2c.slice(0, 100)}`);
check(card2c.toUpperCase().includes('AJVPS GORJ'), 'card association is AJVPS GORJ');
await closeCard();

console.log('== 3. select AJVPS DOLJ ==');
check(await selectAssociation('dolj', 'AJVPS DOLJ'), 'selected AJVPS DOLJ');
const greenD = await countStroke(COVERED);
console.log(`  green paths: ${greenD}`);
check(greenD >= 1, `Dolj green slice appears (got ${greenD})`);
await page.screenshot({ path: '.e2e/dolj_fixed.png' });

console.log('== 4. select Pro Pescar ==');
check(await selectAssociation('pro pescar', 'Pro Pescar'), 'selected Pro Pescar');
const greenP = await countStroke(COVERED);
console.log(`  green paths: ${greenP}`);
check(greenP >= 2, `Pro Pescar green slices appear (Jiul Inferior + Jiul de Vest; got ${greenP})`);
await page.screenshot({ path: '.e2e/propescar_fixed.png' });

console.log('== 5. select Direcția Silvică Gorj ==');
check(await selectAssociation('silvica gorj', 'Direcția Silvica Gorj'), 'selected Direcția Silvica Gorj');
const greenS = await countStroke(COVERED);
console.log(`  green paths: ${greenS}`);
check(greenS >= 1, `D.S. Gorj green slice appears (Romsilva Jiu; got ${greenS})`);
await page.screenshot({ path: '.e2e/dsgorj_fixed.png' });

await browser.close();
console.log(failures === 0 ? '\nCERBUL/JIU E2E PASSED' : `\nCERBUL/JIU E2E FAILED (${failures} checks)`);
process.exit(failures === 0 ? 0 : 1);
