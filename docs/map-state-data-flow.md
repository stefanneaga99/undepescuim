# Map UI State & Data Flow — UndePescuim.ro

**Date:** 2026-08-11  
**Author:** plan-maker (t_a11e1a6c)  
**Parent:** t_532822fe (Orchestrator)  
**References:** map-component-tree.md (t_fced8bd1), component_structure_plan.md, ARCHITECTURE.md  
**Status:** Draft — awaiting reviewer confirmation

---

## 0. Purpose

This document is a **state and data flow specification** — no implementation code. It defines:

1. The complete state surface (what lives where, what types)
2. Which state is local vs lifted vs derived
3. Every data flow path end-to-end (fetch → map, click → sheet, filter → legend)
4. Component props contracts

A reviewer should be able to trace any user interaction through every state change and verify completeness.

---

## 1. State Surface — Complete Inventory

### 1.1 The Zustand Store (`src/stores/map-store.ts`)

This is the **single source of truth** for all cross-component state. Components read selectors and dispatch actions. No component holds a copy of store data in local state.

```
┌─────────────────────────────────────────────────────────────────┐
│                     Zustand Map Store                           │
├──────────────────┬──────────────────┬──────────────────────────┤
│   DATA LAYER     │  SELECTION LAYER │     FILTER LAYER         │
├──────────────────┼──────────────────┼──────────────────────────┤
│ associations[]   │ selectedAssoc    │ countyFilter: string[]   │
│   82 items       │   slug | null    │   [] = show all          │
│                  │                  │                          │
│ waters[]         │ selectedWater    │ waterTypeFilter          │
│   426 items      │   slug | null    │   'all' | 'lac' | 'rau' │
│                  │                  │                          │
│ dataLoaded       │                  │                          │
│   boolean        │                  │                          │
├──────────────────┴──────────────────┴──────────────────────────┤
│  ACTIONS                                                        │
│  loadData()  selectAssociation()  selectWater()                 │
│  toggleCounty()  setWaterTypeFilter()                           │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Store Type Contract

```typescript
// -- State shape --
interface MapState {
  // Data layer (loaded once, never mutated after load)
  associations: Association[];
  waters: Water[];
  dataLoaded: boolean;

  // Selection layer (mutually independent)
  selectedAssociationSlug: string | null;  // null = no association selected
  selectedWaterSlug: string | null;        // null = detail sheet closed

  // Filter layer
  countyFilter: string[];                  // empty [] = all counties
  waterTypeFilter: WaterTypeFilter;        // 'all' | 'lac' | 'rau'
}

// -- Actions --
interface MapActions {
  loadData: () => Promise<void>;
  selectAssociation: (slug: string | null) => void;
  selectWater: (slug: string | null) => void;
  toggleCounty: (county: string) => void;
  setWaterTypeFilter: (type: WaterTypeFilter) => void;
}

type MapStore = MapState & MapActions;
```

### 1.3 Store Initial State

| Field                    | Initial      | Reason                                         |
|--------------------------|--------------|--------------------------------------------------|
| `associations`           | `[]`          | Filled by `loadData()` on mount                  |
| `waters`                 | `[]`          | Filled by `loadData()` on mount                  |
| `dataLoaded`             | `false`       | True after both fetches resolve                  |
| `selectedAssociationSlug`| `null`       | No association selected at start                 |
| `selectedWaterSlug`      | `null`       | Detail sheet closed at start                     |
| `countyFilter`           | `[]`          | Empty = show all counties                        |
| `waterTypeFilter`        | `'all'`       | Show lakes + rivers together                         |

---

## 2. Derived State (Custom Hooks)

These are NOT store fields. They are `useMemo`-wrapped computations that re-derive when their store dependencies change. No component re-implements this logic; they call the hook.

### 2.1 `useFilteredWaters()` — `src/hooks/use-filtered-waters.ts`

```
Input:   store.waters[], store.countyFilter[], store.waterTypeFilter
Output:  Water[]

Algorithm:
  result = store.waters
  if countyFilter.length > 0:
    result = result.filter(w => countyFilter.includes(w.judet))
  if waterTypeFilter !== 'all':
    result = result.filter(w => w.subtype === waterTypeFilter)
  return result
```

| Depends on store field  | Recomputes when                            |
|---------------------------|---------------------------------------------|
| `waters`                  | Initial load completes                      |
| `countyFilter`            | User toggles a county chip (add/remove)      |
| `waterTypeFilter`         | User switches segment (all/lac/rau)          |

### 2.2 `useCounties()` — `src/hooks/use-counties.ts`

```
Input:   store.waters[]
Output:  string[]  (sorted, deduplicated county names)

