/* eslint-disable no-console */
/**
 * Geolocation MVP e2e (t_5ddc6022) — docs/geolocation-feasibility.md AC1-AC7.
 *
 * Three passes:
 *  1. desktop @1280 Bucharest  — granted fix → blue user dot + radius circle
 *     appear, map centers (zoom ≥ 12), "Ape în apropiere" sheet renders rows
 *     with km/county/association, tapping a row opens the existing water card.
 *  2. mobile  @390 Iași        — adaptive radius: 1 contracted water within
 *     25 km → expands to 50 km ("Rază: 50 km"), vaul bottom-sheet branch,
 *     row tap opens the water card drawer.
 *  3. deny @1280               — PERMISSION_DENIED → graceful bubble, map
 *     untouched (no dot, no sheet, tile zoom stays at default).
 *
 * Browser mode:
 *  - default: LOCAL chromium (preferred — isolated window, real
 *    navigator.geolocation via Playwright grantPermissions + setGeolocation).
 *    Requires /tmp/asound (see undepescuim-e2e-playwright skill pitfall 11).
 *  - PLAYWRIGHT_CDP=http://localhost:3000: browserless shared window; the
 *    geolocation API is stubbed with addInitScript (CDP can't emulate
 *    permissions) — exercises the same app flow minus the native prompt.
 *
 * Run: node scripts/_e2e_geolocation.mjs http://172.25.236.246:3100
 *      PLAYWRIGHT_CDP=http://localhost:3000 node scripts/_e2e_geolocation.mjs http://172.25.236.246:3100
 */
import { chromium } from 'playwright';

const ARG_BASE = process.argv[2] || process.env.BASE_URL || 'http://localhost:3100';
const CDP = process.env.PLAYWRIGHT_CDP;
// Local chromium must hit localhost (a secure context — geolocation refuses
// on plain-HTTP LAN IPs: "Only secure origins are allowed"). The browserless
// CDP container can only reach the host via the LAN IP, so it uses the raw
// URL + stubbed geolocation (CDP can't emulate permissions anyway).
const BASE = CDP ? ARG_BASE : ARG_BASE.replace(/^http:\/\/[^/:]+/, 'http://localhost');
const origin = new URL(BASE).origin;

const browser = CDP ? await chromium.connectOverCDP(CDP) : await chromium.launch({ args: ['--no-sandbox'] });

let failures = 0;
const check = (cond, label) => {
  if (cond) console.log(`  PASS  ${label}`);
  else { console.log(`  FAIL  ${label}`); failures += 1; }
};

const tileZoom = (page) =>
  page.evaluate(() => {
    const t = document.querySelector('.leaflet-tile');
    if (!t) return null;
    const m = (t.getAttribute('src') || '').match(/\/(\d+)\/\d+\/\d+(?:@2x)?\.png/);
    return m ? Number(m[1]) : null;
  });

const sheetText = (page) =>
  page.evaluate(() => {
    const el = document.querySelector('[data-nearby-sheet]');
    return el ? (el.textContent || '').trim() : '';
  });

const readSheet = async (page, timeoutMs = 10000) => {
  const deadline = Date.now() + timeoutMs;
  let last = '';
  while (Date.now() < deadline) {
    last = await sheetText(page);
    if (last.includes('Ape în apropiere') && last.includes('km')) return last;
    await page.waitForTimeout(250);
  }
  return last;
};

const cardText = (page) =>
  page.evaluate(() => {
    // Desktop: the water aside contains an <h2> (panel header 'Detalii apă').
    // Mobile: the water drawer carries aria-label="Detalii: <name>" — the
    // literal 'Detalii' is NOT in its textContent, so match the aria-label.
    const aside = document.querySelector('aside:has(h2)');
    const drawer = [...document.querySelectorAll('[data-vaul-drawer]')]
      .find((d) => (d.getAttribute('aria-label') || '').startsWith('Detalii'));
    const el = aside || drawer;
    return el ? (el.textContent || '').trim() : '';
  });

const readCard = async (page, timeoutMs = 12000) => {
  const deadline = Date.now() + timeoutMs;
  let last = '';
  while (Date.now() < deadline) {
    last = await cardText(page);
    if (last && last.trim()) return last;
    await page.waitForTimeout(300);
  }
  return last;
};

const waitForMap = async (page) => {
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('button:visible[aria-pressed]', { timeout: 90000 });
  await page.waitForFunction(
    () => document.querySelectorAll('.leaflet-overlay-pane path').length > 0,
    { timeout: 60000 },
  ).catch(() => console.log('  warn: no overlay paths after load wait'));
  await page.waitForTimeout(1200);
};

/** Stub navigator.geolocation BEFORE app scripts run (CDP / deny paths). */
const stubGeolocation = (page, mode, geolocation) =>
  page.addInitScript(({ mode: m, geolocation: geo }) => {
    Object.defineProperty(navigator, 'geolocation', {
      configurable: true,
      value: {
        getCurrentPosition: (ok, err) => {
          if (m === 'grant') {
            ok({
              coords: { latitude: geo.latitude, longitude: geo.longitude, accuracy: 30 },
              timestamp: Date.now(),
            });
          } else {
            const e = new Error('User denied Geolocation');
            e.code = 1; // PERMISSION_DENIED
            e.PERMISSION_DENIED = 1;
            e.PERMISSION_DENIED_TIMEOUT = 3;
            err(e);
          }
        },
      },
    });
  }, { mode, geolocation });

