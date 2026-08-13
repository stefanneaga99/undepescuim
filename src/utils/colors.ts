import type { PathOptions } from 'leaflet';

/**
 * Coverage coloring contract (component_structure_plan.md §5.5):
 *
 * | Condition                              | Color     | Fill  | Weight |
 * |----------------------------------------|-----------|-------|--------|
 * | coverageSlug === null (neutral view)   | #3b82f6   | 0.2   | 2      |
 * | feature's asociatieSlug === coverageSlug | #16a34a | 0.3  | 2      |
 * | otherwise (not covered / no assoc)     | #9ca3af   | 0.15  | 1      |
 */
export function getFeatureStyle(
  asociatieSlug: string | null,
  coverageSlug: string | null,
): PathOptions {
  if (coverageSlug === null) {
    return { color: '#3b82f6', weight: 2, fillColor: '#3b82f6', fillOpacity: 0.2 };
  }
  if (asociatieSlug === coverageSlug) {
    return { color: '#16a34a', weight: 2, fillColor: '#16a34a', fillOpacity: 0.3 };
  }
  return { color: '#9ca3af', weight: 1, fillColor: '#9ca3af', fillOpacity: 0.15 };
}

/** Neutral-view color (no association selected). */
export const NEUTRAL_COLOR = '#3b82f6';
/** Covered-by-selected-association color. */
export const COVERED_COLOR = '#16a34a';
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
