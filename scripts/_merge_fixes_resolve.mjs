#!/usr/bin/env node
/* Simulate FE contractAtFraction/contractInterval for the fixed groups:
   verify a click at a known fraction resolves to the expected contract. */
import fs from 'fs';

const waters = JSON.parse(fs.readFileSync('public/data/waters.json', 'utf8'));

function isMainCourse(name) {
  return !/^(valea|paraul|parau|pârâu|pârâul)\s/i.test(name);
}
function groupKeyOf(w) {
  return w.riverGroup || (w.name || '').toLowerCase().replace(/^(râul|raul|pârâul|paraul|pârâu|parau|valea)\s+/i, '').replace(/\s+/g, '-');
}
function courseRank(name) {
  const n = name.toLowerCase();
  if (n.includes('superior') || n.includes('superioar')) return 0;
  if (n.includes('mijloci')) return 1;
  if (n.includes('inferior') || n.includes('inferioar')) return 2;
  return 3;
}
function contractGroup(w) {
  const gk = groupKeyOf(w);
  return waters.filter((x) => (isMainCourse(x.name) || x.mainCourse === true) && groupKeyOf(x) === gk);
}
function contractAtFraction(slug, frac) {
  const clicked = waters.find((w) => w.slug === slug);
  if (!clicked) return null;
  const group = contractGroup(clicked);
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

const checks = [
  // [group, ownerSlug, fraction, expectedSlug]
  ['argesel', '0hxo4zi3', 0.10, '0djgr9l8'],
  ['argesel', '0hxo4zi3', 0.50, '0hxo4zi3'],
  ['budacul', 'u1frrl08', 0.10, 'gvmaf2tz'],
  ['budacul', 'u1frrl08', 0.90, 'u1frrl08'],
  ['crisul-negru', '9mfds2yv', 0.05, '7ull4jnk'],
  ['crisul-negru', '9mfds2yv', 0.25, 'jw9il5yo'],
  ['crisul-negru', '9mfds2yv', 0.40, 'w69nse7i'],
  ['crisul-negru', '9mfds2yv', 0.90, '9mfds2yv'],
  ['prahova', '53mzatrd', 0.02, '2g9hg98a'],
  ['prahova', '53mzatrd', 0.25, '0a4d89le'],
  ['prahova', '53mzatrd', 0.70, '53mzatrd'],
  ['somesu-rece', '89j19sek', 0.30, 'i9uffwbx'],
  ['somesu-rece', '89j19sek', 0.70, '9y116j3m'],
  ['somesu-rece', '89j19sek', 0.95, '89j19sek'],
  ['targului', 'rv08w2ty', 0.05, 'k44320iw'],
  ['targului', 'rv08w2ty', 0.20, '2dxykcpr'],
  ['targului', 'rv08w2ty', 0.60, 'rv08w2ty'],
  ['teleajen', '0wn4yfsa', 0.10, '0wn4yfsa'],
  ['teleajen', '0wn4yfsa', 0.35, '44plkztf'],
  ['teleajen', '0wn4yfsa', 0.55, 'yfzdgchv'],
  ['teleajen', '0wn4yfsa', 0.80, 'c1gifahb'],
  ['teleajen', '0wn4yfsa', 0.95, 'c1gifahb'],
];

let pass = 0, fail = 0;
for (const [group, owner, frac, expectSlug] of checks) {
  const res = contractAtFraction(owner, frac);
  const ok = res && res.slug === expectSlug;
  if (ok) pass++; else fail++;
  console.log(`${ok ? 'PASS' : 'FAIL'} ${group} frac=${frac} -> ${res ? res.slug + ' (' + res.name + ')' : 'null'} (expect ${expectSlug})`);
}
console.log(`\n${pass}/${pass + fail} resolution checks passed`);
process.exit(fail ? 1 : 0);
