# Component Structure Plan: UndePescuim.ro Map UI (v3 — CONSOLIDATED)

**Date:** 2026-08-11
**Author:** default (root task t_532822fe) — consolidating t_fced8bd1 + t_a11e1a6c + t_ae385b3c
**Status:** Ready for review (supersedes v2)
**Scope:** Pure design deliverable. No implementation, no production code.

## 0. Purpose

This is the single canonical plan for the core map UI. It consolidates the three
approved specialist specs into one reviewable document and resolves the few
cross-doc inconsistencies between them:

| Spec (normative reference) | Author task | Covers |
|---|---|---|
| `docs/map-component-tree.md` | t_fced8bd1 | Component tree, responsibilities, z-index, SSR map |
| `docs/map-state-data-flow.md` | t_a11e1a6c | Zustand store contract, props contracts, 7 data-flow paths, edge cases |
| `docs/mobile-layout-spec.md` | t_ae385b3c | 3 breakpoints, bottom-sheet states/snap points, interaction state machine |
| `data/data_requirements_note.md` | t_972abeae | Field mapping for every UI element; geometry/permit-note gaps |

Where this document and a spec disagree, **this document wins**. The specs remain
the deep-dive references for the executioner (t_8ba7e9ea).

---

## 1. Decision Log (all accepted decisions)

### 1.1 Confirmed by user
| Decision | Choice |
|---|---|
| Framework | Next.js 16.3 App Router + React 19 (already scaffolded) |
| Map | Leaflet + react-leaflet v5 (installed) |
| Search UI | shadcn/ui Command (cmdk, installed); fuse.js held as fallback only |
| MVP geometry | bbox rectangles via `waterToGeoJSON()`; true GeoJSON polygons/polylines later, zero component changes |
| Detail UI | Mobile: bottom sheet. Desktop/tablet: right side panel. |
| State | Zustand (to install) |

### 1.2 Resolutions of cross-doc conflicts (v3 rulings)
| # | Conflict | Ruling |
|---|---|---|
| R1 | Component count: v2 said 11, tree doc says 12 | **12 components** (page.tsx shell + 11 client components). See tree in §3. |
| R2 | Breakpoints: tree/state docs used 2 tiers (<768 / ≥768); mobile-layout spec uses 3 | **3 tiers**: mobile <768, tablet 768–1023, desktop ≥1024 (Tailwind `md`/`lg`). Sheet = bottom sheet <768, side panel ≥768 (320px tablet / 380px desktop). |
| R3 | Association change vs open sheet: mobile-layout §4.1 said sheet may dismiss; §7.3 said it stays open | **Association selection never filters or dismisses.** It only recolors. Sheet stays open; water simply turns grey if not covered. §4.1's line is superseded by §7.3. |
| R4 | Sheet dismiss: state doc listed "backdrop tap → dismiss"; mobile-layout restricts it | **Mobile-layout is authoritative:** backdrop tap is a no-op at Peek; at Expanded it collapses to Peek. Dismiss only via drag-past-threshold from Collapsed, × button, or ESC. |
| R5 | fuse.js: v2 listed `pnpm add zustand fuse.js`; tree doc says cmdk native | **Install zustand only.** fuse.js deferred until cmdk filtering proves inadequate (risk Rk3 fallback). |
| R6 | Sheet height: tree doc said 60vh max; mobile-layout says Expanded 65vh | **65vh** via vaul snapPoints `[0.1, 0.35, 0.65]` (Collapsed/Peek/Expanded). |
| R7 | Sheet library: tree doc offered shadcn Sheet; mobile-layout mandates vaul | **vaul directly** (powers shadcn Sheet; supports snapPoints natively; already in node_modules). |
| R8 | Store dir: ARCHITECTURE says `src/store/`; all 3 specs say `src/stores/` | **`src/stores/map-store.ts`** (specs win; deviation from ARCHITECTURE noted for executioner). |
| R9 | Filter-out behavior: state doc silent; mobile-layout auto-dismisses | **Adopt auto-dismiss:** if the selected water is filtered OUT by county/type filter, `selectWater(null)` fires automatically + optional toast. |
| R10 | Association select clears water? ARCHITECTURE said `selectAssociation + clearSelectedWater`; state doc made them independent | **Independent.** Selection and filters never clear each other (state doc §6 key insight). |
| R11 | Data load: tree doc offered build-time JSON import; state doc says fetch on mount | **Fetch on mount** via `loadData()` in MapShell. Build-time import = optional optimization only. |
| R12 | Search overlay z-index missing from tree doc | **z-2000** (mobile fullscreen overlay, above sheet z-1200). |

