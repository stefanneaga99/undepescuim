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