Algorithm:
  [...new Set(waters.map(w => w.judet))].sort()
```

| Depends on store field | Recomputes when               |
|-------------------------|-------------------------------|
| `waters`                | Initial load completes        |

Note: County list does NOT change based on filters — it always shows all counties present in the data, so the user can filter to a county even if it has zero visible waters after a water-type filter.

### 2.3 `useSelectedWater()` — inline in WaterDetailSheet (not a separate hook)

```
Input:   store.waters[], store.selectedWaterSlug
Output:  Water | undefined

Algorithm:
  waters.find(w => w.slug === selectedWaterSlug)
```

### 2.4 `useSelectedAssociation()` — inline in WaterDetailCard or ColorLegend

```
Input:   store.associations[], store.selectedAssociationSlug
Output:  Association | undefined

Algorithm:
  associations.find(a => a.slug === selectedAssociationSlug)
```

### 2.5 Derived Visibility States

These are NOT separate hooks — they are computed inline in the components that read them:

| Derived boolean              | Formula                                              | Consumer            |
|------------------------------|------------------------------------------------------|---------------------|
| `isSheetOpen`                | `selectedWaterSlug !== null`                         | WaterDetailSheet    |
| `isAssociationSelected`      | `selectedAssociationSlug !== null`                   | ColorLegend         |
| `isCountyFilterActive`       | `countyFilter.length > 0`                            | CountyFilter (badge)|
| `waterCount` (per association)| `associations.map(a => a.ape)`                      | AssociationSearch   |

---

## 3. Local State — Per Component

State that lives ONLY inside a single component, never read by siblings.

### 3.1 `AssociationSearch.tsx`

| Local state      | Type      | Purpose                                      |
|------------------|-----------|----------------------------------------------|
| `open`           | `boolean` | Whether the cmdk Command dropdown is open     |
| `inputValue`     | `string`  | Current search text (managed by cmdk)         |

**Why local:** cmdk manages these internally. No other component needs to know if the dropdown is open or what the user typed. When the user picks an item, the **side effect** (calling `store.selectAssociation()`) is the only cross-component signal.

### 3.2 `WaterDetailSheet.tsx`

| Local state        | Type      | Purpose                                      |
|--------------------|-----------|----------------------------------------------|
| `dragOffset`       | `number`  | Current Y offset during swipe-down gesture    |
| `isDragging`       | `boolean` | Whether the user is actively dragging         |

**Why local:** The drag gesture is a UI animation detail. When the user releases beyond a threshold, the **side effect** (`store.selectWater(null)`) closes the sheet. The intermediate drag positions are irrelevant to any other component.

### 3.3 `MapView.tsx`

| Local state     | Type                        | Purpose                                 |
|-----------------|-----------------------------|-----------------------------------------|
| `mapInstance`   | `L.Map | null` (ref)        | Leaflet map reference for `flyTo()`     |
| `zoom`          | `number` (derived from map) | Current zoom level (could be used later)|

**Why local:** The map instance is a Leaflet concern. No other component calls `map.flyTo()` — MapView will internally fly to a water when `selectedWaterSlug` changes and the water is outside the viewport. This is an implementation detail of MapView, not shared state.

### 3.4 Components With NO Local State

These are fully controlled components — every visual aspect derives from store or props:

| Component           | Reads from       |
|---------------------|------------------|
| `CountyFilter`      | props (controlled by FilterBar) |
| `WaterTypeFilter`   | props (controlled by FilterBar) |
| `ColorLegend`       | props or store   |
| `WaterDetailCard`   | props (water, association)      |
| `FilterBar`         | store hooks      |
| `Header`            | nothing          |

### 3.5 Summary: Local vs Shared

```
SHARED (Zustand store):
  associations[]  waters[]  dataLoaded
  selectedAssociationSlug  selectedWaterSlug
  countyFilter[]  waterTypeFilter

DERIVED (useMemo hooks):
  useFilteredWaters()  useCounties()
  isSheetOpen  isAssociationSelected

LOCAL (useState / useRef):
  AssociationSearch: open, inputValue
  WaterDetailSheet: dragOffset, isDragging
  MapView: mapInstance (ref)
