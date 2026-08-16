import { chromium } from 'playwright';
const b = await chromium.launch({ args: ['--no-sandbox'] });
const p = await b.newPage();
await p.setViewportSize({ width: 1280, height: 800 });
await p.goto('http://localhost:3100/', { waitUntil: 'domcontentloaded', timeout: 60000 });
await p.waitForFunction(() => document.querySelectorAll('.leaflet-overlay-pane path').length > 0, { timeout: 60000 }).catch(() => {});
await p.waitForTimeout(2500);
const r = await p.evaluate(() => {
  const c = document.querySelector('.leaflet-container');
  const rect = c ? c.getBoundingClientRect() : { left: 0, top: 0, right: 800, bottom: 600 };
  const WATERS = new Set(['#3b82f6', '#22c55e', '#9ca3af', '#14b8a6', '#2dd4bf', '#f97316']);
  const paths = [...document.querySelectorAll('.leaflet-overlay-pane path')].filter((p) => {
    if (!WATERS.has((p.getAttribute('stroke') || '').toLowerCase())) return false;
    const b = p.getBoundingClientRect();
    return b.right > rect.left && b.bottom > rect.top && b.left < rect.right && b.top < rect.bottom && b.width * b.height > 4;
  });
  const candidates = paths.slice(0, 3).map((p) => {
    const b = p.getBoundingClientRect();
    return { stroke: p.getAttribute('stroke'), rect: [b.left, b.top, b.right, b.bottom] };
  });
  // hit-test on the first candidate
  let hit = null;
  if (paths[0]) {
    const pth = paths[0];
    const len = pth.getTotalLength();
    const m = pth.ownerSVGElement.getScreenCTM();
    const fracs = Array.from({ length: 19 }, (_, i) => 0.05 + 0.05 * i);
    for (const frac of fracs) {
      const pt = pth.getPointAtLength(len * frac);
      const sp = new DOMPoint(pt.x, pt.y).matrixTransform(m);
      if (sp.x < rect.left || sp.x > rect.right || sp.y < rect.top || sp.y > rect.bottom) continue;
      const top = document.elementFromPoint(sp.x, sp.y);
      const stroke = pth.getAttribute('stroke') || '';
      if (top === pth || (top && top.getAttribute('stroke') === stroke)) { hit = { x: sp.x, y: sp.y, topTag: top.tagName, topStroke: top.getAttribute('stroke') }; break; }
      if (!hit) hit = { miss: true, x: sp.x, y: sp.y, topTag: top.tagName, topStroke: top && top.getAttribute ? top.getAttribute('stroke') : null };
    }
  }
  return { matchCount: paths.length, candidates, firstHit: hit };
});
console.log(JSON.stringify(r, null, 2));
await b.close();
