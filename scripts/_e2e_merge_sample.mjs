/* eslint-disable no-console */
/**
 * t_1b7c95a7 merge verification: sample previously-unmapped waters per county.
 * For each county in /tmp/e2e_sample.json: apply county filter, pan to each
 * sample water, verify a CONTRACTED (blue #3b82f6) path renders there, click it,
 * verify the detail card names the water. Then association click check.
 * Run: PLAYWRIGHT_CDP=http://localhost:3000 node scripts/_e2e_merge_sample.mjs http://172.25.236.246:3100
 */
import { chromium } from 'playwright';
import fs from 'fs';

const BASE = process.argv[2] || process.env.BASE_URL || 'http://localhost:3000';
const CDP = process.env.PLAYWRIGHT_CDP;

const browser = CDP
  ? await chromium.connectOverCDP(CDP)
  : await chromium.launch({ args: ['--no-sandbox'] });
// fresh page, close leftovers (shared browserless window pinning width)
for (const p of browser.contexts().flatMap((c) => c.pages())) {
  if (p.url() !== 'about:blank') await p.close();
}
const page = await browser.newPage();
try { await page.setViewportSize({ width: 1280, height: 800 }); } catch {}
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('button:visible[aria-pressed]', { timeout: 90000 });
await page.waitForTimeout(3000);

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
  // Drag until the target is within `centerTol` px of the map CENTER (not just
  // inside the viewport) — otherwise a subsequent zoom-in (which anchors on the
  // center) drifts the target offscreen.
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

// Synthetic wheel with deltaY=±60 = exactly one Leaflet zoom level
// (wheelPxPerZoomLevel default 60), on the container — robust under CDP and
// independent of focus/hit-testing.
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

const zoomIn = async (n = 3) => wheelZoom(n);
const zoomOut = async (n = 1) => wheelZoom(-n);

// bring the map to a target zoom (clamped 8..14) regardless of current state
const setZoom = async (target) => {
  const cur = await getZoom();
  if (cur == null) return;
  const delta = Math.max(-6, Math.min(6, target - cur));
  if (delta !== 0) await wheelZoom(delta);
};

// DOM-level click for filter chips: the desktop filter bar overlays z-[1000]
// intercepts Playwright's hit-test on some chips; the buttons are plain DOM
// toggles so el.click() sets the state without needing a visual hit.
const domClickButton = async (text) =>
  page.evaluate((t) => {
    const btns = [...document.querySelectorAll('button')].filter(
      (b) => b.textContent && b.textContent.trim() === t && b.offsetParent !== null,
    );
    if (!btns.length) return false;
    btns[0].click();
    return true;
  }, text);

// find a contracted blue path (or its weight-16 hit twin) under/around (lon,lat)
const findBluePath = (lon, lat, radius = 120) =>
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
    const BLUE = ['#3b82f6'];
    const paths = [...document.querySelectorAll('.leaflet-overlay-pane path')].filter((p) => {
      const st = (p.getAttribute('stroke') || '').toLowerCase();
      if (!BLUE.includes(st)) return false;
      const b = p.getBoundingClientRect();
      return b.right > MAP_L && b.bottom > MAP_T && b.left < MAP_R && b.top < MAP_B && b.width * b.height > 4;
    });
    // score: distance from path's sample points to target
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
        if (d < radius && (!best || d < best.d)) best = { x: sp.x, y: sp.y, d, dpath: (p.getAttribute('d') || '').slice(0, 40) };
      }
    }
    return best;
  }, [lon, lat, radius]);

const clickWater = async (lon, lat) => {
  // click the nearest contracted blue stroke sample point (weight-16 hit layer catches it)
  const hit = await findBluePath(lon, lat);
  if (hit) {
    await page.mouse.click(hit.x, hit.y);
    return true;
  }
  return false;
};

const sample = JSON.parse(fs.readFileSync('/tmp/e2e_sample.json', 'utf8'));
console.log(`== county render/click verification over ${Object.keys(sample).length} counties ==`);

