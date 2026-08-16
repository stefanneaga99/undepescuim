/* eslint-disable no-console */
/**
 * Nearby-waters county/distance e2e (t_6c2ac870) — the 4 wrong-county lake
 * centroids + the nearby-card county chip.
 *
 * Passes (LOCAL chromium only — real geolocation grant path):
 *  1. Poiana Brașov (45.594, 25.556): the nearby list must NOT contain
 *     'Lacul Dumbrăvița' (Timiș — stale centroid was ~18 km from Brașov, real
 *     distance ~330 km), nor Pangrati/Toplița/Arpașu; the 'Râul Dâmbovița'
 *     row must show its OWN county for the visible segment (Argeș — the upper
 *     course nearest Brașov), NOT 'Ilfov' (the AVPS ACVILA seat).
 *  2. Pângărați (Neamț): 'Lac Pangrati' row at a sane distance (< 5 km) with
 *     chip 'Neamț' (was computed from a centroid ~11 km away).
 *  3. Arpașu de Jos (Sibiu side): 'Lac acumulare Arpașu' rows at ~0 km, chip
 *     'Sibiu' — the Brașov-side contract entry (judet=Brașov) shows the
 *     water's own segment county, not the contract county.
 *
 * Run: node scripts/_e2e_nearby_county.mjs   (BASE_URL defaults localhost:3100)
 */
import { chromium } from 'playwright';

const ARG_BASE = process.argv[2] || process.env.BASE_URL || 'http://localhost:3100';
// Local chromium must hit localhost (a secure context — geolocation refuses
// on plain-HTTP LAN IPs: "Only secure origins are allowed").
const BASE = ARG_BASE.replace(/^http:\/\/[^/:]+/, 'http://localhost');
const origin = new URL(BASE).origin;

const browser = await chromium.launch({ args: ['--no-sandbox'] });

let failures = 0;
const check = (cond, label) => {
  if (cond) console.log(`  PASS  ${label}`);
  else { console.log(`  FAIL  ${label}`); failures += 1; }
};

const sheetText = (page) =>
  page.evaluate(() => {
    const el = document.querySelector('[data-nearby-sheet]');
    return el ? (el.textContent || '').trim() : '';
  });

const readSheet = async (page, timeoutMs = 12000) => {
  const deadline = Date.now() + timeoutMs;
  let last = '';
  while (Date.now() < deadline) {
    last = await sheetText(page);
    if (last.includes('Ape în apropiere') && last.includes('km')) return last;
    await page.waitForTimeout(250);
  }
  return last;
};

/** [{text, chip}] rows inside the nearby sheet (chip = the county · assoc line). */
const sheetRows = (page) =>
  page.evaluate(() => {
    const sheet = document.querySelector('[data-nearby-sheet]');
    if (!sheet) return [];
    return [...sheet.querySelectorAll('li')].map((li) => {
      const p = li.querySelector('p');
      return { text: (li.textContent || '').trim(), chip: p ? (p.textContent || '').trim() : '' };
    });
  });

const waitForMap = async (page) => {
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('button:visible[aria-pressed]', { timeout: 90000 });
  await page.waitForFunction(
    () => document.querySelectorAll('.leaflet-overlay-pane path').length > 0,
    { timeout: 60000 },
  ).catch(() => console.log('  warn: no overlay paths after load wait'));
  await page.waitForTimeout(1200);
};

async function runPass(label, geolocation, asserts) {
  console.log(`\n== ${label} @1280px ==`);
  const ctx = await browser.newContext();
  const p = await ctx.newPage();
  await p.setViewportSize({ width: 1280, height: 800 });
  await ctx.grantPermissions(['geolocation'], { origin });
  await ctx.setGeolocation(geolocation);
  await waitForMap(p);

  await p.locator('button[aria-label="Localizează-mă"]').click();
  await p.waitForTimeout(2500); // flyTo + sheet

  const text = await readSheet(p);
  check(text.includes('Ape în apropiere'), 'sheet title "Ape în apropiere"');
  const rows = await sheetRows(p);
  check(rows.length >= 1, `nearby rows rendered (${rows.length})`);
  await asserts({ p, text, rows });
  await p.screenshot({ path: `.e2e/nearby_county_${label.replace(/\s+/g, '_').toLowerCase()}.png` });
  await p.close();
  await ctx.close();
}

// ── Pass 1: Poiana Brașov ────────────────────────────────────────────────
await runPass('poiana-brasov', { latitude: 45.594, longitude: 25.556 }, async ({ text, rows }) => {
  check(text.includes('Rază: 25 km'), 'default 25 km radius (≥3 waters nearby)');
  for (const lake of ['Dumbrăvița', 'Pangrati', 'Toplița', 'Arpașu']) {
    check(!text.includes(lake), `wrong-county lake absent from nearby list (${lake})`);
  }
  const damb = rows.find((r) => r.text.includes('Dâmbovița'));
  check(!!damb, 'Râul Dâmbovița row present');
  if (damb) {
    check(!damb.chip.includes('Ilfov'), `Dâmbovița chip NOT the association seat (got: "${damb.chip}")`);
    check(/Argeș · AVPS ACVILA/.test(damb.chip), `Dâmbovița chip = own county (got: "${damb.chip}")`);
  }
});

// ── Pass 2: Pângărați (Neamț) — Lac Pangrati ─────────────────────────────
await runPass('pangarati-neamt', { latitude: 46.93, longitude: 26.19 }, async ({ rows }) => {
  const row = rows.find((r) => r.text.includes('Lac Pangrati'));
  check(!!row, 'Lac Pangrati row present');
  if (row) {
    // distance renders as "N.N km" or "N m" (under 1 km)
    const km = row.text.match(/(\d+(?:\.\d)?)\s*km/);
    const m = row.text.match(/(\d+)\s*m\b/);
    const distKm = km ? Number(km[1]) : m ? Number(m[1]) / 1000 : null;
    check(distKm !== null && distKm < 5, `Lac Pangrati distance sane (< 5 km, got "${distKm ?? '?'} km")`);
    check(row.chip.includes('Neamț'), `Lac Pangrati chip = Neamț (got: "${row.chip}")`);
  }
});

// ── Pass 3: Arpașu de Jos (Sibiu side of the border lake) ────────────────
await runPass('arpasu-sibiu', { latitude: 45.789, longitude: 24.61 }, async ({ rows }) => {
  const row = rows.find((r) => r.text.includes('Lac acumulare Arpașu'));
  check(!!row, 'Lac acumulare Arpașu row present');
  if (row) {
    const km = row.text.match(/(\d+(?:\.\d)?)\s*km|(\d+)\s*m/);
    check(km && (Number(km[1] ?? 0) < 2), `Arpașu distance ~0 (< 2 km, got "${km?.[1] ?? km?.[2] ?? '?'}")`);
    check(row.chip.includes('Sibiu'), `Arpașu chip = Sibiu (segment county, got: "${row.chip}")`);
  }
});

await browser.close();
console.log(failures === 0 ? 'NEARBY COUNTY E2E PASSED' : `NEARBY COUNTY E2E FAILED (${failures} checks)`);
process.exit(failures === 0 ? 0 : 1);
