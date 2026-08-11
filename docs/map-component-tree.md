# Leaflet Map Component Tree — UndePescuim.ro

**Date:** 2026-08-11  
**Author:** plan-maker (t_fced8bd1)  
**Parent:** t_532822fe (Orchestrator — Multi-step speculation)  
**Status:** Draft — awaiting reviewer confirmation  
**References:** ARCHITECTURE.md (t_13c53320), data_model_proposal.md (t_b05125bc)

---

## 0. Purpose

This document is a **pure design deliverable** — no implementation code. It defines the component hierarchy, responsibilities, file paths, and composition of the UndePescuim.ro map UI. A reviewer should be able to scan the tree, confirm component boundaries, and request adjustments before any code is written.

---

## 1. Component Tree (Full)

```
src/app/[locale]/page.tsx                    Server Component — data shell, <Suspense> boundary
│
├── src/components/layout/Header.tsx          'use client' — top bar
│   └── src/components/associations/AssociationSearch.tsx   'use client' — cmdk Command dropdown
│
└── src/components/map/MapShell.tsx           'use client' — THE client boundary
    │                                           Initializes Zustand store, fetches static JSON
    │
    ├── src/components/map/MapView.tsx         dynamic(ssr:false) — Leaflet MapContainer wrapper
    │   │
    │   ├── <TileLayer>                        OSM tile source (built-in react-leaflet)
    │   │
    │   ├── src/components/map/WaterFeatureLayer.tsx   dynamic(ssr:false) — <GeoJSON> layer
    │   │                                                Converts Water[] → FeatureCollection
    │   │                                                Color: green/grey/blue per coverage
    │   │
    │   ├── <ZoomControl>                     Built-in react-leaflet, positioned top-right
    │   │
    │   ├── src/components/map/FilterBar.tsx   Absolutely positioned overlay, top-left
    │   │   ├── src/components/map/CountyFilter.tsx       Multi-select chip/pill row
    │   │   └── src/components/map/WaterTypeFilter.tsx    Segmented: Toate / Lacuri / Râuri
    │   │
    │   └── src/components/map/ColorLegend.tsx            Overlay, bottom-right of map
    │
    └── src/components/waters/WaterDetailSheet.tsx        Bottom sheet (mobile) / right panel (desktop)
        └── src/components/waters/WaterDetailCard.tsx     Water info content
```

---

## 2. Where the Bottom Sheet Sits Relative to Map Controls

```
┌──────────────────────────────────────────────────────┐
│  Header (z-50)                                       │
│  [Logo] [AssociationSearch]              [RO | EN]    │
├──────────────┬───────────────────────────────────────┤
│ FilterBar    │                                       │
│ (z-1000)     │            MAP VIEWPORT               │
│ [Cluj][BH]   │                                       │
│ ○Toate ●Lac  │       ┌─ WaterFeatureLayer            │
│              │       │  (GeoJSON, z-400)             │
│              │       │                               │
│              │       │       ┌─ ZoomControl          │
│              │       │       │  (z-1000, top-right)  │
│              │       └───────┘                       │
│              │                                       │
│              │                    ColorLegend         │
│              │                    (z-1000, bottom-r)  │
│              │                    ■ Acoperit          │
│              │                    ■ Neacoperit        │
├──────────────┴───────────────────────────────────────┤
│              ↑ map controls ↑                        │
├──────────────────────────────────────────────────────┤
│  Backdrop (z-1100, semi-transparent)                 │
│  ┌──────────────────────────────────────────────────┐│
│  │  ═══  (drag handle)                              ││
│  │                                                  ││
│  │  WaterDetailSheet (z-1200)                       ││
│  │  └─ WaterDetailCard                              ││
│  │     Name, badges, sector, size, contact, ref     ││
│  │                                                  ││
│  └──────────────────────────────────────────────────┘│
│              ↑ bottom sheet ↑                        │
└──────────────────────────────────────────────────────┘
```

**Z-index stacking order (lowest → highest):**
1. `z-0`: Map tiles (TileLayer)
2. `z-400`: Water feature polygons (GeoJSON layer — allows tap/click)
3. `z-1000`: Map controls (FilterBar, ColorLegend, ZoomControl)
4. `z-1100`: Bottom sheet backdrop (semi-transparent overlay)
5. `z-1200`: Bottom sheet content (WaterDetailSheet)

The bottom sheet **overlays the map**, including map controls. When the sheet is open, the backdrop covers the map and controls, preventing interaction with them. Tapping the backdrop dismisses the sheet.

---

## 3. Component Responsibilities & File Paths

### 3.1 `page.tsx` — Server Component Shell

| Field | Value |
|-------|-------|
| **Path** | `src/app/[locale]/page.tsx` |
| **Type** | Server Component (no `'use client'`) |
| **Responsibility** | Thin shell: renders `<Suspense>` boundary, passes locale, renders `<MapShell />`. Does NOT import Leaflet or react-leaflet. |

