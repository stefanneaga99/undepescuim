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
}

/** Normalize a water name to a group key (same as WaterDetailCard). */
function waterKey(name: string): string {
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
function sameRiver(a: string, b: string): boolean {
  if (!a || !b) return false;
  return a.slice(0, 5) === b.slice(0, 5);
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
        // Visible thin line; thick + colored when this river is in focus
        layer.setStyle({
          ...style,
          weight: inFocus ? 6 : 3,
          color: inFocus && focusColor ? focusColor : style.color,
          opacity: inFocus ? 1 : style.opacity ?? 1,
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
    [handleClick, coverageSlug, focusKey, focusColor],
  );

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
