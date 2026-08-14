/* eslint-disable no-console */
/**
 * t_1b7c95a7 run 2 targeted check: the 9 fixed double-draw groups + dragan.
 * For each group owner: pan/zoom, verify a contracted blue path renders
 * (the ONE owner course), click it, verify a card opens. This proves the
 * one-owner-per-group cleanup left each course on the map.
 * Run: LD_LIBRARY_PATH=/tmp/asound/usr/lib/x86_64-linux-gnu node scripts/_e2e_fixed_groups.mjs http://172.25.236.246:3100
 */
import { chromium } from 'playwright';

const BASE = process.argv[2] || 'http://localhost:3100';
const browser = await chromium.launch({ args: ['--no-sandbox'] });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });

let failures = 0;
const check = (cond, label) => {
  if (cond) console.log(`  PASS  ${label}`);
  else { console.log(`  FAIL  ${label}`); failures += 1; }
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

const getZoom = () =>
  page.evaluate(() => {
    const img = document.querySelector('.leaflet-tile-container img.leaflet-tile');
    if (!img) return null;
    const parts = img.src.split('/');
    return Number(parts[parts.length - 3]);
  });

const wheelZoom = async (levels) => {
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

const findBluePath = (lon, lat, radius = 400) =>
  page.evaluate(([lon, lat, radius]) => {
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
    const paths = [...document.querySelectorAll('.leaflet-overlay-pane path')].filter((p) => {
      const st = (p.getAttribute('stroke') || '').toLowerCase();
      if (st !== '#3b82f6') return false;
      const b = p.getBoundingClientRect();
      return b.right > MAP_L && b.bottom > MAP_T && b.left < MAP_R && b.top < MAP_B && b.width * b.height > 4;
    });
    let best = null;
    for (const p of paths) {
      let len = 0;
      try { len = p.getTotalLength(); } catch { continue; }
      if (!len) continue;
      const m = p.ownerSVGElement.getScreenCTM();
      const fracs = Array.from({ length: 25 }, (_, i) => 0.02 + 0.04 * i);
      for (const frac of fracs) {
        const pt = p.getPointAtLength(len * frac);
        const sp = new DOMPoint(pt.x, pt.y).matrixTransform(m);
        const d = Math.hypot(sp.x - target.x, sp.y - target.y);
        if (d < radius && (!best || d < best.d)) best = { x: sp.x, y: sp.y, d };
      }
    }
    return best;
  }, [lon, lat, radius]);

const readCardText = async (timeoutMs = 10000) => {
  const deadline = Date.now() + timeoutMs;
  let last = '';
  while (Date.now() < deadline) {
    last = await page.evaluate(() => {
      const aside = document.querySelector('aside:has(h2)');
      const drawer = document.querySelector('[data-vaul-drawer]');
      const el = aside || drawer;
      return el ? (el.textContent || '').trim() : '';
    });
    if (last && last.trim()) return last;
    await page.waitForTimeout(300);
  }
  return last;
};

// fetch waters to build targets: one owner per fixed group (the ONE geometry owner)
const waters = await (await fetch(`${BASE}/data/waters.json`)).json();
const groups = ['argesel', 'budacul', 'crisul-negru', 'malaia', 'prahova',
  'somesu-rece', 'targului', 'teleajen', 'valea-robesti', 'somesul-cald'];
const targets = [];
for (const g of groups) {
  const mem = waters.filter((w) => w.riverGroup === g);
  const owner = mem.find((w) => w.geometry && w.geometry.type !== 'Polygon' && w.geometry.type !== 'MultiPolygon');
  const lake = mem.find((w) => w.geometry && (w.geometry.type === 'Polygon' || w.geometry.type === 'MultiPolygon'));
  const pick = owner || lake || mem.find((w) => w.geometry);
  if (!pick) { console.log(`  !! no geometry owner in ${g}`); continue; }
  // center = first geometry coord (course start) so we land ON the line
  const coords = pick.geometry.type === 'LineString' ? pick.geometry.coordinates
    : pick.geometry.type === 'MultiLineString' ? pick.geometry.coordinates[0] : null;
  const lon = coords ? coords[Math.floor(coords.length / 2)][0] : null;
  const lat = coords ? coords[Math.floor(coords.length / 2)][1] : null;
  targets.push({ group: g, slug: pick.slug, name: pick.name, lon, lat });
}
// dragan
const dragan = waters.find((w) => w.slug === 'romsilva-bihor-dragan');
if (dragan && dragan.geometry) {
  const coords = dragan.geometry.type === 'MultiLineString' ? dragan.geometry.coordinates[0] : dragan.geometry.coordinates;
  targets.push({ group: 'dragan', slug: dragan.slug, name: dragan.name, lon: coords[Math.floor(coords.length / 2)][0], lat: coords[Math.floor(coords.length / 2)][1] });
}

console.log(`== fixed-groups render check: ${targets.length} targets ==`);
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('button:visible[aria-pressed]', { timeout: 90000 });
await page.waitForTimeout(3000);

for (const t of targets) {
  let pos = await panTo(t.lon, t.lat);
  await setZoom(12);
  pos = await panTo(t.lon, t.lat, 30);
  await page.waitForTimeout(600);
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(400);
  const hit = await findBluePath(t.lon, t.lat, 500);
  if (hit) {
    console.log(`  OK    ${t.group}/${t.name}: blue within ${Math.round(hit.d)}px`);
    await page.mouse.click(hit.x, hit.y);
    await page.waitForTimeout(1500);
    const card = await readCardText();
    check(card && card.trim().length > 20, `${t.group} card opens (${card.split('\n').filter(Boolean).slice(0, 1).join('|')})`);
  } else {
    check(false, `${t.group}/${t.name}: no blue path renders`);
  }
}

await browser.close();
console.log(failures === 0 ? '\nFIXED-GROUPS E2E PASSED' : `\nFIXED-GROUPS E2E FAILED (${failures})`);
process.exit(failures === 0 ? 0 : 1);
