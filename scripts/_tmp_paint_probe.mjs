import { chromium } from 'playwright';
const b = await chromium.launch({ args: ['--no-sandbox'] });
const p = await b.newPage();
await p.setViewportSize({ width: 1280, height: 800 });
await p.goto('http://localhost:3100/', { waitUntil: 'domcontentloaded', timeout: 60000 });
await p.waitForFunction(() => document.querySelectorAll('.leaflet-overlay-pane path').length > 0, { timeout: 60000 }).catch(() => {});
await p.waitForTimeout(2500);
const info = await p.evaluate(() => {
  const paths = [...document.querySelectorAll('.leaflet-overlay-pane path')];
  const strokes = {};
  for (const pth of paths.slice(0, 4000)) {
    const s = (pth.getAttribute('stroke') || 'none').toLowerCase();
    strokes[s] = (strokes[s] || 0) + 1;
  }
  const vis = paths.filter(pth => {
    const b = pth.getBoundingClientRect();
    return b.width * b.height > 4;
  }).length;
  return { total: paths.length, visible: vis, strokes, mapH: (document.querySelector('.leaflet-container')||{}).getBoundingClientRect?.().height ?? -1 };
});
console.log(JSON.stringify(info, null, 2));
await b.close();