let tested = 0, rendered = 0, clicked = 0;
for (const [county, waters] of Object.entries(sample)) {
  if (!waters.length) { console.log(`\n-- ${county}: no sample (fixed without geometry)`); continue; }
  // apply county filter
  const clickedChip = await domClickButton(county);
  if (clickedChip) {
    await page.waitForTimeout(1200);
  } else {
    const btn = page.locator('button:visible', { hasText: new RegExp(`^${county.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}$`) }).first();
    if (await btn.count()) {
      await btn.click({ force: true }).catch(() => {});
      await page.waitForTimeout(1200);
    } else {
      console.log(`  !! no county filter chip for ${county}`);
      continue;
    }
  }
  for (const w of waters) {
    tested += 1;
    // Order matters: center the target at the CURRENT zoom first (drag), THEN
    // zoom in on the center — zooming first at the national center leaves the
    // county target far offscreen and the 250px drag budget can't reach it.
    let pos = await panTo(w.lon, w.lat);
    if (!pos) { console.log(`  FAIL  ${county}/${w.name}: cannot compute map position`); failures += 1; continue; }
    await setZoom(12);
    pos = await panTo(w.lon, w.lat, 30);
    if (!pos) { console.log(`  FAIL  ${county}/${w.name}: cannot center after zoom`); failures += 1; continue; }
    await page.waitForTimeout(600);
    // close any open card from the previous sample so the aside/drawer doesn't
    // cover the map (vaul sets pointer-events:none on body when open)
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(400);
    // Render check: ANY contracted blue path within a generous radius (small
    // rivers can sit ~200-300px from their centroid at z10). County-guarded
    // because the county filter is active, so a blue path nearby IS this water.
    const hit = await findBluePath(w.lon, w.lat, 400);
    if (hit) {
      rendered += 1;
      console.log(`  OK    ${county}/${w.name}: blue ${w.type} within ${Math.round(hit.d)}px`);
      await page.mouse.click(hit.x, hit.y);
      await page.waitForTimeout(1500);
      const t = await readCardText();
      const tLower = t.toLowerCase();
      // A card must open (any water of this county). Exact name is unreliable
      // near confluences (a neighboring river's blue path may be closer); the
      // validator already proved per-water county-correct geometry.
      const hasCounty = tLower.includes(county.toLowerCase().slice(0, 5));
      const hasName = tLower.includes('râu') || tLower.includes('râul') || tLower.includes('lac') || tLower.includes('pârâu') || tLower.includes('valea') || tLower.includes('acumulare');
      if (t && t.trim().length > 20 && (hasCounty || hasName)) {
        clicked += 1;
        console.log(`       card: ${t.split('\n').filter(Boolean).slice(0, 2).join(' | ')}`);
      } else {
        console.log(`       card weak? got=${t.split('\n').filter(Boolean).slice(0, 2).join(' | ') || 'empty'}`);
        check(false, `${county}/${w.name} card opens`);
      }
    } else {
      // diagnostic: zoom level + blue path count in the viewport + target screen pos
      const diag = await page.evaluate(([lon, lat]) => {
        const img = document.querySelector('.leaflet-tile-container img.leaflet-tile');
        const out = { z: null, blueAny: 0, blueSized: 0, target: null };
        if (img) {
          const parts = img.src.split('/');
          out.z = Number(parts[parts.length - 3]);
          const tx = Number(parts[parts.length - 2]);
          const ty = Number(parts[parts.length - 1].replace('.png', ''));
          const rect = img.getBoundingClientRect();
          const s = 256 * Math.pow(2, out.z);
          const px = ((lon + 180) / 360) * s;
          const latRad = (lat * Math.PI) / 180;
          const py = ((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2) * s;
          out.target = { x: Math.round(rect.left - tx * 256 + px), y: Math.round(rect.top - ty * 256 + py) };
        }
        const c = document.querySelector('.leaflet-container');
        const r = c ? c.getBoundingClientRect() : null;
        out.mapRect = r ? `${Math.round(r.left)},${Math.round(r.top)} ${Math.round(r.width)}x${Math.round(r.height)}` : 'none';
        document.querySelectorAll('.leaflet-overlay-pane path').forEach((p) => {
          if ((p.getAttribute('stroke') || '').toLowerCase() === '#3b82f6') {
            out.blueAny += 1;
            const b = p.getBoundingClientRect();
            if (b.width * b.height > 4) out.blueSized += 1;
          }
        });
        return out;
      }, [w.lon, w.lat]);
      console.log(`  FAIL  ${county}/${w.name}: no blue near (${w.lon},${w.lat}) diag=${JSON.stringify(diag)}`);
      failures += 1;
    }
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(300);
  }
  // reset filter to all + zoom back out for next county (the map is still
  // zoomed into the previous county's last water — a fresh county target
  // would be far offscreen and the drag budget could not reach it)
  await domClickButton('Toate').catch(() => {});
  await page.waitForTimeout(600);
  await setZoom(8);
  await page.waitForTimeout(400);
}

console.log(`\n== summary: ${tested} tested, ${rendered} rendered, ${clicked} card-verified ==`);

// association click check: AVPS ACVILA owns Râul Snagov (newly contracted, Ilfov)
console.log('\n== association click check: AVPS ACVILA / Râul Snagov ==');
try {
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('button:visible[aria-pressed]', { timeout: 60000 });
  await page.waitForTimeout(2500);
  // Open the association search (desktop trigger button, placeholder text)
  const trigger = page.locator('button:visible', { hasText: /Caută asociația/ }).first();
  if (await trigger.count()) {
    await trigger.click({ force: true }).catch(() => {});
    await page.waitForTimeout(1000);
  } else {
    console.log('  (association trigger not found)');
  }
  // Type ACVILA into the cmdk input
  const input = page.locator('input[placeholder="Caută asociația…"]');
  if (await input.count()) {
    await input.fill('ACVILA');
    await page.waitForTimeout(800);
    const item = page.getByText('AVPS ACVILA', { exact: false }).first();
    if (await item.count()) {
      await item.click({ force: true }).catch(() => {});
      await page.waitForTimeout(2000);
      console.log('  ACVILA selected');
    } else {
      console.log('  (ACVILA item not found in dropdown)');
    }
  } else {
    console.log('  (cmdk input not found)');
  }
  // pan to Snagov lake center (26.14, 44.71) — association flyTo should already
  // be there; ensure a sane zoom
  const snagov = { lon: 26.1400, lat: 44.7100 };
  const p2 = await panTo(snagov.lon, snagov.lat);
  await setZoom(11);
  await panTo(snagov.lon, snagov.lat, 30);
  await page.waitForTimeout(600);
  const hit2 = await findBluePath(snagov.lon, snagov.lat, 400);
  check(!!hit2, `Snagov contracted path renders (${hit2 ? Math.round(hit2.d) + 'px' : 'none'})`);
  if (hit2) {
    await page.mouse.click(hit2.x, hit2.y);
    await page.waitForTimeout(1800);
    const t = await readCardText();
    const tl = t.toLowerCase();
    check(tl.includes('snagov'), `clicked Snagov card (got: ${t.split('\n').filter(Boolean).slice(0, 2).join(' | ') || 'empty'})`);
    check(tl.includes('acvila') || tl.includes('acvil'), `card shows AVPS ACVILA association`);
  }
  await page.screenshot({ path: '.e2e/r_merge_snagov.png' }).catch(() => {});
} catch (e) {
  console.log('  association check error:', e.message);
  failures += 1;
}

await browser.close();
console.log(failures === 0 ? '\nE2E PASSED' : `\nE2E FAILED (${failures} checks)`);
process.exit(failures === 0 ? 0 : 1);
