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
  const selectedWaterSlug = useMapStore((s) => s.selectedWaterSlug);

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
    // t_21d2f68d: PIN the selected water through the locality filter. A
    // locality pick narrows the VISIBLE waters but the click focus must stay
    // visible — the user clicked a river, then refined to a UAT that does not
    // contain it, and the orange highlight vanished (the old R9 auto-dismiss
    // cleared the selection entirely; even kept, the water was no longer in
    // the rendered set). The selected water is re-appended so its feature
    // renders with the orange focus. Scoped to locality-hiding (a locality is
    // a refinement of the already-selected counties, so the pin's county clip
    // always exists); a county/type/contract filter that hides the selection
    // is respected — the selection persists in state but stays hidden until
    // the filter clears.
    if (selectedWaterSlug && result.every((w) => w.slug !== selectedWaterSlug)) {
      const sel = waters.find((w) => w.slug === selectedWaterSlug);
      const countyOk = countyFilter.length === 0 || countyFilter.includes(sel?.judet ?? '');
      if (sel && countyOk && (waterTypeFilter === 'all' || sel.subtype === waterTypeFilter)) {
        let pinned: Water | null = sel;
        if (countyFilter.length > 0) {
          const clip = countyRenderGeometry(sel);
          if (clip === null) pinned = null; // out-of-county selection stays hidden
          else if (clip && clip !== sel.geometry) pinned = { ...sel, geometry: clip };
        }
        if (pinned) result = [...result, pinned];
      }
    }
    return result;
  }, [waters, countyFilter, localityFilter, waterTypeFilter, contractFilter, selectedWaterSlug]);
}