```

---

## 4. Component Props Contracts

Every component's exact props contract. Components that read the store directly list their store selectors instead of props.

### 4.1 `page.tsx` — Server Component Shell

| Role        | Value                                                   |
|-------------|---------------------------------------------------------|
| Type        | Server Component (async)                                |
| Props       | `{ params: Promise<{ locale: string }> }` (Next.js)     |
| Store reads | None (server-side, no store access)                     |
| Renders     | `<Suspense>` → `<MapShell />`, `<Header />`             |

```
┌─ params.locale ─→ determines translations ─→ not passed down; next-intl reads from context
└─ Renders MapShell (client island)
```

### 4.2 `Header.tsx` — Top Bar

| Role        | Value                                    |
|-------------|------------------------------------------|
| Type        | `'use client'`                           |
| Props       | None                                     |
| Store reads | None (contains AssociationSearch which reads store) |

### 4.3 `AssociationSearch.tsx` — Searchable Selector

| Role        | Value                                                        |
|-------------|--------------------------------------------------------------|
| Type        | `'use client'`                                               |
| Props       | None                                                         |
| Store reads | `store.associations` (full array, 82 items)                  |
| Store writes| `store.selectAssociation(slug \| null)`                      |
| Local state | `open` (boolean), `inputValue` (string) — managed by cmdk    |

```
Data flow:
  store.associations[] ─→ cmdk <Command> items list
  User types ─→ cmdk filters locally (fuzzy)
  User selects "AJVPS Cluj" ─→ store.selectAssociation('ajvps-cluj')
  User selects "Toate asociațiile" ─→ store.selectAssociation(null)
```

### 4.4 `MapShell.tsx` — Client Boundary

| Role        | Value                                                        |
|-------------|--------------------------------------------------------------|
| Type        | `'use client'`                                               |
| Props       | None                                                         |
| Store reads | `store.dataLoaded` (for conditional rendering)               |
| Store writes| `store.loadData()` on mount (useEffect)                      |
| Renders     | MapView (dynamic), WaterDetailSheet, FilterBar, ColorLegend  |

```
Lifecycle:
  1. Mount ─→ useEffect ─→ store.loadData()
  2. loadData(): fetch /data/associations.json → store.associations
                 fetch /data/waters.json       → store.waters
                 set store.dataLoaded = true
  3. dataLoaded === true ─→ MapView mounts (dynamic import resolves)
  4. dataLoaded === false ─→ <MapSkeleton /> shown
```

### 4.5 `MapView.tsx` — Leaflet Container

| Role        | Value                                                        |
|-------------|--------------------------------------------------------------|
| Type        | `'use client'` — loaded via `dynamic(ssr: false)`            |
| Props       | None                                                         |
| Store reads | `store.selectedAssociationSlug` (passed to WaterFeatureLayer)|
|             | `useFilteredWaters()` → waters[] (passed to WaterFeatureLayer)|
| Local state | `mapRef` (L.Map instance, for flyTo)                         |
| Renders     | `<MapContainer>` → TileLayer, ZoomControl, WaterFeatureLayer |

### 4.6 `WaterFeatureLayer.tsx` — GeoJSON Renderer

| Role         | Value                                                       |
|--------------|-------------------------------------------------------------|
| Type         | `'use client'` — loaded via `dynamic(ssr: false)`           |
| Props        | `waters: Water[]`                                           |
|              | `coverageSlug: string \| null`                               |
| Store reads  | None (fully prop-driven — pure component)                   |
| Store writes | `store.selectWater(slug)` on click                          |

```
Props → rendering pipeline:
  waters[] ─→ watersToFeatureCollection() ─→ <GeoJSON data={fc}>
  coverageSlug ─→ getFeatureStyle(f.properties.asociatieSlug, coverageSlug) ─→ style={fn}
  Click ─→ onEachFeature callback ─→ store.selectWater(f.properties.slug)
