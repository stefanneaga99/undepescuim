'use client';

import { useCallback, useMemo, useState } from 'react';
import L from 'leaflet';
import { GeoJSON as LeafletGeoJSON, useMap, useMapEvents } from 'react-leaflet';
import { useMapStore } from '@/stores/map-store';
import { waterToGeoJSON } from '@/utils/geo';
import { getUncontractedLakeStyle, getUncontractedStyle, NEUTRAL_COLOR } from '@/utils/colors';
import { bboxInBounds, lodThresholds, passesLod, viewSuffix } from '@/utils/lod';
import type { Water, WaterFeature } from '@/types/data';

interface UncontractedWaterLayerProps {
  /** filtered uncontracted waters (county/type/contract filter already applied):
   * OSM rivers (LineString) AND lakes/ponds (Polygon) — t_471dad64 + t_51e028c4 */
  waters: Water[];
  /** orange focus color, passed when ANY water is selected (t_b1547e24). The
   * selected water's own feature renders orange — whole feature, no sector
   * slicing (uncontracted waters have no contracts). */
  focusColor?: string | null;
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
export function UncontractedWaterLayer({ waters, focusColor }: UncontractedWaterLayerProps) {
  const selectWater = useMapStore((s) => s.selectWater);
  const selectedWaterSlug = useMapStore((s) => s.selectedWaterSlug);
  // t_9529e678: an active locality filter is an explicit "show me THIS place"
  // intent — the matched set is small (5–30 features), so the zoom LOD must
  // NOT cull its small ponds/rivers (the reported bug: selecting a locality
  // emptied the map because at national zoom every pond was < 100 ha). LOD
  // stays for the county-only / national views.
  const localityActive = useMapStore((s) => s.localityFilter.length > 0);
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
  // waters big enough to be meaningful at the current zoom render. Bypassed
  // entirely while a locality filter is active (t_9529e678). Shared with the
  // contracted layer via utils/lod.ts (plan §7.4 — one source of truth).
  const lod = lodThresholds(view.zoom, localityActive);

  const visibleFeatures = useMemo(() => {
    const out: GeoJSON.Feature[] = [];
    for (const w of waters) {
      if (!passesLod(w, lod)) continue;
      if (!bboxInBounds(w.bbox, view.bounds)) continue;
      out.push(waterToGeoJSON(w) as GeoJSON.Feature);
    }
    return out;
  }, [waters, view, lod]);

  const handleClick = (feature: WaterFeature) => {
    selectWater(feature.properties.slug);
  };

  // Rebuild layers on viewport change (cheap — only visible features).
  // The county/type filter is part of the key: react-leaflet v5 ignores the
  // data prop change without a key change, so the teal layer would otherwise
  // keep stale rivers after a filter toggle (t_117f0b99).
  const filterSig = waters.length ? `${waters.length}:${waters[0].slug}:${waters[waters.length - 1].slug}` : 'empty';
  const layerKey = `${viewSuffix(view.zoom, view.bounds)}|${filterSig}`;

  const isPolygonFeature = (f: GeoJSON.Feature) =>
    f.geometry.type === 'Polygon' || f.geometry.type === 'MultiPolygon';

  // Invisible wide hit polylines — reliable click/tap on thin rivers.
  // (Polygons don't need this: their filled area is the click target.)
  // P1 §4.4 item 3 (mirrored from the contracted layer): at zoom < 10 rivers
  // are too dense to tap individually, so the hit layer is dropped — it
  // halves the SVG path count at national view (M14).
  const hitCollection = useMemo<GeoJSON.FeatureCollection | null>(() => {
    if (view.zoom < 10) return null;
    return {
      type: 'FeatureCollection',
      features: visibleFeatures.filter(
        (f) => f.geometry.type === 'LineString' || f.geometry.type === 'MultiLineString',
      ),
    } as GeoJSON.FeatureCollection;
  }, [visibleFeatures, view.zoom]);

  const riverStyle = useMemo(() => getUncontractedStyle(), []);
  const lakeStyle = useMemo(() => getUncontractedLakeStyle(), []);
  // t_b0ac1e29: when a LOCALITY filter is active the user is drilled into one
  // place and expects that place's waters to "pop" blue like the county's
  // contracted waters do (county `emphasizeNeutral`). Brașov city's waters are
  // almost all UNCONTRACTED, so under a locality filter we render them in the
  // same emphasized blue as the contracted emphasis (NEUTRAL_COLOR weight 4),
  // instead of the muted teal they show at national/county overview. The teal
  // meaning ("no permit at this zoom/overview") is preserved whenever no
  // locality is active.
  const localityEmphasisRiver = useMemo<L.PathOptions>(
    () => ({ color: NEUTRAL_COLOR, weight: 4, opacity: 1, dashArray: [] }),
    [],
  );
  const localityEmphasisLake = useMemo<L.PathOptions>(
    () => ({ color: NEUTRAL_COLOR, weight: 1, opacity: 1, fillColor: NEUTRAL_COLOR, fillOpacity: 0.35 }),
    [],
  );

  // Focus-aware style (t_b1547e24): the clicked water's own feature turns
  // orange — solid stroke for rivers (dash cleared), filled orange for ponds.
  // Matched by slug (uncontracted slugs are unique and never collide with the
  // contracted pool). Must live in the style prop: react-leaflet v5 re-applies
  // it on every re-render, while onEachFeature only runs at mount.
  const focusAwareStyle = useCallback(
    (feature?: GeoJSON.Feature<GeoJSON.Geometry, GeoJSON.GeoJsonProperties>): L.PathOptions => {
      const f = feature as WaterFeature | undefined;
      if (!f) return riverStyle;
      const focused =
        !!focusColor && !!selectedWaterSlug && f.properties?.slug === selectedWaterSlug;
      if (focused) {
        if (isPolygonFeature(f)) {
          return {
            color: focusColor,
            weight: 2,
            opacity: 1,
            fillColor: focusColor,
            fillOpacity: 0.3,
          };
        }
        return { color: focusColor, weight: 4, opacity: 1, dashArray: [] };
      }
      // Locality drill-down emphasis (t_b0ac1e29): show THIS locality's
      // uncontracted waters in blue, matching the contracted blue emphasis.
      if (localityActive) {
        return isPolygonFeature(f) ? localityEmphasisLake : localityEmphasisRiver;
      }
      return isPolygonFeature(f) ? lakeStyle : riverStyle;
    },
    [focusColor, selectedWaterSlug, lakeStyle, riverStyle, localityActive, localityEmphasisLake, localityEmphasisRiver],
  );

  return (
    <>
      {/* Invisible wide hit polylines — reliable click/tap on thin rivers.
          Dropped at zoom < 10 (M14 — rivers too dense to tap individually). */}
      {hitCollection && (
        <LeafletGeoJSON
          key={`hits-${layerKey}`}
          data={hitCollection}
          style={() => ({ weight: 14, opacity: 0 })}
          onEachFeature={(feature, layer: L.Path) => {
            const f = feature as WaterFeature;
            layer.on('click', () => handleClick(f));
          }}
        />
      )}
      {/* Visible layer: dashed teal rivers + filled teal ponds (orange when focused) */}
      <LeafletGeoJSON
        key={`vis-${layerKey}`}
        data={{ type: 'FeatureCollection', features: visibleFeatures } as GeoJSON.FeatureCollection}
        style={focusAwareStyle}
        onEachFeature={(feature, layer: L.Path) => {
          const f = feature as WaterFeature;
          layer.on('click', () => handleClick(f));
          layer.bindTooltip(f.properties.name, { sticky: true, direction: 'top' });
        }}
      />
    </>
  );
}