**Composition:**
- Wraps `MapShell` in `<Suspense fallback={<MapSkeleton />}>`
- Optionally imports `{ associations, waters }` JSON at build time and passes as `initialData` prop to avoid fetch flash
- Reads `locale` from `params` (provided by `[locale]` route segment)

---

### 3.2 `Header.tsx` — Top Bar

| Field | Value |
|-------|-------|
| **Path** | `src/components/layout/Header.tsx` |
| **Type** | `'use client'` |
| **Responsibility** | Fixed top bar (z-50). Logo + site name left. AssociationSearch center. LanguageSwitcher right. On mobile, collapses search into an icon-triggered overlay. |

**Props:** None (reads nothing from store; contains AssociationSearch which reads store).

---

### 3.3 `AssociationSearch.tsx` — Searchable Association Selector

| Field | Value |
|-------|-------|
| **Path** | `src/components/associations/AssociationSearch.tsx` |
| **Type** | `'use client'` |
| **Responsibility** | shadcn/ui `<Command>` component (cmdk). Client-side fuzzy search over 82 association names. On select → `store.selectAssociation(slug)`. "Toate asociațiile" option → `store.selectAssociation(null)` clears selection. |

**Data flow:**
- Reads `store.associations` (82 items)
- cmdk handles filtering natively (no fuse.js needed for 82 items)
- Displays water count badge (`assoc.ape`) next to each row
- Output: calls `store.selectAssociation(slug | null)`

---

### 3.4 `MapShell.tsx` — The Client Boundary

| Field | Value |
|-------|-------|
| **Path** | `src/components/map/MapShell.tsx` |
| **Type** | `'use client'` |
| **Responsibility** | The single `'use client'` boundary. Initializes the Zustand store on mount (fetches `associations.json` + `waters.json`). Dynamic-imports MapView with `ssr: false`. Renders the map + all overlays + bottom sheet inside this island. |

**Why this exists:** Next.js App Router requires a clear client/server boundary. Everything below MapShell runs in the browser. Everything above (page.tsx) runs on the server at build time.

**SSR pattern:**
```typescript
const MapView = dynamic(
  () => import('@/components/map/MapView').then(m => m.MapView),
  { ssr: false, loading: () => <MapSkeleton /> }
);
```

---

### 3.5 `MapView.tsx` — Leaflet MapContainer Wrapper

| Field | Value |
|-------|-------|
| **Path** | `src/components/map/MapView.tsx` |
| **Type** | `'use client'` — loaded via `dynamic(ssr: false)` |
| **Responsibility** | Wraps react-leaflet `<MapContainer>`. Sets Romania center `[45.95, 24.95]`, zoom 7. Provides `<TileLayer>` (OSM). Hosts WaterFeatureLayer as a child. Renders FilterBar, ColorLegend, and ZoomControl as overlays inside the map container. |

**Key decisions:**
- Uses `className="h-[100dvh] w-full"` for full-viewport map
- `zoomControl={false}` on MapContainer → adds `<ZoomControl position="topright" />` separately for z-index control
- Imports `leaflet/dist/leaflet.css` inline (bundled into client chunk)
- Named export (`export function MapView`) so `dynamic()` can target it

---

### 3.6 `WaterFeatureLayer.tsx` — GeoJSON Layer Renderer

| Field | Value |
|-------|-------|
| **Path** | `src/components/map/WaterFeatureLayer.tsx` |
| **Type** | `'use client'` — loaded via `dynamic(ssr: false)` |
| **Responsibility** | Converts `Water[]` → `GeoJSON.FeatureCollection` (via `watersToFeatureCollection()`). Renders a single react-leaflet `<GeoJSON>` component. Colors features green/grey/blue based on coverage state. Attaches click → `store.selectWater(slug)`. |

**Props:**

| Prop | Type | Source |
|------|------|--------|
| `waters` | `Water[]` | `useFilteredWaters()` in MapView |
| `coverageSlug` | `string \| null` | `store.selectedAssociationSlug` |

**Coloring logic (delegated to `src/utils/colors.ts`):**

| State | Color | Fill | Weight |
|-------|-------|------|--------|
| No association selected | `#3b82f6` (blue) | 0.2 | 2 |
| Water is covered by selected assoc | `#16a34a` (green) | 0.3 | 2 |
| Water is NOT covered | `#9ca3af` (grey) | 0.15 | 1 |

**Geometry source:** MVP uses `water.bbox` to draw rectangles. Future: when real polygon/polyline GeoJSON is available, `waterToGeoJSON()` checks `water.geojson` first, falls back to bbox. Zero component changes needed.

---

### 3.7 `FilterBar.tsx` — Filter Overlay Container