```

**Coloring per feature:**

| Condition                          | Color   | Fill | Weight |
|------------------------------------|---------|------|--------|
| `coverageSlug === null`            | #3b82f6 | 0.2  | 2      |
| `f.asociatieSlug === coverageSlug` | #16a34a | 0.3  | 2      |
| otherwise                          | #9ca3af | 0.15 | 1      |

### 4.7 `FilterBar.tsx` — Filter Container

| Role        | Value                                                        |
|-------------|--------------------------------------------------------------|
| Type        | `'use client'`                                               |
| Props       | None                                                         |
| Store reads | `useCounties()` → string[] (passes to CountyFilter)          |
|             | `store.countyFilter` (passes to CountyFilter)                |
|             | `store.waterTypeFilter` (passes to WaterTypeFilter)          |
| Store writes| `store.toggleCounty()`, `store.setWaterTypeFilter()` (via callbacks in child props) |

### 4.8 `CountyFilter.tsx` — Chip List

| Role        | Value                                                        |
|-------------|--------------------------------------------------------------|
| Type        | `'use client'`                                               |
| Props       | `counties: string[]` — all county names (from useCounties)   |
|             | `selected: string[]` — currently toggled counties            |
|             | `onToggle: (county: string) => void`                         |
| Store reads | None (fully prop-driven — pure component)                    |

### 4.9 `WaterTypeFilter.tsx` — Segmented Control

| Role        | Value                                                        |
|-------------|--------------------------------------------------------------|
| Type        | `'use client'`                                               |
| Props       | `selected: WaterTypeFilter`                                  |
|             | `onChange: (type: WaterTypeFilter) => void`                  |
| Store reads | None (fully prop-driven — pure component)                    |

### 4.10 `ColorLegend.tsx` — Coverage Legend

| Role        | Value                                                        |
|-------------|--------------------------------------------------------------|
| Type        | `'use client'`                                               |
| Props       | None                                                         |
| Store reads | `store.selectedAssociationSlug`                              |
| Display     | `null` → shows single "Vedere neutră" row (blue)             |
|             | `'slug'` → shows "Acoperit" (green) + "Neacoperit" (grey)    |

### 4.11 `WaterDetailSheet.tsx` — Bottom Sheet / Side Panel

| Role        | Value                                                        |
|-------------|--------------------------------------------------------------|
| Type        | `'use client'`                                               |
| Props       | None                                                         |
| Store reads | `store.selectedWaterSlug`                                    |
|             | `store.waters[]` (to find the Water object)                  |
|             | `store.associations[]` (to find the Association for the card)|
| Store writes| `store.selectWater(null)` on dismiss                         |
| Local state | `dragOffset`, `isDragging` (swipe gesture)                   |

**Visibility logic:**

| `selectedWaterSlug` | Sheet state      | CSS                        |
|---------------------|------------------|-----------------------------|
| `null`              | Hidden           | `translateY(100%)`, `pointer-events: none` |
| `'abc123'`          | Visible          | `translateY(0)`, shows WaterDetailCard |

**Dismiss triggers:**
- Backdrop tap → `store.selectWater(null)`
- Swipe down past 30% threshold → `store.selectWater(null)`
- ESC key → `store.selectWater(null)`
- Close button (×) → `store.selectWater(null)`

### 4.12 `WaterDetailCard.tsx` — Pure Presentational

| Role  | Value                                                        |
|-------|--------------------------------------------------------------|
| Type  | `'use client'`                                               |
| Props | `water: Water`                                               |
|       | `association: Association \| null`                            |
| Store | None — fully prop-driven                                    |

**Rendered fields:**
- `water.name` — title
- `water.subtype` — badge (lac / rau)
- `water.judet` — county badge
- `water.limite` — sector description
- `water.dimensiune` — size (Ha or km)
- `association.telefon` — phone
- `association.adresa` — address
- `association.siteUrl` — link
- `water.referinta` — legal reference text

---

## 5. Data Flow Paths — End to End

### 5.1 Initial Load (Fetch → Store → Map)

```
Step  Who                  Action
────  ──────────────────── ──────────────────────────────────────────
  1   page.tsx (server)    Renders <MapShell /> inside <Suspense>
  2   MapShell mounts      useEffect fires
  3   MapShell              store.loadData() called
  4   loadData()            fetch('/data/associations.json')
  5   loadData()            fetch('/data/waters.json')
  6   loadData()            zustand setState:
                              associations = [...], waters = [...],
                              dataLoaded = true
  7   MapShell re-renders   dataLoaded===true → renders MapView
  8   MapView mounts        MapContainer creates Leaflet instance
  9   MapView               useFilteredWaters() returns all 426 waters
 10   WaterFeatureLayer     watersToFeatureCollection() → <GeoJSON>
 11   Leaflet               Draws 426 blue rectangles on OSM tiles
 12   ColorLegend           selectedAssociationSlug===null → "Vedere neutră"

    ┌─────────┐    fetch    ┌──────────────┐    renders    ┌─────────┐
    │ MapShell │ ─────────→ │ Zustand Store │ ────────────→ │ MapView │
    │  (mount) │            │ associations │               │         │
    └─────────┘            │ waters[]     │               └────┬────┘
                           │ dataLoaded   │                    │
                           └──────────────┘           ┌────────┴────────┐
                                                      │ WaterFeatureLayer│
                                                      │ (426 rectangles) │
                                                      └─────────────────┘
