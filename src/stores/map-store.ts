import { create } from 'zustand';
import type { Association, ContractFilter, Water, WaterTypeFilter } from '@/types/data';

/**
 * Single source of truth for all cross-component map UI state.
 * Contract: docs/component_structure_plan.md §5.1 + docs/map-state-data-flow.md §1.
 *
 * Rules:
 * - Selection and filters are INDEPENDENT (R10) — no action clears another's state.
 * - R9: if a filter change removes the selected water, the sheet auto-dismisses.
 *
 * t_471dad64: `waters` are the CONTRACTED waters (association cards);
 * `uncontracted` are the OSM rivers with NO contract (teal overlay,
 * 'Necontractat' cards). They stay separate so contract-resolution logic
 * (contractAtFraction over `waters`) never sees the uncontracted entries.
 */

interface MapStore {
  // Data layer (loaded once, never mutated after load)
  associations: Association[];
  waters: Water[];
  uncontracted: Water[];
  dataLoaded: boolean;

  // Selection layer (mutually independent)
  selectedAssociationSlug: string | null; // null = no association selected
  selectedWaterSlug: string | null; // null = detail sheet closed

  // Filter layer
  countyFilter: string[]; // empty [] = all counties
  waterTypeFilter: WaterTypeFilter; // 'all' | 'lac' | 'rau'
  contractFilter: ContractFilter; // 'all' | 'contractate' | 'necontractate'

  // FlyTo gating (t_697ba939): one-shot flag — the association was cleared
  // as a side effect of CLICKING a water outside it, so the next
  // FlyToController pass must NOT re-fit / zoom out to the full dataset.
  suppressAssociationFlyTo: boolean;

  // F2a: association detail sheet visibility (opened from the association
  // chip on the map). Mirrors the water sheet's one-at-a-time rule: opening
  // it clears the selected water, selecting a water closes it.
  associationSheetOpen: boolean;

  // Actions
  loadData: () => Promise<void>;
  selectAssociation: (slug: string | null) => void;
  selectWater: (slug: string | null) => void;
  consumeAssociationFlyToSuppression: () => void;
  openAssociationSheet: () => void;
  closeAssociationSheet: () => void;
  toggleCounty: (county: string) => void;
  setWaterTypeFilter: (type: WaterTypeFilter) => void;
  setContractFilter: (filter: ContractFilter) => void;
}

/** R9: would `slug` survive the given filters? (checked across both pools) */
function isFilteredOut(
  slug: string | null,
  allWaters: Water[],
  countyFilter: string[],
  waterTypeFilter: WaterTypeFilter,
): boolean {
  if (!slug) return false;
  const water = allWaters.find((w) => w.slug === slug);
  if (!water) return true;
  if (countyFilter.length > 0 && !countyFilter.includes(water.judet)) return true;
  if (waterTypeFilter !== 'all' && water.subtype !== waterTypeFilter) return true;
  return false;
}

