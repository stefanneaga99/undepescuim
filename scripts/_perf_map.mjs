#!/usr/bin/env node
/* eslint-disable no-console */
/**
 * Performance budget suite — map home route (docs/performance-test-plan.md §4).
 *
 * Assertions (mobile viewport 390×844, optional Fast 3G + CPU 4× throttle):
 *   M5  CLS on filter/sheet change                        == 0.00 (unexpected shifts only)
 *   M6  Time-to-first-map-paint (window.__perfDataLoaded)  < 5.0 s
 *   M10 Initial JS gzip (home route)                      < 300 KB
 *   M11 Data fetch + parse (first load, no cache)          < 2.5 s
 *   M12 No long task > 100 ms during pan/zoom              (max long task ≤ 100 ms)
 *   M13 Peak JS heap (full dataset)                       < 200 MB
 *   M14 LOD/culling: overlay paths at zoom 7               ≤ 500 features
 *
 * Run against a PRODUCTION build (perf must not be measured on dev):
 *   npm run build && npm run start &
 *   node scripts/_perf_map.mjs http://localhost:3000
 *
 * Env:
 *   PERF_THROTTLE=0   skip Fast 3G + CPU 4× emulation (quick local smoke;
 *                     default is 1 — throttled, the lab condition of record)
 *   PLAYWRIGHT_CDP=…  connect via browserless (fallback; prefers local chromium)
 *
 * Exit code 0 = all budgets PASS, 1 = any FAIL.
 */
import { chromium } from 'playwright';

const BASE = process.argv[2] || process.env.BASE_URL || 'http://localhost:3000';
const CDP = process.env.PLAYWRIGHT_CDP;
const THROTTLE = process.env.PERF_THROTTLE !== '0'; // throttled by default

// Budget limits (plan §4; byte units where applicable)
const BUDGETS = {
  M5: { label: 'M5  CLS on filter/sheet change', target: '== 0.00', limit: 0.001 },
  M6: { label: 'M6  first-map-paint', target: '< 5.0 s', limit: 5000 },
  M10: { label: 'M10 initial JS gzip', target: '< 300 KB', limit: 300 * 1024 },
  M11: { label: 'M11 data fetch+parse', target: '< 2.5 s', limit: 2500 },
  M12: { label: 'M12 max long task (pan/zoom)', target: '<= 100 ms', limit: 100 },
  M13: { label: 'M13 peak JS heap', target: '< 200 MB', limit: 200 * 1024 * 1024 },
  M14: { label: 'M14 overlay paths @ zoom 7', target: '<= 500', limit: 500 },
};

