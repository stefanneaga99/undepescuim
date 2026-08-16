import { chromium } from 'playwright';
const b = await chromium.launch({ args: ['--no-sandbox'] });
const p = await b.newPage();
await p.goto('http://localhost:3100/', { waitUntil: 'domcontentloaded', timeout: 60000 });
await p.waitForFunction(() => document.querySelectorAll('.leaflet-overlay-pane path').length > 0, { timeout: 60000 }).catch(() => {});
await p.waitForTimeout(2000);
const r = await p.evaluate(() => {
  const blacks = [...document.querySelectorAll('.leaflet-overlay-pane path')].filter(x => (x.getAttribute('stroke')||'').toLowerCase() === '#000');
  const sample = blacks.slice(0, 25).map(x => ({
    cls: x.getAttribute('class'),
    d: (x.getAttribute('d')||'').slice(0, 60),
    sw: x.getAttribute('stroke-width'),
    fill: x.getAttribute('fill'),
    parent: x.parentElement?.getAttribute('class') || x.parentElement?.tagName,
  }));
  return { count: blacks.length, sample };
});
console.log(JSON.stringify(r, null, 2));
await b.close();