### 1.3 Data-model gaps carried from t_972abeae (not UI blockers)
- **No polyline/polygon geometry** → MVP draws bbox rectangles (§1.1). Geocoding pipeline (t_04163c8f chain) will supply real geometry later; `waterToGeoJSON()` checks `water.geojson` first, falls back to `water.bbox`.
- **No dedicated permit-note field** → the detail card's "permit note" renders `water.referinta` (legal reference) for MVP. A `permit_note` field is a data-model follow-up, not a UI change.

## 2. Tech Stack & Dependencies

### 2.1 Installed (verified in package.json)
`next ^16.3`, `react ^19`, `tailwindcss ^4` (CSS-based config), `shadcn/ui ^4.16`
primitives, `cmdk ^1.1.1`, `react-leaflet ^5.0.0` (+ `@types/leaflet`),
`lucide-react`. `next.config.ts` already has `transpilePackages: ["react-leaflet"]`.

### 2.2 To install (exactly one new dep)
```
pnpm add zustand
```
fuse.js: NOT installed in this milestone (R5).

### 2.3 Scaffold reality check (what does NOT exist yet)
- `src/app/[locale]/` routing — current app is flat `src/app/{layout,page}.tsx`.
  ARCHITECTURE.md's `[locale]` + next-intl plan is aspirational. **This milestone
  builds the map UI in the current structure**; i18n extraction is a follow-up
  (see Rk5). `page.tsx` gets replaced with the MapShell wrapper.
- No `public/data/` JSON yet — executioner extracts `associations.json` +
  `waters.json` from `data/raw/arebaltapeste_probe/snapshot_*.json`.
- Report/verification components (ReportButton, ReportForm) are OUT of scope for
  this milestone; the card's "Raportează o problemă" button renders as a
  placeholder with no behavior.

---

## 3. Canonical Component Tree (12 components)

```
src/app/[locale]/page.tsx                    Server Component — <Suspense> shell, passes locale
│
├── src/components/layout/Header.tsx         'use client' — top bar (z-50)
│   └── src/components/associations/AssociationSearch.tsx   'use client' — cmdk Command
│                                                           (mobile: icon→fullscreen overlay z-2000)
│
└── src/components/map/MapShell.tsx          'use client' — THE client boundary
    │                                          loads data (loadData), dynamic-imports MapView
    │
    ├── src/components/map/MapView.tsx       dynamic(ssr:false) — <MapContainer> wrapper
    │   ├── <TileLayer>                      OSM tiles (z-0)
    │   ├── src/components/map/WaterFeatureLayer.tsx   dynamic(ssr:false) — <GeoJSON> (z-400)
    │   ├── <ZoomControl>                    react-leaflet built-in, top-right (z-1000)
    │   ├── src/components/map/FilterBar.tsx              overlay top-left (z-1000)
    │   │   ├── src/components/map/CountyFilter.tsx       multi-select chips
    │   │   └── src/components/map/WaterTypeFilter.tsx    segmented Toate/Lacuri/Râuri
    │   └── src/components/map/ColorLegend.tsx            overlay bottom-right (z-1000)
    │
    └── src/components/waters/WaterDetailSheet.tsx        bottom sheet (mobile) / right panel
        └── src/components/waters/WaterDetailCard.tsx     pure presentational content
```

**Z-index stacking (low→high):** z-0 tiles → z-400 features → z-1000 map controls
(FilterBar, ColorLegend, ZoomControl) → z-1100 sheet backdrop → z-1200 sheet →
z-2000 mobile search overlay. Sheet overlays ALL map controls when open.