```

### 5.2 Association Selection → Map Recoloring

```
Step  Who                  Action
────  ──────────────────── ──────────────────────────────────────────
  1   User                 Types "Cluj" in AssociationSearch
  2   cmdk                 Filters 82 associations locally (fuzzy)
  3   User                 Clicks "AJVPS Cluj"
  4   AssociationSearch     store.selectAssociation('ajvps-cluj')
  5   Store                 selectedAssociationSlug = 'ajvps-cluj'
  6   MapView re-renders    coverageSlug === 'ajvps-cluj' (selector)
  7   WaterFeatureLayer     426 features re-styled:
                              - asociatieSlug === 'ajvps-cluj' → green
                              - all others → grey
  8   ColorLegend            selectedAssociationSlug !== null
                              → shows green+gray rows


  ┌──────────────────┐   selectAssociation()   ┌──────────────────┐
  │ AssociationSearch│ ──────────────────────→ │  Zustand Store    │
  │  "AJVPS Cluj"    │                         │  selectedAssoc =  │
  └──────────────────┘                         │  'ajvps-cluj'     │
                                               └────────┬─────────┘
                                                        │
                                          ┌─────────────┼─────────────┐
                                          ▼             ▼             ▼
                                   MapView        WaterFeature   ColorLegend
                                   re-renders     Layer restyles   updates
                                   coverageSlug   green/grey       legend
```

### 5.3 County Filter Toggle → Filtered Map

```
Step  Who                  Action
────  ──────────────────── ──────────────────────────────────────────
  1   User                 Taps "Cluj" chip in CountyFilter
  2   CountyFilter          props.onToggle('Cluj')
  3   FilterBar             store.toggleCounty('Cluj')
  4   Store                 countyFilter = ['Cluj']
  5   useFilteredWaters()   recomputes: filters waters by judet==='Cluj'
  6   MapView               filtered waters change → passes new array
  7   WaterFeatureLayer     <GeoJSON data={...}> sees new array
  8   Leaflet               Clears old features, draws only Cluj waters


  ┌──────────────┐  onToggle('Cluj')  ┌──────────────┐  recompute  ┌──────────────────┐
  │ CountyFilter │ ─────────────────→ │ FilterBar     │ ──────────→ │ useFilteredWaters│
  │  [Cluj] chip │                    │ toggleCounty  │             │  only judet=Cluj │
  └──────────────┘                    └──────────────┘             └────────┬─────────┘
                                                                           │
                                                                  ┌────────┴────────┐
                                                                  │ WaterFeatureLayer│
                                                                  │ (only Cluj)     │
                                                                  └─────────────────┘
```

### 5.4 Water Type Filter → Filtered Map

```
Step  Who                  Action
────  ──────────────────── ──────────────────────────────────────────
  1   User                 Taps "Lacuri" segment
  2   WaterTypeFilter       props.onChange('lac')
  3   FilterBar             store.setWaterTypeFilter('lac')
  4   Store                 waterTypeFilter = 'lac'
  5   useFilteredWaters()   recomputes: filters waters by subtype==='lac'
  6   MapView               passes new filtered array
  7   WaterFeatureLayer     <GeoJSON> redraws with only lakes
  8   Leaflet               Map shows only lake features

Note: If both filters are active (countyFilter=['Cluj'] AND waterTypeFilter='lac'),
the filtered array is the intersection: waters where judet==='Cluj' AND subtype==='lac'.
```

### 5.5 Map Click → Detail Sheet

```
Step  Who                  Action
────  ──────────────────── ──────────────────────────────────────────
  1   User                 Taps a water rectangle on the map
  2   Leaflet              'click' event on GeoJSON feature
  3   WaterFeatureLayer     onEachFeature handler fires
  4   WaterFeatureLayer     store.selectWater(feature.properties.slug)
  5   Store                 selectedWaterSlug = 'lacul-tarnita'
  6   WaterDetailSheet      selectedWaterSlug !== null → opens
                              ─ translates to translateY(0)
                              ─ backdrop appears
  7   WaterDetailSheet      Finds water from store.waters[]
  8   WaterDetailSheet      Finds association from store.associations[]
  9   WaterDetailCard        Renders water + association details


  ┌──────────┐   click    ┌──────────────────┐   selectWater()   ┌──────────────┐
  │   User   │ ─────────→ │ WaterFeatureLayer │ ────────────────→ │  Zustand      │
  │ taps map │            │ onEachFeature     │                   │  selectedWater│
  └──────────┘            └──────────────────┘                   │  = 'xxx'      │
                                                                 └──────┬───────┘
                                                                        │
                                                              ┌─────────┴─────────┐
                                                              │ WaterDetailSheet  │
                                                              │ opens (slides up) │
                                                              │ ┌───────────────┐ │
                                                              │ │ WaterDetailCard│ │
                                                              │ │ name, sector,  │ │
                                                              │ │ phone, address │ │
                                                              │ └───────────────┘ │
                                                              └───────────────────┘
