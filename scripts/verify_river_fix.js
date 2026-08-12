// Simulate the app's click-resolution logic against public/data/waters.json
// to verify the multi-contract river fix (task t_ac697770).
// Mirrors src/components/map/WaterFeatureLayer.tsx EXACTLY (waterKey,
// groupKeyOf, isMainCourse, courseRank, contractAtFraction incl. sector
// intervals) + fractionAtPoint over the geometry owner's course.
const fs = require('fs');
const waters = JSON.parse(fs.readFileSync('public/data/waters.json', 'utf-8'));
const testPoints = JSON.parse(fs.readFileSync('scripts/test_points.json', 'utf-8'));

// --- mirror of WaterFeatureLayer.tsx helpers ---
function strip(s) { return s.normalize('NFD').replace(/[\u0300-\u036f]/g, ''); }
function waterKey(name) {
  const lower = strip(String(name || '').toLowerCase());
  return (
    lower
      .replace(/^(raul|paraul|parau|valea|lacul|balta|acumularea|acumulare)\s+/, '')
      .replace(/[()]/g, '')
      .trim()
      .split(/\s+/)[0] ?? ''
  );
}
function groupKeyOf(w) {
  if (w && w.riverGroup) return w.riverGroup;
  return waterKey(w && w.name);
}
function sameRiver(a, b) {
  if (!a || !b) return false;
  return a.slice(0, 5) === b.slice(0, 5);
}
function isMainCourse(name) {
  return !/^(valea|paraul|parau|pârâu|pârâul)\s/i.test(name);
}
function courseRank(name) {
  const n = String(name).toLowerCase();
  if (n.includes('superior')) return 0;
  if (n.includes('mijlociu')) return 1;
  if (n.includes('inferior')) return 2;
  return 3;
}
function contractAtFraction(clickedRef, frac, allWaters) {
  const clicked =
    (clickedRef.slug && allWaters.find((w) => w.slug === clickedRef.slug)) ||
    (clickedRef.name && allWaters.find((w) => w.name === clickedRef.name)) ||
    { name: clickedRef.name };
  const gk = groupKeyOf(clicked);
  const group = allWaters.filter(
    (w) => (isMainCourse(w.name) || w.mainCourse === true) && groupKeyOf(w) === gk,
  );
  if (group.length <= 1) return null;
  // 1. exact sector intervals — smallest containing interval wins
  let best = null, bestLen = Infinity;
  for (const w of group) {
    const s = w.sectorStart, e = w.sectorEnd;
    if (typeof s !== 'number' || typeof e !== 'number') continue;
    if (frac >= s && frac < e && e - s < bestLen) { bestLen = e - s; best = w; }
  }
  if (best) return best;
  // 2. Voronoi over course_frac
  const ranked = [...group].sort((a, b) => courseRank(a.name) - courseRank(b.name));
  const rankedFrac = (i) => (ranked.length <= 1 ? 0.5 : i / (ranked.length - 1));
  const positioned = ranked
    .map((w, i) => ({ w, f: typeof w.course_frac === 'number' ? w.course_frac : rankedFrac(i) }))
    .sort((a, b) => a.f - b.f);
  const n = positioned.length;
  for (let i = 0; i < n; i++) {
    const f = positioned[i].f;
    const left = i > 0 ? (positioned[i - 1].f + f) / 2 : -Infinity;
    const right = i < n - 1 ? (f + positioned[i + 1].f) / 2 : Infinity;
    if (frac >= left && frac < right) return positioned[i].w;
  }
  return null;
}

// --- geometry helpers (mirror WaterFeatureLayer.tsx) ---
function haversineKm(a, b) {
  const R = 6371;
  const dLat = ((b[1] - a[1]) * Math.PI) / 180;
  const dLon = ((b[0] - a[0]) * Math.PI) / 180;
  const la1 = (a[1] * Math.PI) / 180, la2 = (b[1] * Math.PI) / 180;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(la1) * Math.cos(la2) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}
