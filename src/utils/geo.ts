import type { Water, WaterFeature, WaterFeatureCollection, WaterFeatureProperties } from '@/types/data';

/**
 * Convert a Water to a GeoJSON Feature.
 *
 * Uses REAL geometry when available (geocoding pipeline output: river
 * polylines MultiLineString / lake polygons Polygon), falls back to the
 * bbox rectangle for waters that haven't been geocoded yet.
 */
export function waterToGeoJSON(water: Water): WaterFeature {
  const commonProps: WaterFeatureProperties = {
    slug: water.slug,
    name: water.name,
    subtype: water.subtype,
    judet: water.judet,
    asociatieSlug: water.asociatie?.slug ?? null,
    riverGroup: water.riverGroup ?? null,
    uncontracted: water.uncontracted ?? false,
    lengthKm: water.lengthKm,
    areaHa: water.areaHa,
  };
  // Real geometry from the geocoding pipeline takes priority
  if (water.geometry && water.geometry.coordinates?.length) {
    return {
      type: 'Feature',
      properties: commonProps,
      geometry: water.geometry as GeoJSON.Geometry,
    };
  }

  // Fallback: bbox rectangle (un-geocoded waters). Skip if no bbox at all.
  if (!water.bbox) {
    return {
      type: 'Feature',
      properties: {
        ...commonProps,
        // marker for non-renderable waters (no geometry, no bbox)
        _hidden: true,
      },
      geometry: {
        type: 'Point',
        coordinates: water.coordinates ?? [25, 45.8],
      },
    };
  }
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
    properties: commonProps,
    geometry: {
      type: 'Polygon',
      coordinates,
    },
  };
}

/**
 * Great-circle distance between two [lat, lon] points, in km (Haversine).
 */
export function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371;
  const toRad = (d: number) => (d * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

/**
 * Distance from a user position to a water, in km (geolocation MVP,
 * docs/geolocation-feasibility.md §2b).
 *
 * - lakes: haversine to the centroid (`coordinates`, [lon, lat]);
 * - rivers: axis-aligned distance to the `bbox` (reflects how close the
 *   water's COURSE is, not just its centroid — a long river's centroid can
 *   be far from a user standing on its bank);
 * - missing `coordinates`/`bbox` (ANPA rows without geocoding): falls back
 *   to whichever exists, and `Infinity` when neither (the water cannot be
 *   located, so it can never appear in "nearby").
 */
export function distanceToWaterKm(lat: number, lon: number, w: Water): number {
  const [minLon, minLat, maxLon, maxLat] = w.bbox ?? [Number.NaN, Number.NaN, Number.NaN, Number.NaN];
  const hasBbox = !Number.isNaN(minLon);
  const [clon, clat] = w.coordinates ?? [Number.NaN, Number.NaN];
  const hasCoords = !Number.isNaN(clon);

  if (w.subtype === 'lac' && hasCoords) return haversineKm(lat, lon, clat, clon);
  if (hasBbox) {
    // km distance to the bbox rectangle, with mid-latitude longitude scaling
    const dLon = Math.max(minLon - lon, 0, lon - maxLon);
    const dLat = Math.max(minLat - lat, 0, lat - maxLat);
    const kLon = 111.32 * Math.cos((lat * Math.PI) / 180);
    return Math.hypot(dLat * 111.32, dLon * kLon);
  }
  if (hasCoords) return haversineKm(lat, lon, clat, clon);
  return Infinity;
}

/** A water + its distance from the user, for the "nearby waters" list. */
export interface NearbyWater {
  slug: string;
  km: number;
}

/**
 * The N nearest locatable waters to a position, within `maxKm` (geolocation
 * MVP). One in-memory sort over the already-loaded contracted pool — no
 * spatial index needed at 1k points (<1 ms). Waters without any geometry are
 * skipped (distance Infinity). Sorted nearest-first.
 */
export function nearestWaters(
  lat: number,
  lon: number,
  waters: Water[],
  opts: { limit: number; maxKm: number },
): NearbyWater[] {
  return waters
    .map((w) => ({ slug: w.slug, km: distanceToWaterKm(lat, lon, w) }))
    .filter((e) => Number.isFinite(e.km) && e.km <= opts.maxKm)
    .sort((a, b) => a.km - b.km)
    .slice(0, opts.limit);
}

/** Convert a Water[] into a single GeoJSON FeatureCollection for <GeoJSON>. */
export function watersToFeatureCollection(waters: Water[]): WaterFeatureCollection {
  return {
    type: 'FeatureCollection',
    features: waters
      .map(waterToGeoJSON)
      .filter((f) => !(f.properties as WaterFeatureProperties)._hidden),
  };
}
