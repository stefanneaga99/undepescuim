/* eslint-disable no-console */
/**
 * Bottom-sheet drag handle e2e (t_f21260ee).
 *
 * Regression for the mobile bug report: the sheet grabber bar was too
 * small/thin to grab. After the fix the handle is a full-width, 44px-tall
 * touch target (vaul Drawer.Handle + globals.css override) with tap-to-cycle
 * as a no-drag fallback.
 *
 * Passes:
 *  1. mobile @390×844 (Iași geolocation) — nearby sheet + water card drawers:
 *     handle geometry (full width, height >= 32), hit-testable from edge to
 *     edge (elementFromPoint lands on the handle), tap-to-expand cycles snap
 *     points, drag up/down moves the drawer, content scrolls at the expanded
 *     snap, ESC still closes.
 *  2. desktop @1280×800 (Bucharest) — no drawer, no handle element anywhere
 *     (mobile-only concern; desktop side panel unaffected).
 *
 * Browser: LOCAL chromium required for the real geolocation grant path
 * (see undepescuim-e2e-playwright skill). Falls back to the CDP stub path
 * when PLAYWRIGHT_CDP is set (same flow minus native permission).
 *
 * Run: node scripts/_e2e_sheet_handle.mjs http://172.25.236.246:3100
 */
import { chromium } from 'playwright';

const ARG_BASE = process.argv[2] || process.env.BASE_URL || 'http://localhost:3100';
const CDP = process.env.PLAYWRIGHT_CDP;
// Local chromium must hit localhost (secure context for geolocation).
const BASE = CDP ? ARG_BASE : ARG_BASE.replace(/^http:\/\/[^/:]+/, 'http://localhost');
const origin = new URL(BASE).origin;

const browser = CDP ? await chromium.connectOverCDP(CDP) : await chromium.launch({ args: ['--no-sandbox'] });

let failures = 0;
const check = (cond, label) => {
  if (cond) console.log(`  PASS  ${label}`);
  else { console.log(`  FAIL  ${label}`); failures += 1; }
};

const stubGeolocation = (page, mode, geolocation) =>
  page.addInitScript(({ mode: m, geolocation: geo }) => {
    Object.defineProperty(navigator, 'geolocation', {
      configurable: true,
      value: {
        getCurrentPosition: (ok, err) => {
          if (m === 'grant') {
            ok({ coords: { latitude: geo.latitude, longitude: geo.longitude, accuracy: 30 }, timestamp: Date.now() });
          } else {
            const e = new Error('User denied Geolocation');
            e.code = 1; e.PERMISSION_DENIED = 1; e.PERMISSION_DENIED_TIMEOUT = 3;
            err(e);
          }
        },
      },
    });
  }, { mode, geolocation });

const waitForMap = async (page) => {
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('button:visible[aria-pressed]', { timeout: 90000 });
  await page.waitForFunction(
    () => document.querySelectorAll('.leaflet-overlay-pane path').length > 0,
    { timeout: 60000 },
  ).catch(() => console.log('  warn: no overlay paths after load wait'));
  await page.waitForTimeout(1200);
};

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

const readCard = async (page, timeoutMs = 12000) => {
  const deadline = Date.now() + timeoutMs;
  let last = '';
  while (Date.now() < deadline) {
    last = await page.evaluate(() => {
      const drawer = [...document.querySelectorAll('[data-vaul-drawer]')]
        .find((d) => (d.getAttribute('aria-label') || '').startsWith('Detalii'));
      return drawer ? (drawer.textContent || '').trim() : '';
    });
    if (last && last.trim()) return last;
    await page.waitForTimeout(300);
  }
  return last;
};

/** Handle geometry + hit-test info for a drawer root (or null). */
const handleInfo = (page, drawerSel) =>
  page.evaluate((sel) => {
    const root = sel ? document.querySelector(sel) : document.querySelector('[data-vaul-drawer]');
    const handle = root?.querySelector('[data-vaul-handle]');
    if (!handle) return null;
    const r = handle.getBoundingClientRect();
    const pill = handle.querySelector('[data-vaul-handle-hitarea] span, [data-vaul-handle-hitarea]');
    const pr = pill ? pill.getBoundingClientRect() : null;
    // Hit-test several points across the strip (left edge, center, right edge).
    const samples = [0.1, 0.5, 0.9].map((frac) => {
      const x = r.left + r.width * frac;
      const y = r.top + r.height / 2;
      const el = document.elementFromPoint(x, y);
      return {
        x: Math.round(x), y: Math.round(y),
        hitsHandle: !!el && !!el.closest('[data-vaul-handle]'),
        tag: el ? `${el.tagName}.${(el.className || '').toString().split(' ')[0]}` : 'null',
      };
    });
    return {
      width: Math.round(r.width), height: Math.round(r.height),
      top: Math.round(r.top), left: Math.round(r.left),
      pill: pr ? { w: Math.round(pr.width), h: Math.round(pr.height) } : null,
      samples,
    };
  }, drawerSel);

