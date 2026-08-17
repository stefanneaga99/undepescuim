'use client';

import { useMemo } from 'react';
import { useMapStore } from '@/stores/map-store';
import { localityKey } from '@/hooks/use-localities';

/**
 * Derived (t_e70099a9): per-locality water counts for the CURRENT county
 * selection — display name → number of waters (contracted + uncontracted)
 * whose locality matches, scoped to the selected counties.
 *
 * The locality dropdown surfaces these counts ("Brașov  46") so a user
 * selecting a locality gets an EXPLICIT, immediate signal that the filter
 * matched a non-trivial set — even when the rendered set is only faint
 * headwater streams (the uncontracted LOD / bbox-fallback dots that make
 * the map look "unchanged" at a glance). Counts are AND-scoped exactly like
 * the filter itself: same counties, same pools.
 *
 * Counts are keyed by the same normalized `localityKey` used to dedupe the
 * dropdown options, so visually-identical locality variants share one count
 * (mirror of the dropdown's single visible row).
 */
export function useLocalityCounts(): Map<string, number> {
  const waters = useMapStore((s) => s.waters);
  const uncontracted = useMapStore((s) => s.uncontracted);
  const countyFilter = useMapStore((s) => s.countyFilter);

  return useMemo(() => {
    const counts = new Map<string, number>();
    if (countyFilter.length === 0) return counts;
    const add = (locality: string | null | undefined) => {
      if (!locality) return;
      const display = locality.trim();
      if (!display) return;
      const key = localityKey(display);
      counts.set(key, (counts.get(key) ?? 0) + 1);
    };
    for (const w of waters) {
      if (countyFilter.includes(w.judet)) add(w.locality);
    }
    for (const w of uncontracted) {
      if (countyFilter.includes(w.judet)) add(w.locality);
    }
    return counts;
  }, [waters, uncontracted, countyFilter]);
}
