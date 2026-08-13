/* eslint-disable no-console */
/**
 * t_b1547e24 Râmna (Vrancea, uncontracted) targeted verification.
 * Clicking an UNCONTRACTED teal river must show the orange highlight on that
 * feature (whole feature — no sector slicing) + the Necontractat card.
 * Run: node scripts/_e2e_focus_ramna.mjs [BASE_URL]
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

const countOrange = () =>
  page.evaluate(() => {
    let n = 0;
    document.querySelectorAll('.leaflet-overlay-pane path').forEach((p) => {
      if ((p.getAttribute('stroke') || '').toLowerCase() === '#f97316') n += 1;
    });
    return n;
  });

// Read the detail panel text regardless of viewport branch: desktop renders an
// <aside>, mobile renders a vaul drawer (CDP-connect to browserless ignores
// viewport emulation, so the mobile branch may be active at any claimed width).
const rightPanelText = () =>
  page.evaluate(() => {
    const aside = document.querySelector('aside:has(h2)');
    const drawer = document.querySelector('[data-vaul-drawer]');
    const el = aside || drawer;
    return el ? (el.textContent || '').trim() : '';
  });

/** Poll the panel until it has text (first open can be slow). */
const readCardText = async (timeoutMs = 10000) => {
  const deadline = Date.now() + timeoutMs;
  let last = '';
  while (Date.now() < deadline) {
    last = await rightPanelText();
    if (last && last.trim()) return last;
    await page.waitForTimeout(300);
  }
  return last;
};

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

const mapRect = () =>
  page.evaluate(() => {
    const c = document.querySelector('.leaflet-container');
    if (!c) return { left: 0, top: 0, right: 800, bottom: 600, cx: 400, cy: 300 };
    const r = c.getBoundingClientRect();
    return { left: r.left, top: r.top, right: r.right, bottom: r.bottom, cx: (r.left + r.right) / 2, cy: (r.top + r.bottom) / 2 };
  });

const panTo = async (lon, lat) => {
  let pos = await computePos(lon, lat);
  let m = await mapRect();
  let guard = 0;
  while (pos && (pos.x < m.left + 60 || pos.x > m.right - 60 || pos.y < m.top + 60 || pos.y > m.bottom - 60) && guard < 12) {
    const dx = Math.max(-250, Math.min(250, m.cx - pos.x));
    const dy = Math.max(-250, Math.min(250, m.cy - pos.y));
    await page.mouse.move(m.cx, m.cy);
    await page.mouse.down();
    await page.mouse.move(m.cx + dx, m.cy + dy, { steps: 6 });
    await page.mouse.up();
    await page.waitForTimeout(400);
    pos = await computePos(lon, lat);
    m = await mapRect();
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
  const c = document.querySelector('.leaflet-container');
  const r = c ? c.getBoundingClientRect() : { left: 0, top: 0, right: 800, bottom: 600 };
  const MAP_L = r.left, MAP_R = r.right, MAP_T = r.top, MAP_B = r.bottom;
  const paths = [...document.querySelectorAll('.leaflet-overlay-pane path')].filter((p) => {
    if ((p.getAttribute('stroke') || '').toLowerCase() !== '#14b8a6') return false;
    const b = p.getBoundingClientRect();
    return b.right > MAP_L && b.bottom > MAP_T && b.left < MAP_R && b.top < MAP_B && b.width * b.height > 4;
  });
  for (const p of paths) {
    const len = p.getTotalLength();
    const m = p.ownerSVGElement.getScreenCTM();
    // Dense sampling: dashed teal strokes have 4px gaps — sparse fractions
    // often land in a gap and fail the topmost check.
    const fracs = Array.from({ length: 19 }, (_, i) => 0.05 + 0.05 * i);
    for (const frac of fracs) {
      const pt = p.getPointAtLength(len * frac);
      const sp = new DOMPoint(pt.x, pt.y).matrixTransform(m);
      if (sp.x < MAP_L || sp.x > MAP_R || sp.y < MAP_T || sp.y > MAP_B) continue;
      const top = document.elementFromPoint(sp.x, sp.y);
      const isSelf = top === p || (top && top.getAttribute('stroke') === p.getAttribute('stroke'));
      if (isSelf) return { x: sp.x, y: sp.y, d: (p.getAttribute('d') || '').slice(0, 60), count: paths.length };
    }
  }
  return null;
});
check(!!hit, `found clickable teal river near Râmna (${hit ? hit.d : 'none'})`);
if (hit) {
  await page.mouse.click(hit.x, hit.y);
  await page.waitForTimeout(1500);
  // First open can be slow (sheet hydration) — poll until the panel has text.
  const t = await readCardText();
  const lower = t.toLowerCase();
  check(lower.includes('necontractat'), `card shows Necontractat (got: ${t.split('\n').slice(1, 3).join(' | ') || 'empty'})`);
  const orange = await countOrange();
  console.log(`  orange strokes after Râmna-area click: ${orange}`);
  check(orange > 0, `uncontracted river highlights orange (got ${orange})`);
  await page.screenshot({ path: '.e2e/r_ramna.png' });
}

await browser.close();
console.log(failures === 0 ? 'E2E PASSED' : `E2E FAILED (${failures} checks)`);
process.exit(failures === 0 ? 0 : 1);
