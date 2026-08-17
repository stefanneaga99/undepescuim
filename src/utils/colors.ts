import type { PathOptions } from 'leaflet';

/**
 * Coverage coloring contract (component_structure_plan.md §5.5 + t_b6a0e2fe):
 *
 * | Condition                              | Color     | Fill  | Weight |
 * |----------------------------------------|-----------|-------|--------|
 * | coverageSlug === null (neutral view)   | #3b82f6   | 0.2   | 2      |
 * | feature's asociatieSlug === coverageSlug | #22c55e | 0.5  | 4      |
 * | otherwise (not covered / no assoc)     | #9ca3af   | 0.06  | 1      |
 *
 * t_b6a0e2fe: association selection is now a STRONG highlight — covered
 * waters get a bold bright-green stroke (weight 4, opacity 1, heavier fill
 * for lakes) while every other water is dimmed (thin grey, low opacity), so
 * the selected association's contracted rivers AND lakes stand out clearly.
 * Distinct from the click-focus orange (#f97316) and the neutral blue.
 */
export function getFeatureStyle(
  asociatieSlug: string | null,
  coverageSlug: string | null,
  emphasizeNeutral = false,
): PathOptions {
  if (coverageSlug === null) {
    // t_14463aec: county-filtered waters (NEUTRAL_COLOR blue #3b82f6) get a
    // VISUAL EMPHASIS when a county filter is active — heavier stroke + fuller
    // fill — so the filter visibly "pops" the county's waters instead of
    // rendering them identical to the unfiltered default (weight 2). Keeps the
    // same hue (#3b82f6) per the coloring contract, only the weight/opacity
    // change. Association green and click-focus orange still layer on top.
    if (emphasizeNeutral) {
      return {
        color: '#3b82f6',
        weight: 4,
        opacity: 1,
        fillColor: '#3b82f6',
        fillOpacity: 0.35,
      };
    }
    return { color: '#3b82f6', weight: 2, fillColor: '#3b82f6', fillOpacity: 0.2 };
  }
  if (asociatieSlug === coverageSlug) {
    return {
      color: '#22c55e',
      weight: 4,
      opacity: 1,
      fillColor: '#22c55e',
      fillOpacity: 0.5,
    };
  }
  return {
    color: '#9ca3af',
    weight: 1,
    opacity: 0.35,
    fillColor: '#9ca3af',
    fillOpacity: 0.06,
  };
}

/** Neutral-view color (no association selected). */
export const NEUTRAL_COLOR = '#3b82f6';
/** Covered-by-selected-association color (bold highlight, t_b6a0e2fe). */
export const COVERED_COLOR = '#22c55e';
/** Not-covered color. */
export const UNCOVERED_COLOR = '#9ca3af';
/** Contract sector highlight color (user-requested orange). */
export const FOCUS_COLOR = '#f97316';
/** Uncontracted OSM river overlay (t_471dad64) — thin muted teal. */
export const UNCONTRACTED_COLOR = '#14b8a6';
/** Uncontracted lake/pond polygon fill (t_51e028c4) — lighter teal tint,
 * clearly distinct from contracted lakes (blue #3b82f6 fill 0.2 / orange
 * focus) while staying in the same 'uncontracted' family as the rivers. */
export const UNCONTRACTED_LAKE_COLOR = '#2dd4bf';
export const UNCONTRACTED_LAKE_FILL = '#14b8a6';
/** bbox-fallback water dot color (t_cdb614de): violet, distinct from blue
 * rivers/lakes and teal uncontracted overlay — reads as 'known location,
 * no mapped course'. Coverage (green/grey) still applies on top. */
export const POINT_FALLBACK_COLOR = '#8b5cf6';

/**
 * Style for bbox-fallback waters (t_cdb614de): a water with a known contract
 * bbox but NO real OSM geometry renders as a small filled DOT at the bbox
 * center — not a blue rectangle. Same coverage semantics as rivers/lakes
 * (neutral violet, covered green, uncovered grey) so association selection
 * still highlights them; only the shape + base hue differ.
 */
export function getPointFallbackStyle(
  asociatieSlug: string | null,
  coverageSlug: string | null,
): PathOptions {
  if (coverageSlug === null) {
    return { color: POINT_FALLBACK_COLOR, weight: 2, fillColor: POINT_FALLBACK_COLOR, fillOpacity: 1 };
  }
  if (asociatieSlug === coverageSlug) {
    return {
      color: COVERED_COLOR,
      weight: 2,
      opacity: 1,
      fillColor: COVERED_COLOR,
      fillOpacity: 1,
    };
  }
  return {
    color: UNCOVERED_COLOR,
    weight: 1,
    opacity: 0.5,
    fillColor: UNCOVERED_COLOR,
    fillOpacity: 0.7,
  };
}

/**
 * Style for the uncontracted overlay (t_471dad64): thin, muted teal, clearly
 * distinct from contracted rivers (blue/orange/green) so users can tell at a
 * glance that fishing there is NOT covered by any permit on this site.
 */
export function getUncontractedStyle(): PathOptions {
  return {
    color: UNCONTRACTED_COLOR,
    weight: 1.5,
    opacity: 0.8,
    dashArray: '4 4',
  };
}

/**
 * Style for uncontracted lake/pond polygons (t_51e028c4): light teal fill
 * with a solid teal outline — the polygon counterpart of the dashed river
 * overlay. Filled so the whole pond is clickable, not just its rim.
 */
export function getUncontractedLakeStyle(): PathOptions {
  return {
    color: UNCONTRACTED_LAKE_COLOR,
    weight: 1,
    opacity: 0.9,
    fillColor: UNCONTRACTED_LAKE_FILL,
    fillOpacity: 0.25,
  };
}
