'use client';

import dynamic from 'next/dynamic';
import { useEffect } from 'react';
import { useMapStore } from '@/stores/map-store';
import { FilterBar } from '@/components/map/FilterBar';
import { ColorLegend } from '@/components/map/ColorLegend';
import { WaterDetailSheet } from '@/components/waters/WaterDetailSheet';
import { NearbyWatersSheet } from '@/components/waters/NearbyWatersSheet';
import { AssociationChip } from '@/components/associations/AssociationChip';
import { AssociationDetailSheet } from '@/components/associations/AssociationDetailSheet';
import { LocateButton } from '@/components/map/LocateButton';
import { MapSkeleton } from '@/components/map/MapSkeleton';

/**
 * THE client boundary for the map island (component_structure_plan.md §3.4).
 * Fetches static JSON on mount (R11 — fetch-on-mount), renders the dynamic
 * Leaflet map plus overlays and the detail sheet.
 *
 * Layout (mobile-layout-spec §2):
 *  mobile:  vertical stack — FilterBar (static 44px row) → map → vaul sheet
 *  ≥768px:  horizontal row — map (flex-1) → WaterDetailSheet (side panel)
 */
const MapView = dynamic(() => import('./MapView').then((m) => m.MapView), {
  ssr: false,
  loading: () => <MapSkeleton />,
});

export function MapShell() {
  const dataLoaded = useMapStore((s) => s.dataLoaded);
  const loadData = useMapStore((s) => s.loadData);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  return (
    <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
      <div className="relative flex min-h-0 flex-1 flex-col">
        <FilterBar />
        <div className="relative min-h-0 flex-1">
          {dataLoaded ? <MapView /> : <MapSkeleton />}
          <ColorLegend />
          <AssociationChip />
          <LocateButton />
        </div>
      </div>
      <WaterDetailSheet />
      <NearbyWatersSheet />
      <AssociationDetailSheet />
    </div>
  );
}
