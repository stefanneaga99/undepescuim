/* eslint-disable no-console */
/**
 * Regression: selecting a locality must NOT clear map highlights — t_21d2f68d.
 *
 * Reported (2026-08-17, mobile dark mode): picking a LOCALITATE filter made
 * the association highlight (green bold) + click focus (orange) disappear.
 * Root cause: toggleLocality ran the old R9 auto-dismiss — a locality change
 * that hid the clicked water called selectWater(null), closing the card and
 * wiping the orange focus — and even kept, the water was no longer in the
 * rendered set. Fix (t_21d2f68d):
 *   - filter changes NEVER clear the selected water (map-store);
 *   - the selected water is PINNED back into the rendered set when a locality
 *     filter hides it (use-filtered-waters / use-filtered-uncontracted), so
 *     the orange focus stays visible.
 *
 * Desktop pass (1280, card OPEN — isolates the filter path from the
 * deselect-on-card-close):
 *   1. select AJVPS Buzău            -> green covered paths visible
 *   2. click a covered river         -> orange focus + green still visible
 *   3. county Buzău                 -> orange + green SURVIVE
 *   4. locality Siriu (clicked river is in Unguriu — OUTSIDE Siriu)
 *                                   -> orange + green SURVIVE (pinned)
 * Mobile pass (390): association highlight survives county + locality picks.
 *
 * Run: PLAYWRIGHT_CDP=http://localhost:3000 node scripts/_e2e_repro_locality_highlights.mjs <base>
 */
import { chromium } from 'playwright';

const BASE = process.argv[2] || 'https://undepescuim.vercel.app';
const CDP = process.env.PLAYWRIGHT_CDP;
const browser = CDP
  ? await chromium.connectOverCDP(CDP)
  : await chromium.launch({ args: ['--no-sandbox'] });

if (CDP) {
  for (const ctx of browser.contexts()) {
    for (const p of ctx.pages()) {
      if (p.url() !== 'about:blank') await p.close();
    }
  }
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

let failures = 0;
const check = (cond, label, extra = '') => {
  console.log(`  ${cond ? 'PASS' : 'FAIL'}  ${label}${extra ? `  [${extra}]` : ''}`);
  if (!cond) failures += 1;
};

async function freshPage(width, height) {
  const page = await browser.newPage();
  // CDP shared-window quirk: enforce the viewport BEFORE load and re-check it.
  await page.goto('about:blank');
  await page.setViewportSize({ width, height });
  const errors = [];
  page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));
  return { page, errors };
}

async function loadMap(page) {
  await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForFunction(() => {
    const el = document.querySelector('.leaflet-container');
    return !!el && el.getBoundingClientRect().height > 100;
  }, { timeout: 60000 }).catch(() => {});
  await sleep(2500);
  return page.evaluate(() => window.innerWidth);
}

const overlayStats = (page) => page.evaluate(() => {
  const paths = Array.from(document.querySelectorAll('.leaflet-overlay-pane path'));
  const strokes = paths.map((p) => (p.getAttribute('stroke') || '')).filter(Boolean);
  const count = (c) => strokes.filter((s) => s === c).length;
  return {
    total: paths.length,
    green: count('#22c55e'),
    orange: count('#f97316'),
    teal: count('#14b8a6') + count('#2dd4bf'),
    grey: count('#9ca3af'),
  };
});

async function selectAssociation(page, slug, name) {
  const searchers = page.locator(
    '[data-testid="assoc-search"], [data-testid="assoc-search-mobile"], button[aria-label="Search association"]',
  );
  const visible = await searchers.evaluateAll((els) => els.some((el) => el.offsetParent !== null));
  if (!visible) return false;
  await searchers.filter({ visible: true }).first().click();
  await page.waitForSelector('[data-testid="assoc-option"]', { timeout: 10000 });
  const cand = page.locator(`[data-testid="assoc-option"][data-slug="${slug}"]`);
  if ((await cand.count()) > 0) {
    await cand.first().click();
  } else {
    await page.locator('[data-slot="command-input"]').fill(name.split(' ')[0] ?? name);
    await sleep(400);
    await page.locator('[data-testid="assoc-option"]', { hasText: name }).first().click();
  }
  await page.keyboard.press('Escape').catch(() => {});
  await sleep(2500); // flyTo animates
  return true;
}