```

### 5.6 Detail Sheet Dismissal

```
Step  Who                  Action
────  ──────────────────── ──────────────────────────────────────────
  1   User                 Taps backdrop / swipes down / presses ESC
  2   WaterDetailSheet      Detects dismiss intent
  3   WaterDetailSheet      store.selectWater(null)
  4   Store                 selectedWaterSlug = null
  5   WaterDetailSheet      CSS transition: translateY(100%)
  6   WaterDetailSheet      After 300ms: pointer-events: none, backdrop hidden
  7   MapView               Unchanged — map was always visible behind sheet
```

### 5.7 Combined Filter Cascade (County + Type + Association)

```
All three filters active simultaneously:

  store.countyFilter = ['Cluj', 'Bihor']  (two counties selected)
  store.waterTypeFilter = 'lac'           (lakes only)
  store.selectedAssociationSlug = 'ajvps-cluj'

  useFilteredWaters() returns:
    waters WHERE
      judet IN ('Cluj', 'Bihor')  ← countyFilter
      AND subtype = 'lac'          ← waterTypeFilter
      (no association filter — all lakes shown, colored by coverage)

  WaterFeatureLayer renders:
    - Lakes in Cluj/Bihor covered by AJVPS Cluj → GREEN
    - Lakes in Cluj/Bihor NOT covered by AJVPS Cluj → GREY

  ColorLegend shows: green/grey (association selected)
  CountyFilter shows: Cluj + Bihor chips highlighted
  WaterTypeFilter shows: "Lacuri" segment active
  AssociationSearch shows: "AJVPS Cluj" as selected
