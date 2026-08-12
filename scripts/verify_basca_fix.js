// Verify the Bâsca Mare / Bâsca Mică Romsilva fix (task t_67d8a9a3).
// Simulates the app's click-resolution logic against public/data/waters.json —
// mirrors src/components/map/WaterFeatureLayer.tsx EXACTLY (waterKey,
// groupKeyOf, isMainCourse, courseRank, contractAtFraction incl. sector
// intervals) + fractionAtPoint over the geometry owner's course.
//
// Expected (per the ANPA Romsilva list + county boundary):
//   Bâsca Mare  frac < 0.670  -> Direcția Silvică Covasna (18 Km)
//   Bâsca Mare  frac >= 0.670 -> Direcția Silvică Buzău (45 Km)
//   Bâsca Mică  any           -> Direcția Silvică Buzău (68 Km)
//   Bâsca Rozilei             -> AJVPS BUZĂU (28 Km)   [unchanged]
//   Bâsca Chiojdului          -> AJVPS BUZĂU (17 Km)   [unchanged]
const fs = require('fs');
const waters = JSON.parse(fs.readFileSync('public/data/waters.json', 'utf-8'));
const associations = JSON.parse(fs.readFileSync('public/data/associations.json', 'utf-8'));

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
  let best = null, bestLen = Infinity;
  for (const w of group) {
    const s = w.sectorStart, e = w.sectorEnd;
    if (typeof s !== 'number' || typeof e !== 'number') continue;
    if (frac >= s && frac < e && e - s < bestLen) { bestLen = e - s; best = w; }
  }
  if (best) return best;
  const ranked = [...group].sort((a, b) => courseRank(a.name) - courseRank(b.name));
  const rankedFrac = (i) => (ranked.length <= 1 ? 0.5 : i / (ranked.length - 1));
  const positioned = ranked.map((w, i) => ({ w, f: typeof w.course_frac === 'number' ? w.course_frac : rankedFrac(i) }));
  positioned.sort((a, b) => a.f - b.f);
  const n = positioned.length;
  for (let i = 0; i < n; i++) {
    const f = positioned[i].f;
    const left = i > 0 ? (positioned[i - 1].f + f) / 2 : -Infinity;
    const right = i < n - 1 ? (f + positioned[i + 1].f) / 2 : Infinity;
    if (frac >= left && frac < right) return positioned[i].w;
  }
  return null;
}