async function clickCoveredRiver(page) {
  const greenPaths = page.locator('.leaflet-overlay-pane path[stroke="#22c55e"]');
  const gpCount = await greenPaths.count();
  for (let i = 0; i < Math.min(gpCount, 40); i++) {
    const box = await greenPaths.nth(i).boundingBox().catch(() => null);
    if (!box) continue;
    const hit = await page.evaluate(
      ([x, y]) => {
        const el = document.elementFromPoint(x, y);
        return !!el && (el.tagName === 'path' || el.closest('path'));
      },
      [box.x + box.width / 2, box.y + box.height / 2],
    );
    if (!hit) continue;
    await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
    await sleep(1800);
    return true;
  }
  return false;
}

const desktopCardOpen = (page) =>
  page.evaluate(() => {
    const aside = document.querySelector('aside:has(h2)');
    if (!aside) return false;
    const bold = Array.from(aside.querySelectorAll('h2')).find((h) => h.classList.contains('font-bold'));
    return { name: bold ? bold.textContent : null };
  });

// ── Desktop pass (1280): card OPEN through the whole filter flow ────────────
{
  console.log(`== DESKTOP 1280 (card open) ==`);
  const { page, errors } = await freshPage(1280, 800);
  const w = await loadMap(page);
  console.log('  innerWidth:', w);
  if (w < 1024) {
    console.log('  SKIP desktop pass (shared window stuck at mobile width)');
    await page.close();
  } else {
    // Dark mode (as reported)
    if (!(await page.evaluate(() => document.documentElement.classList.contains('dark')))) {
      await page.locator('[data-testid="theme-toggle"]').first().click().catch(() => {});
      await sleep(500);
    }

    console.log('== 1. select association (AJVPS Buzău) ==');
    if (await selectAssociation(page, 'ajvps-buzao', 'AJVPS Buzău')) {
      let st = await overlayStats(page);
      console.log('  after assoc:', JSON.stringify(st));
      check(st.green > 0, `green covered paths visible (${st.green})`);

      console.log('== 2. click a green covered river ==');
      const clicked = await clickCoveredRiver(page);
      console.log('  clicked covered river:', clicked);
      st = await overlayStats(page);
      console.log('  after click:', JSON.stringify(st));
      check(st.orange > 0, `orange click focus visible (${st.orange})`);
      check(st.green > 0, `green association highlight STILL visible (${st.green})`);
      check(!!(await desktopCardOpen(page)), 'detail card open');

      console.log('== 3. county Buzău (card OPEN) ==');
      await page.locator('[data-testid="county-chip"][data-county="Buzău"]').first().evaluate((el) => el.click());
      await sleep(1800);
      st = await overlayStats(page);
      console.log('  after county:', JSON.stringify(st));
      check(st.orange > 0, `orange focus SURVIVES county filter (${st.orange})`);
      check(st.green > 0, `green highlight SURVIVES county filter (${st.green})`);
      check(!!(await desktopCardOpen(page)), 'detail card still open');

      console.log('== 4. locality Siriu (clicked river is in Unguriu — outside) ==');
      const locTriggers = page.locator('[data-testid="locality-filter"]');
      const locVisible = await locTriggers.evaluateAll((els) => els.some((el) => el.offsetParent !== null));
      if (locVisible) {
        await locTriggers.filter({ visible: true }).first().click();
        await page.waitForSelector('[data-testid="locality-option"]', { timeout: 8000 });
        const siriu = page.locator('[data-testid="locality-option"]', { hasText: /^Siriu$/ }).first();
        if ((await siriu.count()) > 0) await siriu.click();
        else await page.locator('[data-testid="locality-option"]').first().click();
        await sleep(2500);
        st = await overlayStats(page);
        console.log('  after locality:', JSON.stringify(st));
        check(st.orange > 0, `orange focus SURVIVES locality filter (pinned) (${st.orange})`);
        check(st.green > 0, `green highlight SURVIVES locality filter (${st.green})`);
        check(!!(await desktopCardOpen(page)), 'detail card STILL open (selection survives)');
        // Water count must still be narrow — the locality DID filter (15 vs
        // 88 county paths), only the selected water is pinned back.
        check(st.total < 40, `map narrowed to the locality + pinned focus (${st.total} paths)`);
      } else {
        check(false, 'locality filter visible');
        failures += 1;
      }
    } else {
      check(false, 'association search visible');
      failures += 1;
    }
    const interesting = errors.filter((e) => !/favicon|Failed to load resource|net::|Download the React DevTools/.test(e));
    console.log('  desktop console errors:', interesting.length ? interesting[0].slice(0, 200) : '(none)');
    await page.close();
  }
}

