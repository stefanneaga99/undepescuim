/* eslint-disable no-console */
/**
 * t_5f5f2cce — verify contractAtFraction resolution on the Jiu + Sohodol
 * groups after the data fix. Replicates the FE logic (exact sector intervals
 * win, else Voronoi over course_frac) over the full-course fractions.
 */
import { readFileSync } from 'node:fs';

const waters = JSON.parse(readFileSync('public/data/waters.json', 'utf8'));

function groupKeyOf(w) {
  if (w.riverGroup) return w.riverGroup;
  const lower = (w.name || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/^(raul|paraul|parau|valea|lacul|balta|acumularea|acumulare)\s+/, '')
    .replace(/[()]/g, '')
    .trim()
    .split(/\s+/)[0] ?? '';
  return lower;
}

function isMainCourse(name) {
  return !/^(valea|paraul|parau|pârâu|pârâul)\s/i.test(name || '');
}

function courseRank(name) {
  const n = (name || '').toLowerCase();
  if (n.includes('superior') || n.includes('superioar')) return 0;
  if (n.includes('mijloci')) return 1;
  if (n.includes('inferior') || n.includes('inferioar')) return 2;
  return 3;
}

function contractGroup(clicked) {
  const gk = groupKeyOf(clicked);
  return waters.filter(
    (w) => (isMainCourse(w.name) || w.mainCourse === true) && groupKeyOf(w) === gk,
  );
}

function contractAtFraction(clickedRef, frac) {
  const clicked =
    (clickedRef.slug && waters.find((w) => w.slug === clickedRef.slug)) ||
    (clickedRef.name && waters.find((w) => w.name === clickedRef.name)) ||
    { name: clickedRef.name };
  const group = contractGroup(clicked);
  if (group.length <= 1) return null;
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

let failures = 0;
const check = (cond, label) => {
  if (cond) console.log(`  PASS  ${label}`);
  else { console.log(`  FAIL  ${label}`); failures += 1; }
};

console.log('== Jiu group resolution (full-course fractions) ==');
const jiu = waters.find((w) => w.slug === 'qrjybswm');
const cases = [
  [0.005, 'fanvixkg', 'Jiul Inferior (Pro Pescar) — confluence end'],
  [0.012, 'fanvixkg', 'Jiul Inferior (Pro Pescar) — mid'],
  [0.05, 'anpa-romsilva-0239', 'Romsilva Jiu (D.S. Gorj)'],
  [0.10, 'anpa-romsilva-0239', 'Romsilva Jiu (D.S. Gorj) — near Bumbești'],
  [0.20, 'qrjybswm', 'Jiu Gorj (AJVPS GORJ)'],
  [0.30, 'qrjybswm', 'Jiu Gorj (AJVPS GORJ) — Târgu Jiu'],
  [0.45, 'qrjybswm', 'Jiu Gorj (AJVPS GORJ) — near Țânțăreni'],
  [0.60, 'anpa-anpa-0280', 'Jiu Dolj (AJVPS DOLJ)'],
  [0.90, 'anpa-anpa-0280', 'Jiu Dolj (AJVPS DOLJ) — lower'],
];
for (const [frac, expectSlug, label] of cases) {
  const got = contractAtFraction({ slug: jiu.slug }, frac);
  check(got && got.slug === expectSlug, `frac ${frac} → ${expectSlug} (${label}) — got ${got ? got.slug : null}`);
}

console.log('== Sohodol group resolution ==');
const soh = waters.find((w) => w.slug === '2yxhr1b0');
const scases = [
  [0.10, '2yxhr1b0', 'Sohodol I (A.CERBUL CARPATIN) — upper'],
  [0.40, '2yxhr1b0', 'Sohodol I (A.CERBUL CARPATIN) — before Runcu'],
  [0.60, '8rd9jm0l', 'Sohodol II (AJVPS GORJ) — Runcu→Stolojani'],
  [0.70, '8rd9jm0l', 'Sohodol II (AJVPS GORJ) — near Stolojani'],
  [0.90, '8rd9jm0l', 'tail (Stolojani→mouth) falls to Sohodol II via Voronoi'],
];
for (const [frac, expectSlug, label] of scases) {
  const got = contractAtFraction({ slug: soh.slug }, frac);
  check(got && got.slug === expectSlug, `frac ${frac} → ${expectSlug} (${label}) — got ${got ? got.slug : null}`);
}

console.log('== Jiul de vest group resolution (Voronoi over course_frac 0.35/0.85) ==');
const vest = waters.find((w) => w.slug === '6vsle29k');
const vcases = [
  [0.20, '6vsle29k', 'Jiul de vest superior'],
  [0.50, '6vsle29k', 'Jiul de vest superior (mid)'],
  [0.70, 'dcomrepi', 'Jiul de vest mijlociu'],
  [0.95, 'dcomrepi', 'Jiul de vest mijlociu (confluence end)'],
];
for (const [frac, expectSlug, label] of vcases) {
  const got = contractAtFraction({ slug: vest.slug }, frac);
  check(got && got.slug === expectSlug, `frac ${frac} → ${expectSlug} (${label}) — got ${got ? got.slug : null}`);
}

console.log(failures === 0 ? '\nCONTRACT-RESOLUTION VERIFY PASSED' : `\nCONTRACT-RESOLUTION VERIFY FAILED (${failures})`);
process.exit(failures === 0 ? 0 : 1);