```

---

## 6. State Transitions Matrix

Every user action → store mutation → component re-render chain in one table.

| # | User Action | Store Mutation | Selectors Affected | Re-rendered Components |
|---|-------------|----------------|--------------------|------------------------|
| 1 | Page loads | `loadData()` → sets associations, waters, dataLoaded | `dataLoaded` | MapShell (shows MapView instead of skeleton) |
| 2 | Type in search | None (cmdk local) | None | AssociationSearch only (cmdk internal) |
| 3 | Pick association | `selectAssociation(slug)` | `selectedAssociationSlug` | MapView → WaterFeatureLayer (recolor), ColorLegend |
| 4 | Clear association | `selectAssociation(null)` | `selectedAssociationSlug` | WaterFeatureLayer (all blue), ColorLegend (neutral) |
| 5 | Toggle county | `toggleCounty(county)` | `countyFilter` | useFilteredWaters → MapView → WaterFeatureLayer (refilter) |
| 6 | Switch water type | `setWaterTypeFilter(type)` | `waterTypeFilter` | useFilteredWaters → MapView → WaterFeatureLayer (refilter) |
| 7 | Tap water on map | `selectWater(slug)` | `selectedWaterSlug` | WaterDetailSheet (opens) → WaterDetailCard |
| 8 | Dismiss sheet | `selectWater(null)` | `selectedWaterSlug` | WaterDetailSheet (closes) |
| 9 | Pick "Cluj" assoc + toggle county | Both mutations (independent) | Both selectors | WaterFeatureLayer (filter + recolor), ColorLegend |

**Key insight:** Filter changes (5, 6) and selection changes (3, 4) are **independent paths**. Changing a filter does NOT clear the association selection, and vice versa. The `useFilteredWaters` hook handles both simultaneously via its three dependencies.

---

## 7. Edge Cases & Empty States

### 7.1 Data Not Yet Loaded

| State | `dataLoaded === false` |
|-------|------------------------|
| MapShell | Shows `<MapSkeleton />` (pulse animation, "Se încarcă harta...") |
| AssociationSearch | Renders but `associations` is `[]` — cmdk shows "No results" |
| FilterBar | `useCounties()` returns `[]` — CountyFilter n/a |
| WaterDetailSheet | `selectedWaterSlug` is `null` — closed |

**Transition:** When `dataLoaded` flips to `true`, MapSkeleton unmounts and MapView mounts. AssociationSearch, FilterBar, and WaterFeatureLayer immediately populate from the now-filled arrays.

### 7.2 No Association Selected (Neutral View)

| Condition | `selectedAssociationSlug === null` |
|-----------|-------------------------------------|
| Map | All waters rendered in blue (#3b82f6) |
| ColorLegend | Shows single row: "■ Vedere neutră" |
| AssociationSearch | "Toate asociațiile" is highlighted / no item selected |
| WaterFeatureLayer | `coverageSlug === null` → `getFeatureStyle` returns blue for all |

### 7.3 Association Selected But No Waters Match Filter

Example: User selects "AJVPS Cluj" and filters to "Lacuri", but only "Râuri" match.

| Store state | `selectedAssociationSlug = 'ajvps-cluj'`, `waterTypeFilter = 'lac'` |
|-------------|----------------------------------------------------------------------|
| useFilteredWaters | Returns `[]` — no lakes for this association |
| WaterFeatureLayer | `<GeoJSON data={empty FC}>` — map shows no features |
| ColorLegend | Still shows green/grey (association IS selected) |
| Map tiles | Still visible (OSM tiles unaffected) |

**Why this is OK:** The map is still usable. The legend correctly explains the color scheme. The user can change filters or clear them to see features again.

### 7.4 Tap a Water Already Selected

| Action | WaterDetailSheet is open for 'lacul-tarnita' |
|--------|----------------------------------------------|
| User taps 'lacul-tarnita' again | `selectWater('lacul-tarnita')` — same slug |
| Store | No change (slug unchanged) |
| WaterDetailSheet | No re-render (same slug, no state change) |

**Zustand behavior:** If `selectWater(sameSlug)` is called, Zustand does a shallow equality check on the new state vs old state. Since `selectedWaterSlug` is the same string, no subscribers are notified and no re-renders occur. The sheet stays open.

### 7.5 Rapid Filter Toggles

| Scenario | User rapidly taps 3 counties in succession |
|----------|-------------------------------------------|
| Store | `toggleCounty('Cluj')` → `toggleCounty('Bihor')` → `toggleCounty('Brașov')` |
| useFilteredWaters | Recomputes 3 times (React batches state updates in event handlers, but with Zustand each call triggers a synchronous update) |
| WaterFeatureLayer | React batches the re-renders into one DOM update (automatic batching in React 18+) |

**Performance:** 426 waters filtered 3 times is trivial (~0.01ms each). Not a concern.

### 7.6 Association Selected, Then Water Type Changed

| Initial | `selectedAssociationSlug = 'ajvps-cluj'`, `waterTypeFilter = 'all'` |
|---------|----------------------------------------------------------------------|
| Action | User taps "Lacuri" → `setWaterTypeFilter('lac')` |
| Result | Map shows only lakes, but still colored green/grey by AJVPS coverage |

**Why association persists:** Selection and filtering are independent. This is intentional — the user can narrow to lakes while still seeing which association covers them.

### 7.7 Water Has No Association (`water.asociatie === null`)

| Scenario | A water in the dataset has no linked association |
|----------|-------------------------------------------------|
| `asociatieSlug` in feature properties | `null` |
| Color when association selected | Always grey (`f.asociatieSlug !== coverageSlug` → `null !== 'ajvps-cluj'` → false → grey) |
| Detail card | `association` prop is `null` → contact fields show "N/A" or are hidden |

### 7.8 Mobile vs Desktop — Same Store, Different Rendering

| State field | Mobile behavior | Desktop behavior |
|-------------|-----------------|------------------|
| `selectedWaterSlug` | Sheet slides up, 60vh max, backdrop overlay | Fixed right panel, 380px, no backdrop, map resizes |
| `countyFilter` | Horizontal scrollable chip row | Possibly wraps to 2 rows or dropdown |
| Everything else | Identical | Identical |

**Store is the same.** Only the `WaterDetailSheet` component reads a breakpoint (via Tailwind `md:` or `useMediaQuery`) and renders differently. The Zustand state is untouched.

---

## 8. State Flow Diagram (Complete)

```
                               ┌──────────────────────────────────┐
                               │         page.tsx (server)        │
                               │   <Suspense> <MapShell />        │
                               └──────────────┬───────────────────┘
                                              │ mounts
                               ┌──────────────▼───────────────────┐
                               │          MapShell.tsx             │
                               │  ┌─────────────────────────────┐ │
                               │  │  useEffect → loadData()     │ │
                               │  │  fetch assoc + waters JSON   │ │
                               │  └─────────────┬───────────────┘ │
                               │                │                 │
                               │  ┌─────────────▼───────────────┐ │
                               │  │       ZUSTAND STORE          │ │
                               │  │                              │ │
                               │  │  [DATA]        [SELECTION]   │ │
                               │  │  associations  selectedAssoc │ │
                               │  │  waters        selectedWater │ │
                               │  │  dataLoaded                  │ │
                               │  │                [FILTER]      │ │
                               │  │              countyFilter    │ │
                               │  │              waterTypeFilter │ │
                               │  └──┬───────────┬──────────┬───┘ │
                               │     │           │          │     │
                               │     │ reads     │ reads    │reads│
                               │     ▼           ▼          ▼     │
                               │  ┌──────┐  ┌────────┐ ┌───────┐ │
                               │  │Header│  │MapView │ │Sheet  │ │
                               │  │      │  │(dyn)   │ │       │ │
                               │  │ ┌──┐ │  │  ┌───┐ │ │ ┌───┐ │ │
                               │  │ │AS│ │  │  │WFL│ │ │ │WDC│ │ │
                               │  │ └──┘ │  │  │   │ │ │ └───┘ │ │
                               │  │      │  │  └───┘ │ │       │ │
                               │  └──────┘  └────────┘ └───────┘ │
                               └──────────────────────────────────┘

