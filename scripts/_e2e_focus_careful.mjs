/* eslint-disable no-console */
/**
 * t_f9d81184 careful behavior test. Clicks only points where elementFromPoint
 * confirms the intended layer is the TOPMOST interactive element.
 * 1. click a REAL contracted blue river → orange focus SHOULD appear
 * 2. click a REAL uncontracted teal river → card Necontractat + NO orange
 * 3. re-click contracted → orange reappears
 * 4. click a pond → card Privat/Necontractat + no orange
 *
 * Run: node scripts/_e2e_focus_careful.mjs [BASE_URL]
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

/** Find an on-screen path of `stroke` whose midpoint's topmost element is itself.
 * When `preferOpen` is set, only open paths (rivers) are considered — polygons (lakes) end with 'z'. */
const findClickable = (stroke, { minArea = 0, preferOpen = true } = {}) =>
  page.evaluate(({ stroke, minArea, preferOpen }) => {
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

const clickStroke = async (stroke, opts, label) => {
  const r = await findClickable(stroke, opts);
  if (!r) return null;
  await page.mouse.click(r.x, r.y);
  await page.waitForTimeout(1500);
  console.log(`  clicked ${label} (${r.count} on-screen) at ${r.x.toFixed(0)},${r.y.toFixed(0)} d=${r.d}`);
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
await zoomTo(4);

console.log('== 1. contracted blue river → orange ==');
let c1 = await clickStroke('#3b82f6', {}, 'contracted blue');
let guard = 0;
while (!c1 && guard < 3) {
  await page.mouse.move(640, 400); await page.mouse.down();
  await page.mouse.move(690, 400, { steps: 4 }); await page.mouse.up();
  await page.waitForTimeout(400);
  c1 = await clickStroke('#3b82f6', {}, 'contracted blue (retry)');
  guard += 1;
}
check(!!c1, 'found topmost contracted blue river point');
let orange1 = 0;
if (c1) {
  orange1 = await countOrange();
  console.log(`  orange after contracted click: ${orange1}`);
  check(orange1 > 0, `contracted river highlights orange (got ${orange1})`);
  const t = await rightPanelText();
  console.log(`  card: ${t.split('\n').slice(1, 4).join(' | ')}`);
  await page.screenshot({ path: '.e2e/c_contracted.png' });
}

console.log('== 2. uncontracted teal river → orange cleared ==');
let t1 = await clickStroke('#14b8a6', {}, 'uncontracted teal');
guard = 0;
while (!t1 && guard < 3) {
  await page.mouse.move(640, 400); await page.mouse.down();
  await page.mouse.move(590, 400, { steps: 4 }); await page.mouse.up();
  await page.waitForTimeout(400);
  t1 = await clickStroke('#14b8a6', {}, 'uncontracted teal (retry)');
  guard += 1;
}
check(!!t1, 'found topmost uncontracted teal point');
if (t1) {
  const orange = await countOrange();
  console.log(`  orange after uncontracted click: ${orange}`);
  check(orange === 0, `uncontracted click cleared orange (got ${orange})`);
  const t = await rightPanelText();
  const lower = t.toLowerCase();
  check(lower.includes('necontractat'), `card shows Necontractat (got: ${t.split('\n').slice(1, 3).join(' | ') || 'empty'})`);
  await page.screenshot({ path: '.e2e/c_teal.png' });
}

console.log('== 3. re-click contracted → orange reappears ==');
const c2 = await clickStroke('#3b82f6', {}, 'contracted blue again');
check(!!c2, 'found contracted again');
if (c2) {
  const orange = await countOrange();
  console.log(`  orange after 2nd contracted click: ${orange}`);
  check(orange > 0, `orange reappears (got ${orange})`);
}

await browser.close();
console.log(failures === 0 ? 'E2E PASSED' : `E2E FAILED (${failures} checks)`);
process.exit(failures === 0 ? 0 : 1);
