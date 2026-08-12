// Verify the Bistrița-basin mapping fix (task t_66b48ee0, phase 1).
// Simulates the app's click-resolution logic against public/data/waters.json —
// mirrors src/components/map/WaterFeatureLayer.tsx EXACTLY (waterKey,
// groupKeyOf, isMainCourse, courseRank, contractAtFraction incl. sector
// intervals) + fractionAtPoint over the geometry owner's course.
//
// Expected for the reported area (Broșteni/Bicaz/Piatra Neamț, Bistrița basin):
//   Bistrița course (group 'bistrita', owner Râul Bistrița Aurie II):
//     frac 0.0   -> Râul Bistrița Aurie I   (APS AQUA CRISIUS, Suceava)
//     frac 0.5   -> Râul Bistrița II or IV  (Suceava/Neamț sector)
//     frac ~0.75 -> Râul Bistrița VI        (AJVPS NEAMȚ — Bicaz dam/Pangrati)
//     frac ~0.9  -> Râul Bistrița NEAMȚ 32  (AJVPS NEAMȚ — Broșteni→Bacău)
//     frac ~0.98 -> Râul Bistrița BACĂU 39  (AJVPS BACĂU)
//   Bistrița-Năsăud river (group 'bistrita-bn', owner 7oju77qb):
//     frac 0.3 -> Râul Bistrița (AJVPS BISTRIŢA NĂSĂUD, 25 km)
//     frac 0.9 -> Râul Bistrița (AJVPS BISTRIŢA NĂSĂUD, 28 km)
//   Bistricioara Harghita (group 'bistricioara-harghita'):
//     frac 0.1 -> tronson I (D.S. Harghita)
//     frac 0.9 -> tronson II (D.S. Harghita)
//   Moldova (group 'moldova'):
//     frac 0.25 -> Râul Moldova II (AJVPS BOTOȘANI)
//     frac 0.45 -> Râul Moldova SUCEAVA 59 (AJVPS BOTOȘANI)
//     frac 0.60 -> Râul Moldova NEAMȚ BRADUL (AVPS BRADUL PIATRA NEAMȚ)
//     frac 0.68 -> Râul Moldova NEAMȚ ROMAN (AVPS ROMAN)
//     frac 0.80 -> Râul Moldova Iași (AVPS IAȘI)
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

// --- fractionAtPoint mirror ---
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

console.log('=== Bistrița (Siret basin, group bistrita) — owner Râul Bistrița Aurie II ===');
const bOwn = resolveClick('2uxod40o', 0.05);
check('frac 0.05 -> Aurie II (Cârlibaba→Mestecăniș)', bOwn.name, 'Râul Bistrița Aurie II');
const b2 = resolveClick('2uxod40o', 0.35);
check('frac 0.35 -> II (48 km, Zugreni→Mălișor)', b2.name, 'Râul Bistrița II');
const b6 = resolveClick('2uxod40o', 0.60);
check('frac 0.60 -> Bistrița VI (dam→Pangrati)', b6.name, 'Râul Bistrița VI');
const bN = resolveClick('2uxod40o', 0.70);
check('frac 0.70 -> NEAMȚ 32 km contract', bN.name, 'Râul Bistrița');
check('frac 0.70 assoc', bN.association, 'AJVPS NEAMȚ');
check('frac 0.70 dimensiune', bN.dimensiune, '32 km');
const bB = resolveClick('2uxod40o', 0.90);
check('frac 0.90 -> BACĂU 39 km contract', bB.association, 'AJVPS BACĂU');
check('frac 0.90 dimensiune', bB.dimensiune, '39 km');

console.log('=== Bistrița — real latlng clicks in the REPORTED AREA ===');
// Broșteni (47.24N, 25.55E) — inside Bistrița II (baraj Zugreni→pod Mălișor)
check('click Broșteni (25.55, 47.24)', resolveClick('2uxod40o', [25.55, 47.24]).association, 'A.LUCIOPERCA CLUB PESCAR MODERN');
// Bicaz town (46.91N, 25.95E) — Fărcașa→Zahorna sector, AJVPS NEAMȚ
const bicaz = resolveClick('2uxod40o', [25.95, 46.91]);
check('click Bicaz assoc', bicaz.association, 'AJVPS NEAMȚ');
// Piatra Neamț (46.93N, 26.37E) — NEAMȚ 32 sector (Reconstrucția→Bacău)
check('click Piatra Neamț (26.37, 46.93)', resolveClick('2uxod40o', [26.37, 46.93]).association, 'AJVPS NEAMȚ');
// Bacău area (46.57N, 26.91E) — BACĂU 39 sector
check('click Bacău (26.91, 46.57)', resolveClick('2uxod40o', [26.91, 46.57]).association, 'AJVPS BACĂU');

console.log('=== Bistrița-Năsăud river (group bistrita-bn, owner 7oju77qb) ===');
check('frac 0.3 -> 25 km contract', resolveClick('7oju77qb', 0.3).dimensiune, '25 km');
check('frac 0.9 -> 28 km contract', resolveClick('7oju77qb', 0.9).dimensiune, '28 km');

console.log('=== Bistricioara Harghita (group bistricioara-harghita) ===');
const btr = resolveClick('romsilva-harghita-bistricioara-tronson-i', 0.1);
check('frac 0.1 -> tronson I', btr.name, 'Râul Bistricioara tronson I');
check('frac 0.1 assoc', btr.association, 'Direcția Silvică Harghita');
check('frac 0.9 -> tronson II', resolveClick('romsilva-harghita-bistricioara-tronson-i', 0.9).name, 'Râul Bistricioara tronson II');

console.log('=== Moldova (group moldova) ===');
check('frac 0.45 -> SUCEAVA 59 km', resolveClick('anpa-anpa-0391', 0.45).name, 'Râul Moldova');
check('frac 0.60 -> NEAMȚ BRADUL', resolveClick('anpa-anpa-0391', 0.60).association, 'AVPS BRADUL PIATRA NEAMȚ');
check('frac 0.68 -> NEAMȚ BRADUL (upstream of Roman)', resolveClick('anpa-anpa-0391', 0.68).association, 'AVPS BRADUL PIATRA NEAMȚ');
check('frac 0.90 -> NEAMȚ ROMAN (mouth)', resolveClick('anpa-anpa-0391', 0.90).association, 'AVPS ROMAN');
check('frac 0.80 -> Iași', resolveClick('anpa-anpa-0391', 0.80).association, 'AVPS IAȘI');
// real latlng: Roman (46.93N, 26.92E) is the mouth — AVPS ROMAN owns it
check('click Roman (26.92, 46.93)', resolveClick('anpa-anpa-0391', [26.92, 46.93]).association, 'AVPS ROMAN');

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