| Field | Value |
|-------|-------|
| **Path** | `src/components/map/FilterBar.tsx` |
| **Type** | `'use client'` |
| **Responsibility** | Absolutely positioned container (z-1000) hosting CountyFilter + WaterTypeFilter. On mobile (<768px): horizontal scrollable row at top of map. On desktop (>=768px): top-left panel. |

**Props:** None — reads county list from `useCounties()` hook, passes to children.

---

### 3.8 `CountyFilter.tsx` — Multi-Select Chip List

| Field | Value |
|-------|-------|
| **Path** | `src/components/map/CountyFilter.tsx` |
| **Type** | `'use client'` |
| **Responsibility** | Horizontal scrollable chip/pill row. Counties derived from water data (not hardcoded). Tapping a chip toggles it. "Toate județele" shown when nothing selected. |

**Props:**

| Prop | Type | Source |
|------|------|--------|
| `counties` | `string[]` | `useCounties()` hook |
| `selected` | `string[]` | `store.countyFilter` |
| `onToggle` | `(county: string) => void` | calls `store.toggleCounty(county)` |

---

### 3.9 `WaterTypeFilter.tsx` — Segmented Control

| Field | Value |
|-------|-------|
| **Path** | `src/components/map/WaterTypeFilter.tsx` |
| **Type** | `'use client'` |
| **Responsibility** | Three-segment pill control: Toate (All) / Lacuri (Lakes) / Râuri (Rivers). |

**Props:**

| Prop | Type | Source |
|------|------|--------|
| `selected` | `'all' \| 'lac' \| 'rau'` | `store.waterTypeFilter` |
| `onChange` | `(type) => void` | calls `store.setWaterTypeFilter(type)` |

---

### 3.10 `ColorLegend.tsx` — Coverage Legend

| Field | Value |
|-------|-------|
| **Path** | `src/components/map/ColorLegend.tsx` |
| **Type** | `'use client'` |
| **Responsibility** | Absolutely positioned overlay, bottom-right of map (z-1000). Shows 2-3 colored rows: green (covered), grey (not covered). Blue (neutral view) only when no association selected. Semi-transparent background. |

**Props:**

| Prop | Type | Source |
|------|------|--------|
| `coverageSlug` | `string \| null` | `store.selectedAssociationSlug` |

**Display logic:**

| `coverageSlug` | Rows shown |
|----------------|-----------|
| `null` | ■ Vedere neutră (blue) |
| `'ajvps-cluj'` | ■ Acoperit (green), ■ Neacoperit (grey) |

---

### 3.11 `WaterDetailSheet.tsx` — Bottom Sheet / Side Panel

| Field | Value |
|-------|-------|
| **Path** | `src/components/waters/WaterDetailSheet.tsx` |
| **Type** | `'use client'` |
| **Responsibility** | **Mobile (<768px):** slides up from bottom, max-height 60vh, drag handle, semi-transparent backdrop. **Desktop (>=768px):** fixed right panel, 380px wide, map resizes to accommodate. Contains WaterDetailCard. Dismisses on backdrop tap, drag-down, ESC, or close button. |

**Props:** None — reads `store.selectedWaterSlug`. When `null`, sheet is hidden (translateY 100%, pointer-events none).

**Implementation options:**
- **Option A:** shadcn/ui `<Sheet>` component — handles animation, backdrop, drag. Recommended.
- **Option B:** Custom div with Tailwind transitions — lighter but more work for a11y.

**States:**

| `selectedWaterSlug` | Sheet state |
|---------------------|-------------|
| `null` | Hidden (offscreen) |
| `'iwrd2dxy'` | Visible, showing water details |

---

### 3.12 `WaterDetailCard.tsx` — Detail Content

| Field | Value |
|-------|-------|
| **Path** | `src/components/waters/WaterDetailCard.tsx` |
| **Type** | `'use client'` |
| **Responsibility** | Pure presentational card. Renders water name, subtype badge, county badge, sector (limite), size (dimensiune), association contact (telefon, adresa, siteUrl), legal reference (referinta). |

**Props:**

| Prop | Type | Source |
|------|------|--------|
| `water` | `Water` | WaterDetailSheet looks up from store |
| `association` | `Association \| null` | derived from water's `asociatie` |

**Layout:**
```
┌──────────────────────────────────────────────┐
│  Lacul Tarnița                    [lac]      │
│  Județul Cluj                                │
│                                              │
│  Sector: zona de acumulare                   │
│  Dimensiune: 240 Ha                          │
│  ─────────────────────────                   │
│  Asociația: D.S. Cluj                        │
│  📞 0264 420 908                             │
│  📍 Strada Bartók Béla, Nr. 27              │
│  🌐 http://cluj.rosilva.ro/                  │
│  ─────────────────────────                   │
│  Referință: Lista habitatelor...             │
│                                              │
│  [Raportează o problemă]                     │
│  [× Închide]                                 │
└──────────────────────────────────────────────┘
```

