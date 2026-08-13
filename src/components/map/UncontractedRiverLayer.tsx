'use client';

import { useMemo, useState } from 'react';
import L from 'leaflet';
import { GeoJSON as LeafletGeoJSON, useMap, useMapEvents } from 'react-leaflet';
import { useMapStore } from '@/stores/map-store';
import { waterToGeoJSON } from '@/utils/geo';
import { getUncontractedStyle } from '@/utils/colors';
import type { Water, WaterFeature } from '@/types/data';

interface UncontractedRiverLayerProps {
  /** filtered uncontracted rivers (county/type/contract filter already applied) */
  waters: Water[];
}

/**
 * Overlay for OSM rivers with NO contract (t_471dad64).
 *
 * Performance (the dataset is 4k+ polylines — must stay light on mobile):
 * 1. VIEWPORT CULLING — only features whose bbox intersects the current map
 *    viewport are added as Leaflet layers; re-evaluated on every moveend.
 * 2. ZOOM LOD — at national zoom only the major rivers (≥30 km) render; the
 *    threshold drops as you zoom in, so small streams appear exactly when
 *    they're big enough to matter on screen.
 * 3. COMPACT GEOMETRY — the served file is pre-simplified (~200 m tolerance),
 *    so each feature is a handful of points (median 6).
 *
 * Style: thin dashed teal (getUncontractedStyle) — clearly different from
 * contracted waters (blue/green/orange). Click opens the 'Necontractat' card.
 * Rendered BELOW the contracted layer so contracted clicks win on overlap.
 */
export function UncontractedRiverLayer({ waters }: UncontractedRiverLayerProps) {
  const selectWater = useMapStore((s) => s.selectWater);
  const map = useMap();

  // Viewport snapshot (zoom + bounds) — re-captured on every pan/zoom end.
  const [view, setView] = useState<{ zoom: number; bounds: L.LatLngBounds }>(() => ({
    zoom: map.getZoom(),
    bounds: map.getBounds(),
  }));

  useMapEvents({
    moveend: () => setView({ zoom: map.getZoom(), bounds: map.getBounds() }),
  });

  // Zoom LOD thresholds (km): only rivers long enough to be meaningful at the
  // current zoom. National view shows majors; zoom in and the streams appear.
  const minLengthKm = view.zoom < 8 ? 30 : view.zoom < 10 ? 10 : 0;

  const visibleFeatures = useMemo(() => {
    const pad = view.bounds.pad(0.25);
    const west = pad.getWest();
    const east = pad.getEast();
    const south = pad.getSouth();
    const north = pad.getNorth();
    const out: GeoJSON.Feature[] = [];
    for (const w of waters) {
      if ((w.lengthKm ?? 0) < minLengthKm) continue;
      const [bl, bt, br, bb] = w.bbox;
      if (bl > east || br < west || bt > north || bb < south) continue;
      out.push(waterToGeoJSON(w) as GeoJSON.Feature);
    }
    return out;
  }, [waters, view, minLengthKm]);

  const handleClick = (feature: WaterFeature) => {
    selectWater(feature.properties.slug);
  };

  // Rebuild layers on viewport change (cheap — only visible features).
  // The county/type filter is part of the key: react-leaflet v5 ignores the
  // data prop change without a key change, so the teal layer would otherwise
  // keep stale rivers after a filter toggle (t_117f0b99).
  const filterSig = waters.length ? `${waters.length}:${waters[0].slug}:${waters[waters.length - 1].slug}` : 'empty';
  const layerKey = `${view.zoom}|${view.bounds.getWest().toFixed(2)},${view.bounds.getSouth().toFixed(2)},${view.bounds.getEast().toFixed(2)},${view.bounds.getNorth().toFixed(2)}|${filterSig}`;

  const hitCollection = useMemo<GeoJSON.FeatureCollection>(() => {
    return {
      type: 'FeatureCollection',
      features: visibleFeatures.filter(
        (f) => f.geometry.type === 'LineString' || f.geometry.type === 'MultiLineString',
      ),
    } as GeoJSON.FeatureCollection;
  }, [visibleFeatures]);

  const style = getUncontractedStyle();

  return (
    <>
      {/* Invisible wide hit polylines — reliable click/tap on thin rivers */}
      <LeafletGeoJSON
        key={`hits-${layerKey}`}
        data={hitCollection}
        style={() => ({ weight: 14, opacity: 0 })}
        onEachFeature={(feature, layer: L.Path) => {
          const f = feature as WaterFeature;
          layer.on('click', () => handleClick(f));
        }}
      />
      {/* Visible thin teal dashed lines */}
      <LeafletGeoJSON
        key={`vis-${layerKey}`}
        data={{ type: 'FeatureCollection', features: visibleFeatures } as GeoJSON.FeatureCollection}
        style={style}
        onEachFeature={(feature, layer: L.Path) => {
          const f = feature as WaterFeature;
          layer.on('click', () => handleClick(f));
          layer.bindTooltip(f.properties.name, { sticky: true, direction: 'top' });
        }}
      />
    </>
  );
}
