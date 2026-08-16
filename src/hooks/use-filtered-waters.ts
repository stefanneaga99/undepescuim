'use client';

import { useMemo } from 'react';
import { useMapStore } from '@/stores/map-store';
import { countyRenderGeometry } from '@/utils/county-clip';
import type { Water } from '@/types/data';

/**
 * Derived: CONTRACTED waters filtered by countyFilter[] + waterTypeFilter +
 * contractFilter (AND). Read-only — never mutates the store. Association
 * selection does NOT filter (R3/R10) — it only colors via coverageSlug.
 * The uncontracted overlay is filtered separately (use-filtered-uncontracted).
 *
 * County clipping (t_117f0b99): a water's `geometry` is the FULL OSM course,
 * which crosses several counties, so when a county is selected we render the
 * precomputed per-county clip (`geometryByCounty`) instead. The full course is
 * kept for click resolution (see WaterFeatureLayer — fractionAtPoint must walk
 * the whole course so sector intervals stay correct).
 */
export function useFilteredWaters(): Water[] {
  const waters = useMapStore((s) => s.waters);
  const countyFilter = useMapStore((s) => s.countyFilter);
  const localityFilter = useMapStore((s) => s.localityFilter);
  const waterTypeFilter = useMapStore((s) => s.waterTypeFilter);
  const contractFilter = useMapStore((s) => s.contractFilter);

  return useMemo(() => {
    if (contractFilter === 'necontractate') return [];
    let result = waters;
    if (countyFilter.length > 0) {
      result = result
        .filter((w) => countyFilter.includes(w.judet))
        .map((w) => {
          const clip = countyRenderGeometry(w);
          if (clip === null) return null; // geometry outside its county → hide
          if (clip && clip !== w.geometry) return { ...w, geometry: clip };
          return w;
        })
        .filter((w): w is Water => w !== null);
    }
    if (localityFilter.length > 0) {
      result = result.filter((w) => w.locality && localityFilter.includes(w.locality));
    }
    if (waterTypeFilter !== 'all') {
      result = result.filter((w) => w.subtype === waterTypeFilter);
    }
    return result;
  }, [waters, countyFilter, localityFilter, waterTypeFilter, contractFilter]);
}
