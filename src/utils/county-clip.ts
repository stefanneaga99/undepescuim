import type { Water } from '@/types/data';

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
  if (!byCounty) return water.geometry as NonNullable<Water['geometry']> | undefined;
  const key = countyClipKey(water.judet ?? '');
  if (!(key in byCounty)) return water.geometry as NonNullable<Water['geometry']> | undefined;
  const clip = byCounty[key];
  if (!clip) return null;
  return clip as NonNullable<Water['geometry']>;
}
