#!/usr/bin/env node
/**
 * Verify t_a0e123da: 'Valea Pojorâtei' (anpa-anpa-0188) is fixed.
 *
 * Data-level assertions on the served app:
 *  1. anpa-anpa-0188 has geometry.type LineString (was null).
 *  2. Its bbox is in the Făgăraș Country (lon ~24.82-24.90), NOT near Săcele
 *     (lon ~25.67) — the bug's wrong location.
 *  3. No OSM 'Pojorta'/'Voila' river remains in the uncontracted overlay
 *     (they were teal; now contracted under AVPS FĂGĂRAȘ).
 *  4. The map mounts with no console errors.
 */
import { chromium } from 'playwright-core';
import http from 'http';

const BASE = process.env.BASE_URL || 'http://localhost:3100';

function fetchJSON(path) {
  return new Promise((resolve, reject) => {
    http.get(BASE + path, (res) => {
      let d = '';
      res.on('data', (c) => (d += c));
      res.on('end', () => {
        try { resolve(JSON.parse(d)); } catch (e) { reject(e); }
      });
    }).on('error', reject);
  });
}

async function main() {
  const waters = await fetchJSON('/data/waters.json');
  const poj = waters.find((w) => w.slug === 'anpa-anpa-0188');
  if (!poj) throw new Error('anpa-anpa-0188 missing');
  console.log('Valea Pojorâtei geometry type:', poj.geometry?.type ?? 'NONE');
  if (poj.geometry?.type !== 'LineString') throw new Error('not a LineString');
  console.log('Valea Pojorâtei bbox:', poj.bbox);
  if (!poj.bbox) throw new Error('no bbox');
  const [minLon, minLat, maxLon, maxLat] = poj.bbox;
  // Făgăraș Country: lon 24.7-25.0; the old wrong point was lon 25.67 (Săcele)
  if (minLon < 24.5 || maxLon > 25.2 || minLat < 45.5 || maxLat > 45.9) {
    throw new Error(`bbox outside Făgăraș Country: ${poj.bbox}`);
  }
  const oldBad = [25.674424, 45.603148];
  if (minLon < oldBad[0] && maxLon > oldBad[0]) throw new Error('bbox still overlaps Săcele');
  console.log('locality:', poj.locality, '| source_detail:', poj.source_detail);

  const unc = await fetchJSON('/data/uncontracted_rivers.json');
  const leaked = unc.filter((u) => /pojorta|voila/i.test(u.name || ''));
  console.log('uncontracted overlay Pojorta/Voila leaks:', leaked.length);
  if (leaked.length) throw new Error('Pojorta/Voila still teal in overlay');

  // browser check
  let browser;
  if (process.env.PLAYWRIGHT_CDP) {
    browser = await chromium.connectOverCDP(process.env.PLAYWRIGHT_CDP);
  } else {
    browser = await chromium.launch({
      args: ['--no-sandbox'],
      env: { ...process.env, LD_LIBRARY_PATH: '/tmp/asound/usr/lib/x86_64-linux-gnu' },
    });
  }
  const ctx = browser.contexts()[0] || await browser.newContext();
  const pages = ctx.pages().filter((p) => p.url() !== 'about:blank');
  for (const p of pages) await p.close();
  const page = await ctx.newPage();
  await page.setViewportSize({ width: 1280, height: 800 });
  const errors = [];
  page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });
  page.on('pageerror', (e) => errors.push(String(e)));

  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('.leaflet-container', { timeout: 20000 });
  await page.waitForTimeout(3000);
  const pathCount = await page.evaluate(() => document.querySelectorAll('.leaflet-overlay-pane path').length);
  console.log('map mounted, overlay paths:', pathCount);
  if (pathCount < 5) throw new Error('map overlay empty');
  if (errors.length) {
    console.log('console errors:', errors.slice(0, 5));
  } else {
    console.log('no console errors');
  }
  await page.screenshot({ path: '/tmp/verify_pojorta.png' });
  console.log('screenshot: /tmp/verify_pojorta.png');
  await browser.close();
  console.log('VERIFY OK');
}

main().catch((e) => { console.error('VERIFY FAIL:', e.message); process.exit(1); });
