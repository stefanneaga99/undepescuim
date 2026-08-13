/* eslint-disable no-console */
/**
 * t_f9d81184 Râmna (Vrancea, uncontracted) targeted verification.
 * Run: node scripts/_e2e_focus_ramna.mjs [BASE_URL]
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

const computePos = (lon, lat) =>
  page.evaluate(([lon, lat]) => {
    const img = document.querySelector('.leaflet-tile-container img.leaflet-tile');
    if (!img) return null;
    const parts = img.src.split('/');
    const z = Number(parts[parts.length - 3]);
    const tx = Number(parts[parts.length - 2]);
    const ty = Number(parts[parts.length - 1].replace('.png', ''));
    const rect = img.getBoundingClientRect();
    const paneX = rect.left - tx * 256;
    const paneY = rect.top - ty * 256;
    const s = 256 * Math.pow(2, z);
    const px = ((lon + 180) / 360) * s;
    const latRad = (lat * Math.PI) / 180;
    const py = ((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2) * s;
    return { x: paneX + px, y: paneY + py, z };
  }, [lon, lat]);

const panTo = async (lon, lat) => {
  let pos = await computePos(lon, lat);
  let guard = 0;
  while (pos && (pos.x < 150 || pos.x > 1130 || pos.y < 120 || pos.y > 680) && guard < 12) {
    const dx = Math.max(-250, Math.min(250, 640 - pos.x));
    const dy = Math.max(-250, Math.min(250, 400 - pos.y));
    await page.mouse.move(640, 400);
    await page.mouse.down();
    await page.mouse.move(640 + dx, 400 + dy, { steps: 6 });
    await page.mouse.up();
    await page.waitForTimeout(400);
    pos = await computePos(lon, lat);
    guard += 1;
  }
  return pos;
};

console.log(`== load ${BASE} ==`);
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('button:visible[aria-pressed]', { timeout: 90000 });
await page.waitForTimeout(2500);

// Vrancea filter, zoom, pan to Râmna center
await page.locator('button:visible', { hasText: /^Vrancea$/ }).first().click();
await page.waitForTimeout(1000);
for (let i = 0; i < 5; i += 1) {
  await page.locator('.leaflet-control-zoom-in').click();
  await page.waitForTimeout(200);
}
await page.waitForTimeout(600);
const pos = await panTo(27.13256, 45.61123);
check(!!pos, `panned to Râmna (${JSON.stringify(pos)})`);

// find teal path named Râmna near the point, click its midpoint on-stroke
const hit = await page.evaluate(() => {
  const MAP_L = 320, MAP_R = 1270, MAP_T = 70, MAP_B = 770;
  const paths = [...document.querySelectorAll('.leaflet-overlay-pane path')].filter((p) => {
    if ((p.getAttribute('stroke') || '').toLowerCase() !== '#14b8a6') return false;
    const b = p.getBoundingClientRect();
    return b.right > MAP_L && b.bottom > MAP_T && b.left < MAP_R && b.top < MAP_B;
  });
  for (const p of paths) {
    const len = p.getTotalLength();
    const m = p.ownerSVGElement.getScreenCTM();
    for (const frac of [0.2, 0.35, 0.5, 0.65, 0.8]) {
      const pt = p.getPointAtLength(len * frac);
      const sp = new DOMPoint(pt.x, pt.y).matrixTransform(m);
      if (sp.x < MAP_L || sp.x > MAP_R || sp.y < MAP_T || sp.y > MAP_B) continue;
      const top = document.elementFromPoint(sp.x, sp.y);
      const isSelf = top === p || (top && top.getAttribute('stroke') === p.getAttribute('stroke'));
      if (isSelf) return { x: sp.x, y: sp.y, d: (p.getAttribute('d') || '').slice(0, 60) };
    }
  }
  return null;
});
check(!!hit, `found clickable teal river near Râmna (${hit ? hit.d : 'none'})`);
if (hit) {
  await page.mouse.click(hit.x, hit.y);
  await page.waitForTimeout(1500);
  const t = await rightPanelText();
  const lower = t.toLowerCase();
  check(lower.includes('necontractat'), `card shows Necontractat (got: ${t.split('\n').slice(1, 3).join(' | ') || 'empty'})`);
  const orange = await countOrange();
  console.log(`  orange strokes after Râmna-area click: ${orange}`);
  check(orange === 0, `NO orange for uncontracted river (got ${orange})`);
  await page.screenshot({ path: '.e2e/r_ramna.png' });
}

await browser.close();
console.log(failures === 0 ? 'E2E PASSED' : `E2E FAILED (${failures} checks)`);
process.exit(failures === 0 ? 0 : 1);