### 3.1 Component responsibilities (one line each — full contracts in spec refs)
| Component | Responsibility |
|---|---|
| `page.tsx` | Server shell: `<Suspense fallback={<MapSkeleton/>}>` → `<MapShell/>`. No Leaflet imports. |
| `Header` | Fixed top bar: logo left, AssociationSearch center, RO/EN switcher right. No store reads itself. |
| `AssociationSearch` | cmdk fuzzy search over 82 associations; badge with water count; select → `selectAssociation(slug)`, "Toate asociațiile" → `null`. |
| `MapShell` | Single `'use client'` island. `useEffect → loadData()` (fetch both JSONs). Renders MapView (dynamic), FilterBar, ColorLegend, WaterDetailSheet. Reads `dataLoaded` for skeleton. |
| `MapView` | `dynamic(ssr:false)`. `<MapContainer center={[45.95,24.95]} zoom={7} zoomControl={false}>`; OSM TileLayer; hosts WaterFeatureLayer + overlays. Holds `mapRef` for flyTo. |
| `WaterFeatureLayer` | Pure prop-driven. `waters[] + coverageSlug` → `watersToFeatureCollection()` → single `<GeoJSON>`; style fn colors green/grey/blue; click → `selectWater(slug)`. |
| `FilterBar` | Overlay container (mobile: fixed 44px bar; ≥768: left panel). Reads `useCounties()`, `countyFilter`, `waterTypeFilter`; wires children callbacks. |
| `CountyFilter` | Controlled: `counties[]`, `selected[]`, `onToggle`. Chips derived from data, never hardcoded. |
| `WaterTypeFilter` | Controlled: `selected: 'all'|'lac'|'rau'`, `onChange`. Segmented control. |
| `ColorLegend` | Reads `selectedAssociationSlug`. null → "Vedere neutră" (blue) only; selected → green + grey rows. Mobile: collapsible dots, auto-collapse 5s. |
| `WaterDetailSheet` | Reads `selectedWaterSlug` + waters + associations. Mobile: vaul bottom sheet, snapPoints `[0.1,0.35,0.65]`. ≥768: side panel (320/380px). Dismiss → `selectWater(null)`. |
| `WaterDetailCard` | Pure. Props `water: Water`, `association: Association \| null`. Name, subtype + county badges, sector (limite), size (dimensiune), contact (telefon/adresa/siteUrl), referință (permit note), report button placeholder. |

## 4. File Paths Manifest (complete)

### 4.1 Components (12)
| Path | Component |
|---|---|
| `src/app/[locale]/page.tsx` | page shell (server) |
| `src/components/layout/Header.tsx` | Header |
| `src/components/associations/AssociationSearch.tsx` | AssociationSearch |
| `src/components/map/MapShell.tsx` | MapShell |
| `src/components/map/MapView.tsx` | MapView |
| `src/components/map/WaterFeatureLayer.tsx` | WaterFeatureLayer |
| `src/components/map/FilterBar.tsx` | FilterBar |
| `src/components/map/CountyFilter.tsx` | CountyFilter |
| `src/components/map/WaterTypeFilter.tsx` | WaterTypeFilter |
| `src/components/map/ColorLegend.tsx` | ColorLegend |
| `src/components/waters/WaterDetailSheet.tsx` | WaterDetailSheet |
| `src/components/waters/WaterDetailCard.tsx` | WaterDetailCard |

### 4.2 Supporting modules
| Path | Responsibility |
|---|---|
| `src/stores/map-store.ts` | Zustand store (state + actions) |
| `src/hooks/use-filtered-waters.ts` | Derived: filters waters by county[] + type |
| `src/hooks/use-counties.ts` | Derived: sorted dedup county list from waters |
| `src/utils/geo.ts` | `waterToGeoJSON()`, `watersToFeatureCollection()` (bbox → FeatureCollection) |
| `src/utils/colors.ts` | `getFeatureStyle(asociatieSlug, coverageSlug)` → Leaflet PathOptions |
| `src/types/data.ts` | All TS interfaces (see §6) |
| `public/data/associations.json` | 82 associations (from `data/raw/arebaltapeste_probe/snapshot_asociatii.json`) |
| `public/data/waters.json` | 426 waters (from `data/raw/arebaltapeste_probe/snapshot_waters.json`) |

---

## 5. Key Props & State (summary — full contracts in `map-state-data-flow.md` §4)

### 5.1 Zustand store (`src/stores/map-store.ts`) — single source of truth
| Field | Type | Initial |
|---|---|---|
| `associations` | `Association[]` | `[]` |
| `waters` | `Water[]` | `[]` |
| `dataLoaded` | `boolean` | `false` |
| `selectedAssociationSlug` | `string \| null` | `null` |
| `selectedWaterSlug` | `string \| null` | `null` |
| `countyFilter` | `string[]` | `[]` (empty = all) |
| `waterTypeFilter` | `'all' \| 'lac' \| 'rau'` | `'all'` |

Actions: `loadData()` · `selectAssociation(slug|null)` · `selectWater(slug|null)` ·
`toggleCounty(county)` · `setWaterTypeFilter(type)`.
Rule: **selection and filters are independent** (R10) — no action clears another's state.

