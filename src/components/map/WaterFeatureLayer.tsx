'use client';

import { useCallback, useMemo } from 'react';
import L from 'leaflet';
import { GeoJSON as LeafletGeoJSON } from 'react-leaflet';
import { useMapStore } from '@/stores/map-store';
import { watersToFeatureCollection } from '@/utils/geo';
import { getFeatureStyle } from '@/utils/colors';
import { countyRenderGeometry } from '@/utils/county-clip';
import type { Water, WaterFeature } from '@/types/data';

interface WaterFeatureLayerProps {
  waters: Water[];
  /** all waters (unfiltered) — needed to resolve which contract a click belongs to */
  allWaters: Water[];
  /** selected association slug — colors features green/grey (or all blue when null) */
  coverageSlug: string | null;
  /** contract selected from the detail card — highlight the river in its association color */
  focusKey?: string | null;
  focusColor?: string | null;
  /** [start, end] fraction of the river course owned by the focused contract */
  focusRange?: [number, number] | null;
}

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
function haversineKm(a: [number, number], b: [number, number]): number {
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
function partLength(coords: [number, number][]): number {
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
function orderParts(parts: [number, number][][]): [number, number][][] {
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
function sliceMultiLine(
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
function fractionAtPoint(
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
        // fraction = walked + partial distance along this segment
        const segLen = haversineKm(coords[j - 1], coords[j]);
        const abx = coords[j][0] - coords[j - 1][0];
        const aby = coords[j][1] - coords[j - 1][1];
        const apx = pt[0] - coords[j - 1][0];
        const apy = pt[1] - coords[j - 1][1];
        const len2 = abx * abx + aby * aby;
        let t = len2 ? (apx * abx + apy * aby) / len2 : 0;
        t = Math.max(0, Math.min(1, t));
        bestFrac = (walked + (j - 1 > 0 ? 0 : 0) + t * segLen) / total;
        // walked-so-far = lengths of previous parts + length within this part
        // up to segment j-1's start; approximate by adding partial lengths.
        let within = 0;
        for (let k = 1; k < j; k++) within += haversineKm(coords[k - 1], coords[k]);
        bestFrac = (walked + within + t * segLen) / total;
      }
    }
    walked += len;
  }
  return bestFrac;
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
 * Pick the contract (water) whose position covers the given fraction of the
 * river course. Resolution order (t_ac697770):
 *  1. EXACT sector intervals: when a contract declares [sectorStart,
 *     sectorEnd], the SMALLEST interval containing `frac` wins (overlapping
 *     county-wide vs sub-club contracts resolve to the most specific one).
 *  2. Voronoi over `course_frac` (geocoded real position), else name-rank +
 *     uniform spread. Each contract owns the interval between the midpoints
 *     to its neighbours.
 * The group is matched EXACTLY by `riverGroup` when available (fixes
 * Siret/Sirețel, Someș/Someșul Mic, Crișul Repede/Alb/Negru collisions,
 * the 'oltul'/'olt' mismatch, and same-name distinct rivers like the Gorj
 * vs Moldavian Bistrița); otherwise the fuzzy waterKey prefix is used.
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
  const gk = groupKeyOf(clicked);
  const group = allWaters.filter(
    (w) =>
      (isMainCourse(w.name) || w.mainCourse === true) &&
      groupKeyOf(w) === gk,
  );
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
 * Pure prop-driven renderer: waters[] → FeatureCollection → GeoJSON layers.
 *
 * Hitbox strategy: rivers/lakes are drawn TWICE —
 * 1. an invisible 16px-wide "hit" polyline/polygon underneath (weight 16,
 *    opacity 0) that catches clicks/taps on thin rivers,
 * 2. the visible thin line (weight 2-3) on top.
 * This makes clicking a river reliable on both desktop and mobile.
 */
export function WaterFeatureLayer({
  waters,
  allWaters,
  coverageSlug,
  focusKey,
  focusColor,
  focusRange,
}: WaterFeatureLayerProps) {
  const selectWater = useMapStore((s) => s.selectWater);
  const countyFilter = useMapStore((s) => s.countyFilter);
  const selectedWaterSlug = useMapStore((s) => s.selectedWaterSlug);

  const featureCollection = useMemo(() => watersToFeatureCollection(waters), [waters]);

  const layerKey = `${coverageSlug ?? 'neutral'}|${waters.map((w) => w.slug).join(',')}`;

  // Exact river-group key of the focused contract (t_ac697770) — matches
  // focus slices across name variants ('Râul Oltul superior' / 'Râul Olt').
  const focusGroupKey = useMemo(() => {
    if (!focusKey) return null;
    const w = allWaters.find((x) => x.name === focusKey);
    return w ? groupKeyOf(w) : waterKey(focusKey);
  }, [allWaters, focusKey]);

  // Click on a river: resolve the fraction along the course, then select the
  // contract (association) that owns that sector — not just the first one.
  // NOTE: the rendered geometry may be the per-county clip (t_117f0b99), whose
  // fractions are NOT full-course fractions — always resolve against the
  // ORIGINAL full-course geometry (allWaters) so sectorStart/sectorEnd
  // intervals stay correct.
  const handleClick = useCallback(
    (feature: WaterFeature, latlng?: L.LatLng) => {
      if (latlng) {
        const original = allWaters.find((w) => w.slug === feature.properties.slug);
        const g = original?.geometry ?? feature.geometry;
        if (g && (g.type === 'MultiLineString' || g.type === 'LineString')) {
          const parts =
            g.type === 'MultiLineString'
              ? (g.coordinates as [number, number][][])
              : [g.coordinates as [number, number][]];
          const frac = fractionAtPoint(parts, [latlng.lng, latlng.lat]);
          if (frac !== null) {
            const contract = contractAtFraction(
              { slug: feature.properties.slug, name: feature.properties.name },
              frac,
              allWaters,
            );
            if (contract) {
              selectWater(contract.slug);
              return;
            }
          }
        }
      }
      selectWater(feature.properties.slug);
    },
    [selectWater, allWaters],
  );

  const handleEachFeature = useCallback(
    (feature: GeoJSON.Feature, layer: L.Path) => {
      const f = feature as WaterFeature;
      const style = getFeatureStyle(f.properties?.asociatieSlug ?? null, coverageSlug);
      const isLine = f.geometry.type === 'LineString' || f.geometry.type === 'MultiLineString';

      // River match for focus highlighting (contract selected from the card)
      const inFocus =
        !!focusGroupKey && groupKeyOf(f.properties ?? {}) === focusGroupKey;

      if (isLine) {
        // Visible thin line; thick + colored ONLY when this river is focused
        // AND no km-range slice is in play (single-contract rivers get full focus)
        const sliceActive = !!focusKey && !!focusRange;
        layer.setStyle({
          ...style,
          weight: inFocus && !sliceActive ? 6 : 3,
          color: inFocus && !sliceActive && focusColor ? focusColor : style.color,
          opacity: inFocus && !sliceActive ? 1 : style.opacity ?? 1,
        });
        layer.on('click', (e: L.LeafletMouseEvent) => handleClick(f, e.latlng));
        layer.bindTooltip(f.properties.name, { sticky: true, direction: 'top' });
      } else {
        layer.setStyle({
          ...style,
          weight: inFocus ? 4 : style.weight ?? 2,
          color: inFocus && focusColor ? focusColor : style.color,
        });
        layer.on('click', (e: L.LeafletMouseEvent) => handleClick(f, e.latlng));
        layer.bindTooltip(f.properties.name, { sticky: true, direction: 'top' });
      }
    },
    [handleClick, coverageSlug, focusKey, focusGroupKey, focusColor, focusRange],
  );

  // Focus slice: when a contract owns a km-range of a multi-contract river,
  // render ONLY that sector as a thick colored line (the shared course is
  // sliced by fraction). Single-contract rivers use the full-course style above.
  const focusFeatures = useMemo(() => {
    if (!focusGroupKey || !focusRange) return null;
    // County filter active (t_117f0b99): the rendered geometry is already the
    // per-county clip, so slicing it by FULL-course fractions would highlight a
    // random sub-segment. Highlight the focused water's own county clip instead
    // (for sector contracts the clip IS the sector, clipped to the county).
    if (countyFilter.length > 0) {
      const focused =
        (selectedWaterSlug && allWaters.find((x) => x.slug === selectedWaterSlug)) ||
        allWaters.find((x) => x.name === focusKey);
      if (!focused) return null;
      const clip = countyRenderGeometry(focused);
      if (!clip) return null;
      return [
        {
          type: 'Feature',
          properties: { name: focused.name },
          geometry: clip,
        } as GeoJSON.Feature,
      ];
    }
    const [f0, f1] = focusRange;
    const features: GeoJSON.Feature[] = [];
    for (const f of featureCollection.features) {
      if (groupKeyOf(f.properties ?? {}) !== focusGroupKey) continue;
      const g = f.geometry;
      if (g.type === 'MultiLineString') {
        const sliced = sliceMultiLine(g.coordinates as [number, number][][], f0, f1);
        if (sliced.length) {
          features.push({
            ...f,
            geometry: { type: 'MultiLineString', coordinates: sliced },
          });
        }
      } else if (g.type === 'LineString') {
        const sliced = sliceMultiLine([g.coordinates as [number, number][]], f0, f1);
        if (sliced.length) {
          features.push({
            ...f,
            geometry: { type: 'MultiLineString', coordinates: sliced },
          });
        }
      }
    }
    return features.length ? features : null;
  }, [focusGroupKey, focusRange, featureCollection, countyFilter, allWaters, selectedWaterSlug, focusKey]);

  // Invisible wide hit layers for lines (added after the visible layer).
  // react-leaflet's GeoJSON doesn't expose each layer for extra additions, so
  // we add the hit layer inside onEachFeature via layer.bringToBack after
  // cloning is too late — instead we render a SECOND GeoJSON purely for hits.
  const hitCollection = useMemo(() => {
    const fc = featureCollection;
    return {
      ...fc,
      features: fc.features.filter(
        (f) => f.geometry.type === 'LineString' || f.geometry.type === 'MultiLineString',
      ),
    };
  }, [featureCollection]);

  return (
    <>
      {/* key forces remount on filter change — react-leaflet v5 ignores data
          prop changes without a key change (stale hit targets otherwise). */}
      <GeoJSONHits key={`hits-${layerKey}`} data={hitCollection} onFeatureClick={handleClick} />
      <LeafletGeoJSON
        key={layerKey}
        data={featureCollection}
        style={(feature) =>
          getFeatureStyle(feature?.properties?.asociatieSlug ?? null, coverageSlug)
        }
        onEachFeature={handleEachFeature}
      />
      {/* Focus slice on top: only the selected contract's sector, thick + colored */}
      {focusFeatures && focusColor && (
        <LeafletGeoJSON
          data={
            {
              type: 'FeatureCollection',
              features: focusFeatures,
            } as GeoJSON.FeatureCollection
          }
          style={() => ({
            color: focusColor,
            weight: 7,
            opacity: 1,
            fillOpacity: 0,
          })}
          onEachFeature={(feature, layer: L.Path) => {
            const f = feature as WaterFeature;
            layer.on('click', (e: L.LeafletMouseEvent) => handleClick(f, e.latlng));
            layer.bindTooltip(f.properties.name, { sticky: true, direction: 'top' });
          }}
        />
      )}
    </>
  );
}

/** Renders invisible wide polylines solely to enlarge the click target. */
function GeoJSONHits({
  data,
  onFeatureClick,
}: {
  data: GeoJSON.FeatureCollection;
  onFeatureClick: (f: WaterFeature, latlng?: L.LatLng) => void;
}) {
  return (
    <LeafletGeoJSON
      data={data}
      style={() => ({ color: '#000', weight: 16, opacity: 0, fillOpacity: 0 })}
      onEachFeature={(feature, layer: L.Path) => {
        const f = feature as WaterFeature;
        layer.on('click', (e: L.LeafletMouseEvent) => onFeatureClick(f, e.latlng));
      }}
    />
  );
}