function partLength(coords) {
  let len = 0;
  for (let i = 1; i < coords.length; i++) len += haversineKm(coords[i - 1], coords[i]);
  return len;
}
function orderParts(parts) {
  if (parts.length <= 1) return parts;
  const mids = parts.map((p) => p[Math.floor(p.length / 2)]);
  const mx = mids.reduce((a, m) => a + m[0], 0) / mids.length;
  const my = mids.reduce((a, m) => a + m[1], 0) / mids.length;
  let cxx = 0, cyy = 0, cxy = 0;
  for (const m of mids) { cxx += (m[0] - mx) ** 2; cyy += (m[1] - my) ** 2; cxy += (m[0] - mx) * (m[1] - my); }
  const theta = 0.5 * Math.atan2(2 * cxy, cxx - cyy);
  const vx = Math.cos(theta), vy = Math.sin(theta);
  const scored = parts.map((p) => ({ p, t: (p[Math.floor(p.length / 2)][0] - mx) * vx + (p[Math.floor(p.length / 2)][1] - my) * vy }));
  scored.sort((a, b) => a.t - b.t);
  const ordered = scored.map((s) => s.p);
  const half = Math.max(1, Math.floor(ordered.length / 2));
  const latFirst = ordered.slice(0, half).reduce((a, p) => a + p[Math.floor(p.length / 2)][1], 0) / half;
  const latLast = ordered.slice(-half).reduce((a, p) => a + p[Math.floor(p.length / 2)][1], 0) / half;
  return latFirst < latLast ? [...ordered].reverse() : ordered;
}
function fractionAtPoint(parts, pt) {
  const ordered = orderParts(parts);
  const lengths = ordered.map(partLength);
  const total = lengths.reduce((a, b) => a + b, 0);
  if (total <= 0) return null;
  function distToSeg(a, b, p) {
    const abx = b[0] - a[0], aby = b[1] - a[1];
    const apx = p[0] - a[0], apy = p[1] - a[1];
    const len2 = abx * abx + aby * aby;
    let t = len2 ? (apx * abx + apy * aby) / len2 : 0;
    t = Math.max(0, Math.min(1, t));
    return Math.hypot(p[0] - (a[0] + t * abx), p[1] - (a[1] + t * aby));
  }
  let bestFrac = null, bestDist = Infinity, walked = 0;
  for (let i = 0; i < ordered.length; i++) {
    const coords = ordered[i], len = lengths[i];
    for (let j = 1; j < coords.length; j++) {
      const d = distToSeg(coords[j - 1], coords[j], pt);
      if (d < bestDist) {
        bestDist = d;
        const segLen = haversineKm(coords[j - 1], coords[j]);
        const abx = coords[j][0] - coords[j - 1][0], aby = coords[j][1] - coords[j - 1][1];
        const apx = pt[0] - coords[j - 1][0], apy = pt[1] - coords[j - 1][1];
        const len2 = abx * abx + aby * aby;
        let t = len2 ? (apx * abx + apy * aby) / len2 : 0;
        t = Math.max(0, Math.min(1, t));
        let within = 0;
        for (let k = 1; k < j; k++) within += haversineKm(coords[k - 1], coords[k]);
        bestFrac = (walked + within + t * segLen) / total;
      }
    }
    walked += len;
  }
  return bestFrac;
}

// --- geometry owner per river (the member that renders the course) ---
function courseFor(riverGroupKey) {
  const members = waters.filter((w) => groupKeyOf(w) === riverGroupKey);
  let best = null, bestPts = 0;
  for (const w of members) {
    const g = w.geometry;
    if (!g) continue;
    const npts = g.type === 'MultiLineString'
      ? g.coordinates.reduce((a, p) => a + p.length, 0)
      : g.type === 'LineString' ? g.coordinates.length : 0;
    if (npts > bestPts) { bestPts = npts; best = w; }
  }
  return best;
}

// --- run the tests ---
let pass = 0, fail = 0;
const riverOrder = ['olt', 'mures', 'siret', 'prut', 'somes', 'crisul-repede', 'arges', 'ialomita', 'dambovita', 'jiu', 'moldova', 'tarnava-mare', 'colentina', 'aries', 'somesul-mic', 'somesul-mare', 'barzava', 'bistrita-gorj'];
for (const river of riverOrder) {
  const owner = courseFor(river);
  const cases = testPoints[river] || [];
  const g = owner && owner.geometry;
  const parts = g && (g.type === 'MultiLineString' ? g.coordinates : [g.coordinates]);
  console.log(`\n=== ${river} (course owner: ${owner ? owner.name + ' [' + owner.judet + ']' : 'NONE'}, ${cases.length} clicks) ===`);
  if (!parts) { console.log('  !! no course geometry'); continue; }
  const contracts = waters.filter((w) => groupKeyOf(w) === river && (isMainCourse(w.name) || w.mainCourse === true))
    .map((w) => `${w.course_frac ?? '?'} ${w.name.slice(0, 26)} [${(w.asociatie || {}).name}]`)
    .sort();
  console.log(`  contracts (${contracts.length}):`);
  for (const c of contracts) console.log(`    ${c}`);
  for (const t of cases) {
    const frac = fractionAtPoint(parts, [t.lon, t.lat]);
    // Mirror the app: contractAtFraction → null falls back to the clicked water itself
    const c = frac === null ? null : (contractAtFraction({ slug: owner.slug, name: owner.name }, frac, waters) || owner);
    const assoc = (c && c.asociatie && c.asociatie.name) || '(none)';
    const ok = assoc === t.expect;
    if (ok) pass++; else fail++;
    console.log(`  ${ok ? 'PASS' : 'FAIL'}  frac ${frac !== null ? frac.toFixed(4) : 'null'}  ${t.label.padEnd(26)} -> ${assoc.padEnd(32)} (expect ${t.expect})${ok ? '' : '   <- ' + (c ? c.name : '?')}`);
  }
}
console.log(`\n${pass} passed, ${fail} failed`);
