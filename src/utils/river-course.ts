import type { Water } from '@/types/data';

/**
 * River-course math + contract-resolution helpers.
 *
 * Extracted from WaterFeatureLayer.tsx (QA spike t_127c3a36) so the pure
 * geometry/grouping logic is unit-testable WITHOUT importing leaflet /
 * react-leaflet. The component re-imports from here — no behavior change.
 *
 * The SAME math is mirrored in scripts/_mapping_common.py (ordered_parts /
 * km_to_frac / fraction_at_point); tests/test_parity_vs_frontend.py asserts
 * both sides agree on shared fixtures (the course_frac ordering bugs
 * t_9a7cf783 / t_f4ff3853 guard).
 */

/** Normalize a water name to a group key (same as WaterDetailCard). */
export function waterKey(name: string): string {
  const lower = name.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  return (
    lower
      .replace(/^(raul|paraul|parau|valea|lacul|balta|acumularea|acumulare)\s+/, '')
      .replace(/[()]/g, '')
      .trim()
      .split(/\s+/)[0] ?? ''
  );
}

/**
 * Exact river-group key (t_ac697770): waters carrying `riverGroup` (set by
 * the data pipeline on every member of a multi-contract river and on
 * collision-prone singletons) group EXACTLY by it; everything else falls back
 * to the fuzzy waterKey prefix. Accepts a Water or a feature-properties-like
 * object ({ riverGroup?, name }).
 */
export function groupKeyOf(w: { riverGroup?: string | null; name?: string }): string {
  if (w.riverGroup) return w.riverGroup;
  return waterKey(w.name ?? '');
}

/** True when two water keys name the same river (shared 5-char prefix). */
export function sameRiver(a: string, b: string): boolean {
  if (!a || !b) return false;
  return a.slice(0, 5) === b.slice(0, 5);
}

