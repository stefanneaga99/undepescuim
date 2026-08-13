/* eslint-disable no-console */
/**
 * t_f9d81184 pond verification — Dumbrăvița Hălchiu (Brașov) ponds.
 * Click a real uncontracted pond polygon → card Privat/Necontractat + NO orange.
 * Also click a contracted lake → ORANGE SHOULD appear (control).
 *
 * Run: node scripts/_e2e_focus_ponds.mjs [BASE_URL]
 */
import { chromium } from 'playwright';

const BASE = process.argv[2] || process.env.BASE_URL || 'http://localhost:3000';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });

let failures = 0;
const check = (cond, label) => {
  if (cond) console.log(`  PASS  ${label}`);
  else { console.log(`  FAIL  ${label}`); failures += 1; }
};

const countOrange = () =>
  page.evaluate(() => {
    let n = 0;
    document.querySelectorAll('.leaflet-overlay-pane path').forEach((p) => {
      if ((p.getAttribute('stroke') || '').toLowerCase() === '#f97316') n += 1;
    });
    return n;
  });

const rightPanelText = () =>
  page.locator('aside:has(h2:text("Detalii apă"))').innerText().catch(() => '');

const clickPathByStroke = async (stroke, { label = '', minArea = 0, preferOpen = false } = {}) => {
  const r = await page.evaluate(({ stroke, minArea, preferOpen }) => {
    const MAP_L = 320, MAP_R = 1270, MAP_T = 70, MAP_B = 770;
    const paths = [...document.querySelectorAll('.leaflet-overlay-pane path')].filter((p) => {
      if ((p.getAttribute('stroke') || '').toLowerCase() !== stroke) return false;
      if (preferOpen && (p.getAttribute('d') || '').trim().endsWith('z')) return false;
      const b = p.getBoundingClientRect();
      return b.right > MAP_L && b.bottom > MAP_T && b.left < MAP_R && b.top < MAP_B && b.width * b.height >= minArea;
    });
    for (const p of paths) {
      const len = p.getTotalLength();
      for (const frac of [0.2, 0.35, 0.5, 0.65, 0.8]) {
        const pt = p.getPointAtLength(len * frac);
        const m = p.ownerSVGElement.getScreenCTM();
        const sp = new DOMPoint(pt.x, pt.y).matrixTransform(m);
        if (sp.x < MAP_L || sp.x > MAP_R || sp.y < MAP_T || sp.y > MAP_B) continue;
        const top = document.elementFromPoint(sp.x, sp.y);
        const isSelf = top === p || (top && top.getAttribute('stroke') === p.getAttribute('stroke'));
        if (isSelf) return { x: sp.x, y: sp.y, d: (p.getAttribute('d') || '').slice(0, 60), count: paths.length };
      }
    }
    return null;
  }, { stroke, minArea, preferOpen });
  if (!r) return null;
  await page.mouse.click(r.x, r.y);
  await page.waitForTimeout(1500);
  console.log(`  clicked ${label || stroke} (${r.count} on-screen) at ${r.x.toFixed(0)},${r.y.toFixed(0)} d=${r.d}`);
  return r;
};

const zoomTo = async (steps) => {
  for (let i = 0; i < steps; i += 1) {
    await page.locator('.leaflet-control-zoom-in').click();
    await page.waitForTimeout(200);
  }
  await page.waitForTimeout(800);
};

console.log(`== load ${BASE} ==`);
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('button:visible[aria-pressed]', { timeout: 90000 });
await page.waitForTimeout(2500);

// Brașov + Lacuri filter to isolate ponds
await page.locator('button:visible', { hasText: /^Brașov$/ }).first().click();
await page.waitForTimeout(800);
await page.locator('button:visible', { hasText: 'Lacuri' }).first().click();
await page.waitForTimeout(800);
await zoomTo(7);

console.log('== click an uncontracted pond (teal polygon outline #2dd4bf) ==');
const pond = await clickPathByStroke('#2dd4bf', { label: 'pond outline', minArea: 30, preferOpen: false });
check(!!pond, 'found on-screen pond polygon path');
if (pond) {
  const t = await rightPanelText();
  const lower = t.toLowerCase();
  check(lower.includes('privat') || lower.includes('necontractat'), `card shows Privat/Necontractat (got: ${t.split('\n').slice(1, 3).join(' | ') || 'empty'})`);
  const orange = await countOrange();
  console.log(`  orange strokes after pond click: ${orange}`);
  check(orange === 0, `pond click has NO orange (got ${orange})`);
  await page.screenshot({ path: '.e2e/p_pond.png' });
}

// Control: contracted lake (blue fill #3b82f6) — clicking SHOULD highlight orange
console.log('== control: contracted lake (blue #3b82f6) ==');
const lake = await clickPathByStroke('#3b82f6', { label: 'contracted lake', minArea: 30, preferOpen: false });
check(!!lake, 'found on-screen contracted lake path');
if (lake) {
  const orange = await countOrange();
  console.log(`  orange strokes after contracted lake click: ${orange}`);
  check(orange > 0, `contracted lake highlights orange (got ${orange})`);
  const t = await rightPanelText();
  console.log(`  card: ${t.split('\n').slice(1, 3).join(' | ')}`);
  await page.screenshot({ path: '.e2e/p_lake.png' });
}

await browser.close();
console.log(failures === 0 ? 'E2E PASSED' : `E2E FAILED (${failures} checks)`);
process.exit(failures === 0 ? 0 : 1);