---

## 4. Supporting Files (Non-Component)

These are NOT components but are required by the component tree:

### 4.1 Zustand Store

| File | Responsibility |
|------|---------------|
| `src/stores/map-store.ts` | Central state: associations, waters, selectedAssociationSlug, selectedWaterSlug, countyFilter, waterTypeFilter. Actions: loadData, selectAssociation, selectWater, toggleCounty, setWaterTypeFilter. |

### 4.2 Derived Hooks

| File | Responsibility |
|------|---------------|
| `src/hooks/use-filtered-waters.ts` | Memoized: filters `store.waters` by `countyFilter[]` + `waterTypeFilter`. Returns `Water[]`. |
| `src/hooks/use-counties.ts` | Memoized: deduplicates `store.waters.map(w => w.judet)`, sorts alphabetically. Returns `string[]`. |

### 4.3 Utility Functions

| File | Responsibility |
|------|---------------|
| `src/utils/geo.ts` | `waterToGeoJSON(water)`: bbox → GeoJSON Feature. `watersToFeatureCollection(waters[])`: → FeatureCollection. |
| `src/utils/colors.ts` | `getFeatureStyle(asociatieSlug, coverageSlug)`: returns Leaflet PathOptions with correct color/fill/opacity. |

### 4.4 Static Data

| File | Content |
|------|---------|
| `public/data/associations.json` | 82 associations (pre-extracted from arebaltapeste.ro) |
| `public/data/waters.json` | 426 waters with bbox, association refs, metadata |

---

## 5. Data Flow Summary

```
User Action                  Store Mutation              Components React
───────────────────────────────────────────────────────────────────────────────
Types in AssociationSearch   (cmdk internal filter)     Dropdown list updates
Selects association          selectAssociation(slug)    WaterFeatureLayer recolors
                                                        ColorLegend updates
Toggles county chip          toggleCounty(county)       useFilteredWaters recomputes
                                                        WaterFeatureLayer redraws
Selects water type           setWaterTypeFilter(type)   useFilteredWaters recomputes
                                                        WaterFeatureLayer redraws
Taps a water on map          selectWater(slug)          WaterDetailSheet slides up
                                                        WaterDetailCard renders
Closes detail sheet          selectWater(null)          WaterDetailSheet slides down
```

All cross-component communication goes through the Zustand store. No prop drilling across the client/server boundary.

---

## 6. SSR / Dynamic Import Map

Every file that touches `leaflet` or `react-leaflet` MUST be loaded client-side only:

| File | Loading Pattern |
|------|----------------|
| `MapView.tsx` | `dynamic(() => import(...), { ssr: false })` |
| `WaterFeatureLayer.tsx` | `dynamic(() => import(...), { ssr: false })` |

**Why:** react-leaflet v5 is ESM-only. It accesses `window` during module evaluation. SSR would crash with "window is not defined". Next.js `transpilePackages: ["react-leaflet"]` is already in `next.config.ts`.

Components that DON'T import Leaflet (`FilterBar`, `CountyFilter`, `WaterTypeFilter`, `ColorLegend`, `WaterDetailSheet`, `WaterDetailCard`, `AssociationSearch`) do NOT need `dynamic()` — they are regular `'use client'` components.

---

## 7. Responsive Behavior Summary

| Component | Mobile (<768px) | Desktop (>=768px) |
|-----------|-----------------|-------------------|
| Header | Compact, search icon → fullscreen overlay | Full search bar inline |
| FilterBar | Horizontal scrollable chip row below header | Top-left overlay panel on map |
| WaterDetailSheet | Bottom sheet, slides up, 60vh max, drag handle | Fixed right panel, 380px wide |
| ColorLegend | Bottom-right of map, smaller font | Bottom-right of map |
| Map viewport | Full `100dvh` height | Full height, minus panel width when open |

---

## 8. Verification Checklist

A reviewer should be able to confirm:

- [ ] Component tree is a single tree from `page.tsx` down — no orphan components
- [ ] Every component has a clear responsibility (single concern)
- [ ] File paths follow the `src/components/<domain>/` convention
- [ ] Bottom sheet overlays the map AND map controls (z-1200 > z-1000)
- [ ] Mobile-first: bottom sheet on mobile, side panel on desktop
- [ ] `MapShell` is the only `'use client'` boundary for the map island
- [ ] All Leaflet-importing components use `dynamic(ssr: false)`
- [ ] Cross-component communication is via Zustand store, not prop drilling across client/server
- [ ] Filtering is derived (useFilteredWaters, useCounties hooks) — store holds raw data only
- [ ] MVP uses `water.bbox` for geometry; can swap to real GeoJSON without component changes
