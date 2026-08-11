import type { Water, WaterFeature, WaterFeatureCollection } from '@/types/data';

/**
 * Convert a Water to a GeoJSON Feature.
 *
 * Uses REAL geometry when available (geocoding pipeline output: river
 * polylines MultiLineString / lake polygons Polygon), falls back to the
 * bbox rectangle for waters that haven't been geocoded yet.
 */
export function waterToGeoJSON(water: Water): WaterFeature {
  // Real geometry from the geocoding pipeline takes priority
  if (water.geometry && water.geometry.coordinates?.length) {
    return {
      type: 'Feature',
      properties: {
        slug: water.slug,
        name: water.name,
        subtype: water.subtype,
        judet: water.judet,
        asociatieSlug: water.asociatie?.slug ?? null,
      },
      geometry: water.geometry as GeoJSON.Geometry,
    };
  }

  // Fallback: bbox rectangle (un-geocoded waters)
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
