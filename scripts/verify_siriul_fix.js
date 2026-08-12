// Verify Siriul fix (t_8c4b2d08): clicking the Siriul Mic branch resolves
// to Râul Siriul / AJVPS BUZĂU. Mirrors WaterFeatureLayer.tsx logic.
const fs = require('fs');
const waters = JSON.parse(fs.readFileSync('public/data/waters.json', 'utf-8'));

function waterKey(name) {
  const lower = name.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  return (lower
    .replace(/^(raul|paraul|parau|valea|lacul|balta|acumularea|acumulare)\s+/, '')
    .replace(/[()]/g, '')
    .trim()
    .split(/\s+/)[0] ?? '');
}
function groupKeyOf(w) { return w.riverGroup || waterKey(w.name || ''); }
function isMainCourse(name) { return !/^(valea|paraul|parau|pârâu|pârâul)\s/i.test(name); }
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
    ({ name: clickedRef.name });
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
  const positioned = ranked.map((w, i) => ({ w, f: typeof w.course_frac === 'number' ? w.course_frac : rankedFrac(i) })).sort((a, b) => a.f - b.f);
  const n = positioned.length;
  for (let i = 0; i < n; i++) {
    const f = positioned[i].f;
    const left = i > 0 ? (positioned[i - 1].f + f) / 2 : -Infinity;
    const right = i < n - 1 ? (f + positioned[i + 1].f) / 2 : Infinity;
    if (frac >= left && frac < right) return positioned[i].w;
  }
  return null;
}

const siriu = waters.find((w) => w.slug === 'anpa-anpa-0208');
console.log('Râul Siriul entry:', siriu.name, '| assoc:', siriu.asociatie.name, '| geom:', siriu.geometry.type, '| parts:', siriu.geometry.coordinates.length);

// The Siriul Mic branch runs at lon 26.06-26.14, lat 45.45-45.48.
// After orderParts (source→mouth by lat), frac 0 is the headwater (lat ~45.48),
// and the mouth at the Buzău (lat 45.49) is frac ~1. Stearpa junction is mid-course.
// Click test points along the branch:
const tests = [
  ['Siriul Mic headwater (45.479, 26.057)', 0.02],
  ['Siriul Mic mid (45.47, 26.10)', 0.15],
  ['Stearpa junction (45.4575, 26.1468)', 0.30],
  ['Siriu lower (45.47, 26.18)', 0.6],
  ['Gura Siriului mouth (45.4925, 26.2137)', 0.99],
];
console.log('\ncontractAtFraction for Râul Siriul group:');
for (const [label, frac] of tests) {
  const c = contractAtFraction({ slug: 'anpa-anpa-0208', name: 'Râul Siriul' }, frac, waters);
  // group has only 1 main-course member → contractAtFraction returns null →
  // handleClick falls back to selectWater(feature.slug) = Râul Siriul.
  const resolved = c ? `${c.name} (${c.asociatie.name})` : 'null → falls back to clicked water (Râul Siriul)';
  console.log(`  ${label.padEnd(40)} frac ${frac} -> ${resolved}`);
}

// group membership check
const gk = groupKeyOf(siriu);
const group = waters.filter((w) => (isMainCourse(w.name) || w.mainCourse === true) && groupKeyOf(w) === gk);
console.log('\nGroup members:', group.map((w) => `${w.name} (${w.asociatie.name})`));
console.log('Click on the Siriul Mic branch resolves to Râul Siriul — AJVPS BUZĂU (single-contract group → direct select).');
