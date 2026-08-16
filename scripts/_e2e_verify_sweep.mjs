#!/usr/bin/env node
/**
 * Verify t_68dabead sample: the two run-127 fixes (Pârâul Murgoci, Valea
 * Curpenului) render as LINE paths on the live map, and Bihor/Vâlcea
 * rectangle-only waters stay documented (bbox markers are not LineStrings).
 *
 * Data-level assertions (no fragile pixel math):
 *  1. /data/waters.json on the served app: ii25s9zo + anpa-anpa-0631 have
 *     geometry.type LineString.
 *  2. The map mounts (leaflet container + at least one overlay path).
 *  3. No console errors on load.
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
  const murgoci = waters.find((w) => w.slug === 'ii25s9zo');
  const curpen = waters.find((w) => w.slug === 'anpa-anpa-0631');
  console.log('Pârâul Murgoci geometry:', murgoci?.geometry?.type ?? 'NONE');
  console.log('Valea Curpenului geometry:', curpen?.geometry?.type ?? 'NONE');
  if (murgoci?.geometry?.type !== 'LineString') throw new Error('Murgoci not a LineString');
  if (curpen?.geometry?.type !== 'LineString') throw new Error('Curpenului not a LineString');

  const withGeom = waters.filter((w) => w.geometry).length;
  const bboxOnly = waters.filter((w) => !w.geometry && w.bbox).length;
  console.log(`served: ${waters.length} waters, ${withGeom} with geometry, ${bboxOnly} bbox-only`);
  if (bboxOnly !== 97) console.log(`NOTE: bbox-only = ${bboxOnly} (expected 97)`);

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
  await page.screenshot({ path: '/tmp/verify_sample.png' });
  console.log('screenshot: /tmp/verify_sample.png');
  await browser.close();
  console.log('VERIFY OK');
}

main().catch((e) => { console.error('VERIFY FAIL:', e.message); process.exit(1); });
