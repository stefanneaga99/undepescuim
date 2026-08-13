/* eslint-disable no-console */
/**
 * t_b1547e24 pond verification — Dumbrăvița Hălchiu (Brașov) ponds.
 * Click a real uncontracted pond polygon → card Privat/Necontractat AND the
 * pond polygon highlights ORANGE (whole feature). Contracted lake click →
 * orange (control).
 *
 * Run: node scripts/_e2e_focus_ponds.mjs [BASE_URL]
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

// Brașov + Lacuri filter to isolate ponds
await page.locator('button:visible', { hasText: /^Brașov$/ }).first().click();
await page.waitForTimeout(800);
await page.locator('button:visible', { hasText: 'Lacuri' }).first().click();
await page.waitForTimeout(800);
// County filter keeps the default view centered on Romania — pan to the
// Dumbrăvița ponds (Făgăraș area) so they're actually on screen.
await zoomTo(6);
const pos = await panTo(24.87, 45.83);
check(!!pos, `panned to Dumbrăvița ponds (${JSON.stringify(pos)})`);

console.log('== click an uncontracted pond (teal polygon outline #2dd4bf) ==');
const pond = await clickPathByStroke('#2dd4bf', { label: 'pond outline', minArea: 30, preferOpen: false });
check(!!pond, 'found on-screen pond polygon path');
if (pond) {
  // First open can be slow (sheet hydration) — poll until the panel has text.
  const t = await readCardText();
  const lower = t.toLowerCase();
  check(lower.includes('privat') || lower.includes('necontractat'), `card shows Privat/Necontractat (got: ${t.split('\n').slice(1, 3).join(' | ') || 'empty'})`);
  const orange = await countOrange();
  console.log(`  orange strokes after pond click: ${orange}`);
  check(orange > 0, `pond click highlights orange (got ${orange})`);
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
