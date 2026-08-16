import { chromium } from 'playwright';

const BASE = 'http://localhost:3101';
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => window.__perfDataLoaded === true, { timeout: 60000 });
await page.waitForFunction(() => document.querySelectorAll('.leaflet-overlay-pane path').length > 0, { timeout: 60000 });

await page.evaluate(() => {
  window.__shifts = [];
  const obs = new PerformanceObserver((list) => {
    for (const e of list.getEntries()) {
      window.__shifts.push({
        t: Math.round(e.startTime),
        v: e.value,
        recentInput: e.hadRecentInput,
        sources: (e.sources || []).map((s) => {
          const el = s.node;
          return el ? `${el.tagName}.${[...el.classList].join('.')}` : '?';
        }),
      });
    }
  });
  obs.observe({ entryTypes: ['layout-shift'] });
  window.__obs = obs;
});

// 1) toggle Bihor on
const barHeight0 = await page.evaluate(() => document.querySelector('.md\\:hidden').getBoundingClientRect().height);
await page.locator('button:has-text("Bihor")').first().evaluate((el) => el.click());
await page.waitForTimeout(1200);
const barHeight1 = await page.evaluate(() => document.querySelector('.md\\:hidden').getBoundingClientRect().height);
// 2) toggle Bihor off
await page.locator('button:has-text("Bihor")').first().evaluate((el) => el.click());
await page.waitForTimeout(1200);
const barHeight2 = await page.evaluate(() => document.querySelector('.md\\:hidden').getBoundingClientRect().height);

// 3) real pointer click on map center to open sheet
const mapBox = await page.evaluate(() => {
  const r = document.querySelector('.leaflet-container').getBoundingClientRect();
  return { x: r.left, y: r.top, w: r.width, h: r.height };
});
await page.mouse.click(mapBox.x + mapBox.w * 0.5, mapBox.y + mapBox.h * 0.5);
await page.waitForTimeout(1200);
const sheetOpen = await page.evaluate(() => !!document.querySelector('[data-vaul-drawer]'));
await page.keyboard.press('Escape');
await page.waitForTimeout(1200);

const shifts = await page.evaluate(() => { window.__obs.disconnect(); return window.__shifts; });
console.log('bar heights:', { before: barHeight0, afterOn: barHeight1, afterOff: barHeight2 });
console.log('sheetOpen:', sheetOpen);
for (const s of shifts) console.log(JSON.stringify(s));
await browser.close();