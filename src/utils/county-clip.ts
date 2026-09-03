import type { Water } from '@/types/data';

/**
 * Class 4 rendering repair candidates from the bounded audit. Their source
 * geometry is intentionally retained when the lazy clip artifact contains
 * an explicit hide sentinel; this changes only county-filter projection and
 * does not alter the canonical geometry or its unresolved provenance.
 */
export const CLASS4_RENDERING_REPAIR_SLUGS = new Set([
  'anpa-anpa-0202',
  'anpa-anpa-0204',
  'romsilva-bacau-barzauta',
  'romsilva-covasna-sugo',
  'romsilva-maramures-crasna-frumusaua',
  'vb2p0152',
]);

/**
 * Normalize a county name to the key used in `Water.geometryByCounty`
 * (t_117f0b99): lowercase, diacritics stripped, all separators removed.
 * 'Bistrița-Năsăud' and 'Bistrița - Năsăud' both become 'bistritanasaud',
 * matching the offline build script (scripts/build_county_clip_geoms.py).
 */
export function countyClipKey(county: string): string {
  return county
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[\s-]+/g, '');
}

/**
 * Geometry to RENDER for `water` when the county filter is active.
 *
 * - No `geometryByCounty` entry → the water lies fully inside its own county,
 *   so the full `geometry` is already correct (returns it unchanged).
 *   t_9529e678: a water with NO geometry at all (geometry: null — the
 *   ungeocoded ANPA/Romsilva bbox-fallback entries) must NOT be conflated
 *   with "geometry outside its county": it returns `undefined` (no clip
 *   needed) so the caller KEEPS it and the bbox-fallback point dot renders
 *   (t_cdb614de). Previously `water.geometry` (null) leaked through as the
 *   hide-signal and every geometry-less water silently vanished under any
 *   county filter.
 * - `null` entry → the water's geometry does NOT touch its county (misattributed
 *   or foreign fragment) — returns null so the caller hides the water.
 * - GeoJSON entry → the per-county clip (possibly sector-sliced) to render.
 *
 * The full-course `geometry` is always preserved on the water object for click
 * resolution (fractionAtPoint must walk the WHOLE course so sector intervals —
 * full-course fractions — stay correct).
 */
export function countyRenderGeometry(
  water: Water,
): NonNullable<Water['geometry']> | null | undefined {
  const byCounty = water.geometryByCounty;
  if (!byCounty) return (water.geometry as NonNullable<Water['geometry']> | null) ?? undefined;
  const key = countyClipKey(water.judet ?? '');
  if (!(key in byCounty)) return (water.geometry as NonNullable<Water['geometry']> | null) ?? undefined;
  const clip = byCounty[key];
  if (!clip) {
    // The six bounded Class 4 records have stale/over-broad null clip
    // sentinels. Keep their existing source geometry visible rather than
    // changing the data or manufacturing replacement geometry.
    if (CLASS4_RENDERING_REPAIR_SLUGS.has(water.slug) && water.geometry) return water.geometry;
    return null;
  }
  return clip as NonNullable<Water['geometry']>;
}