Legend:
  AS  = AssociationSearch  (reads associations[], writes selectAssociation)
  WFL = WaterFeatureLayer  (reads props: waters[], coverageSlug; writes selectWater)
  WDC = WaterDetailCard    (reads props: water, association; pure)
  Sheet = WaterDetailSheet (reads selectedWaterSlug; writes selectWater(null))

  FilterBar, CountyFilter, WaterTypeFilter, ColorLegend sit alongside
  MapView and read/write the same store selectors.
```

---

## 9. Verification Checklist

A reviewer should be able to trace every interaction end-to-end and confirm:

- [ ] **Initial load:** MapShell mounts → fetches both JSON files → store populated → MapView renders 426 features
- [ ] **Five store fields** (`associations`, `waters`, `selectedAssociationSlug`, `selectedWaterSlug`, `countyFilter`, `waterTypeFilter`) cover all cross-component state
- [ ] **No prop drilling across client/server boundary** — all client components read from Zustand or receive props from sibling client components
- [ ] **AssociationSearch → map coloring:** Selecting an association changes `selectedAssociationSlug` → WaterFeatureLayer recolors → ColorLegend updates — complete chain, no gaps
- [ ] **Map click → detail sheet:** Clicking a feature calls `selectWater(slug)` → WaterDetailSheet opens → WaterDetailCard renders — complete chain
- [ ] **Detail sheet dismiss:** Backdrop tap, swipe, ESC, close button all call `selectWater(null)` → sheet closes
- [ ] **Filter cascade:** Toggle county → `countyFilter` changes → `useFilteredWaters` recomputes → WaterFeatureLayer receives new array — complete chain
- [ ] **Combined filters:** County + water type filters intersect correctly; association selection is independent and persists across filter changes
- [ ] **Derived hooks do not mutate store** — `useFilteredWaters` and `useCounties` are read-only
- [ ] **Local state is truly local** — cmdk open/inputValue, sheet dragOffset/isDragging, mapInstance are never read by sibling components
- [ ] **Empty states handled:** data not loaded (skeleton), no association selected (neutral view), filter yields zero results (empty map but legend intact)
- [ ] **Mobile/desktop share the same store** — only WaterDetailSheet rendering differs
- [ ] **No circular dependencies** — store ← components → store is always: component reads store / component writes store, never component A reads component B's local state

---

## 10. References

- **Component tree:** `/home/stefan/undepescuim/docs/map-component-tree.md` (t_fced8bd1)
- **Component structure plan:** `/home/stefan/undepescuim/docs/component_structure_plan.md`
- **Architecture:** `/home/stefan/undepescuim/docs/ARCHITECTURE.md` (t_13c53320)
- **Data model:** `/home/stefan/undepescuim/data/raw/data_model_proposal.md` (t_b05125bc)

