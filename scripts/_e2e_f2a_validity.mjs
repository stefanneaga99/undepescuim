/* eslint-disable no-console */
/**
 * F2a e2e — permit-validity statement (t_e6ec4b5f).
 *
 * Verifies on desktop (1280) + mobile (390):
 *  1. Selecting an association (APS AQUA CRISIUS) shows the persistent
 *     association chip on the map.
 *  2. Tapping the chip opens the association detail sheet with the validity
 *     statement ("Permisul ... este valabil pe 19 ape în județele: Alba,
 *     Argeș, Brașov, Sibiu, Suceava") + the 'reciprocitate neconfirmată' note.
 *  3. Clicking a contracted water of that association shows the water card's
 *     per-water validity line ("Permisul X este valabil pe acest sector.").
 *  4. A directory-only association (ajvps-campina, ape: 0) renders the
 *     empty-count branch without crashing.
 *
 * Run: PLAYWRIGHT_CDP=http://localhost:3000 node scripts/_e2e_f2a_validity.mjs http://172.25.236.246:3101
 */
import { chromium } from 'playwright';

const BASE = process.argv[2] || process.env.BASE_URL || 'http://localhost:3000';
const CDP = process.env.PLAYWRIGHT_CDP;

const browser = CDP
  ? await chromium.connectOverCDP(CDP)
  : await chromium.launch({ args: ['--no-sandbox'] });
if (CDP) {
  for (const ctx of browser.contexts()) {
    for (const p of ctx.pages()) {
      if (p.url() !== 'about:blank') await p.close().catch(() => {});
    }
  }
}

let failures = 0;
const check = (cond, label) => {
  if (cond) console.log(`  PASS  ${label}`);
  else { console.log(`  FAIL  ${label}`); failures += 1; }
};

/** Read card text from either the desktop aside or the mobile vaul drawer. */
async function panelText(page) {
  return page.evaluate(() => {
    const el = document.querySelector('aside:has(h2)') || document.querySelector('[data-vaul-drawer]');
    return el ? el.innerText : '';
  });
}

