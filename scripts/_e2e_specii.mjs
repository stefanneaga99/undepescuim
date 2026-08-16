// /specii page e2e (t_43bf3295): page renders, search narrows + selects a
// species (scroll + flash), sources block present, caveat present, header
// link, /permis link, water-card 'Dimensiuni de reținere' link.
//
// Run:
//   PLAYWRIGHT_CDP=http://localhost:3000 node scripts/_e2e_specii.mjs http://172.25.236.246:3100
//   (or local chromium when PLAYWRIGHT_CDP unset)
import { chromium } from 'playwright';

const BASE = process.argv[2] || process.env.BASE_URL || 'http://localhost:3000';
const CDP = process.env.PLAYWRIGHT_CDP;

const browser = CDP ? await chromium.connectOverCDP(CDP) : await chromium.launch();
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

console.log('== /specii page renders ==');
await page.goto(`${BASE}/specii`, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('h1', { timeout: 30000 });
const h1 = (await page.textContent('h1')) || '';
check(h1.includes('Dimensiuni minime'), 'H1 is "Dimensiuni minime de reținere"');
const body = (await page.textContent('body')) || '';
check(body.includes('Ultima verificare a faptelor'), 'last-updated line present');
check(body.includes('bălțile private'), 'national-values caveat present ("bălțile private")');
check(body.includes('Surse'), 'sources section present');
check(body.includes('Permis & Reguli 2026'), 'links to /permis present');

const rows = page.locator('[id^="specii-"]');
const rowCount = await rows.count();
console.log(`  species rows: ${rowCount}`);
check(rowCount > 0, 'at least one species row rendered from data/species.json');
await page.screenshot({ path: '.e2e/specii_page.png' });

console.log('== search "somn" (diacritic-insensitive) ==');
await page.locator('button[aria-label="Caută o specie"]:visible').click();
await page.waitForTimeout(500);
const input = page.locator('[data-slot="command-input"]');
await input.fill('somn');
await page.waitForTimeout(600);
const items = page.locator('[data-slot="command-item"]');
const itemTexts = await items.allTextContents();
console.log(`  items: ${itemTexts.map((t) => t.replace(/\s+/g, ' ').trim()).join(' | ')}`);
check(
  itemTexts.some((t) => /somn/i.test(t)) && itemTexts.every((t) => /somn/i.test(t)),
  'search "somn" narrows to somn rows',
);
// Click the somn row (first item matching the RO name) → scroll + flash.
let clicked = false;
for (let i = 0; i < itemTexts.length; i += 1) {
  if (/^Somn/i.test(itemTexts[i].trim())) {
    await items.nth(i).click();
    clicked = true;
    break;
  }
}
check(clicked, 'tapped somn item');
await page.waitForTimeout(1200);
const somnRow = page.locator('#specii-somn');
const somnCount = await somnRow.count();
check(somnCount === 1, 'somn row exists (id=specii-somn)');
if (somnCount === 1) {
  const somnText = ((await somnRow.textContent()) || '').replace(/\s+/g, ' ').trim();
  console.log(`  somn row: ${somnText.slice(0, 100)}`);
  check(/\d+\s*cm/.test(somnText), 'somn row shows a numeric min size in cm');
  const flashed = await somnRow
    .waitForFunction(
      (el) => el.classList.contains('species-flash'),
      undefined,
      { timeout: 6000 },
    )
    .then(() => true)
    .catch(() => false);
  console.log(`  flash class: ${flashed}`);
  check(flashed, 'selected species row is flash-highlighted');
}
await page.screenshot({ path: '.e2e/specii_somn.png' });

console.log('== search by size ("40") matches a species ==');
await page.locator('button[aria-label="Caută o specie"]:visible').click();
await page.waitForTimeout(400);
await input.fill('40');
await page.waitForTimeout(600);
const sizeItems = await page.locator('[data-slot="command-item"]').allTextContents();
console.log(`  items: ${sizeItems.map((t) => t.replace(/\s+/g, ' ').trim()).join(' | ')}`);
check(sizeItems.length > 0 && sizeItems.some((t) => /40\s*cm/.test(t)), 'search by size ("40") returns a species row');
await page.keyboard.press('Escape').catch(() => {});
await page.keyboard.press('Escape').catch(() => {});
await page.waitForTimeout(300);

console.log('== header link ==');
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('button:visible[aria-pressed]', { timeout: 90000 }).catch(() => {});
const headerLink = page.locator('header a[href="/specii"]');
check((await headerLink.count()) === 1, 'header has a "Specii" link');
if ((await headerLink.count()) === 1) {
  await headerLink.click();
  await page.waitForTimeout(1000);
  check(page.url().includes('/specii'), 'header link navigates to /specii');
}

console.log('== /permis page links to /specii ==');
await page.goto(`${BASE}/permis`, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('h1', { timeout: 30000 });
const permisLinks = await page.$$eval('a[href="/specii"]', (as) => as.map((a) => a.textContent));
check(permisLinks.length >= 1, `permis page links to /specii (${permisLinks.length} link(s))`);

console.log('== water card shows "Dimensiuni de reținere" link ==');
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('button:visible[aria-pressed]', { timeout: 90000 }).catch(() => {});
await page.waitForFunction(() => document.querySelectorAll('.leaflet-overlay-pane path').length > 0, { timeout: 60000 }).catch(() => {});
await page.waitForTimeout(1500);
// Pick any on-screen river — contracted green preferred, else teal uncontracted.
const greenClicked = await clickStroke(COVERED);
const tealClicked = greenClicked ? false : await clickStroke('#14b8a6');
check(greenClicked || tealClicked, 'clicked a river on the map');
await page.waitForFunction(
  () => {
    const aside = document.querySelector('aside:has(h2)');
    const drawer = document.querySelector('[data-vaul-drawer]');
    const el = aside || drawer;
    return !!el && (el.textContent || '').trim().length > 10;
  },
  { timeout: 15000 },
).catch(() => {});
const card = await cardText();
console.log(`  card: ${card.slice(0, 120)}`);
check(card.includes('Dimensiuni de reținere'), 'water card shows "Dimensiuni de reținere" link');
check(card.includes('Permis & Reguli 2026'), 'water card still shows "Permis & Reguli 2026" link');

await browser.close();
console.log(failures === 0 ? 'SPECII E2E PASSED' : `SPECII E2E FAILED (${failures} checks)`);
process.exit(failures === 0 ? 0 : 1);