// ── Mobile pass (390): full reported flow — highlight survives card close
// ── and county + locality picks ─────────────────────────────────────────────
{
  console.log(`== MOBILE 390 (reported flow: click → close card → filters) ==`);
  const { page, errors } = await freshPage(390, 844);
  const w = await loadMap(page);
  console.log('  innerWidth:', w);
  if (w >= 768) {
    console.log('  SKIP mobile pass (shared window stuck at desktop width)');
    await page.close();
  } else {
    console.log('== 1. select association (AJVPS Buzău) ==');
    if (await selectAssociation(page, 'ajvps-buzao', 'AJVPS Buzău')) {
      let st = await overlayStats(page);
      console.log('  after assoc:', JSON.stringify(st));
      check(st.green > 0, `green covered paths visible (${st.green})`);

      console.log('== 2. click a green covered river (sheet opens) ==');
      const clicked = await clickCoveredRiver(page);
      console.log('  clicked covered river:', clicked);
      st = await overlayStats(page);
      console.log('  after click:', JSON.stringify(st));
      check(st.orange > 0, `orange click focus visible (${st.orange})`);
      check(st.green > 0, `green association highlight visible (${st.green})`);

      console.log('== 3. close the card (Escape) — selection must SURVIVE ==');
      await page.keyboard.press('Escape').catch(() => {});
      await sleep(800);
      st = await overlayStats(page);
      console.log('  after close:', JSON.stringify(st));
      check(st.orange > 0, `orange focus SURVIVES card close (${st.orange})`);
      check(st.green > 0, `green highlight SURVIVES card close (${st.green})`);

      console.log('== 4. county Buzău ==');
      const chip = page.locator('[data-testid="county-chip"][data-county="Buzău"]').first();
      await chip.evaluate((el) => el.click());
      await sleep(1800);
      st = await overlayStats(page);
      console.log('  after county:', JSON.stringify(st));
      check(st.orange > 0, `orange focus SURVIVES county filter (${st.orange})`);
      check(st.green > 0, `green highlight SURVIVES county filter (${st.green})`);

      console.log('== 5. locality Siriu (clicked river is in Unguriu — outside) ==');
      const locTriggers = page.locator('[data-testid="locality-filter"]');
      const locVisible = await locTriggers.evaluateAll((els) => els.some((el) => el.offsetParent !== null));
      if (locVisible) {
        await locTriggers.filter({ visible: true }).first().click();
        await page.waitForSelector('[data-testid="locality-option"]', { timeout: 8000 });
        const siriu = page.locator('[data-testid="locality-option"]', { hasText: /^Siriu$/ }).first();
        if ((await siriu.count()) > 0) await siriu.click();
        else await page.locator('[data-testid="locality-option"]').first().click();
        await sleep(2500);
        st = await overlayStats(page);
        console.log('  after locality:', JSON.stringify(st));
        check(st.orange > 0, `orange focus SURVIVES locality filter (pinned) (${st.orange})`);
        check(st.green > 0, `green association highlight SURVIVES locality (${st.green})`);
      } else {
        check(false, 'locality filter visible');
        failures += 1;
      }
    } else {
      check(false, 'association search visible');
      failures += 1;
    }
    const interesting = errors.filter((e) => !/favicon|Failed to load resource|net::|Download the React DevTools/.test(e));
    console.log('  mobile console errors:', interesting.length ? interesting[0].slice(0, 200) : '(none)');
    await page.close();
  }
}

await browser.close();
console.log(failures === 0 ? 'ALL CHECKS PASSED' : `${failures} CHECKS FAILED`);
process.exit(failures === 0 ? 0 : 1);