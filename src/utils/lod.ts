/**
 * P1 §4.4 / §7.4 — SHARED zoom-LOD thresholds + viewport culling helpers.
 *
 * Single source of truth for the level-of-detail thresholds used by BOTH the
 * uncontracted overlay (UncontractedWaterLayer) and the contracted layer
 * (WaterFeatureLayer) so the two never drift (plan §7.4 risk 4). Also used by
 * scripts/build_uncontracted_majors.py to build the first-paint "majors"
 * subset (rivers ≥30km + lakes ≥100ha — exactly this module's zoom<8 tier),
 * so the shipped majors file and the FE LOD stay in lockstep.
 *
 * Tiers (zoom thresholds:
 *   zoom < 8  → majors only (rivers ≥ 30 km, lakes ≥ 100 ha)  [national view]
 *   zoom < 10 → rivers ≥ 10 km, lakes ≥ 10 ha
 *   zoom >= 10→ no LOD (0) — everything renders
 * A locality filter bypasses LOD entirely (t_9529e678: "show me THIS place"),
 * so disabled thresholds = 0.
 */
import type { LatLngBounds } from 'leaflet';
import type { BBox } from '@/types/data';

export interface LodThresholds {
  minLengthKm: number;
  minAreaHa: number;
}

/** Zoom-tier LOD thresholds (shared by both water layers). */
export function lodThresholds(zoom: number, localityActive = false): LodThresholds {
  if (localityActive) return { minLengthKm: 0, minAreaHa: 0 };
  if (zoom < 8) return { minLengthKm: 30, minAreaHa: 100 };
  if (zoom < 10) return { minLengthKm: 10, minAreaHa: 10 };
  return { minLengthKm: 0, minAreaHa: 0 };
}

/**
 * Does a water pass the zoom-LOD size gate? A water with NO size field
 * (bbox-fallback dot / ungeocoded) always passes — discrete points must render
 * at any zoom (plan §4.4: culling is the win for contracted; such entries are
 * few). Rivers are gated on lengthKm, lakes/ponds on areaHa.
 */
export function passesLod(
  w: { lengthKm?: number; areaHa?: number; subtype?: string },
  t: LodThresholds,
): boolean {
  if (w.areaHa != null) return w.areaHa >= t.minAreaHa;
  if (w.lengthKm != null) return w.lengthKm >= t.minLengthKm;
  return true; // no size metadata → keep it (dots are cheap)
}

/**
 * Does a bbox [minLon, minLat, maxLon, maxLat] intersect a padded viewport?
 */
export function bboxInBounds(bbox: BBox | undefined, bounds: LatLngBounds, pad = 0.25): boolean {
  if (!bbox) return true;
  const padded = bounds.pad(pad);
  const west = padded.getWest();
  const east = padded.getEast();
  const south = padded.getSouth();
  const north = padded.getNorth();
  const [minLon, minLat, maxLon, maxLat] = bbox;
  return minLon <= east && maxLon >= west && minLat <= north && maxLat >= south;
}

/**
 * Compact signature of a viewport for react-leaflet layer re-keying —
 * mirrors the UncontractedWaterLayer layerKey, so pan/zoom remounts the layer.
 */
export function viewSuffix(zoom: number, bounds: LatLngBounds): string {
  return `${zoom}|${bounds.getWest().toFixed(2)},${bounds.getSouth().toFixed(2)},${bounds.getEast().toFixed(2)},${bounds.getNorth().toFixed(2)}`;
}
