import type { Water, WaterFeature, WaterFeatureCollection } from '@/types/data';

/**
 * Convert a Water to a GeoJSON Feature.
 *
 * MVP geometry: the water's bbox rendered as a rectangle. When the geocoding
 * pipeline (t_04163c8f) supplies real polygon/polyline geometry, check
 * `water.geojson` FIRST and fall back to the bbox — zero component changes.
 */
export function waterToGeoJSON(water: Water): WaterFeature {
  const [minLon, minLat, maxLon, maxLat] = water.bbox;
  const coordinates: GeoJSON.Polygon['coordinates'] = [
    [
      [minLon, minLat],
      [maxLon, minLat],
      [maxLon, maxLat],
      [minLon, maxLat],
      [minLon, minLat],
    ],
  ];

  return {
    type: 'Feature',
    properties: {
      slug: water.slug,
      name: water.name,
      subtype: water.subtype,
      judet: water.judet,
      asociatieSlug: water.asociatie?.slug ?? null,
    },
    geometry: {
      type: 'Polygon',
      coordinates,
    },
  };
}

/** Convert a Water[] into a single GeoJSON FeatureCollection for <GeoJSON>. */
export function watersToFeatureCollection(waters: Water[]): WaterFeatureCollection {
  return {
    type: 'FeatureCollection',
    features: waters.map(waterToGeoJSON),
  };
}
