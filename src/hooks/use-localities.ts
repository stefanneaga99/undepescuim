'use client';

import { useMemo } from 'react';
import { useMapStore } from '@/stores/map-store';

/**
 * Derived (t_dd918db7): sorted, deduplicated locality (UAT) list for the
 * CURRENT county selection. Locality is county-scoped — same-name UATs in
 * different counties (Călărași ×4, Unirea ×4) never collide because the list
 * is derived only from waters whose judet is selected. Waters without a
 * resolved locality simply contribute nothing.
 *
 * Empty when no county is selected — the UI hides the locality control
 * entirely in that case (locality is meaningless without a county).
 */
export function useLocalities(): string[] {
  const waters = useMapStore((s) => s.waters);
  const uncontracted = useMapStore((s) => s.uncontracted);
  const countyFilter = useMapStore((s) => s.countyFilter);

  return useMemo(() => {
    if (countyFilter.length === 0) return [];
    const set = new Set<string>();
    for (const w of [...waters, ...uncontracted]) {
      if (!countyFilter.includes(w.judet)) continue;
      if (w.locality) set.add(w.locality);
    }
    return [...set].sort((a, b) => a.localeCompare(b, 'ro'));
  }, [waters, uncontracted, countyFilter]);
}