/** Haversine distance in km between two [lon, lat] points. */
export function haversineKm(a: [number, number], b: [number, number]): number {
  const R = 6371;
  const dLat = ((b[1] - a[1]) * Math.PI) / 180;
  const dLon = ((b[0] - a[0]) * Math.PI) / 180;
  const la1 = (a[1] * Math.PI) / 180;
  const la2 = (b[1] * Math.PI) / 180;
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(la1) * Math.cos(la2) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

/** Length of a line part in km. */
export function partLength(coords: [number, number][]): number {
  let len = 0;
  for (let i = 1; i < coords.length; i++) len += haversineKm(coords[i - 1], coords[i]);
  return len;
}

/**
 * Order MultiLineString parts along the river course (source → mouth).
 * OSM splits long rivers into many ways in arbitrary order. We sort parts by
 * their centroid projected onto the river's principal direction (PCA on the
 * part midpoints), then orient so the source end (higher latitude — rivers
 * in Romania flow from the mountains in the N/center toward the S/E) starts
 * at fraction 0.
 */
export function orderParts(parts: [number, number][][]): [number, number][][] {
  if (parts.length <= 1) return parts;
  const mids = parts.map((p) => p[Math.floor(p.length / 2)]);
  const mx = mids.reduce((a, m) => a + m[0], 0) / mids.length;
  const my = mids.reduce((a, m) => a + m[1], 0) / mids.length;
  // 2x2 covariance, principal eigenvector
  let cxx = 0, cyy = 0, cxy = 0;
  for (const m of mids) {
    cxx += (m[0] - mx) ** 2;
    cyy += (m[1] - my) ** 2;
    cxy += (m[0] - mx) * (m[1] - my);
  }
  const theta = 0.5 * Math.atan2(2 * cxy, cxx - cyy);
  const vx = Math.cos(theta), vy = Math.sin(theta);

  const scored = parts.map((p) => {
    const m = p[Math.floor(p.length / 2)];
    return { p, t: (m[0] - mx) * vx + (m[1] - my) * vy };
  });
  scored.sort((a, b) => a.t - b.t);
  const ordered = scored.map((s) => s.p);

  // Orient: the source (first half of parts) sits at higher latitude in
  // Romania's geography (mountains N/center → plains S/E).
  const half = Math.max(1, Math.floor(ordered.length / 2));
  const latFirst = ordered.slice(0, half).reduce((a, p) => a + p[Math.floor(p.length / 2)][1], 0) / half;
  const latLast = ordered.slice(-half).reduce((a, p) => a + p[Math.floor(p.length / 2)][1], 0) / half;
  return latFirst < latLast ? [...ordered].reverse() : ordered;
}

/**
 * Slice an ordered MultiLineString to the fraction range [f0, f1] of its
 * total length. Returns the sub-geometry (MultiLineString with the parts
 * intersecting the range, trimmed at boundaries).
 */
export function sliceMultiLine(
  parts: [number, number][][],
  f0: number,
  f1: number,
): [number, number][][] {
  const ordered = orderParts(parts);
  const lengths = ordered.map(partLength);
  const total = lengths.reduce((a, b) => a + b, 0);
  if (total <= 0) return [];
  const d0 = f0 * total;
  const d1 = f1 * total;

  const out: [number, number][][] = [];
  let walked = 0;
  for (let i = 0; i < ordered.length; i++) {
    const coords = ordered[i];
    const len = lengths[i];
    const segStart = walked;
    const segEnd = walked + len;
    walked = segEnd;
    if (segEnd <= d0 || segStart >= d1) continue; // outside slice

    // Trim this part's coordinates to the [d0, d1] window
    const trimmed: [number, number][] = [];
    let acc = segStart;
    for (let j = 0; j < coords.length; j++) {
      const pt = coords[j];
      if (j > 0) acc += haversineKm(coords[j - 1], pt);
      if (acc < d0) {
        if (trimmed.length) trimmed[trimmed.length - 1] = pt;
        continue;
      }
      if (acc > d1) {
        if (!trimmed.length || trimmed[trimmed.length - 1] !== coords[j - 1]) {
          trimmed.push(coords[j - 1]);
        }
        trimmed.push(pt);
        break;
      }
      trimmed.push(pt);
    }
    if (trimmed.length >= 2) out.push(trimmed);
  }
  return out;
}

/**
 * Find the fraction [0,1] along an ordered MultiLineString nearest to a point.
 * Returns null when the geometry can't be measured.
 */
export function fractionAtPoint(
  parts: [number, number][][],
  pt: [number, number],
): number | null {
  const ordered = orderParts(parts);
  const lengths = ordered.map(partLength);
  const total = lengths.reduce((a, b) => a + b, 0);
  if (total <= 0) return null;

  // Distance from point to a segment (2D, lon/lat as planar — good enough for
  // picking the nearest river point; km-level accuracy not needed here).
  function distToSeg(a: [number, number], b: [number, number], p: [number, number]): number {
    const abx = b[0] - a[0], aby = b[1] - a[1];
    const apx = p[0] - a[0], apy = p[1] - a[1];
    const len2 = abx * abx + aby * aby;
    let t = len2 ? (apx * abx + apy * aby) / len2 : 0;
    t = Math.max(0, Math.min(1, t));
    const cx = a[0] + t * abx, cy = a[1] + t * aby;
    return Math.hypot(p[0] - cx, p[1] - cy);
  }

  let bestFrac: number | null = null;
  let bestDist = Infinity;
  let walked = 0;
  for (let i = 0; i < ordered.length; i++) {
    const coords = ordered[i];
    const len = lengths[i];
    for (let j = 1; j < coords.length; j++) {
      const d = distToSeg(coords[j - 1], coords[j], pt);
      if (d < bestDist) {
        bestDist = d;
        // fraction = walked-so-far + partial distance along this segment
        const segLen = haversineKm(coords[j - 1], coords[j]);
        const abx = coords[j][0] - coords[j - 1][0];
        const aby = coords[j][1] - coords[j - 1][1];
        const apx = pt[0] - coords[j - 1][0];
        const apy = pt[1] - coords[j - 1][1];
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

/** Return the point at a measured fraction of an ordered river course. */
export function pointAtFraction(
  parts: [number, number][][],
  fraction: number,
): [number, number] | null {
  if (!Number.isFinite(fraction) || fraction < 0 || fraction > 1) return null;
  const ordered = orderParts(parts);
  const lengths = ordered.map(partLength);
  const total = lengths.reduce((a, b) => a + b, 0);
  if (total <= 0) return null;
  const target = fraction * total;
  let walked = 0;
  for (let i = 0; i < ordered.length; i++) {
    const coords = ordered[i];
    for (let j = 1; j < coords.length; j++) {
      const segment = haversineKm(coords[j - 1], coords[j]);
      if (segment <= 0) continue;
      if (walked + segment >= target || (i === ordered.length - 1 && j === coords.length - 1)) {
        const t = Math.max(0, Math.min(1, (target - walked) / segment));
        return [
          coords[j - 1][0] + (coords[j][0] - coords[j - 1][0]) * t,
          coords[j - 1][1] + (coords[j][1] - coords[j - 1][1]) * t,
        ];
      }
      walked += segment;
    }
  }
  return ordered[ordered.length - 1]?.[ordered[ordered.length - 1].length - 1] ?? null;
}

/**
 * True when a name starts with a tributary-looking prefix ('Valea X',
 * 'Pârâul X') — such contracts are usually separate streams, not sectors of
 * the clicked river's main course. Note the diacritics: 'Pârâu'/'Pârâul'
 * must be matched explicitly or they slip through (pârâu != paraul).
 * Prefix-named SECTORS (e.g. 'Pârâu Buzăul Mijlociu') opt back in via the
 * water's `mainCourse` flag — see contractAtFraction.
 */
export function isMainCourse(name: string): boolean {
  return !/^(valea|paraul|parau|pârâu|pârâul)\s/i.test(name);
}

/** River-course order rank: superior < mijlociu < inferior < (plain, i.e. mouth section).
 * Sector names come in both genders — 'Superioară'/'mijlocie'/'inferioara'
 * (Romsilva lists, e.g. 'Râul Zăbala Superioară', 'Râul Putna Mijlocie') and
 * masculine 'superior'/'mijlociu'/'inferior' — match the shared stem so both
 * rank correctly (t_9a7cf783). */
export function courseRank(name: string): number {
  const n = name.toLowerCase();
  if (n.includes('superior') || n.includes('superioar')) return 0;
  if (n.includes('mijloci')) return 1;
  if (n.includes('inferior') || n.includes('inferioar')) return 2;
  return 3;
}

/**
 * Contracts sharing the same river course as `w` — the group used by
 * contractAtFraction / contractInterval / coverage slicing (t_5f5f2cce).
 * Matched EXACTLY by `riverGroup` when available (fixes Siret/Sirețel,
 * Someș/Someșul Mic, Crișul Repede/Alb/Negru collisions, the 'oltul'/'olt'
 * mismatch, and same-name distinct rivers like the Gorj vs Moldavian
 * Bistrița); otherwise the fuzzy waterKey prefix is used. Prefix-named
 * tributaries ('Valea X', 'Pârâu X') are excluded unless mainCourse is set.
 */
export function contractGroup(w: { slug?: string; riverGroup?: string | null; name?: string }, allWaters: Water[]): Water[] {
  const gk = groupKeyOf(w);
  return allWaters.filter(
    (x) =>
      (isMainCourse(x.name) || x.mainCourse === true) &&
      groupKeyOf(x) === gk,
  );
}

/**
 * Pick the contract (water) whose position covers the given fraction of the
 * river course. Resolution order (t_ac697770):
 *  1. EXACT sector intervals: when a contract declares [sectorStart,
 *     sectorEnd], the SMALLEST interval containing `frac` wins (overlapping
 *     county-wide vs sub-club contracts resolve to the most specific one).
 *  2. Voronoi over `course_frac` (geocoded real position), else name-rank +
 *     uniform spread. Each contract owns the interval between the midpoints
 *     to its neighbours.
 * The clicked river is identified by slug first (unambiguous), falling back
 * to name. Returns the water, or null when no grouping applies.
 */
export function contractAtFraction(
  clickedRef: { slug?: string; name?: string; riverGroup?: string },
  frac: number,
  allWaters: Water[],
): Water | null {
  const clicked =
    (clickedRef.slug && allWaters.find((w) => w.slug === clickedRef.slug)) ||
    (clickedRef.name && allWaters.find((w) => w.name === clickedRef.name)) ||
    ({ name: clickedRef.name } as Water);
  const group = contractGroup(clicked, allWaters);
  if (group.length <= 1) return null;

  // 1. exact sector intervals — smallest containing interval wins
  let best: Water | null = null;
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

  // 2. Voronoi: position each contract along the course (geocoded fraction,
  // or fallback to name-rank spread evenly across [0,1]).
  const ranked = [...group].sort((a, b) => courseRank(a.name) - courseRank(b.name));
  const rankedFrac = (i: number) => ranked.length <= 1 ? 0.5 : i / (ranked.length - 1);

  const positioned = ranked.map((w, i) => {
    const f = typeof w.course_frac === 'number' ? w.course_frac : rankedFrac(i);
    return { w, f };
  });
  positioned.sort((a, b) => a.f - b.f);

  // Voronoi: a contract owns from the midpoint to its left neighbour to the
  // midpoint to its right neighbour.
  const n = positioned.length;
  for (let i = 0; i < n; i++) {
    const f = positioned[i].f;
    const left = i > 0 ? (positioned[i - 1].f + f) / 2 : -Infinity;
    const right = i < n - 1 ? (f + positioned[i + 1].f) / 2 : Infinity;
    if (frac >= left && frac < right) return positioned[i].w;
  }
  return null;
}

/**
 * Contract interval [start, end] fraction of a multi-contract river owned by
 * `selected` (t_b6a0e2fe — extracted from MapView.focusRange so association
 * highlighting reuses the exact same geometry math). Resolution order:
 *  1. EXACT sector intervals when the water declares [sectorStart, sectorEnd]
 *     (e.g. Râul Buzăul superior D.S. Brașov 0.0–0.081).
 *  2. Voronoi interval over `course_frac` within the water's riverGroup
 *     (matched exactly by riverGroup, else the fuzzy waterKey prefix) —
 *     each contract owns the midpoint-to-midpoint span around its position.
 * Single-contract rivers return [0, 1] (whole course).
 */
export function contractInterval(selected: Water, allWaters: Water[]): [number, number] {
  if (typeof selected.sectorStart === 'number' && typeof selected.sectorEnd === 'number') {
    return [selected.sectorStart, selected.sectorEnd];
  }
  const group = contractGroup(selected, allWaters);
  if (group.length <= 1) return [0, 1];
  const ranked = [...group].sort((a, b) => courseRank(a.name) - courseRank(b.name));
  const rankedFrac = (i: number) => (ranked.length <= 1 ? 0.5 : i / (ranked.length - 1));
  const positioned = ranked
    .map((w, i) => ({ w, f: typeof w.course_frac === 'number' ? w.course_frac : rankedFrac(i) }))
    .sort((a, b) => a.f - b.f);
  const idx = positioned.findIndex((p) => p.w.slug === selected.slug);
  if (idx < 0) return [0, 1];
  const f = positioned[idx].f;
  const left = idx > 0 ? (positioned[idx - 1].f + f) / 2 : 0;
  const right = idx < positioned.length - 1 ? (f + positioned[idx + 1].f) / 2 : 1;
  return [left, right];
}
