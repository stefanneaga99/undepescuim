import { create } from 'zustand';
import type { Association, Water, WaterTypeFilter } from '@/types/data';

/**
 * Single source of truth for all cross-component map UI state.
 * Contract: docs/component_structure_plan.md §5.1 + docs/map-state-data-flow.md §1.
 *
 * Rules:
 * - Selection and filters are INDEPENDENT (R10) — no action clears another's state.
 * - R9: if a filter change removes the selected water, the sheet auto-dismisses.
 */

interface MapStore {
  // Data layer (loaded once, never mutated after load)
  associations: Association[];
  waters: Water[];
  dataLoaded: boolean;

  // Selection layer (mutually independent)
  selectedAssociationSlug: string | null; // null = no association selected
  selectedWaterSlug: string | null; // null = detail sheet closed

  // Filter layer
  countyFilter: string[]; // empty [] = all counties
  waterTypeFilter: WaterTypeFilter; // 'all' | 'lac' | 'rau'

  // Actions
  loadData: () => Promise<void>;
  selectAssociation: (slug: string | null) => void;
  selectWater: (slug: string | null) => void;
  toggleCounty: (county: string) => void;
  setWaterTypeFilter: (type: WaterTypeFilter) => void;
}

/** R9: would `slug` survive the given filters? */
function isFilteredOut(
  slug: string | null,
  waters: Water[],
  countyFilter: string[],
  waterTypeFilter: WaterTypeFilter,
): boolean {
  if (!slug) return false;
  const water = waters.find((w) => w.slug === slug);
  if (!water) return true;
  if (countyFilter.length > 0 && !countyFilter.includes(water.judet)) return true;
  if (waterTypeFilter !== 'all' && water.subtype !== waterTypeFilter) return true;
  return false;
}

export const useMapStore = create<MapStore>((set, get) => ({
  associations: [],
  waters: [],
  dataLoaded: false,

  selectedAssociationSlug: null,
  selectedWaterSlug: null,

  countyFilter: [],
  waterTypeFilter: 'all',

  loadData: async () => {
    try {
      const [assocRes, watersRes] = await Promise.all([
        fetch('/data/associations.json'),
        fetch('/data/waters.json'),
      ]);
      if (!assocRes.ok || !watersRes.ok) throw new Error(`fetch failed: ${assocRes.status} / ${watersRes.status}`);
      const [associations, waters] = (await Promise.all([
        assocRes.json(),
        watersRes.json(),
      ])) as [Association[], Water[]];
      set({ associations, waters, dataLoaded: true });
    } catch (err) {
      // Never leave the skeleton spinning forever — render an empty map instead.
      console.error('[map-store] loadData failed:', err);
      set({ dataLoaded: true });
    }
  },

  selectAssociation: (slug) => set({ selectedAssociationSlug: slug }),

  selectWater: (slug) => set({ selectedWaterSlug: slug }),

  toggleCounty: (county) => {
    const { countyFilter, waters, selectedWaterSlug, waterTypeFilter } = get();
    const next = countyFilter.includes(county)
      ? countyFilter.filter((c) => c !== county)
      : [...countyFilter, county];
    set({
      countyFilter: next,
      selectedWaterSlug: isFilteredOut(selectedWaterSlug, waters, next, waterTypeFilter)
        ? null
        : selectedWaterSlug,
    });
  },

  setWaterTypeFilter: (type) => {
    const { countyFilter, waters, selectedWaterSlug } = get();
    set({
      waterTypeFilter: type,
      selectedWaterSlug: isFilteredOut(selectedWaterSlug, waters, countyFilter, type)
        ? null
        : selectedWaterSlug,
    });
  },
}));
