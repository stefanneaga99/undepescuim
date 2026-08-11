'use client';

import { useCallback, useMemo } from 'react';
import { GeoJSON } from 'react-leaflet';
import { useMapStore } from '@/stores/map-store';
import { watersToFeatureCollection } from '@/utils/geo';
import { getFeatureStyle } from '@/utils/colors';
import type { Water, WaterFeature } from '@/types/data';

interface WaterFeatureLayerProps {
  waters: Water[];
  /** selected association slug — colors features green/grey (or all blue when null) */
  coverageSlug: string | null;
}

/**
 * Pure prop-driven renderer: waters[] → FeatureCollection → single <GeoJSON>.
 * Click → store.selectWater(slug). Style per coverage contract (§5.5).
 *
 * The `key` remounts the layer when coverage changes so Leaflet re-applies the
 * style function (react-leaflet GeoJSON applies `style` at creation time).
 * 426 bbox rectangles is trivially cheap to redraw.
 */
export function WaterFeatureLayer({ waters, coverageSlug }: WaterFeatureLayerProps) {
  const selectWater = useMapStore((s) => s.selectWater);

  const featureCollection = useMemo(() => watersToFeatureCollection(waters), [waters]);

  // react-leaflet v5's GeoJSON only updates `style` on prop change — it never
  // calls setData. Remount the layer when the filtered set or coverage changes
  // (426 bbox rectangles redraw in well under a frame).
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
      layer.on('click', () => handleClick(f));
      layer.bindTooltip(f.properties.name, { sticky: true, direction: 'top' });
    },
    [handleClick],
  );

  return (
    <GeoJSON
      key={layerKey}
      data={featureCollection}
      style={(feature) =>
        getFeatureStyle(feature?.properties?.asociatieSlug ?? null, coverageSlug)
      }
      onEachFeature={handleEachFeature}
    />
  );
}
