/**
 * Mobile report-flow e2e (t_d9e8196e).
 *
 * Regression for the report button being unreachable on mobile: "Raportează
 * o problemă" used to render below the viewport inside the water-detail sheet
 * (y≈1125 at 844px viewport) so a real tap timed out. The fix surfaces a
 * FIXED bottom action bar (sibling of the vaul Drawer.Content, portaled to
 * body so vaul's transform can't push it off-screen) that stays in view at
 * ANY sheet snap/scroll.
 *
 * Uses TRUE mobile context (isMobile + hasTouch, 390x844) via local chromium:
 *   - click a water → the fixed "Raportează o problemă" button must be full
 *     in the viewport, topmost under its center, and a REAL locator.click()
 *     (no force / no scroll-into-view trickery) must open the dialog;
 *   - the reason flow still works (radios + submit) with /api/report stubbed;
 *   - desktop regression: no fixed bar at ≥1024px; the inline card buttons
 *     still open the dialog.
 *
 * Run: /tmp/asound-run.sh node scripts/_e2e_report_mobile.mjs http://localhost:3103
 */
import { chromium } from 'playwright';

const BASE = process.argv[2] || process.env.BASE_URL || 'http://localhost:3100';
const CDP = process.env.PLAYWRIGHT_CDP;

const browser = CDP
  ? await chromium.connectOverCDP(CDP)
  : await chromium.launch({ args: ['--no-sandbox'] });
for (const ctx of browser.contexts()) {
  for (const p of ctx.pages()) {
    if (p.url() !== 'about:blank') await p.close().catch(() => {});
  }
}

let failures = 0;
const check = (cond, label) => {
  if (cond) console.log(`  PASS  ${label}`);
  else { console.log(`  FAIL  ${label}`); failures += 1; }
};

/** Click the first hit-testable water path (exact water doesn't matter). */
async function clickAnyWater(page) {
  const r = await page.evaluate(() => {
    const c = document.querySelector('.leaflet-container');
    const b = c ? c.getBoundingClientRect() : { left: 0, top: 0, right: 390, bottom: 844 };
    return { left: b.left, top: b.top, right: b.right, bottom: b.bottom };
  });
  const hit = await page.evaluate((rect) => {
    const WATERS = new Set(['#3b82f6', '#22c55e', '#9ca3af', '#14b8a6', '#2dd4bf', '#f97316']);
    const paths = [...document.querySelectorAll('.leaflet-overlay-pane path')].filter((p) => {
      if (!WATERS.has((p.getAttribute('stroke') || '').toLowerCase())) return false;
      const b = p.getBoundingClientRect();
      return b.right > rect.left && b.bottom > rect.top && b.left < rect.right && b.top < rect.bottom && b.width * b.height > 4;
    });
    for (const p of paths.slice(0, 40)) {
      const len = p.getTotalLength();
      const m = p.ownerSVGElement.getScreenCTM();
      for (const frac of Array.from({ length: 9 }, (_, i) => 0.1 + 0.1 * i)) {
        const pt = p.getPointAtLength(len * frac);
        const sp = new DOMPoint(pt.x, pt.y).matrixTransform(m);
        if (sp.x < rect.left || sp.x > rect.right || sp.y < rect.top || sp.y > rect.bottom) continue;
        const top = document.elementFromPoint(sp.x, sp.y);
        const stroke = p.getAttribute('stroke') || '';
        const sameStroke = top && typeof top.getAttribute === 'function' && top.getAttribute('stroke') === stroke;
        if (top === p || sameStroke) return { x: sp.x, y: sp.y };
      }
    }
    return null;
  }, r);
  return hit;
}

