/* eslint-disable no-console */
/**
 * F3 report-flow e2e (t_5b1250b3).
 *
 * Opens a water card, checks the report entry points ("Raportează o problemă"
 * + the quick positive-signal "Datele sunt corecte"), opens the dialog, picks
 * a reason, and stubs POST /api/report so the success/confirmation state can
 * be asserted WITHOUT creating real GitHub issues. The real GitHub round-trip
 * is verified separately via curl (see the F3 plan §6).
 *
 * Run: PLAYWRIGHT_CDP=http://localhost:3000 node scripts/_e2e_report.mjs http://172.25.236.246:3100
 */
import { chromium } from 'playwright';

const BASE = process.argv[2] || process.env.BASE_URL || 'http://localhost:3000';
const CDP = process.env.PLAYWRIGHT_CDP;

const browser = CDP ? await chromium.connectOverCDP(CDP) : await chromium.launch();
// Close leftover pages from crashed runs — they share the single browserless window.
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

const cardText = () =>
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
    last = await cardText();
    if (last && last.trim()) return last;
    await page.waitForTimeout(300);
  }
  return last;
};

/** Click the midpoint of the first visible water path (any color) — every card
 * has the F3 report buttons, so the exact water doesn't matter. */
const clickAnyWater = async () => {
  return page.evaluate(() => {
    const c = document.querySelector('.leaflet-container');
    const r = c ? c.getBoundingClientRect() : { left: 0, top: 0, right: 800, bottom: 600 };
    const WATERS = new Set(['#3b82f6', '#22c55e', '#9ca3af', '#14b8a6', '#2dd4bf', '#f97316']);
    const paths = [...document.querySelectorAll('.leaflet-overlay-pane path')].filter((p) => {
      if (!WATERS.has((p.getAttribute('stroke') || '').toLowerCase())) return false;
      const b = p.getBoundingClientRect();
      return b.right > r.left && b.bottom > r.top && b.left < r.right && b.top < r.bottom && b.width * b.height > 4;
    });
    if (!paths.length) return null;
    const p = paths[0];
    const len = p.getTotalLength();
    const m = p.ownerSVGElement.getScreenCTM();
    const fracs = Array.from({ length: 19 }, (_, i) => 0.05 + 0.05 * i);
    for (const frac of fracs) {
      const pt = p.getPointAtLength(len * frac);
      const sp = new DOMPoint(pt.x, pt.y).matrixTransform(m);
      if (sp.x < r.left || sp.x > r.right || sp.y < r.top || sp.y > r.bottom) continue;
      const top = document.elementFromPoint(sp.x, sp.y);
      const stroke = p.getAttribute('stroke') || '';
      if (top === p || (top && top.getAttribute('stroke') === stroke)) return { x: sp.x, y: sp.y };
    }
    return null;
  });
};

async function runPass(width, height, label) {
  console.log(`\n== ${label} @${width}px ==`);
  const p = await browser.newPage();
  await p.setViewportSize({ width, height });
  global.page = p;

  // Stub the API so the confirmation state is exercised without real issues.
  await p.route('**/api/report', async (route) => {
    const post = route.request().postDataJSON();
    const ok = post && typeof post.reason === 'string' && post.waterSlug && post.waterName;
    await route.fulfill({
      status: ok ? 200 : 400,
      contentType: 'application/json',
      body: JSON.stringify({ ok, issueUrl: ok ? 'https://github.com/neagastefan99/undepescuim/issues/999' : null }),
    });
  });

  await p.goto(BASE, { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('button:visible[aria-pressed]', { timeout: 90000 });
  await p.waitForFunction(
    () => document.querySelectorAll('.leaflet-overlay-pane path').length > 0,
    { timeout: 60000 },
  ).catch(() => console.log('  warn: no overlay paths after load wait'));
  await p.waitForTimeout(1500);

  const hit = await clickAnyWater();
  check(!!hit, `clickable contracted blue water found (${hit ? `(${hit.x.toFixed(0)},${hit.y.toFixed(0)})` : 'none'})`);
  if (hit) await p.mouse.click(hit.x, hit.y);
  const text = await readCardText();
  check(text.includes('Raportează o problemă'), 'card shows "Raportează o problemă" button');
  check(text.includes('Datele sunt corecte'), 'card shows "Datele sunt corecte" positive-signal button');

  // Open the report dialog via the "Raportează o problemă" button.
  // The shared browserless window pins ~800px so the card renders in the vaul
  // drawer and the button may sit outside the viewport — click in-page.
  const reportBtn = p.locator('button', { hasText: 'Raportează o problemă' }).first();
  await reportBtn.evaluate((el) => el.click()).catch(async () => {
    await reportBtn.scrollIntoViewIfNeeded().catch(() => {});
    await reportBtn.click({ force: true });
  });
  await p.waitForTimeout(800);
  const dialog = p.locator('[data-slot="dialog-content"]');
  check(await dialog.isVisible().catch(() => false), 'report dialog opens');

  const radios = dialog.locator('input[type="radio"]');
  const radioCount = await radios.count();
  check(radioCount === 5, `5 reason radios rendered (got ${radioCount})`);
  check(!!(await dialog.textContent()).includes('Raportezi date pentru'), 'dialog shows water context');

  const submitBtn = dialog.locator('button[type="submit"]');
  check(await submitBtn.isDisabled(), 'submit disabled until a reason is chosen');
  await radios.nth(3).check(); // wrong_coordinates
  await p.waitForTimeout(200);
  check(!(await submitBtn.isDisabled()), 'submit enabled after choosing a reason');

  await submitBtn.click();
  await p.waitForTimeout(900);
  const after = await dialog.textContent();
  check(after.includes('Mulțumim'), 'success/confirmation state shown');
  check(after.includes('GitHub'), 'confirmation links to the GitHub issue');
  await p.screenshot({ path: `.e2e/report_${width}_success.png` });

  // Close the dialog via its X button (present in both form and success
  // phases; Escape would bubble to the card sheet's close handler and unmount
  // the card entirely).
  await dialog.locator('[data-slot="dialog-close"]').click().catch(() => {});
  await p.waitForTimeout(600);
  const posBtn = p.locator('button', { hasText: 'Datele sunt corecte' }).first();
  try {
    await posBtn.evaluate((el) => el.click());
  } catch {
    await posBtn.scrollIntoViewIfNeeded().catch(() => {});
    await posBtn.click({ force: true });
  }
  await p.waitForTimeout(800);
  const dialog2 = p.locator('[data-slot="dialog-content"]');
  const checkedVal = await dialog2.locator('input[type="radio"]:checked').getAttribute('value').catch(() => null);
  check(checkedVal === 'data_correct', `positive tap pre-selects data_correct (got ${checkedVal})`);
  await p.screenshot({ path: `.e2e/report_${width}_positive.png` });

  await p.close();
}

await runPass(1280, 800, 'desktop');
await runPass(390, 844, 'mobile');

await browser.close();
console.log(failures === 0 ? 'REPORT E2E PASSED' : `REPORT E2E FAILED (${failures} checks)`);
process.exit(failures === 0 ? 0 : 1);
