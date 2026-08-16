import { chromium } from 'playwright';
const browser = await chromium.launch({ args: ['--no-sandbox'] });
const page = await browser.newPage();
const consoleErrors = [];
page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
page.on('pageerror', e => consoleErrors.push('PAGEERROR: ' + e.message));
await page.goto('http://localhost:3100/', { waitUntil: 'domcontentloaded', timeout: 90000 });
await page.waitForFunction(() => document.querySelectorAll('.leaflet-container').length > 0, { timeout: 60000 }).catch(() => {});
await page.waitForTimeout(4000);
const info = await page.evaluate(() => ({
  hasMap: !!document.querySelector('.leaflet-container'),
  overlayPaths: document.querySelectorAll('.leaflet-overlay-pane path').length,
  tiles: document.querySelectorAll('.leaflet-tile').length,
  csp: document.querySelector('meta[http-equiv="Content-Security-Policy"]')?.content || '(header)',
}));
console.log('MAP PROBE:', JSON.stringify(info, null, 2));
console.log('CONSOLE ERRORS:', consoleErrors.length ? consoleErrors.slice(0, 8) : 'none');
await browser.close();
