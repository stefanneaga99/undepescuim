'use client';

import { useMemo } from 'react';
import { useMapStore } from '@/stores/map-store';
import type { Water } from '@/types/data';

/**
 * Derived: waters filtered by countyFilter[] + waterTypeFilter (AND).
 * Read-only — never mutates the store. Association selection does NOT filter
 * (R3/R10) — it only colors via coverageSlug.
 */
export function useFilteredWaters(): Water[] {
  const waters = useMapStore((s) => s.waters);
  const countyFilter = useMapStore((s) => s.countyFilter);
  const waterTypeFilter = useMapStore((s) => s.waterTypeFilter);

  return useMemo(() => {
    let result = waters;
    if (countyFilter.length > 0) {
      result = result.filter((w) => countyFilter.includes(w.judet));
    }
    if (waterTypeFilter !== 'all') {
      result = result.filter((w) => w.subtype === waterTypeFilter);
    }
    return result;
  }, [waters, countyFilter, waterTypeFilter]);
}
