'use client';

import { useMemo } from 'react';
import { useMapStore } from '@/stores/map-store';
import type { Water } from '@/types/data';

/**
 * Derived: UNCONTRACTED OSM rivers (t_471dad64) filtered by countyFilter[] +
 * waterTypeFilter + contractFilter (AND). Read-only. Hidden entirely when the
 * contract filter is 'contractate'.
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
      result = result.filter((w) => countyFilter.includes(w.judet));
    }
    if (waterTypeFilter !== 'all') {
      result = result.filter((w) => w.subtype === waterTypeFilter);
    }
    return result;
  }, [uncontracted, countyFilter, waterTypeFilter, contractFilter]);
}