const results = {};
const failures = [];
const check = (key, ok, value) => {
  results[key] = { ok, value };
  console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${BUDGETS[key].label.padEnd(34)} ${BUDGETS[key].target.padEnd(12)} got ${value}`);
  if (!ok) failures.push(key);
};
const report = (label, value) => console.log(`  INFO  ${label.padEnd(34)} ${value}`);

const browser = CDP ? await chromium.connectOverCDP(CDP) : await chromium.launch();
let page = await browser.newPage({ viewport: { width: 390, height: 844 } });

if (CDP) {
  // browserless shares one window — force the width like the e2e scripts
  for (let i = 0; i < 8; i += 1) {
    await page.setViewportSize({ width: 390, height: 844 }).catch(() => {});
    await page.waitForTimeout(200);
    const iw = await page.evaluate(() => window.innerWidth).catch(() => 0);
    if (iw === 390) break;
  }
}

console.log(`Perf suite → ${BASE}  (viewport 390×844, throttle=${THROTTLE ? 'Fast 3G + CPU 4×' : 'off'})\n`);

// ---- Fast 3G + CPU 4× throttle (plan §5.5) ----
if (THROTTLE) {
  try {
    const cdp = await page.context().newCDPSession(page);
    await cdp.send('Network.enable');
    await cdp.send('Network.emulateNetworkConditions', {
      offline: false,
      latency: 150,
      downloadThroughput: 204800, // 1.6 Mbps / 8 = 200 KB/s
      uploadThroughput: 96000, // 750 Kbps / 8 ≈ 94 KB/s
      connectionType: 'cellular3g',
    });
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
    report('throttle', 'Fast 3G (1.6 Mbps, 150 ms RTT) + CPU 4×');
  } catch (err) {
    console.log(`  warn: CDP throttle unavailable (${err.message.split('\n')[0]}) — running unthrottled`);
  }
}

// ---- Load + wait for the map data gate (instrumented in map-store.ts) ----
const navStart = Date.now();
await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 60000 });
try {
  await page.waitForFunction(() => window.__perfDataLoaded === true, { timeout: 180000 });
} catch {
  await page.waitForTimeout(5000);
  console.log('  warn: __perfDataLoaded never flipped — the map data gate did not open; continuing with what rendered');
}
await page.waitForFunction(() => document.querySelectorAll('.leaflet-overlay-pane path').length > 0, { timeout: 60000 }).catch(() => {});

// ---- M6 / M11 / M10 from performance entries ----
const perf = await page.evaluate(() => {
  const nav = performance.getEntriesByType('navigation')[0] || {};
  const loadedAt = window.__perfDataLoadedAt ?? performance.now();
  const resources = performance.getEntriesByType('resource') || [];
  const data = resources.filter((r) => r.name.includes('/data/'));
  const dataStart = data.length ? Math.min(...data.map((r) => r.startTime)) : null;
  const js = resources.filter((r) => r.name.includes('/_next/static/chunks/'));
  return {
    navStart: nav.startTime ?? 0,
    loadedAt,
    dataStart,
    dataTransfer: data.reduce((a, r) => a + (r.transferSize || 0), 0),
    dataRows: data.map((r) => ({ name: r.name.split('/data/')[1], transfer: r.transferSize || 0, dur: Math.round(r.duration) })),
    jsTransfer: js.reduce((a, r) => a + (r.transferSize || 0), 0),
  };
});

const m6 = perf.loadedAt - perf.navStart;
check('M6', m6 < BUDGETS.M6.limit, `${(m6 / 1000).toFixed(2)} s`);
report('data resources (on-wire)', `${(perf.dataTransfer / 1024).toFixed(0)} KB`);
for (const r of perf.dataRows.sort((a, b) => b.transfer - a.transfer)) {
  report(`  ${r.name}`, `${(r.transfer / 1024).toFixed(0)} KB in ${(r.dur / 1000).toFixed(2)} s`);
}
const m11 = perf.dataStart != null ? perf.loadedAt - perf.dataStart : NaN;
check('M11', Number.isFinite(m11) && m11 < BUDGETS.M11.limit, `${(m11 / 1000).toFixed(2)} s`);
const m10 = perf.jsTransfer;
check('M10', m10 < BUDGETS.M10.limit, `${(m10 / 1024).toFixed(1)} KB`);

// ---- M14: LOD/culling effectiveness at the default zoom 7 ----
const pathCount = await page.evaluate(() => document.querySelectorAll('.leaflet-overlay-pane path').length);
check('M14', pathCount <= BUDGETS.M14.limit, `${pathCount} paths`);

// ---- M13: peak JS heap with the full dataset loaded ----
const heap = await page.evaluate(() => (performance.memory ? performance.memory.usedJSHeapSize : null)).catch(() => null);
if (heap == null) {
  console.log('  warn: performance.memory unavailable (non-Chromium) — M13 skipped');
} else {
  check('M13', heap < BUDGETS.M13.limit, `${(heap / 1048576).toFixed(0)} MB`);
}

// ---- M12: long tasks during zoom 7 → 11 (synthetic wheel, skill pattern) ----
await page.evaluate(() => {
  window.__perfLongTasks = [];
  const obs = new PerformanceObserver((list) => {
    for (const e of list.getEntries()) {
      window.__perfLongTasks.push({ name: e.name, start: Math.round(e.startTime), dur: Math.round(e.duration) });
    }
  });
  obs.observe({ entryTypes: ['longtask'] });
  window.__perfLongTaskObs = obs;
});

const zoomLevel = async () =>
  page.evaluate(() => {
    const t = document.querySelector('.leaflet-tile');
    const m = t && t.src.match(/\/(\d+)\/\d+\/\d+(?:@2x)?\.png/);
    return m ? Number(m[1]) : null;
  });

const z0 = await zoomLevel();
await page.evaluate(() => {
  const el = document.querySelector('.leaflet-container');
  const r = el.getBoundingClientRect();
  const cx = r.left + r.width / 2;
  const cy = r.top + r.height / 2;
  for (let i = 0; i < 5; i += 1) {
    el.dispatchEvent(new WheelEvent('wheel', { deltaY: -60, clientX: cx, clientY: cy, bubbles: true, cancelable: true }));
  }
});
await page.waitForTimeout(5000); // let the zoom chain + LOD re-renders settle
const z1 = await zoomLevel();
const longTasks = await page.evaluate(() => window.__perfLongTasks);
const maxLong = longTasks.length ? Math.max(...longTasks.map((t) => t.dur)) : 0;
report('zoom', `${z0 ?? '?'} → ${z1 ?? '?'} (${longTasks.length} long tasks recorded)`);
check('M12', maxLong <= BUDGETS.M12.limit, `${maxLong} ms`);
if (longTasks.length > 10) {
  const top = [...longTasks].sort((a, b) => b.dur - a.dur).slice(0, 5);
  for (const t of top) report(`  long task ${t.dur} ms @ ${t.start} ms (${t.name})`, '');
}

// ---- M5: unexpected layout shift across a filter toggle + sheet open ----
await page.evaluate(() => {
  window.__perfCls = { unexpected: 0, unexpectedShifts: 0, raw: 0, rawShifts: 0 };
  const obs = new PerformanceObserver((list) => {
    for (const e of list.getEntries()) {
      if (!e.hadRecentInput) {
        window.__perfCls.unexpected += e.value;
        window.__perfCls.unexpectedShifts += 1;
      } else {
        window.__perfCls.raw += e.value;
      }
      window.__perfCls.rawShifts += 1;
    }
  });
  obs.observe({ entryTypes: ['layout-shift'] });
  window.__perfClsObs = obs;
});

// Toggle a county chip twice (filter mutation re-renders the map overlays)
const chip = page.locator('button:has-text("Bihor")').first();
const chipVisible = await chip.isVisible().catch(() => false);
if (chipVisible) {
  await chip.evaluate((el) => el.click()).catch(() => {});
  await page.waitForTimeout(600);
  await chip.evaluate((el) => el.click()).catch(() => {});
  await page.waitForTimeout(600);
} else {
  console.log('  warn: county chip not visible — filter-toggle CLS coverage skipped');
}

// Open the water detail sheet (click a path near the map centre; retry a few points)
let sheetOpened = false;
const mapBox = await page.evaluate(() => {
  const r = document.querySelector('.leaflet-container').getBoundingClientRect();
  return { x: r.left, y: r.top, w: r.width, h: r.height };
});
for (const [fx, fy] of [[0.5, 0.5], [0.35, 0.55], [0.6, 0.4]]) {
  await page.mouse.click(mapBox.x + mapBox.w * fx, mapBox.y + mapBox.h * fy);
  await page.waitForTimeout(800);
  sheetOpened = await page
    .evaluate(() => !!(document.querySelector('[data-vaul-drawer]') || document.querySelector('aside:has(h2)')))
    .catch(() => false);
  if (sheetOpened) {
    await page.keyboard.press('Escape');
    await page.waitForTimeout(500);
    break;
  }
}
if (!sheetOpened) console.log('  warn: no water sheet opened from map clicks — sheet CLS coverage skipped');

const cls = await page.evaluate(() => {
  window.__perfClsObs.disconnect();
  return window.__perfCls;
});
check('M5', cls.unexpected < BUDGETS.M5.limit, `unexpected=${cls.unexpected.toFixed(4)} (${cls.unexpectedShifts} shifts; raw incl. input=${cls.raw.toFixed(4)})`);

await browser.close();

console.log('\nBudget summary:');
for (const [k, b] of Object.entries(BUDGETS)) {
  const r = results[k];
  if (!r) continue;
  console.log(`  ${r.ok ? 'PASS' : 'FAIL'}  ${b.label} — ${r.value}`);
}
console.log(failures.length === 0 ? '\nPERF SUITE PASSED' : `\nPERF SUITE FAILED (${failures.length}: ${failures.join(', ')})`);
process.exit(failures.length === 0 ? 0 : 1);
