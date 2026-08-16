'use client';

import { useCounties } from '@/hooks/use-counties';
import { useLocalities } from '@/hooks/use-localities';
import { useMapStore } from '@/stores/map-store';
import { CountyFilter } from '@/components/map/CountyFilter';
import { LocalityFilter } from '@/components/map/LocalityFilter';
import { WaterTypeFilter } from '@/components/map/WaterTypeFilter';
import { ContractFilter } from '@/components/map/ContractFilter';

/**
 * Filter overlay container (component_structure_plan.md §3.7).
 * - Mobile (<768px): static 44px bar — horizontally scrollable chips +
 *   segmented control (mobile-layout-spec §5.1).
 * - Tablet/desktop (≥768px): left overlay panel with wrapping chips.
 *
 * t_dd918db7: the locality dropdown appears only when ≥1 county is selected —
 * locality is a refinement of county (a locality list only exists for the
 * currently selected counties).
 */
export function FilterBar() {
  const counties = useCounties();
  const localities = useLocalities();
  const countyFilter = useMapStore((s) => s.countyFilter);
  const localityFilter = useMapStore((s) => s.localityFilter);
  const waterTypeFilter = useMapStore((s) => s.waterTypeFilter);
  const contractFilter = useMapStore((s) => s.contractFilter);
  const toggleCounty = useMapStore((s) => s.toggleCounty);
  const toggleLocality = useMapStore((s) => s.toggleLocality);
  const clearLocalities = useMapStore((s) => s.clearLocalities);
  const setWaterTypeFilter = useMapStore((s) => s.setWaterTypeFilter);
  const setContractFilter = useMapStore((s) => s.setContractFilter);

  const content = (
    <>
      <CountyFilter counties={counties} selected={countyFilter} onToggle={toggleCounty} />
      {countyFilter.length > 0 && (
        <LocalityFilter
          localities={localities}
          selected={localityFilter}
          onToggle={toggleLocality}
          onClear={clearLocalities}
        />
      )}
      <div className="flex flex-wrap gap-x-4 gap-y-2 md:flex-col md:items-start md:gap-y-2.5">
        <WaterTypeFilter selected={waterTypeFilter} onChange={setWaterTypeFilter} />
        <ContractFilter selected={contractFilter} onChange={setContractFilter} />
      </div>
    </>
  );

  return (
    <>
      {/* Mobile: fixed bar below header */}
      <div className="z-[1000] flex shrink-0 flex-col gap-1.5 border-b bg-background/95 px-3 py-2 backdrop-blur md:hidden">
        {content}
      </div>

      {/* Tablet/desktop: left overlay panel on the map */}
      <div className="absolute left-3 top-3 z-[1000] hidden max-h-[calc(100dvh-80px)] max-w-[280px] flex-col gap-2.5 overflow-y-auto rounded-xl border bg-white/90 p-3 shadow-md backdrop-blur-sm md:flex dark:bg-neutral-900/90">
        {content}
      </div>
    </>
  );
}
