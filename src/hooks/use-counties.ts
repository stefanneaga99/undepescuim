'use client';

import { useMemo } from 'react';
import { useMapStore } from '@/stores/map-store';

/**
 * Derived: sorted, deduplicated county list from contracted waters AND
 * uncontracted OSM rivers (t_471dad64 — the county filter must cover both).
 * Independent of filters — chips always show the complete county set.
 */
export function useCounties(): string[] {
  const waters = useMapStore((s) => s.waters);
  const uncontracted = useMapStore((s) => s.uncontracted);

  return useMemo(() => {
    return [...new Set([...waters, ...uncontracted].map((w) => w.judet))].sort((a, b) =>
      a.localeCompare(b, 'ro'),
    );
  }, [waters, uncontracted]);
}
