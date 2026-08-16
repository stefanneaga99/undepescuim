/* eslint-disable no-console */
/**
 * t_cdb614de point-fallback verification.
 * After the second-pass match, waters with a bbox but NO real OSM geometry
 * must render as small violet DOTS (circleMarker), NOT blue rectangle
 * polygons. Checks:
 *  1. No Polygon features in the contracted overlay pane (all bbox-only
 *     waters are now points or have real geometry).
 *  2. Violet dot circle markers exist (fill #8b5cf6) and are clickable →
 *     the water card opens.
 *  3. Spot-check counties: Botoșani, Bihor, Maramureș each have dots.
 * Run: node scripts/_e2e_point_fallback.mjs [BASE_URL]
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

const rightPanelText = () =>
  page.evaluate(() => {
    const aside = document.querySelector('aside:has(h2)');
    const drawer = document.querySelector('[data-vaul-drawer]');
    const el = aside || drawer;
    return el ? (el.textContent || '').trim() : '';
  });

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

// Set zoom/center to a specific county view.
const setView = (lat, lon, zoom) =>
  page.evaluate(([lat, lon, zoom]) => {
    const map = window.__map || null;
    // try leaflet map handle from react-leaflet internals via DOM events is hard;
    // use the zoom controls only for zoom, pan via drag not needed — we use
    // synthetic wheel + setView through the map instance stored on the pane.
    const pane = document.querySelector('.leaflet-map-pane');
    if (pane && pane._leaflet_id) {
      // find map via pane parent chain
      let el = pane;
      while (el && !el._leaflet_map) el = el.parentElement;
      const m = el?._leaflet_map;
      if (m) { m.setView([lat, lon], zoom); return true; }
    }
    return false;
  }, [lat, lon, zoom]);

const waitMap = async () => {
  await page.waitForSelector('.leaflet-tile-container img.leaflet-tile', { timeout: 15000 });
  await page.waitForTimeout(1200);
};

const countPolygons = () =>
  page.evaluate(() => {
    // Blue rectangle bbox polygons would appear as <path> with a fill in the
    // overlay pane. A bbox rectangle Polygon renders as a 5-point path; real
    // lake polygons exist too but they're legit geometry. What we assert:
    // NO path whose points form a tiny axis-aligned rectangle WITHOUT any
    // geometry-backed water having it — hard to distinguish from lake polys,
    // so instead count features by their fill color: bbox rectangles were
    // blue #3b82f6 with fillOpacity 0.2 (same as lakes). The REAL signal is
    // waterToGeoJSON: bbox-only waters now emit Point geometry, so count
    // circle markers vs polygons with fill.
    const paths = document.querySelectorAll('.leaflet-overlay-pane path');
    const circles = document.querySelectorAll('.leaflet-overlay-pane path[fill="#8b5cf6"]');
    return { paths: paths.length, violetDots: circles.length };
  });

const clickAt = async (x, y) => {
  await page.mouse.click(x, y);
  await page.waitForTimeout(700);
};

(async () => {
  console.log(`point-fallback e2e @ ${BASE}`);
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await waitMap();

  // 1. No blue rectangle polygons: every bbox-only water must be a Point.
  //    Count violet dots at national zoom (all 94 should exist as circles).
  const counts = await countPolygons();
  console.log(`  overlay paths=${counts.paths} violetDots=${counts.violetDots}`);
  check(counts.violetDots > 50, `violet point dots rendered at national zoom (${counts.violetDots})`);

  // The previous behavior rendered bbox-only waters as Polygon rectangles
  // (blue fill). With the fix, no blue axis-aligned 5-point rect should exist:
  // parse the first 5 coordinates of each path and look for a closed quad
  // whose corners are axis-aligned (x==x or y==y) — a real lake polygon has
  // many more points and meanders.
  const rects = await page.evaluate(() => {
    let n = 0;
    document.querySelectorAll('.leaflet-overlay-pane path').forEach((p) => {
      const d = p.getAttribute('d') || '';
      const fill = (p.getAttribute('fill') || '').toLowerCase();
      if (!(fill === '#3b82f6' || fill.startsWith('rgb(59, 130, 246'))) return;
      // only single-subpath closed quads
      if ((d.match(/M/g) || []).length !== 1) return;
      const m = d.match(/^M([\d.]+) ([\d.]+)L([\d.]+) ([\d.]+)L([\d.]+) ([\d.]+)L([\d.]+) ([\d.]+)L([\d.]+) ([\d.]+)z/);
      if (!m) return;
      const pts = [[+m[1], +m[2]], [+m[3], +m[4]], [+m[5], +m[6]], [+m[7], +m[8]], [+m[9], +m[10]]];
      // axis-aligned: each segment shares an x or y with the previous
      let aligned = true;
      for (let i = 0; i < 4; i++) {
        const a = pts[i], b = pts[(i + 1) % 4];
        if (Math.abs(a[0] - b[0]) > 0.01 && Math.abs(a[1] - b[1]) > 0.01) { aligned = false; break; }
      }
      // real rectangle is larger than a clipping fragment
      const xs = pts.map((q) => q[0]), ys = pts.map((q) => q[1]);
      const w = Math.max(...xs) - Math.min(...xs), h = Math.max(...ys) - Math.min(...ys);
      if (aligned && w > 8 && h > 8) n += 1;
    });
    return n;
  });
  check(rects === 0, `no blue bbox rectangle polygons in overlay pane (${rects})`);

  // 2. Click a Botoșani dot (Râul Bahna bbox center 26.2445, 47.9365).
  const mr = await mapRect();
  await setView(47.94, 26.24, 9);
  await page.waitForTimeout(1500);
  const pos = await computePos(26.2445, 47.9365);
  if (pos) {
    await clickAt(pos.x, pos.y);
    const text = await readCardText();
    check(/Bahna/i.test(text), `click Bahna dot opens card ('${text.slice(0, 60)}')`);
  } else {
    check(false, 'computePos failed for Bahna');
  }

  // 3. Spot-check Bihor (Holod bbox center 22.109, 46.771) dot exists & clickable.
  await setView(46.77, 22.11, 10);
  await page.waitForTimeout(1500);
  const pos2 = await computePos(22.109, 46.771);
  if (pos2) {
    await clickAt(pos2.x, pos2.y);
    const text = await readCardText();
    check(/Holod/i.test(text), `click Holod dot opens card ('${text.slice(0, 60)}')`);
  } else {
    check(false, 'computePos failed for Holod');
  }

  // 4. Maramureș (Botiza bbox center 24.152, 47.669) dot.
  await setView(47.67, 24.15, 10);
  await page.waitForTimeout(1500);
  const pos3 = await computePos(24.152, 47.669);
  if (pos3) {
    await clickAt(pos3.x, pos3.y);
    const text = await readCardText();
    check(/Botiza/i.test(text), `click Botiza dot opens card ('${text.slice(0, 60)}')`);
  } else {
    check(false, 'computePos failed for Botiza');
  }

  console.log(failures === 0 ? '\nALL PASS' : `\n${failures} FAILURES`);
  await browser.close();
  process.exit(failures === 0 ? 0 : 1);
})().catch((e) => { console.error('e2e error:', e); process.exit(2); });