// --- fractionAtPoint mirror (geo.ts / assign_course_frac) ---
function haversineKm(a, b) {
  const R = 6371.0;
  const la1 = (a[1] * Math.PI) / 180, lo1 = (a[0] * Math.PI) / 180;
  const la2 = (b[1] * Math.PI) / 180, lo2 = (b[0] * Math.PI) / 180;
  const h = Math.sin((la2 - la1) / 2) ** 2 + Math.cos(la1) * Math.cos(la2) * Math.sin((lo2 - lo1) / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}
function orderParts(parts) {
  if (parts.length <= 1) return parts;
  const mids = parts.map((p) => p[Math.floor(p.length / 2)]);
  const mx = mids.reduce((s, m) => s + m[0], 0) / mids.length;
  const my = mids.reduce((s, m) => s + m[1], 0) / mids.length;
  const cxx = mids.reduce((s, m) => s + (m[0] - mx) ** 2, 0);
  const cyy = mids.reduce((s, m) => s + (m[1] - my) ** 2, 0);
  const cxy = mids.reduce((s, m) => s + (m[0] - mx) * (m[1] - my), 0);
  const theta = 0.5 * Math.atan2(2 * cxy, cxx - cyy);
  const vx = Math.cos(theta), vy = Math.sin(theta);
  const scored = mids.map((m) => (m[0] - mx) * vx + (m[1] - my) * vy);
  const order = parts.map((p, i) => ({ p, s: scored[i] })).sort((x, y) => x.s - y.s).map((x) => x.p);
  const half = Math.max(1, Math.floor(order.length / 2));
  const latFirst = order.slice(0, half).reduce((s, p) => s + p[Math.floor(p.length / 2)][1], 0) / half;
  const latLast = order.slice(-half).reduce((s, p) => s + p[Math.floor(p.length / 2)][1], 0) / half;
  return latFirst >= latLast ? order : [...order].reverse();
}
function fractionAtPoint(parts, pt) {
  const ordered = orderParts(parts);
  let total = 0;
  for (const p of ordered) for (let i = 1; i < p.length; i++) total += haversineKm(p[i - 1], p[i]);
  if (total <= 0) return null;
  const distToSeg = (a, b, p) => {
    const abx = b[0] - a[0], aby = b[1] - a[1];
    const apx = p[0] - a[0], apy = p[1] - a[1];
    const l2 = abx * abx + aby * aby;
    let t = l2 ? (apx * abx + apy * aby) / l2 : 0;
    t = Math.max(0, Math.min(1, t));
    return Math.hypot(p[0] - (a[0] + t * abx), p[1] - (a[1] + t * aby));
  };
  let best = null, bd = Infinity, walked = 0;
  for (const coords of ordered) {
    for (let j = 1; j < coords.length; j++) {
      const a = coords[j - 1], b = coords[j];
      const d = distToSeg(a, b, pt);
      if (d < bd) {
        bd = d;
        const segLen = haversineKm(a, b);
        const abx = b[0] - a[0], aby = b[1] - a[1];
        const apx = pt[0] - a[0], apy = pt[1] - a[1];
        const l2 = abx * abx + aby * aby;
        let t = l2 ? (apx * abx + apy * aby) / l2 : 0;
        t = Math.max(0, Math.min(1, t));
        let within = 0;
        for (let k = 1; k < j; k++) within += haversineKm(coords[k - 1], coords[k]);
        best = (walked + within + t * segLen) / total;
      }
    }
    for (let i = 1; i < coords.length; i++) walked += haversineKm(coords[i - 1], coords[i]);
  }
  return best;
}

// --- resolve a click on a water at fraction frac (or a real latlng) ---
function resolveClick(slug, fracOrPoint) {
  const owner = waters.find((w) => w.slug === slug);
  if (!owner || !owner.geometry) return { error: `no geometry owner for ${slug}` };
  const parts = owner.geometry.type === 'MultiLineString' ? owner.geometry.coordinates : [owner.geometry.coordinates];
  const frac = typeof fracOrPoint === 'number' ? fracOrPoint : fractionAtPoint(parts, fracOrPoint);
  const contract = contractAtFraction({ slug: owner.slug, name: owner.name }, frac, waters);
  const w = contract || owner;
  const assoc = associations.find((a) => a.slug === w.asociatie?.slug) || w.asociatie;
  return { frac: frac === null ? null : +frac.toFixed(4), slug: w.slug, name: w.name, judet: w.judet, limite: w.limite, dimensiune: w.dimensiune, association: assoc?.name ?? null };
}

let pass = 0, fail = 0;
function check(label, actual, expected) {
  const ok = actual === expected;
  if (ok) pass++; else fail++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}: got "${actual}"${ok ? '' : `, expected "${expected}"`}`);
}

console.log('=== Bâsca Mare — fraction clicks (geometry owner basca-mare) ===');
check('frac 0.10 (headwater)', resolveClick('basca-mare', 0.10).association, 'Direcția Silvică Covasna');
check('frac 0.33 (mid headwater)', resolveClick('basca-mare', 0.33).association, 'Direcția Silvică Covasna');
check('frac 0.66 (just above border)', resolveClick('basca-mare', 0.66).association, 'Direcția Silvică Covasna');
check('frac 0.67 (at border)', resolveClick('basca-mare', 0.67).association, 'Direcția Silvică Buzău');
check('frac 0.80 (downstream)', resolveClick('basca-mare', 0.80).association, 'Direcția Silvică Buzău');
check('frac 0.95 (near junction)', resolveClick('basca-mare', 0.95).association, 'Direcția Silvică Buzău');
const cov = resolveClick('basca-mare', 0.30);
check('Covasna sector slug', cov.slug, 'basca-mare-covasna');
check('Covasna sector dimensiune', cov.dimensiune, '18 Km');
check('Covasna sector judet', cov.judet, 'Covasna');
const buz = resolveClick('basca-mare', 0.80);
check('Buzău sector slug', buz.slug, 'basca-mare');
check('Buzău sector dimensiune', buz.dimensiune, '45 Km');
check('Buzău sector judet', buz.judet, 'Buzău');

console.log('=== Bâsca Mare — real latlng clicks ===');
// source area (Comandău, Covasna)
check('click at source (26.30, 45.74)', resolveClick('basca-mare', [26.30, 45.74]).association, 'Direcția Silvică Covasna');
// below the border (~lat 45.58, lng 26.35 — Gura Teghii area)
check('click downstream (26.35, 45.58)', resolveClick('basca-mare', [26.35, 45.58]).association, 'Direcția Silvică Buzău');

console.log('=== Bâsca Mică ===');
check('frac 0.30', resolveClick('basca-mica', 0.30).association, 'Direcția Silvică Buzău');
check('frac 0.70', resolveClick('basca-mica', 0.70).association, 'Direcția Silvică Buzău');
check('dimensiune', resolveClick('basca-mica', 0.5).dimensiune, '68 Km');
check('judet', resolveClick('basca-mica', 0.5).judet, 'Buzău');

console.log('=== Bâsca Rozilei (unchanged — AJVPS BUZĂU) ===');
check('frac 0.50', resolveClick('anpa-anpa-0209', 0.50).association, 'AJVPS BUZĂU');
check('frac 0.80', resolveClick('anpa-anpa-0209', 0.80).association, 'AJVPS BUZĂU');

console.log('=== Bâsca Chiojdului (unchanged — AJVPS BUZĂU) ===');
check('frac 0.50', resolveClick('anpa-anpa-0217', 0.50).association, 'AJVPS BUZĂU');

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