const drawerTop = (page, drawerSel) =>
  page.evaluate((sel) => {
    const el = document.querySelector(sel);
    return el ? Math.round(el.getBoundingClientRect().top) : null;
  }, drawerSel);

async function runMobilePass() {
  console.log('\n== mobile @390x844 (București — nearby sheet + water card) ==');
  const p = CDP ? await browser.newPage() : await (await browser.newContext()).newPage();
  await p.setViewportSize({ width: 390, height: 844 });
  if (CDP) {
    await stubGeolocation(p, 'grant');
  } else {
    const ctx = p.context();
    await ctx.grantPermissions(['geolocation'], { origin });
    await ctx.setGeolocation({ latitude: 44.4268, longitude: 26.1025 });
  }
  await waitForMap(p);

  await p.locator('button[aria-label="Localizează-mă"]').click();
  await readSheet(p);
  await p.waitForTimeout(900); // open animation + snap settle

  const nearbySel = '[data-nearby-sheet]';
  const h1 = await handleInfo(p, nearbySel);
  check(!!h1, 'nearby sheet has a drag handle');
  check(h1 && h1.width >= 380, `nearby handle full-width (${h1?.width}px >= 380)`);
  check(h1 && h1.height >= 32, `nearby handle tall enough (${h1?.height}px >= 32)`);
  check(h1 && h1.samples.every((s) => s.hitsHandle),
    `nearby handle hit-testable edge-to-edge (${h1?.samples.map((s) => `${s.tag}@${s.x},${s.y}${s.hitsHandle ? '✓' : '✗'}`).join(' ')})`);
  check(h1 && h1.pill && h1.pill.w > 0 && h1.pill.h > 0, `visual pill present (${h1?.pill?.w}x${h1?.pill?.h})`);
  await p.screenshot({ path: '.e2e/sheet_handle_nearby_collapsed.png' });

  // ── tap-to-expand (no drag fallback): tap cycles 0.15 → 0.45
  const topBeforeTap = await drawerTop(p, nearbySel);
  const tapPoint = { x: Math.round((h1.left + h1.width / 2) / 1), y: Math.round(h1.top + h1.height / 2) };
  await p.mouse.click(tapPoint.x, tapPoint.y);
  await p.waitForTimeout(800);
  const topAfterTap = await drawerTop(p, nearbySel);
  check(topAfterTap !== null && topBeforeTap !== null && topAfterTap < topBeforeTap,
    `tap handle expands sheet (top ${topBeforeTap}px -> ${topAfterTap}px)`);

  // ── drag up on the handle moves the drawer (re-read handle: sheet moved)
  let hNow = await handleInfo(p, nearbySel);
  const dragStart = { x: Math.round(hNow.left + hNow.width / 2), y: Math.round(hNow.top + hNow.height / 2) };
  const topBeforeDrag = await drawerTop(p, nearbySel);
  await p.mouse.move(dragStart.x, dragStart.y);
  await p.mouse.down();
  await p.mouse.move(dragStart.x, dragStart.y - 160, { steps: 10 });
  await p.mouse.up();
  await p.waitForTimeout(800);
  const topAfterDragUp = await drawerTop(p, nearbySel);
  check(topAfterDragUp !== null && topAfterDragUp < topBeforeDrag,
    `drag UP on handle lifts sheet (top ${topBeforeDrag}px -> ${topAfterDragUp}px)`);

  // ── content scrolls at the top snap (list is inside its own scroller)
  const nearbyScroll = await p.evaluate(() => {
    const sheet = document.querySelector('[data-nearby-sheet]');
    const scroller = sheet?.querySelector('[class*="overflow-y-auto"]');
    if (!scroller) return { found: false };
    return { found: true, scrollHeight: scroller.scrollHeight, clientHeight: scroller.clientHeight };
  });
  if (nearbyScroll.found && nearbyScroll.scrollHeight > nearbyScroll.clientHeight) {
    const st = await p.evaluate(() => {
      const sheet = document.querySelector('[data-nearby-sheet]');
      const scroller = sheet.querySelector('[class*="overflow-y-auto"]');
      scroller.scrollTop = 0;
      scroller.scrollTo({ top: Math.min(scroller.scrollHeight, 200), behavior: 'instant' });
      return scroller.scrollTop;
    });
    check(st > 0, `nearby list scrolls at top snap (scrollTop ${st}px)`);
  } else {
    console.log(`  warn: nearby list fits at top snap (${nearbyScroll.scrollHeight}<=${nearbyScroll.clientHeight}) — no scroll to verify`);
  }

  // ── drag down on the handle lowers it back (re-read handle again)
  hNow = await handleInfo(p, nearbySel);
  const dragDownStart = { x: Math.round(hNow.left + hNow.width / 2), y: Math.round(hNow.top + hNow.height / 2) };
  const topBeforeDragDown = await drawerTop(p, nearbySel);
  await p.mouse.move(dragDownStart.x, dragDownStart.y);
  await p.mouse.down();
  await p.mouse.move(dragDownStart.x, dragDownStart.y + 220, { steps: 10 });
  await p.mouse.up();
  await p.waitForTimeout(800);
  const topAfterDragDown = await drawerTop(p, nearbySel);
  check(topAfterDragDown !== null && topAfterDragDown > topBeforeDragDown,
    `drag DOWN on handle lowers sheet (top ${topBeforeDragDown}px -> ${topAfterDragDown}px)`);

  // ── open water cards from nearby rows; verify handle + tap-to-expand +
  //    content-scroll on each, moving to the next row until a card overflows
  const rows = p.locator('[data-nearby-sheet] li button');
  const rowCount = await rows.count();
  check(rowCount >= 1, `nearby rows rendered (${rowCount})`);
  let scrollVerified = false;
  for (let i = 0; i < rowCount; i++) {
    const row = rows.nth(i);
    const rowText = ((await row.textContent().catch(() => '')) || '').split('\n')[0].trim();
    await row.click().catch(async () => row.evaluate((el) => el.click()));
    const card = await readCard(p);
    check(card.includes('Asociație') || card.includes('Permis'), `row tap opens water card (row: ${rowText})`);
    await p.waitForTimeout(700);

    // ── water card drawer handle (the z-[1200] drawer sits above nearby)
    const waterSel = '[data-vaul-drawer][aria-label^="Detalii"]';
    const h2 = await handleInfo(p, waterSel);
    check(!!h2, 'water card drawer has a drag handle');
    check(h2 && h2.width >= 380, `water handle full-width (${h2?.width}px >= 380)`);
    check(h2 && h2.height >= 32, `water handle tall enough (${h2?.height}px >= 32)`);
    check(h2 && h2.samples.every((s) => s.hitsHandle),
      `water handle hit-testable edge-to-edge (${h2?.samples.map((s) => `${s.tag}@${s.x},${s.y}${s.hitsHandle ? '✓' : '✗'}`).join(' ')})`);

    // ── water handle tap: 0.35 → 0.65 (tap-to-expand fallback)
    const wTopBefore = await drawerTop(p, waterSel);
    await p.mouse.click(Math.round(h2.left + h2.width / 2), Math.round(h2.top + h2.height / 2));
    await p.waitForTimeout(800);
    const wTopAfter = await drawerTop(p, waterSel);
    check(wTopAfter !== null && wTopBefore !== null && wTopAfter < wTopBefore,
      `tap water handle expands card (top ${wTopBefore}px -> ${wTopAfter}px)`);

    // ── content scrolls at the expanded snap (first overflowing card proves it)
    const scrollInfo = await p.evaluate(() => {
      const drawer = document.querySelector('[data-vaul-drawer][aria-label^="Detalii"]');
      const scroller = drawer?.querySelector('.overflow-y-auto') || drawer?.querySelector('[class*="overflow-y-auto"]');
      if (!scroller) return { found: false };
      return { found: true, scrollHeight: scroller.scrollHeight, clientHeight: scroller.clientHeight };
    });
    if (scrollInfo.found && scrollInfo.scrollHeight > scrollInfo.clientHeight) {
      const scrollTop = await p.evaluate(() => {
        const drawer = document.querySelector('[data-vaul-drawer][aria-label^="Detalii"]');
        const scroller = drawer.querySelector('.overflow-y-auto') || drawer.querySelector('[class*="overflow-y-auto"]');
        scroller.scrollTop = 0;
        scroller.scrollTo({ top: Math.min(scroller.scrollHeight, 300), behavior: 'instant' });
        return scroller.scrollTop;
      });
      check(scrollTop > 0, `content scrolls inside card (row: ${rowText}, scrollTop ${scrollTop}px of ${scrollInfo.scrollHeight - scrollInfo.clientHeight}px)`);
      scrollVerified = true;
      await p.screenshot({ path: '.e2e/sheet_handle_water_expanded.png' });
      break;
    }
    console.log(`  note: card "${rowText}" fits at expanded snap (${scrollInfo.scrollHeight}<=${scrollInfo.clientHeight}) — trying next row`);
    await p.keyboard.press('Escape');
    await p.waitForTimeout(600);
  }
  check(scrollVerified, 'content scrolls in an expanded water card');

  // ── ESC still closes the open water drawer
  await p.keyboard.press('Escape');
  await p.waitForTimeout(600);
  const waterGone = await p.evaluate(() =>
    !document.querySelector('[data-vaul-drawer][aria-label^="Detalii"]'));
  check(waterGone, 'ESC closes the water card');

  await p.screenshot({ path: '.e2e/sheet_handle_nearby_after_esc.png' });
  await p.close();
  if (!CDP) await p.context().close();
}