async function runGrantPass(width, height, label, geolocation, expectRadius) {
  console.log(`\n== ${label} @${width}px ==`);
  const p = CDP ? await browser.newPage() : await (await browser.newContext()).newPage();
  await p.setViewportSize({ width, height });
  if (CDP) {
    await stubGeolocation(p, 'grant');
  } else {
    const ctx = p.context();
    await ctx.grantPermissions(['geolocation'], { origin });
    await ctx.setGeolocation(geolocation);
  }
  await waitForMap(p);

  const zoomBefore = await tileZoom(p);
  const locateBtn = p.locator('button[aria-label="Localizează-mă"]');
  check(await locateBtn.isVisible(), 'Locate button visible (FAB)');
  await locateBtn.click();
  await p.waitForTimeout(2500); // flyTo + sheet

  const zoomAfter = await tileZoom(p);
  check(zoomAfter !== null && zoomAfter >= 12, `map centers on user (zoom ${zoomAfter}, was ${zoomBefore})`);

  check(await p.locator('.user-position-dot').isVisible().catch(() => false), 'blue user dot rendered');
  const circleStrokes = await p.evaluate(() =>
    [...document.querySelectorAll('.leaflet-overlay-pane path')]
      .filter((el) => (el.getAttribute('stroke') || '').toLowerCase() === '#2563eb').length,
  );
  check(circleStrokes >= 1, `radius circle drawn (#2563eb paths: ${circleStrokes})`);

  const text = await readSheet(p);
  check(text.includes('Ape în apropiere'), 'sheet title "Ape în apropiere"');
  check(text.includes('date 2026'), 'honest "date 2026" freshness label');
  if (expectRadius) check(text.includes(`Rază: ${expectRadius} km`), `adaptive radius label "Rază: ${expectRadius} km"`);
  const rowCount = await p.evaluate(() =>
    document.querySelector('[data-nearby-sheet]')?.querySelectorAll('li').length ?? 0,
  );
  check(rowCount >= 1, `nearby rows rendered (${rowCount})`);
  check(/\d+(\.\d)? km|\d+ m/.test(text), 'rows show distances (km/m)');
  await p.screenshot({ path: `.e2e/geolocation_${label.replace(/\s+/g, '_').toLowerCase()}.png` });

  // Tap the first row → existing water detail card opens
  const firstRow = p.locator('[data-nearby-sheet] li button').first();
  const rowText = ((await firstRow.textContent().catch(() => '')) || '').split('\n')[0].trim();
  await firstRow.click().catch(async () => firstRow.evaluate((el) => el.click()));
  const card = await readCard(p);
  check(card.includes('Asociație') || card.includes('Permis'), `row tap opens water card (row: ${rowText})`);

  await p.close();
  if (!CDP) await p.context().close();
}

async function runDenyPass() {
  console.log('\n== deny @1280px (PERMISSION_DENIED) ==');
  const p = CDP ? await browser.newPage() : await (await browser.newContext()).newPage();
  await p.setViewportSize({ width: 1280, height: 800 });
  if (CDP) {
    await stubGeolocation(p, 'deny', { latitude: 44.4, longitude: 26.1 });
  } else {
    // Real permission flow: deny via permissions policy override.
    await p.context().clearPermissions();
    await stubGeolocation(p, 'deny', { latitude: 44.4, longitude: 26.1 });
  }
  await waitForMap(p);

  const zoomBefore = await tileZoom(p);
  await p.locator('button[aria-label="Localizează-mă"]').click();
  await p.waitForTimeout(1200);

  const bodyText = await p.evaluate(() => document.body.textContent || '');
  check(bodyText.includes('Accesul la locație este blocat'), 'denied bubble shown (localized)');
  check(!(await p.locator('.user-position-dot').count()), 'no user dot on deny');
  check(!bodyText.includes('Ape în apropiere'), 'no nearby sheet on deny');
  const zoomAfter = await tileZoom(p);
  check(zoomAfter === zoomBefore, `map view untouched on deny (zoom ${zoomAfter})`);
  await p.screenshot({ path: '.e2e/geolocation_deny.png' });
  await p.close();
  if (!CDP) await p.context().close();
}

// Close leftover pages from crashed runs — they share the single browserless window.
if (CDP) {
  for (const ctx of browser.contexts()) {
    for (const p of ctx.pages()) {
      if (p.url() !== 'about:blank') await p.close().catch(() => {});
    }
  }
}

await runGrantPass(
  1280, 800, 'desktop-bucharest',
  { latitude: 44.4268, longitude: 26.1025 },
  null, // 4 contracted waters within 25 km → default radius, no expansion
);
await runGrantPass(
  390, 844, 'mobile-iasi',
  { latitude: 47.1585, longitude: 27.6014 },
  50, // 1 within 25 km → adaptive expansion to 50 km
);
await runDenyPass();

await browser.close();
console.log(failures === 0 ? 'GEOLOCATION E2E PASSED' : `GEOLOCATION E2E FAILED (${failures} checks)`);
process.exit(failures === 0 ? 0 : 1);
