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
  const localityFilter = useMapStore((s) => s.localityFilter);
  const waterTypeFilter = useMapStore((s) => s.waterTypeFilter);
  const contractFilter = useMapStore((s) => s.contractFilter);
  const selectedWaterSlug = useMapStore((s) => s.selectedWaterSlug);

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
    if (localityFilter.length > 0) {
      result = result.filter((w) => w.locality && localityFilter.includes(w.locality));
    }
    if (waterTypeFilter !== 'all') {
      result = result.filter((w) => w.subtype === waterTypeFilter);
    }
    // t_21d2f68d: PIN the selected UNCONTRACTED water through the locality
    // filter (mirror of use-filtered-waters) — the teal river / private pond
    // the user clicked stays visible with its orange focus even when the
    // picked UAT does not contain it. The LOD bypass for an active locality
    // (UncontractedWaterLayer) renders small pinned features too.
    if (selectedWaterSlug && result.every((w) => w.slug !== selectedWaterSlug)) {
      const sel = uncontracted.find((w) => w.slug === selectedWaterSlug);
      const countyOk = countyFilter.length === 0 || countyFilter.includes(sel?.judet ?? '');
      if (sel && countyOk && (waterTypeFilter === 'all' || sel.subtype === waterTypeFilter)) {
        result = [...result, sel];
      }
    }
    return result;
  }, [uncontracted, countyFilter, localityFilter, waterTypeFilter, contractFilter, selectedWaterSlug]);
}