### 5.2 Derived hooks (read-only, never mutate store)
| Hook | Input → Output |
|---|---|
| `useFilteredWaters()` | `waters[] + countyFilter + waterTypeFilter` → filtered `Water[]` (AND of filters) |
| `useCounties()` | `waters[]` → sorted unique `string[]` (independent of filters — chips always complete) |

### 5.3 Local state (only these 3 components)
| Component | Local state | Why local |
|---|---|---|
| AssociationSearch | `open`, `inputValue` (cmdk-managed) | dropdown visibility/typing is internal |
| WaterDetailSheet | `dragOffset`, `isDragging` | swipe gesture is an animation detail |
| MapView | `mapRef: L.Map \| null` | Leaflet instance for `flyTo()` |

### 5.4 Store readers/writers per component
| Component | Reads | Writes |
|---|---|---|
| AssociationSearch | `associations` | `selectAssociation` |
| MapShell | `dataLoaded` | `loadData` (on mount) |
| MapView | `selectedAssociationSlug`, `useFilteredWaters()` | — (passes props down) |
| WaterFeatureLayer | — (props only) | `selectWater` (on click) |
| FilterBar | `useCounties()`, `countyFilter`, `waterTypeFilter` | `toggleCounty`, `setWaterTypeFilter` (via child callbacks) |
| CountyFilter / WaterTypeFilter | — (props only, fully controlled) | — |
| ColorLegend | `selectedAssociationSlug` | — |
| WaterDetailSheet | `selectedWaterSlug`, `waters`, `associations` | `selectWater(null)` (dismiss) |
| WaterDetailCard | — (props only, pure) | — |

### 5.5 Coloring contract (`getFeatureStyle`)
| Condition | Color | Fill | Weight |
|---|---|---|---|
| `coverageSlug === null` (neutral) | `#3b82f6` blue | 0.2 | 2 |
| feature `asociatieSlug === coverageSlug` | `#16a34a` green | 0.3 | 2 |
| otherwise (not covered / no association) | `#9ca3af` grey | 0.15 | 1 |

## 6. Data Flow (summary — full paths in `map-state-data-flow.md` §5)

### 6.1 Initial load
`MapShell mount → loadData() → fetch /data/associations.json + /data/waters.json
→ setState → dataLoaded=true → MapView mounts → useFilteredWaters() (all 426) →
watersToFeatureCollection() → <GeoJSON> draws blue rectangles → legend shows
"Vedere neutră"`.

### 6.2 Interaction paths (user action → store mutation → components react)
| User action | Store mutation | Components that react |
|---|---|---|
| Select association | `selectAssociation(slug)` | WaterFeatureLayer recolors (green/grey), ColorLegend rows |
| Clear association | `selectAssociation(null)` | All features blue, legend neutral |
| Toggle county chip | `toggleCounty(county)` | useFilteredWaters → WaterFeatureLayer redraw |
| Switch type segment | `setWaterTypeFilter(type)` | useFilteredWaters → WaterFeatureLayer redraw |
| Tap water on map | `selectWater(slug)` | Sheet slides up (mobile) / panel shows (desktop), card renders |
| Dismiss sheet | `selectWater(null)` | Sheet hides |
| Filter removes selected water | `selectWater(null)` auto (R9) | Sheet hides + optional toast |

### 6.3 Interaction rules (from mobile-layout-spec §7 state machine)
- Tapping empty map area = **no-op** (never dismisses sheet — panning wins).
- Filter change: selected water still visible → sheet stays open; filtered OUT → auto-dismiss (R9).
- Association change: sheet **always stays open**; water just recolors (R3).
- Water has `asociatie: null` → card shows "Fără asociație", contact fields hidden, report button stays.
- No phone/address/site → fields simply don't render (no "—"/"N/A" placeholders).
- Rapid taps: last-tapped water wins, debounce store updates ~50ms.

---

## 7. Responsive Layout (summary — full spec in `mobile-layout-spec.md`)

### 7.1 Three tiers
| Tier | Range | Detail UI | Filters | Search | Map |
|---|---|---|---|---|---|
| Mobile | <768px | Bottom sheet (vaul, snap `[0.1,0.35,0.65]` vh) | Fixed 44px bar: scrollable chips + segmented control | Icon → fullscreen overlay (z-2000) | `calc(100dvh - 48px - 44px)` |
| Tablet | 768–1023px | Collapsible right panel 320px (48px tab when collapsed) | Left overlay panel, wrapping chips | Inline dropdown in header | Grid `1fr 320px` |
| Desktop | ≥1024px | Persistent right panel 380px | Left overlay panel | Inline dropdown (max 480px) | Grid `1fr 380px` |

