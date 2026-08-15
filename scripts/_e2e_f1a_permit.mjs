#!/usr/bin/env node
/**
 * F1a e2e check — permit rows on the water detail card.
 *
 * Drives the real map UI (browserless CDP, per skills/undepescuim-e2e-playwright):
 *   1. Lac acumulare Pecineagu (APS Aqua Crisius — permitUrl known)
 *      → expect "Cumpără permis online" + the national ANADSPA row.
 *   2. Acumulare Agrement (AJVPS Bacău — no permitUrl)
 *      → expect the "Permis: verifică cu asociația" fallback + national row.
 *
 * Both are contracted lakes; we pan to the bbox center via the tile-math
 * drag helper (the same one _e2e_focus_ramna.mjs uses), zoom in, then click
 * the blue contracted polygon (stroke/fill #3b82f6) at that point.
 */
import { chromium } from 'playwright-core';

const BASE = process.argv[2] || 'http://172.25.236.246:3100';
const CDP = process.env.PLAYWRIGHT_CDP || 'http://localhost:3000';

let failures = 0;
const check = (ok, label) => {
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}`);
  if (!ok) failures += 1;
};

const computePos = (page) => ([lon, lat]) =>
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

const mapRect = (page) =>
  page.evaluate(() => {
    const c = document.querySelector('.leaflet-container');
    if (!c) return { left: 0, top: 0, right: 800, bottom: 600, cx: 400, cy: 300 };
    const r = c.getBoundingClientRect();
    return { left: r.left, top: r.top, right: r.right, bottom: r.bottom, cx: (r.left + r.right) / 2, cy: (r.top + r.bottom) / 2 };
  });

const panTo = async (page, lon, lat) => {
  let pos = await computePos(page)([lon, lat]);
  let m = await mapRect(page);
  let guard = 0;
  while (pos && (pos.x < m.left + 60 || pos.x > m.right - 60 || pos.y < m.top + 60 || pos.y > m.bottom - 60) && guard < 12) {
    const dx = Math.max(-250, Math.min(250, m.cx - pos.x));
    const dy = Math.max(-250, Math.min(250, m.cy - pos.y));
    await page.mouse.move(m.cx, m.cy);
    await page.mouse.down();
    await page.mouse.move(m.cx + dx, m.cy + dy, { steps: 6 });
    await page.mouse.up();
    await page.waitForTimeout(400);
    pos = await computePos(page)([lon, lat]);
    m = await mapRect(page);
    guard += 1;
  }
  return pos;
};

const readCard = (page) =>
  page.evaluate(() => {
    const card = document.querySelector('aside:has(h2)') || document.querySelector('[data-vaul-drawer]');
    return card ? card.innerText : '';
  });

async function openWaterCard(page, lon, lat, label) {
  // Interleave pan + zoom so the target stays centered: pan until the target
  // is within the central zone, zoom one level at the map CENTER (which is
  // the target after panning), repeat until zoom 12.
  let z = 0;
  for (let step = 0; step < 10; step += 1) {
    await panTo(page, lon, lat);
    const pos = await computePos(page)([lon, lat]);
    const m = await mapRect(page);
    if (!pos) break;
    const centered = pos.x > m.left + 80 && pos.x < m.right - 80 && pos.y > m.top + 80 && pos.y < m.bottom - 80;
    if (!centered) continue;
    // Zoom exactly one level via synthetic wheel at the center.
    await page.evaluate(() => {
      const c = document.querySelector('.leaflet-container');
      const r = c.getBoundingClientRect();
      c.dispatchEvent(new WheelEvent('wheel', { deltaY: -60, clientX: r.left + r.width / 2, clientY: r.top + r.height / 2, bubbles: true }));
    });
    z += 1;
    await page.waitForTimeout(350);
    if (z >= 5) break;
  }
  await panTo(page, lon, lat);
  await page.waitForTimeout(600);

  const hit = await page.evaluate(({ lon, lat }) => {
    const c = document.querySelector('.leaflet-container');
    const r = c.getBoundingClientRect();
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
    const px = paneX + ((lon + 180) / 360) * s;
    const latRad = (lat * Math.PI) / 180;
    const py = paneY + ((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2) * s;
    // Sample around the exact target: the point itself + 8 neighbors — a lake
    // polygon center can sit in a fill-only region while stroke-based rivers
    // need a stroke sample. Accept any hit whose path is blue (#3b82f6).
    const pts = [[px, py]];
    for (let a = 0; a < 8; a += 1) {
      const ang = (a * Math.PI) / 4;
      pts.push([px + 8 * Math.cos(ang), py + 8 * Math.sin(ang)]);
    }
    for (const [sx, sy] of pts) {
      const top = document.elementFromPoint(sx, sy);
      if (!top) continue;
      const isBluePath =
        top.tagName === 'path' &&
        ((top.getAttribute('stroke') || '').toLowerCase() === '#3b82f6' ||
          (top.getAttribute('fill') || '').toLowerCase() === '#3b82f6');
      if (isBluePath) return { x: sx, y: sy, d: (top.getAttribute('d') || '').slice(0, 40) };
    }
    return null;
  }, { lon, lat });
  if (!hit) throw new Error(`${label}: no blue contracted polygon at ${lon},${lat}`);
  await page.mouse.click(hit.x, hit.y);
  let text = '';
  for (let i = 0; i < 20; i++) {
    text = await readCard(page);
    if (text && text.length > 30) break;
    await page.waitForTimeout(500);
  }
  console.log(`--- ${label} card (${hit.n} blue paths on screen) ---`);
  console.log(text.slice(0, 700));
  console.log('---');
  return text;
}

async function main() {
  const browser = await chromium.connectOverCDP(CDP);
  const ctxs = browser.contexts();
  for (const c of ctxs) for (const p of c.pages()) if (p.url() !== 'about:blank') await p.close();
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('button:visible[aria-pressed]', { timeout: 90000 });
  await page.waitForTimeout(2500);

  // Lac acumulare Pecineagu — APS Aqua Crisius (permitUrl known)
  const known = await openWaterCard(page, 25.070759, 45.569838, 'Pecineagu (known)');
  check(/Cumpără permis online/.test(known), 'known: "Cumpără permis online" link');
  check(/Permis național de pescuit/.test(known), 'known: national ANADSPA row');
  check(/AQUA CRISIUS|Aqua Crisius/i.test(known), 'known: association name shown');

  // Acumulare Agrement — AJVPS Bacău (no permitUrl)
  const unknown = await openWaterCard(page, 26.92668, 46.56464, 'Agrement (unknown)');
  check(/verifică cu asociația/.test(unknown), 'unknown: "verifică cu asociația" fallback');
  check(/Permis național de pescuit/.test(unknown), 'unknown: national ANADSPA row');
  check(/AJVPS BACĂU|AJVPS Bacău|Bacău/i.test(unknown), 'unknown: association name shown');

  await browser.close();
  console.log(failures === 0 ? 'F1A E2E PASSED' : `F1A E2E FAILED (${failures} checks)`);
  process.exit(failures === 0 ? 0 : 1);
}

main().catch((e) => { console.error('F1a e2e failed:', e.message); process.exit(1); });
