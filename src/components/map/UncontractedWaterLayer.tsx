'use client';

import { useMemo, useState } from 'react';
import L from 'leaflet';
import { GeoJSON as LeafletGeoJSON, useMap, useMapEvents } from 'react-leaflet';
import { useMapStore } from '@/stores/map-store';
import { waterToGeoJSON } from '@/utils/geo';
import { getUncontractedLakeStyle, getUncontractedStyle } from '@/utils/colors';
import type { Water, WaterFeature } from '@/types/data';

interface UncontractedWaterLayerProps {
  /** filtered uncontracted waters (county/type/contract filter already applied):
   * OSM rivers (LineString) AND lakes/ponds (Polygon) — t_471dad64 + t_51e028c4 */
  waters: Water[];
}

/**
 * Overlay for OSM waters with NO contract: named rivers (t_471dad64) and all
 * ponds/lakes (t_51e028c4). Rivers render as thin dashed teal polylines;
 * lakes/ponds as light teal filled polygons — the polygon counterpart of the
 * river overlay, clearly distinct from contracted lakes (blue/orange).
 *
 * Performance (the combined dataset is 4k+ rivers and thousands of ponds —
 * must stay light on mobile):
 * 1. VIEWPORT CULLING — only features whose bbox intersects the current map
 *    viewport are added as Leaflet layers; re-evaluated on every moveend.
 * 2. ZOOM LOD — at national zoom only the major rivers (≥30 km) and big lakes
 *    (≥100 ha) render; thresholds drop as you zoom in.
 * 3. COMPACT GEOMETRY — the served files are pre-simplified, so each feature
 *    is a handful of points.
 *
 * Click opens the 'Necontractat' card. Rendered BELOW the contracted layer so
 * contracted clicks win on overlap.
 */
export function UncontractedWaterLayer({ waters }: UncontractedWaterLayerProps) {
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

  // Zoom LOD thresholds: rivers by length (km), lakes by surface (ha). Only
  // waters big enough to be meaningful at the current zoom render.
  const minLengthKm = view.zoom < 8 ? 30 : view.zoom < 10 ? 10 : 0;
  const minAreaHa = view.zoom < 8 ? 100 : view.zoom < 10 ? 10 : 0;

  const visibleFeatures = useMemo(() => {
    const pad = view.bounds.pad(0.25);
    const west = pad.getWest();
    const east = pad.getEast();
    const south = pad.getSouth();
    const north = pad.getNorth();
    const out: GeoJSON.Feature[] = [];
    for (const w of waters) {
      // lake/pond (Polygon data) → area LOD; river → length LOD
      const isLake = w.areaHa != null;
      if (isLake) {
        if (w.areaHa! < minAreaHa) continue;
      } else if ((w.lengthKm ?? 0) < minLengthKm) {
        continue;
      }
      const [bl, bt, br, bb] = w.bbox;
      if (bl > east || br < west || bt > north || bb < south) continue;
      out.push(waterToGeoJSON(w) as GeoJSON.Feature);
    }
    return out;
  }, [waters, view, minLengthKm, minAreaHa]);

  const handleClick = (feature: WaterFeature) => {
    selectWater(feature.properties.slug);
  };

  // Rebuild layers on viewport change (cheap — only visible features).
  // The county/type filter is part of the key: react-leaflet v5 ignores the
  // data prop change without a key change, so the teal layer would otherwise
  // keep stale rivers after a filter toggle (t_117f0b99).
  const filterSig = waters.length ? `${waters.length}:${waters[0].slug}:${waters[waters.length - 1].slug}` : 'empty';
  const layerKey = `${view.zoom}|${view.bounds.getWest().toFixed(2)},${view.bounds.getSouth().toFixed(2)},${view.bounds.getEast().toFixed(2)},${view.bounds.getNorth().toFixed(2)}|${filterSig}`;

  const isPolygonFeature = (f: GeoJSON.Feature) =>
    f.geometry.type === 'Polygon' || f.geometry.type === 'MultiPolygon';

  // Invisible wide hit polylines — reliable click/tap on thin rivers.
  // (Polygons don't need this: their filled area is the click target.)
  const hitCollection = useMemo<GeoJSON.FeatureCollection>(() => {
    return {
      type: 'FeatureCollection',
      features: visibleFeatures.filter(
        (f) => f.geometry.type === 'LineString' || f.geometry.type === 'MultiLineString',
      ),
    } as GeoJSON.FeatureCollection;
  }, [visibleFeatures]);

  const riverStyle = getUncontractedStyle();
  const lakeStyle = getUncontractedLakeStyle();

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
      {/* Visible layer: dashed teal rivers + filled teal ponds */}
      <LeafletGeoJSON
        key={`vis-${layerKey}`}
        data={{ type: 'FeatureCollection', features: visibleFeatures } as GeoJSON.FeatureCollection}
        style={(feature) =>
          isPolygonFeature(feature as GeoJSON.Feature) ? lakeStyle : riverStyle
        }
        onEachFeature={(feature, layer: L.Path) => {
          const f = feature as WaterFeature;
          layer.on('click', () => handleClick(f));
          layer.bindTooltip(f.properties.name, { sticky: true, direction: 'top' });
        }}
      />
    </>
  );
}
