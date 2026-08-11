'use client';

import { useCallback, useMemo } from 'react';
import L from 'leaflet';
import { GeoJSON as LeafletGeoJSON } from 'react-leaflet';
import { useMapStore } from '@/stores/map-store';
import { watersToFeatureCollection } from '@/utils/geo';
import { getFeatureStyle } from '@/utils/colors';
import type { Water, WaterFeature } from '@/types/data';

interface WaterFeatureLayerProps {
  waters: Water[];
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
 * OSM splits long rivers into many ways in arbitrary order; we project each
 * part's midpoint onto the source→mouth axis (first part start → last part
 * end as approximation) and sort by that projection.
 */
function orderParts(parts: [number, number][][]): [number, number][][] {
  if (parts.length <= 1) return parts;
  // Axis: from the westernmost-ish start to the easternmost-ish end — use the
  // first part's start and last part's end as a coarse source→mouth vector.
  const src = parts[0][0];
  const mth = parts[parts.length - 1][parts[parts.length - 1].length - 1];
  const dx = mth[0] - src[0];
  const dy = mth[1] - src[1];
  const axisLen = Math.hypot(dx, dy) || 1;

  const scored = parts.map((p) => {
    const mid = p[Math.floor(p.length / 2)];
    const t = ((mid[0] - src[0]) * dx + (mid[1] - src[1]) * dy) / (axisLen * axisLen);
    return { p, t };
  });
  scored.sort((a, b) => a.t - b.t);
  return scored.map((s) => s.p);
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

/** True when the water's name marks it as on the main course (not a valley tributary). */
export function isMainCourse(name: string): boolean {
  return !/^(valea|paraul|parau)\s/i.test(name);
}

/** River-course order rank: superior < mijlociu < inferior < (plain, i.e. mouth section). */
export function courseRank(name: string): number {
  const n = name.toLowerCase();
  if (n.includes('superior')) return 0;
  if (n.includes('mijlociu')) return 1;
  if (n.includes('inferior')) return 2;
  return 3;
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
  coverageSlug,
  focusKey,
  focusColor,
  focusRange,
}: WaterFeatureLayerProps) {
  const selectWater = useMapStore((s) => s.selectWater);

  const featureCollection = useMemo(() => watersToFeatureCollection(waters), [waters]);

  const layerKey = `${coverageSlug ?? 'neutral'}|${waters.map((w) => w.slug).join(',')}`;

  const handleClick = useCallback(
    (feature: WaterFeature) => {
      selectWater(feature.properties.slug);
    },
    [selectWater],
  );

  const handleEachFeature = useCallback(
    (feature: GeoJSON.Feature, layer: L.Path) => {
      const f = feature as WaterFeature;
      const style = getFeatureStyle(f.properties?.asociatieSlug ?? null, coverageSlug);
      const isLine = f.geometry.type === 'LineString' || f.geometry.type === 'MultiLineString';

      // River match for focus highlighting (contract selected from the card)
      const inFocus =
        !!focusKey && sameRiver(focusKey, waterKey(f.properties?.name ?? ''));

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
        layer.on('click', () => handleClick(f));
        layer.bindTooltip(f.properties.name, { sticky: true, direction: 'top' });
      } else {
        layer.setStyle({
          ...style,
          weight: inFocus ? 4 : style.weight ?? 2,
          color: inFocus && focusColor ? focusColor : style.color,
        });
        layer.on('click', () => handleClick(f));
        layer.bindTooltip(f.properties.name, { sticky: true, direction: 'top' });
      }
    },
    [handleClick, coverageSlug, focusKey, focusColor, focusRange],
  );

  // Focus slice: when a contract owns a km-range of a multi-contract river,
  // render ONLY that sector as a thick colored line (the shared course is
  // sliced by fraction). Single-contract rivers use the full-course style above.
  const focusFeatures = useMemo(() => {
    if (!focusKey || !focusRange) return null;
    const [f0, f1] = focusRange;
    const features: GeoJSON.Feature[] = [];
    for (const f of featureCollection.features) {
      const name = f.properties?.name ?? '';
      if (!sameRiver(focusKey, waterKey(name))) continue;
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
  }, [focusKey, focusRange, featureCollection]);

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
      <GeoJSONHits data={hitCollection} onFeatureClick={handleClick} />
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
            layer.on('click', () => handleClick(f));
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
  onFeatureClick: (f: WaterFeature) => void;
}) {
  return (
    <LeafletGeoJSON
      data={data}
      style={() => ({ color: '#000', weight: 16, opacity: 0, fillOpacity: 0 })}
      onEachFeature={(feature, layer: L.Path) => {
        const f = feature as WaterFeature;
        layer.on('click', () => onFeatureClick(f));
      }}
    />
  );
}
