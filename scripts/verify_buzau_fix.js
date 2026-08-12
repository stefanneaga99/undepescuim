// Simulate the app's click-resolution logic against public/data/waters.json
// to verify the Buzău sector split (tasks t_84b29064 + t_17797a8d).
// Mirrors WaterFeatureLayer.tsx: groupKeyOf / isMainCourse / courseRank /
// contractAtFraction (exact sector intervals first, then Voronoi over course_frac).
const fs = require('fs');
const waters = JSON.parse(fs.readFileSync('public/data/waters.json', 'utf-8'));

// --- mirror of WaterFeatureLayer.tsx helpers ---
function waterKey(name) {
  const lower = name.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  return (
    lower
      .replace(/^(raul|paraul|parau|valea|lacul|balta|acumularea|acumulare)\s+/, '')
      .replace(/[()]/g, '')
      .trim()
      .split(/\s+/)[0] ?? ''
  );
}
function groupKeyOf(w) {
  if (w.riverGroup) return w.riverGroup;
  return waterKey(w.name ?? '');
}
function isMainCourse(name) {
  return !/^(valea|paraul|parau|pârâu|pârâul)\s/i.test(name);
}
function courseRank(name) {
  const n = name.toLowerCase();
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
    (w) =>
      (isMainCourse(w.name) || w.mainCourse === true) &&
      groupKeyOf(w) === gk,
  );
  if (group.length <= 1) return null;

  // 1. exact sector intervals — smallest containing interval wins
  let best = null;
  let bestLen = Infinity;
  for (const w of group) {
    const s = w.sectorStart;
    const e = w.sectorEnd;
    if (typeof s !== 'number' || typeof e !== 'number') continue;
    if (frac >= s && frac < e && e - s < bestLen) {
      bestLen = e - s;
      best = w;
    }
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

// --- test cases: {label, frac} for clicks along the Râul Buzău ---
// fracs computed by projecting geocoded places onto the OSM course
const cases = [
  ['source 0.0', 0.0],
  ['Vama Buzăului (0.0567) — user click area', 0.0567],
  ['Brădet village CV (0.0803)', 0.0803],
  ['Întorsura Buzăului (0.093)', 0.093],
  ['Crasna conf (0.1537)', 0.1537],
  ['Lacul Siriu (0.1892)', 0.1892],
  ['Barajul Siriu (0.2004)', 0.2004],
  ['USER CLICK Gura Siriului (0.2155)', 0.2155],
  ['Siriu comuna (0.2105)', 0.2105],
  ['Nehoiu (0.2398)', 0.2398],
  ['Sibiciu conf (0.277)', 0.277],
  ['Pătârlagele (0.2863)', 0.2863],
  ['Cislău (0.3179)', 0.3179],
  ['Berca (0.426)', 0.426],
  ['Buzău city (0.4968)', 0.4968],
  ['Jirlău geocode (0.7541)', 0.7541],
  ['Voinești/mouth (0.9927)', 0.9927],
  ['mouth 1.0', 1.0],
];

let pass = 0, fail = 0;
console.log('Buzău click resolution (shared course, frac along course):\n');
for (const [label, frac] of cases) {
  const c = contractAtFraction({ slug: 'ufdigh4c', name: 'Râul Buzău' }, frac, waters);
  const name = c ? c.name : '(null)';
  const assoc = c?.asociatie?.name ?? '';
  console.log(`  frac ${frac.toFixed(4)}  ${label.padEnd(38)} -> ${(name + ' — ' + assoc).padEnd(60)}`);

  // expectations
  let ok = true;
  if (frac < 0.081) ok = name === 'Râul Buzăul superior' && assoc === 'Direcția Silvică Brașov';
  else if (frac <= 0.124) ok = name === 'Pârâu Buzăul Mijlociu' && assoc === 'AJVPS COVASNA';
  else if (frac < 0.165) ok = name === 'Valea Buzăului superior' && assoc === 'AJVPS BUZĂU';
  else if (frac < 0.1882) ok = name === 'Râul Buzăul superior cu afluenții săi' && assoc === 'AJVPS BUZĂU';
  else if (frac < 0.2387) ok = name === 'Valea Buzăului inferior' && assoc === 'AJVPS BUZĂU';
  else if (frac < 0.6385) ok = name === 'Râul Buzăul inferior' && assoc === 'AJVPS BUZĂU';
  else ok = name === 'Râul Buzău' && assoc === 'AJVPS Brăila';
  if (ok) { pass++; } else { fail++; console.log(`    ✗ EXPECTED different (MISMATCH)`); }
}
console.log(`\n${pass} passed, ${fail} failed`);

// key acceptance checks from the tasks
console.log('\nKEY ACCEPTANCE CHECKS:');
const rom = contractAtFraction({ slug: 'ufdigh4c', name: 'Râul Buzău' }, 0.05, waters);
console.log(` 1. Headwater click 0.05 (izvoare→Brădet) -> ${rom?.name} (${rom?.asociatie?.name})  ${rom?.asociatie?.slug === 'directia-silvica-brasov' ? 'PASS' : 'FAIL'}`);
const bradet = contractAtFraction({ slug: 'ufdigh4c', name: 'Râul Buzău' }, 0.0803, waters);
console.log(` 2. Brădet village click -> ${bradet?.name} (${bradet?.asociatie?.name})  ${bradet?.name === 'Râul Buzăul superior' ? 'PASS' : 'FAIL'}`);
const cov = contractAtFraction({ slug: 'ufdigh4c', name: 'Râul Buzău' }, 0.093, waters);
console.log(` 3. Întorsura Buzăului -> ${cov?.name} (${cov?.asociatie?.name})  ${cov?.asociatie?.slug === 'ajvps-covasna' ? 'PASS' : 'FAIL'}`);
const dam = contractAtFraction({ slug: 'ufdigh4c', name: 'Râul Buzău' }, 0.2004, waters);
console.log(` 4. Siriu dam click  -> ${dam?.name} (${dam?.asociatie?.name})  ${dam?.asociatie?.slug === 'ajvps-buzau' ? 'PASS' : 'FAIL'}`);
const user = contractAtFraction({ slug: 'ufdigh4c', name: 'Râul Buzău' }, 0.2155, waters);
console.log(` 5. User click 0.2155 -> ${user?.name} (${user?.asociatie?.name})  ${user?.name === 'Valea Buzăului inferior' && user?.asociatie?.slug === 'ajvps-buzau' ? 'PASS' : 'FAIL'}`);

// Romsilva water must have no own geometry (single geometry owner per group)
const romsilva = waters.find((w) => w.slug === 'romsilva-brasov-buzaul-superior');
console.log(` 6. Romsilva shares course (no own geometry) -> ${romsilva?.geometry ? 'FAIL' : 'PASS'}`);
console.log(`    sector [${romsilva?.sectorStart}, ${romsilva?.sectorEnd}] group=${romsilva?.riverGroup}`);

// ordering check: fracs must satisfy Romsilva < Covasna < superior < inferior < Brăila
const buzau = waters.filter((w) => groupKeyOf(w) === 'buzau' && typeof w.course_frac === 'number');
const sorted = [...buzau].sort((a, b) => a.course_frac - b.course_frac);
console.log('\n 7. Final course_frac ordering (buzau group):');
for (const w of sorted) console.log(`    ${String(w.course_frac).padStart(7)}  ${w.name} (${w.asociatie?.name})`);
