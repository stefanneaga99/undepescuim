'use client';

import { useMemo } from 'react';
import { useMapStore } from '@/stores/map-store';

/**
 * Derived: sorted, deduplicated county list from waters.
 * Independent of filters — chips always show the complete county set.
 */
export function useCounties(): string[] {
  const waters = useMapStore((s) => s.waters);

  return useMemo(() => {
    return [...new Set(waters.map((w) => w.judet))].sort((a, b) =>
      a.localeCompare(b, 'ro'),
    );
  }, [waters]);
}
