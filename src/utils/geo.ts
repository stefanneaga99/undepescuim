import type { CountyFeature, Water, WaterFeature, WaterFeatureCollection, WaterFeatureProperties } from '@/types/data';

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

  // Fallback (t_cdb614de): a water with a known contract bbox but no real
  // OSM geometry renders as a discreet POINT at the bbox center — a small dot
  // (distinct from rivers/lakes), clickable -> card. NOT a blue rectangle:
  // the bbox rectangle was the ugly artifact the user reported at zoom-out.
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

  return {
    type: 'Feature',
    properties: {
      ...commonProps,
      _bboxFallback: true,
    },
    geometry: {
      type: 'Point',
      // center of the contract bbox (or the stored coordinate when present)
      coordinates: [
        water.coordinates?.[0] ?? (minLon + maxLon) / 2,
        water.coordinates?.[1] ?? (minLat + maxLat) / 2,
      ],
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
 * - rivers AND lakes: axis-aligned distance to the `bbox` when one exists.
 *   For rivers the bbox reflects how close the water's COURSE is (a long
 *   river's centroid can be far from a user standing on its bank); for lakes
 *   the bbox reflects the lake's EXTENT — the stored centroid can be stale
 *   (t_6c2ac870: 4 lakes carried centroids in the WRONG county, far from
 *   their real geometry/bbox, so a Timiș lake showed ~18km from Brașov) and
 *   is also a poor proxy for big reservoirs (a user on the shore of a huge
 *   lake should read ~0 km, not the distance to its center).
 * - missing `bbox`, `coordinates` fallback (haversine to the centroid,
 *   [lon, lat]);
 * - missing both (ANPA rows without geocoding): Infinity — the water cannot
 *   be located, so it never appears in "nearby".
 */
export function distanceToWaterKm(lat: number, lon: number, w: Water): number {
  const [minLon, minLat, maxLon, maxLat] = w.bbox ?? [Number.NaN, Number.NaN, Number.NaN, Number.NaN];
  const hasBbox = !Number.isNaN(minLon);

  if (hasBbox) {
    // km distance to the bbox rectangle, with mid-latitude longitude scaling
    const dLon = Math.max(minLon - lon, 0, lon - maxLon);
    const dLat = Math.max(minLat - lat, 0, lat - maxLat);
    const kLon = 111.32 * Math.cos((lat * Math.PI) / 180);
    return Math.hypot(dLat * 111.32, dLon * kLon);
  }
  const [clon, clat] = w.coordinates ?? [Number.NaN, Number.NaN];
  const hasCoords = !Number.isNaN(clon);
  if (hasCoords) return haversineKm(lat, lon, clat, clon);
  return Infinity;
}

/** A water + its distance from the user, for the "nearby waters" list. */
export interface NearbyWater {
  slug: string;
  km: number;
  /**
   * County of the water's segment nearest the user (t_6c2ac870) — computed
   * from the water's geometry/bbox, NOT the contract county (which for
   * multi-county rivers is the association's seat). Null when the water has
   * no locatable geometry and the county lookup misses.
   */
  county: string | null;
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
    .map((w) => ({ slug: w.slug, km: distanceToWaterKm(lat, lon, w), county: null }))
    .filter((e) => Number.isFinite(e.km) && e.km <= opts.maxKm)
    .sort((a, b) => a.km - b.km)
    .slice(0, opts.limit);
}

/** All ring/part points of a water's geometry as [lon, lat] pairs. */
export function geometryParts(geom: NonNullable<Water['geometry']>): [number, number][][] {
  const coords = geom.coordinates;
  if (geom.type === 'LineString') return [coords as [number, number][]];
  if (geom.type === 'MultiLineString') return coords as [number, number][][];
  if (geom.type === 'Polygon') return coords.flat() as [number, number][][];
  if (geom.type === 'MultiPolygon') return coords.flat() as [number, number][][];
  return [];
}

/**
 * The water's location point nearest to the user, as [lon, lat]
 * (t_6c2ac870). Geometry vertices first (the county of the segment the user
 * is closest to), then the bbox rectangle's nearest point, then the stored
 * coordinates as a last resort. Null when the water has none of the three.
 */
export function nearestWaterPoint(lat: number, lon: number, w: Water): [number, number] | null {
  const geom = w.geometry;
  if (geom && geom.coordinates?.length) {
    let best: [number, number] | null = null;
    let bestD = Infinity;
    for (const part of geometryParts(geom)) {
      for (const pt of part) {
        const d = (pt[0] - lon) ** 2 + (pt[1] - lat) ** 2;
        if (d < bestD) {
          bestD = d;
          best = pt;
        }
      }
    }
    if (best) return best;
  }
  if (w.bbox) {
    const [minLon, minLat, maxLon, maxLat] = w.bbox;
    return [Math.min(Math.max(lon, minLon), maxLon), Math.min(Math.max(lat, minLat), maxLat)];
  }
  if (w.coordinates) return w.coordinates as [number, number];
  return null;
}

/** Ray-casting point-in-polygon over a single ring ([lon, lat] points). */
function pointInRing(lat: number, lon: number, ring: [number, number][]): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    if (yi > lat !== yj > lat && lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) {
      inside = !inside;
    }
  }
  return inside;
}

/**
 * County name containing a [lat, lon] point, or null (t_6c2ac870).
 * Counties come from /data/counties.geojson (simplified Nominatim polygons).
 */
export function countyOfPoint(lat: number, lon: number, counties: CountyFeature[]): string | null {
  for (const f of counties) {
    const g = f.geometry;
    if (g.type === 'Polygon') {
      if (pointInRing(lat, lon, g.coordinates[0] as [number, number][])) return f.properties.name;
    } else {
      for (const poly of g.coordinates) {
        if (pointInRing(lat, lon, poly[0] as [number, number][])) return f.properties.name;
      }
    }
  }
  return null;
}

/**
 * County of the water's segment nearest to the user position (t_6c2ac870):
 * resolve the nearest point on the water's geometry/bbox, then attribute it
 * to a county polygon. This is the county shown on the nearby card — the
 * water's OWN county for the visible segment, not the association's seat.
 */
export function nearbyCounty(
  lat: number,
  lon: number,
  w: Water,
  counties: CountyFeature[],
): string | null {
  const p = nearestWaterPoint(lat, lon, w);
  if (!p) return null;
  return countyOfPoint(p[1], p[0], counties);
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