async function openWaterCard(page) {
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('button:visible[aria-pressed]', { timeout: 90000 });
  await page.waitForFunction(() => document.querySelectorAll('.leaflet-overlay-pane path').length > 0, { timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(1800);
  const hit = await clickAnyWater(page);
  check(!!hit, 'clickable water found');
  if (!hit) return false;
  await page.mouse.click(hit.x, hit.y);
  await page.waitForFunction(() => {
    const d = document.querySelector('[data-vaul-drawer]') || document.querySelector('aside:has(h2)');
    return d && (d.textContent || '').length > 5;
  }, { timeout: 15000 });
  await page.waitForTimeout(500);
  return true;
}

async function runMobile() {
  console.log('\n== MOBILE @390x844 (isMobile, hasTouch) ==');
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 1 });
  const p = await ctx.newPage();
  await p.route('**/api/report', async (route) => {
    const post = route.request().postDataJSON();
    const ok = post && typeof post.reason === 'string';
    await route.fulfill({ status: ok ? 200 : 400, contentType: 'application/json', body: JSON.stringify({ ok, issueUrl: ok ? 'https://github.com/neagastefan99/undepescuim/issues/999' : null }) });
  });

  if (!(await openWaterCard(p))) { await p.close(); return; }

  // 1) fixed bar in viewport + hit-testable
  const probe = await p.evaluate(() => {
    const btn = document.querySelector('button[data-testid="report-flag-fixed"]');
    if (!btn) return { found: false };
    const r = btn.getBoundingClientRect();
    const topEl = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    return { found: true, rect: { top: r.top, bottom: r.bottom }, ih: window.innerHeight, hitTestIsBtn: topEl === btn || (topEl && topEl.closest && topEl.closest('button') === btn) };
  });
  check(probe.found, 'fixed "Raportează o problemă" action bar is present');
  if (probe.found) {
    check(probe.rect.top >= 0 && probe.rect.bottom <= probe.ih, `fixed button fully within viewport (top=${probe.rect.top.toFixed(0)}, bottom=${probe.rect.bottom.toFixed(0)}, ih=${probe.ih})`);
    check(probe.hitTestIsBtn, 'fixed button is topmost under its centre (real tap would land on it)');
    // ensure Playwright did NOT need to scroll/force — scroll must be unchanged
    const scTop = await p.evaluate(() => { const s = document.querySelector('[data-vaul-drawer] [class*="overflow-y-auto"]'); return s ? s.scrollTop : -1; });
    check(scTop === -1 || scTop === 0 || scTop <= 1, 'no auto-scroll needed to reach the button');
  }

  // 2) REAL tap (would time out if unreachable) → dialog opens
  const fixedBtn = p.locator('button[data-testid="report-flag-fixed"]');
  let tapped = true;
  try { await fixedBtn.click({ timeout: 5000 }); } catch (e) { tapped = false; console.log('  tap error:', e.message.split('\n')[0]); }
  check(tapped, 'real tap on fixed report button succeeds (no timeout)');

  await p.waitForTimeout(800);
  const dialog = p.locator('[data-slot="dialog-content"]');
  check(await dialog.isVisible().catch(() => false), 'report dialog opens after tapping fixed button');
  const radios = dialog.locator('input[type="radio"]');
  check((await radios.count()) === 5, '5 reason radios rendered');
  const submitBtn = dialog.locator('button[type="submit"]');
  check(await submitBtn.isDisabled(), 'submit disabled until a reason is chosen');
  await radios.nth(3).check();
  await p.waitForTimeout(200);
  check(!(await submitBtn.isDisabled()), 'submit enabled after choosing a reason');
  await submitBtn.click();
  await p.waitForTimeout(900);
  check(((await dialog.textContent()) || '').includes('Mulțumim'), 'success/confirmation state shown');
  await p.screenshot({ path: `.e2e/report_mobile_${failures ? 'fail' : 'ok'}.png` }).catch(() => {});
  await dialog.locator('[data-slot="dialog-close"]').click().catch(() => {});
  // wait for the dialog to fully close before the next interaction
  await dialog.waitFor({ state: 'detached', timeout: 5000 }).catch(() => {});
  await p.waitForTimeout(300);

  // 3) positive-signal quick tap pre-selects data_correct
  const posBtn = p.locator('button[data-testid="report-positive-fixed"]');
  await posBtn.click().catch((e) => console.log('  positive tap warn:', e.message.split('\n')[0]));
  const gotDataCorrect = await p.waitForFunction(
    () => {
      const checked = document.querySelector('[data-slot="dialog-content"] input[type="radio"]:checked');
      return checked && checked.getAttribute('value') === 'data_correct';
    },
    { timeout: 6000 },
  ).then(() => true, () => false);
  check(gotDataCorrect, 'positive quick-tap pre-selects data_correct');

  await p.close();
}

async function runDesktop() {
  console.log('\n== DESKTOP @1280x800 ==');
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const p = await ctx.newPage();
  await p.route('**/api/report', async (route) => {
    const post = route.request().postDataJSON();
    const ok = post && typeof post.reason === 'string';
    await route.fulfill({ status: ok ? 200 : 400, contentType: 'application/json', body: JSON.stringify({ ok, issueUrl: ok ? 'https://github.com/neagastefan99/undepescuim/issues/999' : null }) });
  });
  if (!(await openWaterCard(p))) { await p.close(); return; }
  const hasFixed = await p.evaluate(() => !!document.querySelector('button[data-testid="report-flag-fixed"]'));
  check(!hasFixed, 'no fixed action bar on desktop (aside inline buttons only)');
  const inline = p.locator('aside button', { hasText: 'Raportează o problemă' });
  check((await inline.count()) > 0, 'desktop aside shows inline report button');
  await inline.first().click().catch(async () => { await inline.first().evaluate((el) => el.click()); });
  await p.waitForTimeout(800);
  check(await p.locator('[data-slot="dialog-content"]').isVisible().catch(() => false), 'desktop dialog opens from inline button');
  await p.close();
}

await runMobile();
await runDesktop();

await browser.close();
console.log(failures === 0 ? 'REPORT MOBILE E2E PASSED' : `REPORT MOBILE E2E FAILED (${failures} checks)`);
process.exit(failures === 0 ? 0 : 1);