async function pass(width, height) {
  console.log(`\n== pass @${width}px ==`);
  const page = await browser.newPage();
  await page.setViewportSize({ width, height });
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(
    () => document.querySelectorAll('.leaflet-overlay-pane path').length > 0,
    { timeout: 90000 },
  ).catch(() => console.log('  warn: no overlay paths'));
  await page.waitForTimeout(1200);
  console.log('  innerWidth:', await page.evaluate(() => window.innerWidth));

  const isMobile = width < 1024;

  // 1. Open the association search and pick APS AQUA CRISIUS.
  if (isMobile) {
    await page.click('[aria-label="Caută asociația"]');
    await page.waitForSelector('[placeholder="Caută asociația…"]', { timeout: 10000 });
    await page.fill('[placeholder="Caută asociația…"]', 'AQUA CRISIUS');
    await page.waitForTimeout(400);
    await page.click('.command-item:has-text("APS AQUA CRISIUS")').catch(async () => {
      // fallback: click the first command item matching the name
      await page.evaluate(() => {
        const items = [...document.querySelectorAll('[cmdk-item]')];
        const it = items.find((i) => i.textContent.includes('APS AQUA CRISIUS'));
        if (it) it.click();
      });
    });
  } else {
    // Desktop: inline trigger + portaled dropdown.
    await page.click('button:has-text("Caută asociația…")');
    await page.waitForSelector('[placeholder="Caută asociația…"]', { timeout: 10000 });
    await page.fill('[placeholder="Caută asociația…"]', 'AQUA CRISIUS');
    await page.waitForTimeout(400);
    await page.evaluate(() => {
      const items = [...document.querySelectorAll('[cmdk-item]')];
      const it = items.find((i) => i.textContent.includes('APS AQUA CRISIUS'));
      if (it) it.click();
    });
  }
  await page.waitForTimeout(1500);

  // 2. The chip should be visible.
  const chip = page.locator('button[aria-label^="Detalii "]');
  const chipVisible = await chip.isVisible().catch(() => false);
  check(chipVisible, 'association chip visible after selection');
  const chipText = chipVisible ? (await chip.innerText()) : '';
  check(chipText.includes('APS AQUA CRISIUS'), 'chip shows association name');
  check(/\b19\b/.test(chipText), 'chip shows ape count 19');

  // 3. Tap the chip → detail sheet with validity statement.
  if (chipVisible) await chip.click();
  await page.waitForTimeout(1200);
  let text = await panelText(page);
  check(text.includes('este valabil pe'), 'sheet shows validity sentence');
  check(text.includes('19 ape'), 'sheet shows "19 ape"');
  check(text.includes('Alba') && text.includes('Suceava'), 'sheet lists counties (Alba…Suceava)');
  check(text.includes('neconfirmat'), 'sheet shows "reciprocitate neconfirmată"');
  check(text.includes('AGVPS'), 'sheet cites the AGVPS legal note');
  check(text.includes('Asociația Cerbul Carpatin') === false, 'sheet is for AQUA CRISIUS, not another assoc');

  // Close the sheet (ESC works in both branches).
  await page.keyboard.press('Escape');
  await page.waitForTimeout(600);
  text = await panelText(page);
  check(!text.includes('19 ape'), 'sheet closes on ESC');

  // 4. Click a contracted water of AQUA CRISIUS → water card validity line.
  //    We click a covered (green) path. A path's bounding-rect CENTER can be
  //    off-stroke for long meandering rivers (the click would land on a
  //    different water), so sample fractions along the real path outline via
  //    getPointAtLength and require the topmost element at that point to be
  //    the green path itself (skill: dash/target sampling).
  const clickRes = await page.evaluate(() => {
    const paths = [...document.querySelectorAll('.leaflet-overlay-pane path')];
    const green = paths.find((p) => (p.getAttribute('stroke') || '').toLowerCase() === '#22c55e');
    if (!green) return { ok: false, reason: 'no green covered path found' };
    try {
      const ctm = green.getScreenCTM();
      const len = green.getTotalLength();
      for (let f = 0.05; f <= 0.95; f += 0.05) {
        const u = green.getPointAtLength(len * f);
        // getPointAtLength returns SVG user-space coords; transform to
        // client/viewport coords before elementFromPoint.
        const pt = new DOMPoint(u.x, u.y).matrixTransform(ctm);
        const el = document.elementFromPoint(pt.x, pt.y);
        const hit = el && (el === green || (el instanceof SVGPathElement && (el.getAttribute('stroke') || '').toLowerCase() === '#22c55e'));
        if (hit) return { ok: true, x: pt.x, y: pt.y };
      }
      return { ok: false, reason: 'no on-stroke point found' };
    } catch (e) {
      return { ok: false, reason: 'getTotalLength failed: ' + e.message };
    }
  });
  check(clickRes.ok, `found on-stroke point on covered (green) path${clickRes.ok ? '' : ' — ' + clickRes.reason}`);
  if (clickRes.ok) {
    await page.mouse.click(clickRes.x, clickRes.y);
    await page.waitForTimeout(1200);
    text = await panelText(page);
    check(text.includes('Detalii apă') || text.includes('Sector'), 'water card opened');
    check(text.includes('este valabil pe acest sector'), 'water card shows per-water validity line');
    check(text.includes('APS AQUA CRISIUS'), 'water card resolves the association');
  }

  // 5. Directory-only association (ape 0) — empty-count branch, no crash.
  if (isMobile) {
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);
    await page.click('[aria-label="Caută asociația"]');
    await page.waitForSelector('[placeholder="Caută asociația…"]', { timeout: 10000 });
  } else {
    // Desktop: inline trigger + portaled dropdown (trigger shows the selected
    // name after a previous selection — target it via its chevron icon).
    await page.click('header button:has(svg.lucide-chevron-down)');
    await page.waitForSelector('[placeholder="Caută asociația…"]', { timeout: 10000 });
  }
  await page.fill('[placeholder="Caută asociația…"]', 'Câmpina');
  await page.waitForTimeout(400);
  await page.evaluate(() => {
    const items = [...document.querySelectorAll('[cmdk-item]')];
    const it = items.find((i) => i.textContent.includes('CÂMPINA'));
    if (it) it.click();
  });
  await page.waitForTimeout(1200);
  const chip2 = page.locator('button[aria-label^="Detalii "]');
  if (await chip2.isVisible().catch(() => false)) {
    await chip2.click();
    await page.waitForTimeout(1000);
    text = await panelText(page);
    check(text.includes('nu are ape contractate'), 'ape:0 association shows empty-count branch');
  } else {
    check(false, 'chip visible for directory-only association');
  }

  await page.close();
}

await pass(1280, 900);
await pass(390, 844);

console.log(failures === 0 ? '\nALL PASS' : `\n${failures} FAILURES`);
process.exit(failures === 0 ? 0 : 1);
