# UndePescuim.ro — Architecture & Implementation Plan

**Date:** 2026-08-11  
**Author:** plan-maker (t_13c53320)  
**Parent:** t_33de9e28 (Orchestrator — Multi-step speculation)  
**Dependency:** Project scaffold at `~/undepescuim` (created by executioner t_0fdf467e)  
**Status:** Final draft — awaiting scaffold for placement at `~/undepescuim/docs/ARCHITECTURE.md`

---

## Table of Contents

1. [Goals & Scope](#1-goals--scope)
2. [Tech Stack](#2-tech-stack)
3. [Data Model & TypeScript Interfaces](#3-data-model--typescript-interfaces)
4. [Project Structure](#4-project-structure)
5. [Route Design](#5-route-design)
6. [Component Tree & Props](#6-component-tree--props)
7. [i18n Strategy](#7-i18n-strategy)
8. [PWA Plan](#8-pwa-plan)
9. [Data Refresh Mechanism](#9-data-refresh-mechanism)
10. [State Management & Data Flow](#10-state-management--data-flow)
11. [Deployment (Vercel)](#11-deployment-vercel)
12. [Pilot → Full Expansion Plan](#12-pilot--full-expansion-plan)
13. [Risks & Tradeoffs](#13-risks--tradeoffs)
14. [Implementation Sequence](#14-implementation-sequence)

---

## 1. Goals & Scope

UndePescuim.ro is a bilingual (Romanian + English), mobile-first, static-site directory of Romanian fishing waters. Users can:
- Browse waters on a Leaflet/OpenStreetMap map
- Select an angling association to see which waters it covers (green/grey coloring)
- Filter by county or water type (lake/river)
- Tap a water to see its detail card (name, sector, size, association contact)
- Submit a verification report ("data correct", "water no longer valid", etc.)
- Install as a PWA for offline map access

**Pilot scope:** 4–5 Romanian counties (Cluj, Bihor, Brașov, Sibiu + optional Mureș).
**Full scope:** All 41 counties.
**Backend:** None. Static JSON files. Vercel free tier.
---

## 2. Tech Stack

| Layer | Choice | Version | Rationale |
|-------|--------|---------|-----------|
| Framework | Next.js (App Router) | ^16.3 | Static export, layouts, route groups, Vercel-native |
| Language | TypeScript | ^5 | Type safety for water/association data shapes |
| Styling | Tailwind CSS | ^4 | Mobile-first utility classes; matches reference site |
| UI Primitives | shadcn/ui | ^4.16 | 19 pre-approved components (Button, Card, Command, etc.) |
| Icons | lucide-react | ^1.30 | Paired with shadcn/ui conventions |
| Map | Leaflet + react-leaflet | ^4.2 + ^5 | No API key needed, good OSM coverage for Romania |
| i18n | next-intl | ^4 | Server + client translations, RO/EN prefix routing |
| State | Zustand | ^5 | Lightweight; 82 associations + 426 waters fit in-memory |
| Search | fuse.js | ^7 | Fuzzy client-side search over 82 association names |
| Forms | React Hook Form + Zod | ^7 + ^3 | Crowdsource verification form validation |
| PWA | next-pwa (or manual SW) | via serwist | Service worker for offline map tiles + data |
| Package mgr | pnpm | ^11 | Matches reference site conventions |
| Hosting | Vercel | Free tier | Static export, custom domain, auto-deploy |

### Why NOT...

- **Mapbox/Google Maps**: Require API keys, paid tiers, and are heavier. OSM is free and has good Romanian coverage.
- **Redux/Recoil**: Too much boilerplate. Zustand is ~1KB and fits this state surface.
- **TinaCMS/Contentful**: Headless CMS adds hosting cost and complexity for data that changes once per year.
- **Next.js SSR/ISR**: Static export to JSON files eliminates server costs entirely. The data is pre-baked.

---

## 3. Data Model & TypeScript Interfaces

All interfaces go in `src/types/data.ts`. These are derived from the probe data at `~/undepescuim/data/raw/arebaltapeste_probe/snapshot_waters.json`.

### 3.1 Core Entities

```typescript
// src/types/data.ts

/** A fishing association that manages waters */
export interface Association {
  slug: string;           // "ajvps-cluj"
  name: string;           // "AJVPS Cluj"
  name_long: string;      // "Asociația Județeană a Vânătorilor și Pescarilor Sportivi Cluj"
  ape: number;            // count of public waters managed
  adresa?: string;        // "Strada Bartók Béla, Nr. 27, Cluj-Napoca"
  telefon?: string;       // "0264 420 908"
  siteUrl?: string;       // "http://cluj.rosilva.ro/"
  bbox: BBox;             // association's coverage bounding box
  id: string;             // MongoDB ObjectId from source
}
```

### 3.2 Geo Types

```typescript
/** WGS84 longitude, latitude pair — GeoJSON convention */
export type LngLat = [number, number]; // [lon, lat]

/** Bounding box: [minLon, minLat, maxLon, maxLat] */
export type BBox = [number, number, number, number];

/** Water type discriminator */
export type WaterSubtype = "lac" | "rau";

/** Water type filter state */
export type WaterTypeFilter = "all" | WaterSubtype;

/** County name as stored in water.judet (e.g. "Cluj", "Bihor") */
export type County = string;
```

### 3.3 Water Entity

```typescript
/** A public fishing water (lake or river section) */
export interface Water {
  slug: string;              // "iwrd2dxy"
  name: string;              // "Lacul Tarnița"
  judet: County;             // "Cluj"
  type: "ape";               // always "ape" for public waters
  subtype: WaterSubtype;     // "lac" | "rau"
  limite: string;            // "zona de acumulare" — sector boundary description
  dimensiune: string;        // "240 Ha" | "35 km" — size with unit
  pescuit_interzis: boolean; // fishing banned flag
  referinta: string;         // legal reference document title
  coordinates: LngLat;       // center point [lon, lat]
  driving: LngLat;           // directions anchor point
  bbox: BBox;                // [minLon, minLat, maxLon, maxLat]
  asociatie: {
    name: string;
    slug: string;
    telefon?: string;
    adresa?: string;
    siteUrl?: string;
  } | null;                  // null = no association assigned
  // FUTURE: true polygon/polyline geometry
  // geojson?: GeoJSON.Geometry;
}
```

### 3.4 GeoJSON Feature Types (for Leaflet rendering)

```typescript
/** GeoJSON feature built from Water data */
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
### 3.5 Crowdsource Report Types

```typescript
/** Report form submission */
export type ReportReason =
  | "data_correct"          // "I fished here, data is correct"
  | "water_invalid"         // "This water no longer exists / is not fishable"
  | "association_changed"   // "Association changed"
  | "wrong_coordinates"     // "Coordinates are wrong"
  | "other";                // Free-text

export interface VerificationReport {
  waterSlug: string;
  waterName: string;
  reason: ReportReason;
  details?: string;          // optional free-text details
  contactEmail?: string;     // optional, for follow-up
  submittedAt: string;       // ISO 8601
}
```

### 3.6 County Registry

```typescript
/** Static county metadata for the pilot → full expansion path */
export interface CountyMeta {
  slug: string;          // "cluj"
  name: string;          // "Cluj"
  enabled: boolean;      // true = in pilot, false = future
  waterCount: number;
  associationCount: number;
}
```

---

## 4. Project Structure

```
~/undepescuim/
├── .github/
│   └── workflows/
│       └── data-refresh.yml        # Annual re-scrape + rebuild CI
│
├── public/
│   ├── data/
│   │   ├── associations.json       # 82 associations (all counties)
│   │   ├── waters.json             # 426 waters (all counties)
│   │   ├── counties.json           # County metadata registry
│   │   └── geo/
│   │       └── waters.geojson      # FUTURE: pre-built GeoJSON FeatureCollection
│   ├── manifest.json               # PWA manifest
│   ├── sw.js                       # Service worker (generated)
│   ├── favicon.ico
│   └── icons/                      # PWA icons (192, 512)
│       ├── icon-192.png
│       └── icon-512.png
│
├── messages/
│   ├── ro.json                     # Romanian translations
│   └── en.json                     # English translations
│
├── scripts/
│   ├── scrape-arebaltapeste.ts     # Data extraction from arebaltapeste.ro
│   └── generate-geojson.ts         # FUTURE: bbox → GeoJSON builder
│
├── src/
│   ├── app/
│   │   ├── [locale]/               # i18n prefix routes: /ro, /en
│   │   │   ├── layout.tsx          # Root layout: fonts, metadata, PWA meta
│   │   │   ├── page.tsx            # Home/map page
│   │   │   ├── not-found.tsx       # 404
│   │   │   └── loading.tsx         # Suspense fallback
│   │   └── api/                    # OPTIONAL: API routes for report form
│   │       └── report/
│   │           └── route.ts        # POST /api/report → GitHub issue / form service
│   │
│   ├── components/
│   │   ├── map/
│   │   │   ├── MapView.tsx         # Leaflet map container + tile layer
│   │   │   ├── WaterFeatureLayer.tsx  # GeoJSON layer with coloring + events
│   │   │   ├── FilterBar.tsx       # County + water-type filter overlay
│   │   │   ├── CountyFilter.tsx    # Multi-select chip list
│   │   │   ├── WaterTypeFilter.tsx # Segmented control: All / Lakes / Rivers
│   │   │   └── ColorLegend.tsx     # Green/grey/blue legend overlay
│   │   │
│   │   ├── associations/
│   │   │   └── AssociationSearch.tsx  # Command palette / searchable dropdown
│   │   │
│   │   ├── waters/
│   │   │   ├── WaterDetailSheet.tsx   # Mobile bottom sheet + desktop panel
│   │   │   └── WaterDetailCard.tsx    # Water info card content
│   │   │
│   │   ├── verification/
│   │   │   ├── ReportButton.tsx       # Floating action button
│   │   │   └── ReportForm.tsx         # Form dialog with reason selection
│   │   │
│   │   ├── layout/
│   │   │   ├── Header.tsx             # Top bar with logo + association search
│   │   │   ├── Footer.tsx             # Minimal footer with credits
│   │   │   └── LanguageSwitcher.tsx   # RO/EN toggle
│   │   │
│   │   └── ui/                        # shadcn/ui primitives (19 components)
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── input.tsx
│   │       ├── select.tsx
│   │       ├── label.tsx
│   │       ├── badge.tsx
│   │       ├── tabs.tsx
│   │       ├── sheet.tsx
│   │       ├── dropdown-menu.tsx
│   │       ├── command.tsx
│   │       ├── dialog.tsx
│   │       ├── skeleton.tsx
│   │       ├── separator.tsx
│   │       ├── checkbox.tsx
│   │       ├── switch.tsx
│   │       ├── popover.tsx
│   │       ├── tooltip.tsx
│   │       ├── scroll-area.tsx
│   │       └── table.tsx
│   │
│   ├── lib/
│   │   ├── utils.ts               # cn() helper (clsx + tailwind-merge)
│   │   ├── i18n.ts                # next-intl request config + navigation
│   │   ├── data-loader.ts         # fetch + cache static JSON files
│   │   ├── geo.ts                 # bbox → GeoJSON, LngLat → LatLng conversion
│   │   └── colors.ts              # coverage coloring logic
│   │
│   ├── hooks/
│   │   ├── useAssociations.ts     # fetch associations + fuse.js search
│   │   ├── useWaters.ts           # fetch waters
│   │   ├── useFilteredWaters.ts   # derived state: waters → filtered subset
│   │   ├── useCounties.ts         # derived: deduplicated county list
│   │   └── useMapStore.ts         # Zustand selectors
│   │
│   ├── store/
│   │   └── map-store.ts           # Zustand store: state + actions
│   │
│   ├── types/
│   │   └── data.ts                # All TypeScript interfaces (Section 3)
│   │
│   └── middleware.ts              # next-intl locale detection + redirect
│
├── docs/
│   └── ARCHITECTURE.md            # This file
│
├── next.config.ts                 # Static export + i18n config
├── next-env.d.ts
├── tailwind.config.ts             # Or postcss.config for Tailwind v4
├── tsconfig.json
├── package.json
├── .gitignore
└── README.md
```

### Key Structural Decisions

- **`src/` root**: Matches reference site convention (not a flat top-level app directory).
- **`[locale]` route group**: All pages live under `/ro/...` or `/en/...`. The root `/` redirects to the detected locale.
- **Feature-based component folders**: `map/`, `associations/`, `waters/`, `verification/`, `layout/` — each folder is a self-contained feature.
- **`ui/` is flat**: All 19 shadcn/ui primitives in one folder, matching shadcn's `npx shadcn add` convention.
- **`lib/` for pure utilities**: Zero component imports. `data-loader.ts` abstracts fetch from component code.
- **`hooks/` for data access**: Components never call `fetch()` directly — they use hooks that wrap the store.
---

## 5. Route Design

All routes are under `src/app/[locale]/` with next-intl prefix-based routing.

| Route | Page | Component | Purpose |
|-------|------|-----------|---------|
| `/` | Redirect | — | Detect locale → `/ro` or `/en` |
| `/ro` | `page.tsx` | `<MapPage />` | Romanian home: full map UI |
| `/en` | `page.tsx` | `<MapPage />` | English home: full map UI |
| `/ro/despre` | `despre/page.tsx` | `<AboutPage />` | About the project (RO) |
| `/en/about` | `about/page.tsx` | `<AboutPage />` | About the project (EN) |
| `/ro/confidentialitate` | `confidentialitate/page.tsx` | `<PrivacyPage />` | Privacy policy (RO) |
| `/en/privacy` | `privacy/page.tsx` | `<PrivacyPage />` | Privacy policy (EN) |
| `/api/report` | `api/report/route.ts` | — | POST handler for verification reports |
| `[...rest]` | `not-found.tsx` | `<NotFound />` | 404 catch-all |

### Report API — `/api/report` (F3, implemented)

POST handler (`src/app/api/report/route.ts`) that turns an in-app verification
report into a **GitHub issue** on `neagastefan99/undepescuim` with the `report`
label. This is the review queue: maintainer closes the issue after fixing the
data → commit → Vercel auto-deploy.

Request body (JSON):

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `reason` | `ReportReason` | yes | one of `data_correct` / `water_invalid` / `association_changed` / `wrong_coordinates` / `other` |
| `waterSlug` | string | yes | water slug, auto-attached by the form |
| `waterName` | string | yes | water name, auto-attached by the form |
| `details` | string | no | free text, ≤2000 chars |
| `contactEmail` | string | no | optional follow-up contact |
| `website` | string | no | honeypot — bots fill it, route silently drops |

Responses: `200 {ok:true, issueUrl}` · `400 invalid_json/invalid_reason/missing_water` ·
`503 not_configured` (missing token) · `502 github_error`. Honeypot submissions
get a silent `200 {ok:true, issueUrl:null}`.

**Env secret (server-side only, never `NEXT_PUBLIC_`):** `REPORT_GITHUB_TOKEN` —
a GitHub token with `repo` / fine-grained **Issues: Read & Write** scope on
`neagastefan99/undepescuim`. Required in production (Vercel env: Production +
Preview) and locally (`.env.local`) for the route to create issues; without it
the route returns 503. The `report` label must exist on the repo or issue
creation 422s (`gh label create report`).

**Static-site constraint:** this route REQUIRES a serverless runtime. Do **not**
set `output: "export"` in `next.config.ts` or `/api/report` silently 404s. If
serverless is ever dropped, the documented fallback (t_c21762e3) swaps the form's
submit handler to open the Google Form with a prefill param.

### Layout Hierarchy

```
RootLayout (src/app/[locale]/layout.tsx)
├── NextIntlClientProvider        (translations + timezone)
├── ThemeProvider?                (optional: light/dark)
├── Header
│   ├── Logo + site name
│   ├── AssociationSearch         (Command component)
│   └── LanguageSwitcher          (RO/EN pill toggle)
├── <main>
│   └── {children}               (page content)
└── Footer                        (credits, links, last updated)
```

### Route Design Decisions

- **Prefix-based (`/ro/...`, `/en/...`), NOT domain-based (`ro.undepescuim.ro`)** — simpler Vercel config, single domain, SEO-friendly hreflang tags.
- **Root `/` redirects via middleware** — `Accept-Language` header detection with Romanian fallback.
- **Single-page map app** — the entire map UX (filters, detail sheet, legend) is one page. No separate detail pages (no `/ro/ape/lacul-tarnita`). Detail is shown in a bottom sheet / side panel. This keeps the map state alive — no navigating away to see a water.
- **Why no deep links for waters?** The static export model makes dynamic `[slug]` routes costly (one HTML file per water = 426 files). Instead, use URL hash state: `/ro#water=iwrd2dxy`. The map page reads `window.location.hash` on mount and opens the detail sheet. This approach:
  - Works with static export (no server-side routing needed)
  - Allows sharing links to specific waters
  - Keeps the map in-view and state alive
- **About + Privacy are separate static pages** — thin, fast, no map needed.
---

## 6. Component Tree & Props

### 6.1 Full Component Tree

```
MapPage
├── MapView (full-viewport map)
│   ├── <MapContainer> (react-leaflet)
│   │   ├── <TileLayer> (OSM tiles)
│   │   └── WaterFeatureLayer (GeoJSON layer, color-coded)
│   ├── FilterBar (overlay, top-left)
│   │   ├── CountyFilter (chip list)
│   │   └── WaterTypeFilter (segmented control)
│   └── ColorLegend (overlay, bottom-right)
│
├── WaterDetailSheet (bottom sheet / side panel)
│   └── WaterDetailCard
│       ├── Badge (subtype)
│       ├── Association contact info
│       └── Sector + size info
│
└── ReportButton (floating FAB) → ReportForm (Dialog)
```

### 6.2 Per-Component Props & Responsibilities

#### MapView
```typescript
// src/components/map/MapView.tsx
interface MapViewProps {
  children: React.ReactNode;  // overlays: FilterBar, ColorLegend
}
```
- Wraps the `MapContainer` from react-leaflet
- Sets default center (Romania: ~[45.94, 25.0]) and zoom (7)
- Provides TileLayer with OSM `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`
- Full viewport: `className="h-[100dvh] w-full"`

#### WaterFeatureLayer
```typescript
// src/components/map/WaterFeatureLayer.tsx
interface WaterFeatureLayerProps {
  waters: Water[];                   // filtered list from useFilteredWaters()
  coverageSlug: string | null;      // selected association slug
}
```
- Converts `Water[]` → `GeoJSON.FeatureCollection` via `waterToGeoJSON()`
- Renders a single `<GeoJSON>` component from react-leaflet
- `style` callback: green (`#16a34a`) for covered, grey (`#9ca3af`) for uncovered, blue (`#3b82f6`) when no association selected
- `onEachFeature` callback: attaches click → `store.selectWater(slug)`, hover → pointer cursor
- **MVP**: uses `bbox` to draw rectangles. **Future**: swaps to `geojson` polygon/polyline when available — same component, zero changes

#### FilterBar
```typescript
// src/components/map/FilterBar.tsx
// No props — reads from store directly
```
- Creates absolute-positioned overlay on the map
- Contains CountyFilter + WaterTypeFilter
- On mobile (<768px): horizontal scrollable pill row at top
- On desktop (>=768px): top-left panel

#### CountyFilter
```typescript
// src/components/map/CountyFilter.tsx
interface CountyFilterProps {
  counties: string[];                    // all available counties (from useCounties())
  selected: string[];                    // currently selected (from store)
  onChange: (selected: string[]) => void;
}
```
- Renders a horizontal scrollable chip/pill row
- Tapping toggles selection
- "All counties" chip clears selection (when none selected)
- Derived from water data; no hardcoded county list

#### WaterTypeFilter
```typescript
// src/components/map/WaterTypeFilter.tsx
interface WaterTypeFilterProps {
  selected: WaterTypeFilter;  // "all" | "lac" | "rau"
  onChange: (type: WaterTypeFilter) => void;
}
```
- Segmented control / button group
- Three options: Toate (All), Lacuri (Lakes), Râuri (Rivers)
- Labels come from i18n

#### ColorLegend
```typescript
// src/components/map/ColorLegend.tsx
interface ColorLegendProps {
  coverageSlug: string | null;
}
```
- Absolute-positioned bottom-right on the map
- Shows 2-3 rows: green (covered), grey (not covered), blue (neutral — only when no association selected)
- Labels from i18n
#### AssociationSearch
```typescript
// src/components/associations/AssociationSearch.tsx
// No props — reads from store directly
```
- Uses shadcn/ui `Command` component (cmdk-based)
- Fuse.js fuzzy search over `associations[].name` + `associations[].name_long`
- Each result row: association name + water count badge
- On select: `store.selectAssociation(slug)` + `store.clearSelectedWater()`
- Clear button (×) resets to `null` (all waters, neutral coloring)
- Placed in Header on mobile, in a dedicated top bar on desktop

#### WaterDetailSheet
```typescript
// src/components/waters/WaterDetailSheet.tsx
interface WaterDetailSheetProps {
  water: Water | null;
  association: Association | null;
  onClose: () => void;
}
```
- Uses shadcn/ui `Sheet` component
- **Mobile (<768px)**: bottom sheet, slides up, max-height 60vh, drag handle, backdrop
- **Desktop (>=768px)**: right-side panel, 380px wide, map resizes to fill remaining space
- Contains WaterDetailCard
- Opening animation: `transition: transform 300ms ease`
- Close: tap backdrop, drag down, × button, or ESC

#### WaterDetailCard
```typescript
// src/components/waters/WaterDetailCard.tsx
interface WaterDetailCardProps {
  water: Water;
  association: Association | null;
}
```
**Layout:**
```
┌──────────────────────────────────────────┐
│  Lacul Tarnița               [Lac] [Cluj]│   ← Badge for subtype, Badge for county
│                                          │
│  Sector: zona de acumulare               │   ← limite
│  Dimensiune: 240 Ha                      │   ← dimensiune
│                                          │
│  ── Asociația ──                         │   ← Separator
│  D.S. Cluj                               │   ← association.name
│  📞 0264 420 908                         │   ← association.telefon
│  📍 Strada Bartók Béla, Nr. 27           │   ← association.adresa
│  🌐 cluj.rosilva.ro                      │   ← association.siteUrl (link)
│                                          │
│  Referință: Lista habitatelor...         │   ← referinta, muted style
│                                          │
│  [Raportează o problemă]                 │   ← opens ReportForm
└──────────────────────────────────────────┘
```
- "Raportează o problemă" button pre-fills the waterSlug + waterName in the report form

#### ReportButton
```typescript
// src/components/verification/ReportButton.tsx
// No props — reads store for selectedWater
```
- Floating action button (FAB), bottom-right of map (above legend)
- Icon: Flag or exclamation mark
- Opens ReportForm in a Dialog
- If a water is currently selected, pre-fills waterSlug + waterName

#### ReportForm
```typescript
// src/components/verification/ReportForm.tsx
interface ReportFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  prefilledWaterSlug?: string;
  prefilledWaterName?: string;
}
```
- Uses shadcn/ui `Dialog`
- Form fields:
  1. Water name (read-only if prefilled, text input otherwise)
  2. Reason (Radio group): "Datele sunt corecte", "Această apă nu mai există", "Asociația s-a schimbat", "Coordonatele sunt greșite", "Altceva"
  3. Details (Textarea, optional)
  4. Email (Input, optional, for follow-up)
- Validation: Zod schema, React Hook Form
- Submit: POST to `/api/report` — which forwards to a GitHub Issue or form service (Formspree, Google Forms, etc.)
- Success toast + close dialog

#### Header
```typescript
// src/components/layout/Header.tsx
// No props
```
- Fixed top bar, z-50
- Left: Logo + "UndePescuim" text (links to `/`)
- Center/Right: AssociationSearch (on desktop)
- Right: LanguageSwitcher
- On mobile (<768px): AssociationSearch collapses into a full-screen Command overlay triggered by a search icon

#### LanguageSwitcher
```typescript
// src/components/layout/LanguageSwitcher.tsx
// No props — uses next-intl
```
- RO | EN pill toggle
- Calls `router.replace()` to switch locale while preserving the current path
- Active language: bold + primary color
---

## 7. i18n Strategy

### 7.1 Library: next-intl v4

- **Why next-intl**: Native Next.js App Router support, server + client components, ICU message format, type-safe translations, prefix-based routing built-in.
- **Alternatives considered**: next-i18next (stable but heavier), react-intl (FormatJS, no Next.js routing), custom solution (too much work).

### 7.2 Route Pattern

```
/                           → 302 redirect to /ro or /en (Accept-Language detection)
/ro                         → Romanian home
/en                         → English home
/ro/despre                  → About (RO)
/en/about                   → About (EN)
```

- **Middleware** (`src/middleware.ts`) handles locale detection + redirect.
- Default locale: Romanian (`ro`).
- Strategy: `prefixAlways` — every URL has the locale prefix. This avoids the ambiguity of a default-locale strip and makes `next export` simpler.

### 7.3 Translation Key Structure

```json
// messages/ro.json — Romanian
{
  "common": {
    "siteName": "UndePescuim",
    "siteTagline": "Harta apelor de pescuit din România",
    "loading": "Se încarcă...",
    "error": "A apărut o eroare",
    "close": "Închide",
    "selectLanguage": "Selectează limba"
  },
  "header": {
    "searchPlaceholder": "Caută o asociație...",
    "searchEmpty": "Nicio asociație găsită",
    "allAssociations": "Toate asociațiile"
  },
  "map": {
    "title": "Hartă",
    "filterByCounty": "Filtrează după județ",
    "allCounties": "Toate județele",
    "filterByType": "Tipul apei",
    "waterTypeAll": "Toate",
    "waterTypeLake": "Lacuri",
    "waterTypeRiver": "Râuri",
    "legendTitle": "Legendă",
    "legendCovered": "Acoperit de asociația selectată",
    "legendNotCovered": "Neacoperit",
    "legendNeutral": "Vedere neutră",
    "noWatersFound": "Nicio apă găsită pentru filtrele selectate"
  },
  "water": {
    "detailTitle": "Detalii apă",
    "sector": "Sector",
    "size": "Dimensiune",
    "association": "Asociația",
    "phone": "Telefon",
    "address": "Adresă",
    "website": "Website",
    "reference": "Referință legală",
    "fishingBanned": "Pescuit interzis",
    "noAssociation": "Fără asociație atribuită"
  },
  "report": {
    "title": "Raportează o problemă",
    "waterLabel": "Apa",
    "reasonLabel": "Motivul raportării",
    "reasonDataCorrect": "Am pescuit aici, datele sunt corecte",
    "reasonWaterInvalid": "Această apă nu mai există / nu se poate pescui",
    "reasonAssociationChanged": "Asociația s-a schimbat",
    "reasonWrongCoordinates": "Coordonatele sunt greșite",
    "reasonOther": "Altceva",
    "detailsLabel": "Detalii suplimentare",
    "detailsPlaceholder": "Oferă mai multe informații...",
    "emailLabel": "Email (opțional, pentru follow-up)",
    "submit": "Trimite raportul",
    "success": "Raport trimis. Mulțumim!",
    "error": "Eroare la trimitere. Încearcă din nou."
  },
  "pwa": {
    "installPrompt": "Instalează aplicația pentru acces offline",
    "install": "Instalează",
    "dismiss": "Mai târziu"
  },
  "footer": {
    "credits": "Date furnizate de arebaltapeste.ro",
    "lastUpdated": "Ultima actualizare",
    "about": "Despre",
    "privacy": "Confidențialitate",
    "reportIssue": "Raportează o problemă"
  },
  "about": {
    "title": "Despre UndePescuim",
    "body": "..."
  }
}
```

### 7.4 Key Design Rules

1. **Namespaces by domain**: `common`, `header`, `map`, `water`, `report`, `pwa`, `footer`, `about`. No flat key soup.
2. **ICU MessageFormat for plurals and variables** where needed (e.g. `"{count} ape"` → `"{count, plural, one {# apă} few {# ape} other {# de ape}}"`).
3. **Both JSON files must have identical key structure** — TypeScript enforces this via `next-intl`'s type generation.
4. **Translation keys use camelCase**, matching JS convention (not kebab-case or snake_case).
5. **Loading state per component**: each component that uses translations wraps in `useTranslations('namespace')` and handles the loading/error boundary.

### 7.5 Configuration

```typescript
// src/lib/i18n.ts
import { getRequestConfig } from "next-intl/server";
import { notFound } from "next/navigation";

export const locales = ["ro", "en"] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = "ro";

export default getRequestConfig(async ({ requestLocale }) => {
  let locale = await requestLocale;
  if (!locale || !locales.includes(locale as Locale)) {
    locale = defaultLocale;
  }
  return {
    locale,
    messages: (await import(`../../messages/${locale}.json`)).default,
  };
});
```

```typescript
// src/middleware.ts
import createMiddleware from "next-intl/middleware";
import { locales, defaultLocale } from "./lib/i18n";

export default createMiddleware({
  locales,
  defaultLocale,
  localePrefix: "always",
  localeDetection: true,
});

export const config = {
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};
```
---

## 8. PWA Plan

### 8.1 Goal

"PWA light" in MVP — installable on mobile home screen, works offline for:
- Map tiles (cached from previous online sessions)
- Static data files (associations.json, waters.json)
- App shell (HTML, CSS, JS, icons)

Users can browse the map and view cached waters even without internet. The app degrades gracefully: map tiles that aren't cached show grey tiles, data is served from cache.

### 8.2 Manifest

```json
// public/manifest.json
{
  "name": "UndePescuim",
  "short_name": "UndePescuim",
  "description": "Harta apelor de pescuit din România — Romanian fishing waters map",
  "start_url": "/ro",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#3b82f6",
  "orientation": "any",
  "icons": [
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "maskable"
    }
  ],
  "lang": "ro",
  "categories": ["navigation", "sports"]
}
```

### 8.3 Service Worker Strategy (via Serwist)

Use `@serwist/next` (successor to `next-pwa`) for service worker integration that plays well with Next.js static export.

**Cache tiers (3 levels):**

| Tier | What | Strategy | Max Size | TTL |
|------|------|----------|----------|-----|
| **App Shell** | HTML, CSS, JS, fonts, icons | Precache on install | ~2 MB | — (versioned in build) |
| **Map Tiles** | `*.tile.openstreetmap.org/*` | Cache-first, then network | 50 MB | 30 days |
| **Data** | `/data/*.json` | Network-first, fallback to cache | 5 MB | 7 days |

**Service worker lifecycle:**

```
Install
  → Precache app shell assets (from webpack manifest)
  → Cache public/data/*.json

Activate
  → Clean old caches (versioned by SW hash)

Fetch — App Shell
  → Cache-first: serve from cache, update in background (stale-while-revalidate)

Fetch — Map Tiles
  → Cache-first: if in cache, serve immediately
  → If not, fetch from network, cache it, serve it
  → On fetch failure: show grey tile (no 404 panic)

Fetch — Data
  → Network-first: fetch fresh JSON
  → On network failure: serve cached version
  → On success: update cache
```

### 8.4 Offline UX

**States to handle:**

1. **Online, fresh load** — fetch JSON from network, render map normally. Cache tiles + data.
2. **Online, cached tiles** — serve tiles from cache for instant map display. Background-update any stale tiles.
3. **Offline, previously cached** — serve cached JSON + tiles. Map works. Show a small "Offline — date afișate din 12 Aug 2026" banner.
4. **Offline, never cached** — show empty state: "Harta necesită o conexiune la internet pentru prima utilizare."

### 8.5 PWA Enhancement: BeforeInstallPrompt

- Detect `beforeinstallprompt` event
- Show a subtle banner/popover at the bottom: "Instalează aplicația pentru acces offline"
- "Instalează" button triggers `prompt()`
- Track: if user dismissed, don't show again for 7 days (localStorage)

### 8.6 Implementation Path

```typescript
// serwist.config.ts (or next.config.ts plugin)
import withSerwist from "@serwist/next";

const withPWA = withSerwist({
  swSrc: "src/app/sw.ts",
  swDest: "public/sw.js",
  // precache all static assets from the build
  globDirectory: "out",
  globPatterns: ["**/*.{html,js,css,json,ico,png,svg,woff2}"],
  // runtime caching rules
  runtimeCaching: [
    {
      urlPattern: /^https:\/\/.*\.tile\.openstreetmap\.org\/.*/,
      handler: "CacheFirst",
      options: {
        cacheName: "map-tiles",
        expiration: { maxEntries: 5000, maxAgeSeconds: 30 * 24 * 60 * 60 },
      },
    },
    {
      urlPattern: /\/data\/.*\.json$/,
      handler: "NetworkFirst",
      options: {
        cacheName: "data-files",
        expiration: { maxEntries: 50, maxAgeSeconds: 7 * 24 * 60 * 60 },
      },
    },
  ],
});
```

### 8.7 Recommended Offline Tile Provider

For a more robust offline experience beyond OSM's tile caching, consider adding a **vector tile layer** (MapTiler free tier or Protomaps) as an optional improvement post-MVP. Vector tiles compress better (fewer tiles for the same zoom levels) and Protomaps can serve a single `.pmtiles` file for all of Romania (~100 MB).
---

## 9. Data Refresh Mechanism

### 9.1 Current State

Data lives as static JSON files under `public/data/`. These are manually extracted from arebaltapeste.ro probe HTML files. The data changes roughly once per year (new fishing season, association or water list updates).

### 9.2 Refresh Pipeline

```
Trigger (manual or scheduled)
  → GitHub Actions workflow
    → Run scripts/scrape-arebaltapeste.ts
      → Fetch fresh HTML pages from arebaltapeste.ro
      → Parse __INITIAL_STATE__ JSON
      → Extract associations + waters
      → Write public/data/associations.json + waters.json
    → Run npm run build
    → Deploy to Vercel (auto-deploy on push to main)
```

### 9.3 GitHub Actions Workflow

```yaml
# .github/workflows/data-refresh.yml
name: Annual Data Refresh
on:
  schedule:
    # Run annually on January 15th (post-holiday, pre-season)
    - cron: "0 0 15 1 *"
  workflow_dispatch:  # Manual trigger via GitHub UI

jobs:
  refresh-data:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v4
        with:
          version: 11

      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: "pnpm"

      - name: Install dependencies
        run: pnpm install

      - name: Run data extraction
        run: pnpm tsx scripts/scrape-arebaltapeste.ts

      - name: Check for changes
        id: check
        run: |
          if git diff --quiet public/data/; then
            echo "changed=false" >> $GITHUB_OUTPUT
          else
            echo "changed=true" >> $GITHUB_OUTPUT
          fi

      - name: Commit updated data
        if: steps.check.outputs.changed == 'true'
        run: |
          git config user.name "data-refresh-bot"
          git config user.email "bot@undepescuim.ro"
          git add public/data/
          git commit -m "chore(data): annual data refresh $(date +%Y)"
          git push

      - name: Trigger Vercel deploy
        if: steps.check.outputs.changed == 'true'
        run: |
          curl -X POST "${{ secrets.VERCEL_DEPLOY_HOOK }}"
```

### 9.4 Manual Refresh Script

```typescript
// scripts/scrape-arebaltapeste.ts
// 1. Fetch https://arebaltapeste.ro/ape (GET, SSR page)
// 2. Extract window.__INITIAL_STATE__ from HTML
// 3. Parse waters array from the state
// 4. Normalize fields (strip MongoDB ids, flatten association data)
// 5. Write to public/data/waters.json
// 6. Similarly for /asociatii → public/data/associations.json
```

**Fallback**: If the HTML structure changes and the scraper breaks, the workflow exits gracefully (no push). Human fixes the scraper selectors and re-runs manually via `workflow_dispatch`.

### 9.5 Data Integrity Checks

The refresh script should:
- Assert `waters.length > 0` (no empty data push)
- Assert `waters[0].coordinates` is `[number, number]` (shape validation)
- Log a diff summary: how many waters added/removed/changed since last run
- Write `public/data/last-refreshed.json` with ISO timestamp
---

## 10. State Management & Data Flow

### 10.1 Zustand Store

```typescript
// src/store/map-store.ts
import { create } from "zustand";
import type { Association, Water, WaterTypeFilter, County } from "@/types/data";

interface MapStore {
  // --- Data ---
  associations: Association[];
  waters: Water[];
  counties: County[];
  dataLoaded: boolean;
  loadError: string | null;

  // --- Selection ---
  selectedAssociationSlug: string | null;
  selectedWaterSlug: string | null;

  // --- Filters ---
  countyFilter: County[];
  waterTypeFilter: WaterTypeFilter;

  // --- Actions ---
  loadData: () => Promise<void>;
  selectAssociation: (slug: string | null) => void;
  selectWater: (slug: string | null) => void;
  toggleCounty: (county: County) => void;
  clearCountyFilter: () => void;
  setWaterTypeFilter: (type: WaterTypeFilter) => void;
}

export const useMapStore = create<MapStore>((set, get) => ({
  associations: [],
  waters: [],
  counties: [],
  dataLoaded: false,
  loadError: null,
  selectedAssociationSlug: null,
  selectedWaterSlug: null,
  countyFilter: [],
  waterTypeFilter: "all",

  loadData: async () => {
    try {
      const [assocRes, watersRes] = await Promise.all([
        fetch("/data/associations.json"),
        fetch("/data/waters.json"),
      ]);
      const associations: Association[] = await assocRes.json();
      const waters: Water[] = await watersRes.json();
      const counties = [...new Set(waters.map((w) => w.judet))].sort();
      set({ associations, waters, counties, dataLoaded: true });
    } catch (err) {
      set({ loadError: (err as Error).message });
    }
  },

  selectAssociation: (slug) => set({ selectedAssociationSlug: slug }),
  selectWater: (slug) => set({ selectedWaterSlug: slug }),

  toggleCounty: (county) =>
    set((s) => ({
      countyFilter: s.countyFilter.includes(county)
        ? s.countyFilter.filter((c) => c !== county)
        : [...s.countyFilter, county],
    })),
  clearCountyFilter: () => set({ countyFilter: [] }),
  setWaterTypeFilter: (type) => set({ waterTypeFilter: type }),
}));
```

### 10.2 Derived State Hooks

```typescript
// src/hooks/useFilteredWaters.ts
import { useMemo } from "react";
import { useMapStore } from "@/store/map-store";
import type { Water } from "@/types/data";

export function useFilteredWaters(): Water[] {
  const waters = useMapStore((s) => s.waters);
  const countyFilter = useMapStore((s) => s.countyFilter);
  const waterTypeFilter = useMapStore((s) => s.waterTypeFilter);

  return useMemo(() => {
    let result = waters;
    if (countyFilter.length > 0) {
      result = result.filter((w) => countyFilter.includes(w.judet));
    }
    if (waterTypeFilter !== "all") {
      result = result.filter((w) => w.subtype === waterTypeFilter);
    }
    return result;
  }, [waters, countyFilter, waterTypeFilter]);
}

export function useSelectedWater(): Water | null {
  const waters = useMapStore((s) => s.waters);
  const slug = useMapStore((s) => s.selectedWaterSlug);
  return useMemo(() => waters.find((w) => w.slug === slug) ?? null, [waters, slug]);
}

export function useSelectedAssociation(): Association | null {
  const associations = useMapStore((s) => s.associations);
  const slug = useMapStore((s) => s.selectedAssociationSlug);
  return useMemo(
    () => associations.find((a) => a.slug === slug) ?? null,
    [associations, slug]
  );
}
```

### 10.3 Data Loading (App Shell)

```typescript
// src/app/[locale]/page.tsx
"use client";
import { useEffect } from "react";
import { useMapStore } from "@/store/map-store";
import { MapView } from "@/components/map/MapView";
// ... other components

export default function MapPage() {
  const loadData = useMapStore((s) => s.loadData);
  const dataLoaded = useMapStore((s) => s.dataLoaded);
  const loadError = useMapStore((s) => s.loadError);

  useEffect(() => { loadData(); }, [loadData]);

  if (loadError) return <ErrorState message={loadError} />;
  if (!dataLoaded) return <LoadingSkeleton />;

  return (
    <div className="relative h-[100dvh] w-full">
      <MapView>
        <FilterBar />
        <ColorLegend coverageSlug={useMapStore(s => s.selectedAssociationSlug)} />
      </MapView>
      <WaterDetailSheet />
      <ReportButton />
    </div>
  );
}
```

### 10.4 Data Flow Diagram

```
App mount
  └→ mapStore.loadData()
       ├→ fetch /data/associations.json → store.associations
       └→ fetch /data/waters.json → store.waters
            └→ dataLoaded = true → render map

User selects "AJVPS Cluj" in AssociationSearch
  └→ store.selectAssociation("ajvps-cluj")
       ├→ WaterFeatureLayer: re-renders with new coverageSlug
       │    ├→ waters where asociatie.slug === "ajvps-cluj" → GREEN
       │    └→ all other waters → GREY
       └→ ColorLegend: updates to show green/grey explanation

User taps "Lacuri" filter
  └→ store.setWaterTypeFilter("lac")
       └→ useFilteredWaters() recomputes
            └→ WaterFeatureLayer receives new waters[] → redraws

User taps a water polygon on map
  └→ Leaflet click event
       └→ store.selectWater("iwrd2dxy")
            └→ WaterDetailSheet opens with that water's data

User submits verification report
  └→ POST /api/report
       └→ GitHub Issue created (via GitHub API)
            └→ Toast: "Raport trimis"
```

---

## 11. Deployment (Vercel)

### 11.1 Configuration

```typescript
// next.config.ts
import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./src/lib/i18n.ts");

const nextConfig: NextConfig = {
  output: "export",            // static HTML export
  trailingSlash: true,        // /ro/ not /ro
  images: { unoptimized: true }, // static export can't optimize images
};

export default withNextIntl(nextConfig);
```

### 11.2 Vercel Setup

1. Connect GitHub repo → Vercel project
2. Framework preset: Next.js (detected automatically)
3. Build command: `pnpm build`
4. Output directory: `out` (Next.js static export default)
5. Root directory: `/` (monorepo not needed)
6. Custom domain: `undepescuim.ro` + `www.undepescuim.ro`
7. Environment variables: `VERCEL_DEPLOY_HOOK` (for data-refresh workflow)
8. No serverless functions needed — entirely static

### 11.3 Build Output

```
out/
├── index.html                 → redirects to /ro/
├── ro/
│   ├── index.html             → map page (RO)
│   ├── despre.html            → about page (RO)
│   └── confidentialitate.html → privacy page (RO)
├── en/
│   ├── index.html             → map page (EN)
│   ├── about.html             → about page (EN)
│   └── privacy.html           → privacy page (EN)
├── data/
│   ├── associations.json
│   ├── waters.json
│   └── last-refreshed.json
├── manifest.json
├── sw.js
├── icons/
└── _next/                     → static assets (JS, CSS, fonts)
```
---

## 12. Pilot → Full Expansion Plan

### 12.1 Pilot Counties

Start with 4–5 counties that have good data coverage and geographic diversity:

| County | Waters | Associations |
|--------|--------|-------------|
| Cluj | ~18 | 3 (D.S. Cluj, AJVPS Cluj, etc.) |
| Bihor | ~22 | 2 (AJVPS Bihor, APS Aqua Crișius) |
| Brașov | ~15 | 2 (AJPS Brașov) |
| Sibiu | ~12 | 2 (AJVPS Sibiu, Fly Fishing Club Sibiu) |
| Mureș (optional) | ~10 | 2 |

**Total pilot:** ~77 waters, ~11 associations.

### 12.2 Expansion Barrier: Data Pre-filtering

The full dataset (426 waters, all 41 counties) is already extracted into `public/data/waters.json`. The expansion is purely a **filtering** step:

1. **Option A: Single JSON, filter at runtime** — the data file (~650 KB) includes all counties. The `CountyFilter` shows only pilot counties initially. A config flag (`NEXT_PUBLIC_PILOT_MODE=true`) hides non-pilot counties. When ready to expand, flip the flag + add new counties to the enabled list.
2. **Option B (Recommended): Per-county JSON files** — split `waters.json` into `public/data/waters/cluj.json`, `bihor.json`, etc. The app loads only the enabled county files. Expansion = add new JSON files.

**Recommendation: Option A for MVP**, because:
- 650 KB is negligible (one small JPEG)
- The full file is already available from the probe data
- No extra build step or file splitting needed
- Expansion is a one-line config change

**When to switch to Option B**: if data grows to >2 MB (unlikely unless we add private lakes or ANPA data).

### 12.3 County Registry

```json
// public/data/counties.json
[
  { "slug": "cluj", "name": "Cluj", "enabled": true, "waterCount": 18, "associationCount": 3 },
  { "slug": "bihor", "name": "Bihor", "enabled": true, "waterCount": 22, "associationCount": 2 },
  { "slug": "brasov", "name": "Brașov", "enabled": true, "waterCount": 15, "associationCount": 2 },
  { "slug": "sibiu", "name": "Sibiu", "enabled": true, "waterCount": 12, "associationCount": 2 },
  { "slug": "mures", "name": "Mureș", "enabled": false, "waterCount": 10, "associationCount": 2 },
  // ... remaining 36 counties, all enabled: false
]
```

The `CountyFilter` chip list derives from counties where `enabled: true`. To expand, flip `enabled` to `true` and redeploy.

---

## 13. Risks & Tradeoffs

| Risk | Impact | Mitigation |
|------|--------|------------|
| **No polygon/polyline geometry** | Map shows axis-aligned rectangles instead of true water shapes. Rivers look crude. | WaterFeatureLayer accepts both `bbox` and `geojson` geometries. Swap data when available — no code changes. |
| **arebaltapeste.ro changes HTML structure** | Data refresh scraper breaks, leaving stale data. | GitHub Actions exits gracefully on parse failure. Manual fix + re-run. Add a data-freshness dashboard check. |
| **OSM tile rate limiting** | Heavy map usage may hit OSM's tile usage policy. | Use a tile proxy CDN or switch to a free-tier provider (Stadia Maps, MapTiler free). Cache tiles aggressively via SW. |
| **Static export + i18n routing** | next-intl with `output: "export"` has known edge cases with middleware. | Test the `prefixAlways` + `trailingSlash` combo early. Fallback: switch to `prefix: "as-needed"` with default RO. |
| **No server → no form POST endpoint** | Verification reports need a receiving endpoint. | Use GitHub Issues API (free, no infra), Formspree (free tier 50/month), or Google Forms. The `/api/report` route can't work in static export — replace with a client-side fetch to the external service. |
| **426 waters in one GeoJSON layer** | Leaflet performance may degrade with many features. | Current count (426) is well within Leaflet's comfort zone. If it grows past 1000, add marker clustering or canvas renderer. |
| **County filter chip list is long (41 counties)** | Scrolling through 41 chips is poor UX on mobile. | Show pilot counties as chips, others in a "More counties" dropdown (Select component). Only expand the chip list as counties are enabled. |
| **i18n coverage gaps** | Some translations may be missing at launch. | Romanian is the default. English keys that are missing fall back to Romanian with a console warning. |
---

## 14. Implementation Sequence

### Phase 0: Scaffold & Foundation (executioner t_0fdf467e — parallel)
1. `pnpm create next-app undepescuim --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"`
2. Install dependencies: `next-intl`, `react-leaflet`, `leaflet`, `@types/leaflet`, `zustand`, `fuse.js`, `react-hook-form`, `zod`, `@serwist/next`, `@radix-ui/*` (for shadcn/ui)
3. Initialize shadcn/ui: `npx shadcn@latest init` + add all 19 components
4. Set up `next.config.ts` with static export + next-intl plugin
5. Create `messages/ro.json` and `messages/en.json` with initial keys
6. Set up `src/lib/i18n.ts` and `src/middleware.ts` for locale routing
7. Deploy to Vercel to verify static export works

### Phase 1: Data Layer (1 session)
1. Copy `snapshot_waters.json` + `snapshot_asociatii.json` to `public/data/` with normalization
2. Write TypeScript interfaces in `src/types/data.ts`
3. Write `src/lib/data-loader.ts` (fetch + cache)
4. Write Zustand store `src/store/map-store.ts`
5. Write derived hooks: `useFilteredWaters`, `useSelectedWater`, `useSelectedAssociation`
6. **Test**: `console.log` the loaded data in the MapPage

### Phase 2: Map Core (1-2 sessions)
1. Write `src/lib/geo.ts` — `waterToGeoJSON()`, `bboxToRectangle()`, `lngLatToLeaflet()`
2. Write `src/lib/colors.ts` — `getFeatureStyle(coverageSlug, feature)`
3. Write `MapView.tsx` — MapContainer + TileLayer
4. Write `WaterFeatureLayer.tsx` — GeoJSON layer with coloring + click handler
5. **Test**: map renders, waters appear as rectangles, clicking logs water slug
6. Write `FilterBar.tsx`, `CountyFilter.tsx`, `WaterTypeFilter.tsx`, `ColorLegend.tsx`
7. **Test**: filters reduce visible waters, legend updates

### Phase 3: Association Search (1 session)
1. Write `AssociationSearch.tsx` using shadcn Command + fuse.js
2. Place in Header
3. Wire `selectAssociation` → map recoloring
4. **Test**: typing filters associations, selecting one colors the map

### Phase 4: Water Detail (1 session)
1. Write `WaterDetailSheet.tsx` — mobile bottom sheet + desktop panel
2. Write `WaterDetailCard.tsx` — all water fields
3. Wire `selectWater` → sheet opens
4. Add URL hash state: `#water=iwrd2dxy` restores detail sheet on load
5. **Test**: tapping a water polygon opens the sheet, tapping backdrop closes it

### Phase 5: Verification Form (1 session)
1. Write `ReportForm.tsx` with React Hook Form + Zod validation
2. Write `ReportButton.tsx` (FAB)
3. Set up GitHub Issue creation via client-side fetch to GitHub API
4. OR set up Formspree/Google Forms endpoint
5. **Test**: submit form, verify issue/entry appears

### Phase 6: PWA (1 session)
1. Create `public/manifest.json`
2. Wire up Serwist with `@serwist/next`
3. Configure runtime caching rules (tiles + data)
4. Add BeforeInstallPrompt handler
5. **Test**: Lighthouse PWA audit ≥ 90, install on mobile

### Phase 7: Polish & Launch (1-2 sessions)
1. Finalize RO/EN translations (all keys filled)
2. About page + Privacy page
3. Mobile responsive audit (test on 320px, 375px, 768px, 1024px, 1440px)
4. SEO: hreflang tags, OpenGraph images, sitemap.xml
5. Analytics: optional Plausible/Umami (privacy-friendly)
6. Deploy to undepescuim.ro

---

## Appendix A: External Dependencies

| Service | Purpose | Free Tier | Notes |
|---------|---------|-----------|-------|
| Vercel | Hosting + auto-deploy | 100 GB bandwidth | Custom domain supported |
| OpenStreetMap | Map tiles | Free (with attribution) | Rate-limit: fair use policy |
| GitHub Actions | Data refresh CI | 2000 min/month (free) | More than enough for annual |
| GitHub Issues | Verification report sink | Free | Authenticated via fine-grained PAT |
| Formspree (fallback) | Form submission | 50 submissions/month | Alternative to GitHub Issues |
| Serwist | PWA service worker | Free (open source) | Successor to next-pwa |

## Appendix B: Verification Checklist

A reviewer should confirm:

- [ ] Data model covers all fields in `snapshot_waters.json` and `snapshot_asociatii.json`
- [ ] Every UI element in the task spec has a matching component with defined props
- [ ] Component tree is mobile-first: bottom sheet on <768px, side panel on >=768px
- [ ] i18n keys are symmetric between `ro.json` and `en.json`
- [ ] PWA strategy covers app shell, map tiles, and data JSON with appropriate cache rules
- [ ] Data refresh pipeline is documented and has a failure mode (graceful exit)
- [ ] Static export is the deployment method — no server-side routes needed
- [ ] Geometry gap is addressed: WaterFeatureLayer works with bbox now, supports GeoJSON later
- [ ] Report form destination is external (GitHub Issues or form service) — no API route required
- [ ] Pilot → full expansion is a config change, not a code rewrite

## Appendix C: What This Plan Does NOT Cover

1. **Actual implementation code** — this is architecture, not implementation
2. **Scraper implementation** — the `scrape-arebaltapeste.ts` script is described but not written
3. **True geometry acquisition** — OSM/Overpass query strategy for water polygons
4. **ANPA cross-reference** — matching ANPA contract numbers to arebaltapeste.ro waters
5. **Performance optimization** — 426 features are small enough to skip optimization
6. **Analytics integration** — described as optional in Phase 7
7. **CI/CD beyond data refresh** — linting, type checking, preview deploys are standard Vercel features
8. **Accessibility audit** — should be done before launch but is out of scope for this plan
