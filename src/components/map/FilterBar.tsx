'use client';

import { useCounties } from '@/hooks/use-counties';
import { useMapStore } from '@/stores/map-store';
import { CountyFilter } from '@/components/map/CountyFilter';
import { WaterTypeFilter } from '@/components/map/WaterTypeFilter';
import { ContractFilter } from '@/components/map/ContractFilter';

/**
 * Filter overlay container (component_structure_plan.md §3.7).
 * - Mobile (<768px): static 44px bar — horizontally scrollable chips +
 *   segmented control (mobile-layout-spec §5.1).
 * - Tablet/desktop (≥768px): left overlay panel with wrapping chips.
 */
export function FilterBar() {
  const counties = useCounties();
  const countyFilter = useMapStore((s) => s.countyFilter);
  const waterTypeFilter = useMapStore((s) => s.waterTypeFilter);
  const contractFilter = useMapStore((s) => s.contractFilter);
  const toggleCounty = useMapStore((s) => s.toggleCounty);
  const setWaterTypeFilter = useMapStore((s) => s.setWaterTypeFilter);
  const setContractFilter = useMapStore((s) => s.setContractFilter);

  const content = (
    <>
      <CountyFilter counties={counties} selected={countyFilter} onToggle={toggleCounty} />
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
      <div className="absolute left-3 top-3 z-[1000] hidden max-h-[calc(100dvh-80px)] max-w-[280px] flex-col gap-2.5 overflow-y-auto rounded-xl border bg-white/90 p-3 shadow-md backdrop-blur-sm md:flex">
        {content}
      </div>
    </>
  );
}