async function runDesktopPass() {
  console.log('\n== desktop @1280x800 (Bucharest — no drawer) ==');
  const p = CDP ? await browser.newPage() : await (await browser.newContext()).newPage();
  await p.setViewportSize({ width: 1280, height: 800 });
  if (CDP) {
    await stubGeolocation(p, 'grant');
  } else {
    const ctx = p.context();
    await ctx.grantPermissions(['geolocation'], { origin });
    await ctx.setGeolocation({ latitude: 44.4268, longitude: 26.1025 });
  }
  await waitForMap(p);

  const handlesBefore = await p.evaluate(() => document.querySelectorAll('[data-vaul-handle]').length);
  check(handlesBefore === 0, 'no drawer handle before locate (mobile-only concern)');

  await p.locator('button[aria-label="Localizează-mă"]').click();
  await readSheet(p);
  await p.waitForTimeout(900);
  const isDrawer = await p.evaluate(() => !!document.querySelector('[data-nearby-sheet] [data-vaul-handle]'));
  check(!isDrawer, 'nearby list is a floating panel on desktop (no drawer handle)');

  const firstRow = p.locator('[data-nearby-sheet] li button').first();
  const rowText = ((await firstRow.textContent().catch(() => '')) || '').split('\n')[0].trim();
  await firstRow.click().catch(async () => firstRow.evaluate((el) => el.click()));
  const card = await p.evaluate(() => {
    const aside = document.querySelector('aside:has(h2)');
    return aside ? (aside.textContent || '').trim() : '';
  }).catch(() => '');
  const cardReady = await p.waitForFunction(
    () => !!document.querySelector('aside:has(h2)') && (document.querySelector('aside:has(h2)').textContent || '').trim().length > 50,
    { timeout: 12000 },
  ).then(() => true).catch(() => false);
  check(cardReady, `water card opens in side panel (row: ${rowText})`);
  const handlesAfter = await p.evaluate(() => document.querySelectorAll('[data-vaul-handle]').length);
  check(handlesAfter === 0, 'still no drawer handle with card open (desktop unaffected)');
  await p.screenshot({ path: '.e2e/sheet_handle_desktop.png' });

  await p.close();
  if (!CDP) await p.context().close();
}

// Close leftover pages from crashed runs (shared browserless window).
if (CDP) {
  for (const ctx of browser.contexts()) {
    for (const p of ctx.pages()) {
      if (p.url() !== 'about:blank') await p.close().catch(() => {});
    }
  }
}

await runMobilePass();
await runDesktopPass();

await browser.close();
console.log(failures === 0 ? 'SHEET-HANDLE E2E PASSED' : `SHEET-HANDLE E2E FAILED (${failures} checks)`);
process.exit(failures === 0 ? 0 : 1);
