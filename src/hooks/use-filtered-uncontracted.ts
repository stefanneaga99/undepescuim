'use client';

import { useMemo } from 'react';
import { useMapStore } from '@/stores/map-store';
import { countyRenderGeometry } from '@/utils/county-clip';
import type { Water } from '@/types/data';

/**
 * Derived: UNCONTRACTED OSM rivers (t_471dad64) filtered by countyFilter[] +
 * waterTypeFilter + contractFilter (AND). Read-only. Hidden entirely when the
 * contract filter is 'contractate'.
 *
 * County clipping (t_117f0b99): like the contracted pool, when a county is
 * selected the full-course geometry is replaced by the precomputed per-county
 * clip so no river renders outside the county's territory.
 */
export function useFilteredUncontracted(): Water[] {
  const uncontracted = useMapStore((s) => s.uncontracted);
  const countyFilter = useMapStore((s) => s.countyFilter);
  const waterTypeFilter = useMapStore((s) => s.waterTypeFilter);
  const contractFilter = useMapStore((s) => s.contractFilter);

  return useMemo(() => {
    if (contractFilter === 'contractate') return [];
    let result = uncontracted;
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
    if (waterTypeFilter !== 'all') {
      result = result.filter((w) => w.subtype === waterTypeFilter);
    }
    return result;
  }, [uncontracted, countyFilter, waterTypeFilter, contractFilter]);
}
