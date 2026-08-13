/* eslint-disable no-console */
/**
 * t_1b7c95a7: association click check (AVPS ACVILA / Râul Snagov) standalone.
 * Reuses the robust helpers from _e2e_merge_sample.mjs.
 */
import { chromium } from 'playwright';

const BASE = process.argv[2] || process.env.BASE_URL || 'http://localhost:3000';
const browser = await chromium.launch({ args: ['--no-sandbox'] });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });

let failures = 0;
const check = (cond, label) => {
  if (cond) console.log(`  PASS  ${label}`);
  else { console.log(`  FAIL  ${label}`); failures += 1; }
};

const rightPanelText = () =>
  page.evaluate(() => {
    const aside = document.querySelector('aside:has(h2)');
    const drawer = document.querySelector('[data-vaul-drawer]');
    const el = aside || drawer;
    return el ? (el.textContent || '').trim() : '';
  });

const readCardText = async (timeoutMs = 12000) => {
  const deadline = Date.now() + timeoutMs;
  let last = '';
  while (Date.now() < deadline) {
    last = await rightPanelText();
    if (last && last.trim()) return last;
    await page.waitForTimeout(300);
  }
  return last;
};

const getZoom = () =>
  page.evaluate(() => {
    const img = document.querySelector('.leaflet-tile-container img.leaflet-tile');
    if (!img) return null;
    const parts = img.src.split('/');
    return Number(parts[parts.length - 3]);
  });

const wheelZoom = async (levels) => {
  if (!levels) return;
  await page.evaluate((lv) => {
    const c = document.querySelector('.leaflet-container');
    const r = c.getBoundingClientRect();
    c.dispatchEvent(new WheelEvent('wheel', {
      deltaY: -60 * lv, clientX: r.left + r.width / 2, clientY: r.top + r.height / 2,
      bubbles: true, cancelable: true,
    }));
  }, levels);
  await page.waitForTimeout(400);
};

const setZoom = async (target) => {
  const cur = await getZoom();
  if (cur == null) return;
  const delta = Math.max(-6, Math.min(6, target - cur));
  if (delta !== 0) await wheelZoom(delta);
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

const panTo = async (lon, lat, centerTol = 60) => {
  let pos = await computePos(lon, lat);
  let m = await mapRect();
  let guard = 0;
  while (pos && (Math.abs(pos.x - m.cx) > centerTol || Math.abs(pos.y - m.cy) > centerTol) && guard < 16) {
    const dx = Math.max(-250, Math.min(250, m.cx - pos.x));
    const dy = Math.max(-250, Math.min(250, m.cy - pos.y));
    await page.mouse.move(m.cx, m.cy);
    await page.mouse.down();
    await page.mouse.move(m.cx + dx, m.cy + dy, { steps: 6 });
    await page.mouse.up();
    await page.waitForTimeout(350);
    pos = await computePos(lon, lat);
    m = await mapRect();
    guard += 1;
  }
  return pos;
};

const findBluePath = (lon, lat, radius = 400, colors = ['#3b82f6']) =>
  page.evaluate(([lon, lat, radius, colors]) => {
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
    const target = { x: paneX + px, y: paneY + py };
    const c = document.querySelector('.leaflet-container');
    const r = c ? c.getBoundingClientRect() : { left: 0, top: 0, right: 800, bottom: 600 };
    const MAP_L = r.left, MAP_R = r.right, MAP_T = r.top, MAP_B = r.bottom;
    const wanted = colors.map((x) => x.toLowerCase());
    const paths = [...document.querySelectorAll('.leaflet-overlay-pane path')].filter((p) => {
      const st = (p.getAttribute('stroke') || '').toLowerCase();
      if (!wanted.includes(st)) return false;
      const b = p.getBoundingClientRect();
      return b.right > MAP_L && b.bottom > MAP_T && b.left < MAP_R && b.top < MAP_B && b.width * b.height > 4;
    });
    let best = null;
    for (const p of paths) {
      let len = 0;
      try { len = p.getTotalLength(); } catch { continue; }
      if (!len) continue;
      const m = p.ownerSVGElement.getScreenCTM();
      const fracs = Array.from({ length: 13 }, (_, i) => 0.04 + 0.08 * i);
      for (const frac of fracs) {
        const pt = p.getPointAtLength(len * frac);
        const sp = new DOMPoint(pt.x, pt.y).matrixTransform(m);
        const d = Math.hypot(sp.x - target.x, sp.y - target.y);
        if (d < radius && (!best || d < best.d)) best = { x: sp.x, y: sp.y, d };
      }
    }
    return best;
  }, [lon, lat, radius, colors]);

console.log(`== load ${BASE} ==`);
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('button:visible[aria-pressed]', { timeout: 90000 });
await page.waitForTimeout(3000);

// 1. select AVPS ACVILA via the association search
const trigger = page.locator('button:visible', { hasText: /Caută asociația/ }).first();
check((await trigger.count()) > 0, 'association trigger found');
if (await trigger.count()) {
  await trigger.click({ force: true }).catch(() => {});
  await page.waitForTimeout(1000);
}
const input = page.locator('input[placeholder="Caută asociația…"]');
if (await input.count()) {
  await input.fill('ACVILA');
  await page.waitForTimeout(800);
  const item = page.getByText('AVPS ACVILA', { exact: false }).first();
  check((await item.count()) > 0, 'ACVILA item in dropdown');
  if (await item.count()) {
    await item.click({ force: true }).catch(() => {});
    await page.waitForTimeout(2500);
    console.log('  ACVILA selected (flyTo should center on its area)');
  }
} else {
  check(false, 'cmdk input found');
}

// 2. pan/zoom to Snagov lake and confirm the contracted path renders
const snagov = { lon: 26.1400, lat: 44.7100 };
let pos = await panTo(snagov.lon, snagov.lat);
check(!!pos, 'map position computed');
await setZoom(11);
await panTo(snagov.lon, snagov.lat, 30);
await page.waitForTimeout(800);
const hit = await findBluePath(snagov.lon, snagov.lat, 400, ['#22c55e', '#3b82f6']);
check(!!hit, `Snagov contracted path renders (${hit ? Math.round(hit.d) + 'px' : 'none'})`);

// 3. click it and verify the card
if (hit) {
  await page.mouse.click(hit.x, hit.y);
  await page.waitForTimeout(1800);
  const t = await readCardText();
  const tl = t.toLowerCase();
  check(tl.includes('snagov'), `card names Snagov (got: ${t.split('\n').filter(Boolean).slice(0, 2).join(' | ') || 'empty'})`);
  check(tl.includes('acvila') || tl.includes('acvil'), 'card shows AVPS ACVILA');
  await page.screenshot({ path: '.e2e/r_merge_snagov.png' }).catch(() => {});
}

await browser.close();
console.log(failures === 0 ? '\nASSOC E2E PASSED' : `\nASSOC E2E FAILED (${failures})`);
process.exit(failures === 0 ? 0 : 1);