export const useMapStore = create<MapStore>((set, get) => ({
  associations: [],
  waters: [],
  uncontracted: [],
  dataLoaded: false,

  selectedAssociationSlug: null,
  selectedWaterSlug: null,

  countyFilter: [],
  waterTypeFilter: 'all',
  contractFilter: 'all',
  suppressAssociationFlyTo: false,
  associationSheetOpen: false,

  loadData: async () => {
    try {
      const [assocRes, watersRes, uncRes, uncLakesRes] = await Promise.all([
        fetch('/data/associations.json'),
        fetch('/data/waters.json'),
        fetch('/data/uncontracted_rivers.json'),
        fetch('/data/uncontracted_lakes.json'),
      ]);
      if (!assocRes.ok || !watersRes.ok) throw new Error(`fetch failed: ${assocRes.status} / ${watersRes.status}`);
      const [associations, waters] = (await Promise.all([
        assocRes.json(),
        watersRes.json(),
      ])) as [Association[], Water[]];
      let uncontracted: Water[] = [];
      if (uncRes.ok) {
        uncontracted = (await uncRes.json()) as Water[];
      }
      // t_51e028c4: ponds/lakes with no contract join the same uncontracted
      // pool — county/type/contract filters and the 'Necontractat' card UX
      // apply to them automatically.
      if (uncLakesRes.ok) {
        const lakes = (await uncLakesRes.json()) as Water[];
        uncontracted = [...uncontracted, ...lakes];
      }
      set({ associations, waters, uncontracted, dataLoaded: true });
    } catch (err) {
      // Never leave the skeleton spinning forever — render an empty map instead.
      console.error('[map-store] loadData failed:', err);
      set({ dataLoaded: true });
    }
  },

  selectAssociation: (slug) =>
    set({ selectedAssociationSlug: slug, associationSheetOpen: false }),

  // F2a: the chip opens the association detail sheet; opening it dismisses
  // the water sheet (one-at-a-time, mirrors the existing selection rules).
  openAssociationSheet: () =>
    set({ associationSheetOpen: true, selectedWaterSlug: null }),
  closeAssociationSheet: () => set({ associationSheetOpen: false }),

  selectWater: (slug) => {
    // t_7a7192ea Bug 2: clicking a river/lake takes over from any active
    // association filter — clear selectedAssociationSlug so the map stops
    // showing the association's green/grey coverage, then select the clicked
    // water (existing orange focus + detail card behavior takes over).
    // t_abccfd6c: EXCEPT when the clicked water BELONGS to the selected
    // association — then the association filter stays (coverage keeps
    // highlighting the association's waters) and the map does NOT re-fit /
    // zoom out (FlyToController only reacts to selectedAssociationSlug
    // changes). Only a click on a water OUTSIDE the association clears it.
    // Also drop a county/type filter that would hide the clicked water (a
    // defensive "as needed" — normally only waters that pass the filters are
    // rendered/clickable, but never leave a selection invisible).
    if (slug === null) {
      set({ selectedWaterSlug: null });
      return;
    }
    const { countyFilter, waterTypeFilter, waters, uncontracted, selectedAssociationSlug } = get();
    const water =
      waters.find((w) => w.slug === slug) ??
      uncontracted.find((w) => w.slug === slug) ??
      null;
    // Same equality the coverage styling uses (colors.ts getFeatureStyle),
    // so a green-highlighted water keeps the association and a grey/dimmed
    // one clears it — visually consistent. Uncontracted waters have no
    // asociatie, so they always clear.
    const belongsToAssociation =
      selectedAssociationSlug !== null &&
      water !== null &&
      water.asociatie?.slug === selectedAssociationSlug;
    // t_697ba939: a click on a water OUTSIDE the association clears the
    // filter (t_7a7192ea), but that clear is a SIDE EFFECT of the click,
    // not the user leaving the association — FlyToController must NOT
    // re-fit / zoom out to the full dataset. Arm the one-shot suppression;
    // only set it when an association is actually being cleared (never
    // leave a stale flag that could swallow a later explicit clear).
    const clearingAssociationByClick = !belongsToAssociation && selectedAssociationSlug !== null;
    set({
      selectedWaterSlug: slug,
      selectedAssociationSlug: belongsToAssociation ? selectedAssociationSlug : null,
      associationSheetOpen: false,
      suppressAssociationFlyTo: clearingAssociationByClick,
      countyFilter:
        water && countyFilter.length > 0 && !countyFilter.includes(water.judet)
          ? []
          : countyFilter,
      waterTypeFilter:
        water && waterTypeFilter !== 'all' && water.subtype !== waterTypeFilter
          ? 'all'
          : waterTypeFilter,
    });
  },

  // t_697ba939: consumed by FlyToController — the association was cleared by
  // a water click, so the map stays put (no zoom-out to the national view).
  consumeAssociationFlyToSuppression: () => set({ suppressAssociationFlyTo: false }),

  toggleCounty: (county) => {
    const { countyFilter, waters, uncontracted, selectedWaterSlug, waterTypeFilter } = get();
    const next = countyFilter.includes(county)
      ? countyFilter.filter((c) => c !== county)
      : [...countyFilter, county];
    set({
      countyFilter: next,
      selectedWaterSlug: isFilteredOut(selectedWaterSlug, [...waters, ...uncontracted], next, waterTypeFilter)
        ? null
        : selectedWaterSlug,
    });
  },

  setWaterTypeFilter: (type) => {
    const { countyFilter, waters, uncontracted, selectedWaterSlug } = get();
    set({
      waterTypeFilter: type,
      selectedWaterSlug: isFilteredOut(selectedWaterSlug, [...waters, ...uncontracted], countyFilter, type)
        ? null
        : selectedWaterSlug,
    });
  },

  setContractFilter: (filter) => {
    // R9: a filter change that hides the selected water dismisses the sheet.
    const { selectedWaterSlug, uncontracted } = get();
    let nextSlug = selectedWaterSlug;
    if (selectedWaterSlug) {
      const isUnc = uncontracted.some((w) => w.slug === selectedWaterSlug);
      if (filter === 'contractate' && isUnc) nextSlug = null;
      if (filter === 'necontractate' && !isUnc) nextSlug = null;
    }
    set({ contractFilter: filter, selectedWaterSlug: nextSlug });
  },
}));
