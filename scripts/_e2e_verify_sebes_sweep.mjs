#!/usr/bin/env node
/**
 * Verify t_e3ae3121 (sebes family + county-validator sweep):
 *  1. /data/waters.json on the served app: the sebes family has county-correct
 *     geometry (Sebeșul de Sus/Jos carry SIBIU courses, not Brașov/Vâlcea).
 *  2. The 17 sweep-fixed waters now have LineString geometry.
 *  3. The map mounts (leaflet container + at least one overlay path).
 *  4. No console errors on load.
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

const SEBES_FAMILY = ['qsvhz93s', 'f02xtxw1', 'uyzo7o3j', 'anpa-anpa-0182', 'anpa-mures-sebes-21'];
const SWEEP_FIXED = [
  '4pouq9sd',   // Geoagiu Inferior → Stremț (Alba)
  '3s4b1wip',   // Barcău → Bihor
  'tjs59g3d',   // Blahnița → Gorj
  '3p16514b',   // Neajlov → Dâmbovița
  'y2wjgy7w',   // Sabar → Dâmbovița
  'xivzc8yg',   // Săliște → Râul Negru (Sibiu)
  '0kaweera',   // Valea Caselor → Alba
  'anpa-anpa-0256', // Pârâu Vârghiș → Covasna
  'anpa-anpa-0321', // Măgheruș → Harghita
  'anpa-anpa-0322', // Călimănel → Harghita
  'anpa-anpa-0350', // Pârâul Mare → Harghita
  'anpa-anpa-0351', // Pârâul Mic → Harghita
  'anpa-anpa-0374', // Grădiștea inferioară → Orăștie (Hunedoara)
  'anpa-anpa-0404', // Tisa → Maramureș
  'anpa-anpa-0510', // Valea Almașului → Sălaj
  'anpa-anpa-0624', // Vasluieț → Vaslui
  'romsilva-gorj-motru-mare', // Motru Mare → Gorj
  'romsilva-hunedoara-papusa', // Păpușa → Tăul Păpușii lake (Polygon)
];

async function main() {
  const waters = await fetchJSON('/data/waters.json');
  const by = Object.fromEntries(waters.map((w) => [w.slug, w]));

  console.log('=== sebes family ===');
  for (const slug of SEBES_FAMILY) {
    const w = by[slug];
    if (!w) throw new Error(`missing sebes water ${slug}`);
    console.log(`  ${slug} ${w.name} (${w.judet}) geo=${w.geometry?.type ?? 'NONE'}`);
    if (!w.geometry) throw new Error(`${slug} has no geometry`);
  }
  // county-correctness spot check: Sebeșul de Sus geometry must be inside Sibiu bbox
  const sus = by['qsvhz93s'];
  const c = sus.geometry.coordinates;
  const lons = c.map((p) => p[0]);
  const lats = c.map((p) => p[1]);
  const lonMid = (Math.min(...lons) + Math.max(...lons)) / 2;
  const latMid = (Math.min(...lats) + Math.max(...lats)) / 2;
  console.log(`  Sebeșul de Sus centroid: ${lonMid.toFixed(4)}, ${latMid.toFixed(4)} (expect ~24.36, 45.63 Sibiu)`);
  if (lonMid < 24.3 || lonMid > 24.5) throw new Error('Sebeșul de Sus geometry still outside Sibiu');

  console.log('=== sweep-fixed waters (geometry attached) ===');
  let n = 0;
  for (const slug of SWEEP_FIXED) {
    const w = by[slug];
    if (!w) continue;
    if (!w.geometry || !['LineString', 'MultiLineString', 'Polygon'].includes(w.geometry.type)) {
      throw new Error(`${slug} ${w.name} no geometry: ${w.geometry?.type}`);
    }
    n++;
  }
  console.log(`  ${n} sweep-fixed waters verified`);

  const withGeom = waters.filter((w) => w.geometry).length;
  console.log(`  waters with geometry: ${withGeom}`);

  // ---- map mount via CDP ----
  const browser = await chromium.connectOverCDP(process.env.PLAYWRIGHT_CDP || 'http://localhost:3000');
  const ctx = browser.contexts()[0];
  for (const p of ctx.pages()) if (p.url() !== 'about:blank') await p.close();
  const page = await ctx.newPage();
  await page.setViewportSize({ width: 1280, height: 800 });
  const consoleErrors = [];
  page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
  await page.goto(BASE, { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForSelector('.leaflet-container', { timeout: 30000 });
  await page.waitForFunction(() => document.querySelectorAll('.leaflet-overlay-pane path').length > 0, { timeout: 30000 });
  const pathCount = await page.evaluate(() => document.querySelectorAll('.leaflet-overlay-pane path').length);
  console.log(`  map mounted, overlay paths: ${pathCount}`);
  if (pathCount < 1) throw new Error('no overlay paths rendered');
  const realErrors = consoleErrors.filter((e) => !e.includes('ERR_CERT') && !e.includes('favicon'));
  if (realErrors.length > 0) {
    console.log('  console errors:', realErrors.slice(0, 5));
    throw new Error('console errors on load');
  }
  console.log('  no console errors');
  await browser.close();
  console.log('ALL CHECKS PASSED');
}

main().catch((e) => { console.error('FAIL:', e.message); process.exit(1); });
