// F5 verification (t_286cf213): /permis page + WaterDetailCard links.
// Uses the proven clickStroke pattern (getScreenCTM + page.mouse.click) from
// _e2e_assoc_clear.mjs — synthetic dispatch never reaches Leaflet's listener.
import { chromium } from 'playwright';

const BASE = process.argv[2] || process.env.BASE_URL || 'http://172.25.236.246:3100';
const CDP = process.env.PLAYWRIGHT_CDP || 'http://localhost:3000';

const browser = await chromium.connectOverCDP(CDP);
for (const ctx of browser.contexts()) {
  for (const p of ctx.pages()) {
    if (p.url() !== 'about:blank') await p.close().catch(() => {});
  }
}
const page = await browser.newPage();
let failures = 0;
const check = (cond, label) => {
  console.log(`  ${cond ? 'PASS' : 'FAIL'}  ${label}`);
  if (!cond) failures += 1;
};

const COVERED = '#22c55e';
const TEAL = '#14b8a6';

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

console.log('== /permis page ==');
await page.goto(`${BASE}/permis`, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('h1', { timeout: 30000 });
const h1 = (await page.textContent('h1')) || '';
check(h1.includes('Permis & Reguli 2026'), 'H1 is "Permis & Reguli 2026"');
const body = (await page.textContent('body')) || '';
check(body.includes('Ultima verificare a faptelor: 2026-08-15'), 'last-updated date shown');
check(body.includes('ANADSPA'), 'ANADSPA present');
check(body.includes('OUG nr. 92/2025'), 'OUG 92/2025 present');
check(body.includes('28 februarie'), 'catch-sheet deadline 28 feb present');
const sourceLinks = await page.$$eval('a[href^="http"]', (as) => as.map((a) => a.getAttribute('href')));
check(sourceLinks.length >= 5, `source links on page (${sourceLinks.length})`);
check(sourceLinks.includes('https://permise.anpa.ro:12443/portal-public/permis'), 'portal link present');

console.log('== header link ==');
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('button:visible[aria-pressed]', { timeout: 90000 }).catch(() => {});
const headerLink = page.locator('header a[href="/permis"]');
check((await headerLink.count()) === 1, 'header link to /permis exists');
if ((await headerLink.count()) === 1) {
  await headerLink.click();
  await page.waitForTimeout(1000);
  check(page.url().includes('/permis'), 'header link navigates to /permis');
}

console.log('== card: contracted water shows "Permis & Reguli 2026" button ==');
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('button:visible[aria-pressed]', { timeout: 90000 });
await page.waitForFunction(() => document.querySelectorAll('.leaflet-overlay-pane path').length > 0, { timeout: 60000 }).catch(() => {});
await page.waitForTimeout(1500);
check(await selectAssociation('buzau', 'AJVPS BUZĂU'), 'selected AJVPS BUZĂU');
check(await waitForStrokeCount(COVERED, 4), 'green covered paths appeared');
check(await clickStroke(COVERED), 'clicked a green river');
check(await waitForCardText(), 'detail card opened');
const card = await cardText();
console.log(`  card: ${card.slice(0, 120)}`);
check(card.includes('Permis & Reguli 2026'), 'card shows "Permis & Reguli 2026" button');
check(card.includes('Raportează o problemă'), 'card still shows report button');
check(card.includes('Asociație'), 'card shows association section');
await page.screenshot({ path: '.e2e/permis_contracted_card.png' });

console.log('== card: uncontracted water shows "Vezi ghidul" link ==');
const cardOpen = await page.evaluate(
  () => !!document.querySelector('[data-vaul-drawer]') || !!document.querySelector('aside:has(h2)'),
);
if (cardOpen) {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(500);
}
// Pick an uncontracted teal river on-screen and click it (clears assoc + opens its card)
check(await clickStroke(TEAL), 'clicked a teal uncontracted river');
await page.waitForTimeout(800);
check(await waitForCardText(), 'uncontracted card opened');
const card2 = await cardText();
console.log(`  card: ${card2.slice(0, 120)}`);
check(card2.includes('Apă necontractată'), 'card shows uncontracted notice');
check(card2.includes('Vezi ghidul') && card2.includes('Permis & Reguli 2026'), 'card shows "Vezi ghidul Permis & Reguli 2026" link');
await page.screenshot({ path: '.e2e/permis_uncontracted_card.png' });

await browser.close();
console.log(failures === 0 ? 'PERMIS-GUIDE E2E PASSED' : `PERMIS-GUIDE E2E FAILED (${failures} checks)`);
process.exit(failures === 0 ? 0 : 1);