Use `height: 100lvh; height: 100dvh` for mobile viewport; safe-area insets
(`env(safe-area-inset-bottom/top)`); `touch-action: manipulation` on interactive
elements; `user-select: none` on chips/handle.

### 7.2 Bottom sheet states (mobile)
| State | Height | Backdrop | Map interaction |
|---|---|---|---|
| Hidden | 0 | none | Full |
| Collapsed | ~10vh | none (0) | Full (pan OK) |
| Peek | ~35vh | 0.20 | Pan + tap features OK (switch water = content crossfade) |
| Expanded | ~65vh | 0.50 | Blocked; backdrop tap → collapse to Peek |

Dismiss only: drag-past-threshold from Collapsed, × button, ESC (R4). Physics:
spring stiffness 300 / damping 30, settle 250ms, velocity flings >0.5px/ms jump
snap points. Legend: mobile collapsible dots (auto-collapse 5s); when sheet at
Peek, legend moves up `calc(35vh + 8px)`; hidden at Expanded; ≥768 always full labels.

## 8. TypeScript Interfaces (`src/types/data.ts`)

```typescript
/** WGS84 longitude, latitude pair — GeoJSON convention ([lon, lat]) */
export type LngLat = [number, number];

/** Bounding box: [minLon, minLat, maxLon, maxLat] */
export type BBox = [number, number, number, number];

/** Water type discriminator */
export type WaterSubtype = 'lac' | 'rau';

/** Water type filter state */
export type WaterTypeFilter = 'all' | WaterSubtype;

/** County name as stored in water.judet (e.g. "Cluj", "Bihor") */
export type County = string;

/** A fishing association that manages waters */
export interface Association {
  slug: string;
  name: string;
  name_long: string;
  ape: number;            // water count
  adresa?: string;
  telefon?: string;
  siteUrl?: string;
  bbox: BBox;
  id: string;
}

/** A public fishing water (lake or river section) */
export interface Water {
  slug: string;
  name: string;
  judet: County;
  type: 'ape';            // always "ape" for public waters
  subtype: WaterSubtype;
  limite: string;         // sector boundary description
  dimensiune: string;     // size with unit ("240 Ha" | "35 km")
  pescuit_interzis: boolean;
  referinta: string;      // legal reference — MVP stand-in for "permit note"
  coordinates: LngLat;
  driving: LngLat;
  bbox: BBox;
  asociatie: {
    name: string;
    slug: string;
    telefon?: string;
    adresa?: string;
    siteUrl?: string;
  } | null;
  // FUTURE: true polygon/polyline geometry (geocoding pipeline t_04163c8f)
  // geojson?: GeoJSON.Geometry;
}

/** GeoJSON feature properties for Leaflet rendering */
export interface WaterFeatureProperties {
  slug: string;
  name: string;
  subtype: WaterSubtype;
  judet: County;
  asociatieSlug: string | null;
}

export type WaterFeature = GeoJSON.Feature<
  GeoJSON.Geometry,
  WaterFeatureProperties
>;

export type WaterFeatureCollection = GeoJSON.FeatureCollection<
  GeoJSON.Geometry,
  WaterFeatureProperties
>;
```

`GeoJSON` namespace comes from `@types/geojson` (transitive dep of `@types/leaflet`,
already in node_modules). These interfaces match ARCHITECTURE.md §3 and the probe
data at `data/raw/arebaltapeste_probe/snapshot_waters.json`.

## 9. SSR / Next.js Patterns (from v2 §10, confirmed)

1. **Dynamic import for all Leaflet-touching files** — react-leaflet v5 is ESM-only
   and touches `window` at module eval. `MapView.tsx` and `WaterFeatureLayer.tsx`
   MUST be loaded via `dynamic(() => import(...), { ssr: false })` from MapShell.
   `transpilePackages: ["react-leaflet"]` is already configured.
2. **Named exports** — use `export function MapView()` so `dynamic()` can target
   them. Components that DON'T import Leaflet (all other 10) are plain
   `'use client'`, no dynamic needed.
3. **Leaflet CSS** — `import 'leaflet/dist/leaflet.css'` inside MapView.tsx
   (bundled into the client chunk).
4. **Data loading** — fetch on mount in MapShell (`loadData()`). Build-time JSON
   import in page.tsx is an optional optimization, NOT the spec (R11).
5. **No `useSearchParams`** — locale comes from `params` (or is absent for now),
   compatible with static export.

## 10. Risks & Tradeoffs (updated from v2 §11)

| Risk | Mitigation |
|---|---|
| SSR hydration mismatch from Leaflet | All Leaflet components `dynamic(ssr:false)`; transpilePackages set (Rk1) |
| react-leaflet v5 API changes | v5 largely v4-compatible but ESM-only; test early; docs react-leaflet.js.org |
| cmdk filtering inadequate for 82 items | Unlikely; fallback = fuse.js as cmdk custom `filter` fn — zero component API change (R5) |
| bbox rectangles look crude | Acceptable MVP; `waterToGeoJSON()` single function swaps to real GeoJSON when geocoding pipeline lands |
| 426 features on one GeoJSON layer | Leaflet handles it; if slow, `interactive:false` beyond zoom threshold |
| i18n (`[locale]`, next-intl) not yet scaffolded | Hardcode Romanian strings this milestone; extract i18n as follow-up task (R12-adjacent) |
| vaul drag vs Leaflet pan gesture conflict | vaul gesture detection wins on sheet; `touch-action: manipulation` on map container |
| Selected water filtered out UX | Auto-dismiss + optional toast (R9); documented in state machine |

## 11. Implementation Sequence (for executioner t_8ba7e9ea)

1. `pnpm add zustand`
2. `src/types/data.ts` — interfaces from §8
3. `src/utils/geo.ts`, `src/utils/colors.ts`
4. `src/stores/map-store.ts` — store contract §5.1
5. `src/hooks/use-filtered-waters.ts`, `src/hooks/use-counties.ts`
6. `public/data/associations.json`, `public/data/waters.json` — extract from
   `data/raw/arebaltapeste_probe/snapshot_asociatii.json` + `snapshot_waters.json`
7. Replace `src/app/page.tsx` placeholder with `<Suspense><MapShell/></Suspense>`
8. Components bottom-up: AssociationSearch → ColorLegend → FilterBar →
   WaterFeatureLayer → MapView → WaterDetailCard → WaterDetailSheet (vaul) →
   MapShell → Header
9. `pnpm dev` + browser verification (checklist §12)
10. Block for human review of the working UI

## 12. Verification Criteria (merged from v2 §13 + 3 specs)

- [ ] `pnpm dev` starts with zero console errors
- [ ] Map renders OSM tiles centered on Romania `[45.95, 24.95]` zoom 7
- [ ] All 426 waters drawn as bbox rectangles, blue when no association selected
- [ ] AssociationSearch filters as you type (cmdk); water-count badges shown;
      "Toate asociațiile" clears
- [ ] Selecting an association → matching waters green, others grey; legend shows
      Acoperit/Neacoperit; sheet (if open) stays open, content recolors
- [ ] County chips toggle; map redraws; county list derived from data
- [ ] WaterTypeFilter segmented control filters lac/rau
- [ ] Tap water → bottom sheet slides to Peek (mobile) / panel opens (≥768px)
- [ ] Sheet shows: name, subtype badge, county, sector (limite), size, association
      contact (phone/address/site), referință; missing fields simply absent
- [ ] Sheet states: Collapsed/Peek/Expanded heights ~10/35/65vh; drag snapping
      works; backdrop opacity 0/0/0.20/0.50; × and ESC dismiss; empty-map tap no-op
- [ ] Filtering out the selected water auto-dismisses the sheet
- [ ] Desktop ≥1024: 380px persistent right panel; tablet: 320px collapsible
- [ ] Mobile: `100dvh` map height, no layout jump; safe-area insets respected
- [ ] Legend mobile-collapsible with 5s auto-collapse; ≥768 always visible

## 13. References

| Doc | Path | Role |
|---|---|---|
| This plan (v3 consolidated) | `docs/component_structure_plan.md` | Canonical — wins on conflict |
| Component tree spec | `docs/map-component-tree.md` | Tree detail, z-index, SSR map |
| State & data flow spec | `docs/map-state-data-flow.md` | Store contract, 7 flow paths, edge cases |
| Mobile layout spec | `docs/mobile-layout-spec.md` | Breakpoints, sheet states, interaction machine |
| Data requirements note | `data/data_requirements_note.md` | Field mappings, geometry/permit-note gaps |
| Architecture | `docs/ARCHITECTURE.md` | Stack, routes, data model (aspirational parts flagged in §2.3) |





