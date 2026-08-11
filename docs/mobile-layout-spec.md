# Mobile-First Layout & Bottom-Sheet Interaction Spec — UndePescuim.ro

**Date:** 2026-08-11  
**Author:** plan-maker (t_ae385b3c)  
**Parent:** t_fced8bd1 (Map Component Tree)  
**Status:** Draft — awaiting reviewer confirmation  
**References:**
- `map-component-tree.md` — 12 components, z-index stacking, responsive summary
- `component_structure_plan.md` — data flow, props, SSR strategy
- `ARCHITECTURE.md` — tech stack (Next.js 16.3, Tailwind v4, shadcn/ui, Zustand)

---

## 0. Purpose

This document defines the **layout, breakpoints, bottom-sheet states, drag/close behavior, backdrop behavior, filter placement, and interaction model** for the UndePescuim.ro core map UI. It is a **pure design deliverable** — no implementation code. A reviewer should be able to scan, confirm the interaction model, and request adjustments before any layout code is written.

---

## 1. Breakpoint Definitions

Three viewport tiers. These align with Tailwind v4 defaults (`md`, `lg`) and reflect real device behavior.

| Tier | Breakpoint | Typical devices | Map layout |
|------|-----------|-----------------|------------|
| **Mobile** | `< 768px` | iPhone SE → Pro Max, Android phones | Full-viewport map. Bottom sheet for details. Filters as scrollable row. |
| **Tablet** | `768px – 1023px` | iPad (portrait), Android tablets, foldables | Map + collapsible right panel (320px). Filters as left overlay. |
| **Desktop** | `≥ 1024px` | Laptops, monitors, iPad (landscape) | Map + persistent right panel (380px). Filters as left overlay. |

### 1.1 Viewport Height Handling

Mobile browsers shrink the visible viewport when the address bar appears. Use `100dvh` (dynamic viewport height) to prevent layout jumps, with `100lvh` (large viewport height) as a fallback:

```css
/* map-container height */
height: 100lvh;               /* fallback */
height: 100dvh;               /* preferred — adapts to browser chrome */
```

---

## 2. Layout Grid

### 2.1 Mobile (`< 768px`) — Vertical Stack

```
┌─────────────────────────────────────┐
│  Header (z-50, h-48px)             │
│  [Logo] [ 🔍 ]            [RO|EN]  │  ← search icon opens fullscreen overlay
├─────────────────────────────────────┤
│  FilterBar (z-1000, h-44px)        │
│  ← scroll → [Cluj] [Bihor] [Brașov] │  ← horizontally scrollable chips
│  [ Toate | Lacuri | Râuri ]         │  ← segmented control, inline
├─────────────────────────────────────┤
│                                     │
│          MAP VIEWPORT               │
│          (fills remaining           │
│           vertical space)           │
│                                     │
│              ┌──────┐              │
│              │Legend│  (z-1000)    │  ← collapsed: 2-row, bottom-right
│              └──────┘              │
├─────────────────────────────────────┤
│  ┌─────────────────────────────┐   │
│  │  ═══  Lacul Tarnița    [×] │   │  ← Bottom Sheet (z-1200)
│  │  Județul Cluj | 240 Ha     │   │     WaterDetailSheet + WaterDetailCard
│  │  Asociația: D.S. Cluj      │   │
│  │  📞 0264 420 908           │   │
│  │  [Raportează o problemă]   │   │
│  └─────────────────────────────┘   │
│  Backdrop (z-1100) behind sheet    │
└─────────────────────────────────────┘
```

**Key mobile constraints:**
- Header is a fixed 48px bar, not scrollable
- FilterBar is a fixed 44px bar, always visible (doesn't scroll with map)
- Map fills remaining vertical space: `calc(100dvh - 48px - 44px)` when sheet is hidden
- When bottom sheet is open, the backdrop prevents map interaction above the sheet
- ColorLegend is positioned bottom-right of the map viewport, ABOVE the sheet

### 2.2 Tablet (`768px – 1023px`) — Map + Collapsible Panel

```
┌──────────────────────────────────────────────────────────────┐
│  Header (z-50, h-48px)                                      │
│  [Logo] [ 🔍 Search associations...         ▼ ]   [RO|EN]   │
├──────────────────────────────┬───────────────────────────────┤
│  FilterBar (z-1000)          │                               │
│  [Cluj] [Bihor] [Brașov]     │        MAP VIEWPORT           │
│  ○ Toate ● Lac ○ Râuri       │                               │
│                              │           ┌──────┐            │
│                              │           │Legend│  (z-1000)  │
│                              │           └──────┘            │
├──────────────────────────────┤                               │
│  ┌──────────────────────┐    │                               │
│  │ WaterDetailSheet     │    │                               │
│  │                      │    │                               │
│  │ (side panel, 320px)  │    │                               │
│  │ collapsible via [×]  │    │                               │
│  │ or [‹] toggle        │    │                               │
│  └──────────────────────┘    │                               │
└──────────────────────────────┴───────────────────────────────┘
```

**Key tablet constraints:**
- AssociationSearch is inline (not fullscreen overlay) — dropdown below header bar
- Side panel is 320px wide; map fills the rest
- Panel has a collapse toggle: when collapsed, a narrow tab (48px) with a "‹" button remains
- ColorLegend sits bottom-right of map viewport (not inside panel)
- No backdrop on tablet/desktop — panel is a layout sibling, not an overlay

### 2.3 Desktop (`≥ 1024px`) — Map + Persistent Panel

```
┌──────────────────────────────────────────────────────────────┐
│  Header (z-50, h-56px)                                      │
│  [Logo] [ 🔍 Caută asociația...             ▼ ]   [RO|EN]   │
├──────────────────────────────┬───────────────────────────────┤
│  FilterBar (z-1000)          │                               │
│  [Cluj] [Bihor] [Brașov]     │        MAP VIEWPORT           │
│  ○ Toate ● Lac ○ Râuri       │                               │
│                              │           ┌──────┐            │
│                              │           │Legend│  (z-1000)  │
│                              │           └──────┘            │
├──────────────────────────────┤                               │
│  ┌──────────────────────┐    │                               │
│  │ WaterDetailSheet     │    │                               │
│  │                      │    │                               │
│  │ (side panel, 380px)  │    │                               │
│  │ always visible when  │    │                               │
│  │ water is selected.   │    │                               │
│  │ [×] closes selection │    │                               │
│  └──────────────────────┘    │                               │
└──────────────────────────────┴───────────────────────────────┘
```

**Key desktop constraints:**
- Wider header (56px) with generous search bar width (max 480px)
- Side panel is 380px wide, sticky, scrollable independently
- No collapse toggle needed — plenty of screen real estate
- When no water is selected, panel slot is hidden; map expands to full width with a smooth transition

---

## 3. Bottom Sheet Specification (Mobile Only)

The WaterDetailSheet on mobile uses a multi-snap-point bottom sheet with four states.

### 3.1 State Definitions

| State | Height (vh) | Height (px on 667px screen) | Backdrop | Map interaction | Trigger |
|-------|------------|----------------------------|----------|----------------|---------|
| **Hidden** | 0 (offscreen) | 0px | None | Full | `selectWater(null)` |
| **Collapsed** | ~10vh | ~64px | None | Full | Drag down from Peek |
| **Peek** | ~35vh | ~233px | Subtle (opacity 0.20) | Map visible above; pan OK, tap features OK | Map click (initial open) |
| **Expanded** | ~65vh | ~433px | Full (opacity 0.50) | Blocked (backdrop intercepts) | Drag up from Peek |

### 3.2 State Content per Sheet Height

#### Collapsed (64px, 10vh)

```
┌─────────────────────────────────────────────┐
│  ═══  Lacul Tarnița  [lac]  Județul Cluj  [×] │
└─────────────────────────────────────────────┘
```

- Drag handle (centered, 32px wide, 4px tall, grey)
- Water name (bold, 15px, truncate to 1 line)
- Subtype badge: small colored pill — "lac" (blue) or "râu" (teal)
- County name (13px, grey)
- Close button (×, 24px tap target, top-right)
- User can still pan/zoom the map fully

#### Peek (233px, 35vh)

```
┌─────────────────────────────────────────────┐
│  ═══  Lacul Tarnița                   [lac] │
│  Județul Cluj                        240 Ha │
│  ─────────────────────────────────────────  │
│  Sector: zona de acumulare                  │
│  ─────────────────────────────────────────  │
│  Asociația: Direcția Silvică Cluj           │
│  📞 0264 420 908                            │
└─────────────────────────────────────────────┘
```

- Drag handle (top)
- Water name (18px, bold)
- Subtype badge + county badge (inline)
- Size with unit (240 Ha / 35 km)
- Divider
- Sector description (limite) — max 3 lines, truncated with "…" if longer
- Association name
- Association phone number (tappable `tel:` link)
- Map is visible above the sheet; user can tap other water features to switch

#### Expanded (433px, 65vh)

```
┌─────────────────────────────────────────────┐
│  ═══  Lacul Tarnița                   [lac] │
│  Județul Cluj                        240 Ha │
│  ─────────────────────────────────────────  │
│  Sector:                                   │
│  zona de acumulare, baraj la ieșire,        │
│  malul stâng până la podul rutier           │
│  ─────────────────────────────────────────  │
│  Asociația:                                │
│  Direcția Silvică Cluj                      │
│  📞 0264 420 908                            │
│  📍 Strada Bartók Béla, Nr. 27, Cluj-Napoca │
│  🌐 cluj.rosilva.ro/                        │
│  ─────────────────────────────────────────  │
│  Referință:                                 │
│  Lista habitatelor piscicole... (HG...)     │
│  ─────────────────────────────────────────  │
│  [ Raportează o problemă ]                  │
│  [ × Închide ]                              │
└─────────────────────────────────────────────┘
```

- All fields from WaterDetailCard, no truncation
- Sector: full text, no line limit
- Association: full contact — phone, address, website (all tappable)
- Legal reference (referinta) — collapsible if longer than 2 lines
- "Raportează o problemă" button (outlined, secondary)
- "× Închide" button (text, subtle)
- Scrollable within the sheet if content exceeds 65vh
- Backdrop blocks all map interaction

### 3.3 Snap Points & Drag Behavior

```
        Expanded  ────  65vh  ────  drag down → Peek
           │
           │  drag up
           │
        Peek      ────  35vh  ────  drag down → Collapsed
           │                         drag up → Expanded
           │  drag down
           │
        Collapsed ────  10vh  ────  drag down → Hidden
           │                         drag up → Peek
           │  drag down past 5vh threshold
           │
        Hidden    ────   0vh
```

**Snap thresholds (percentage of drag distance):**

| From → To | Threshold | Behavior |
|-----------|-----------|----------|
| Expanded → Peek | 20% of sheet height dragged down (~87px) | Snaps to Peek |
| Expanded → Collapsed | 50% of sheet height dragged down fast (velocity > 0.3px/ms) | Snaps to Collapsed (rare, fast swipe) |
| Peek → Expanded | 25% of sheet height dragged up (~58px) | Snaps to Expanded |
| Peek → Collapsed | 30% of sheet height dragged down (~70px) | Snaps to Collapsed |
| Peek → Hidden | 60% of sheet height dragged down fast (velocity > 0.5px/ms) | Dismisses (selectWater(null)) |
| Collapsed → Peek | 30% of sheet height dragged up (~19px) | Snaps to Peek |
| Collapsed → Hidden | 30% of sheet height dragged down (~19px) | Dismisses (selectWater(null)) |

**Animation physics:**
- Spring animation: stiffness 300, damping 30 (snappy, no bounce)
- Duration: 250ms to settle at snap point
- On fast flings (velocity > 0.5px/ms): target the next/previous snap point based on direction

### 3.4 Backdrop Behavior

| Sheet State | Backdrop Opacity | Backdrop Tappable | Effect of Tapping Backdrop |
|-------------|-----------------|-------------------|---------------------------|
| Hidden | 0 | No (pointer-events: none) | — |
| Collapsed | 0 | No (pointer-events: none) | — |
| Peek | 0.20 | Yes (only above sheet area) | Selects another water if tap lands on a feature; otherwise no-op |
| Expanded | 0.50 | Yes (full) | Collapses sheet to Peek state |

**Backdrop specifics:**
- Color: `#000000` (black), with opacity varying per state
- Transition: `opacity 200ms ease-out`
- On Peek state: backdrop covers only the map area ABOVE the sheet, not the sheet itself. This lets the user tap map features visible above the sheet while slightly dimming them.
- On Expanded state: backdrop covers the entire viewport behind the sheet. Tapping anywhere on the backdrop collapses to Peek.
- Tapping map features on the visible portion above a Peek sheet calls `selectWater(newSlug)`, which replaces the current sheet content (no dismiss → re-open flicker — the sheet stays open and crossfades content).

### 3.5 Dismiss Triggers

The sheet returns to Hidden (`selectWater(null)`) when:

1. **Drag down past threshold** from Collapsed state (drag velocity > threshold OR drag distance > 30%)
2. **Close button (×)** tapped in any state
3. **ESC key** pressed (desktop keyboard)
4. **`selectWater(null)` called** from store (e.g., "Toate asociațiile" clears association → clears water if the water was association-filtered)

### 3.6 Sheet Content Transitions

When the user taps a different water feature while the sheet is already open:

```
Current water: "Lacul Tarnița" (Peek)
User taps "Someșul Rece" on the map
   │
   ▼
store.selectWater('somesul-rece')
   │
   ▼
Sheet stays at Peek height; content crossfades (200ms opacity 0 → opacity 1):
   - Water name, badges, county, size update
   - Sector text updates
   - Association info updates
   │
   ▼
No dismiss → re-open flicker. Smooth content swap.
```

### 3.7 Scrim / No-Scrim Decision

- **Collapsed state:** No scrim (backdrop). User must be able to pan the map behind the thin strip.
- **Peek state:** Subtle scrim (opacity 0.20) over the visible map area above the sheet. This signals "the map is still interactive but dimmed."
- **Expanded state:** Full scrim (opacity 0.50). The map is not interactive. Tapping the scrim collapses to Peek.

---

## 4. AssociationSearch Interaction Model

### 4.1 Mobile (`< 768px`): Icon → Fullscreen Overlay

```
┌────────────────────────────────┐
│  Header                         │
│  [Logo]          [🔍] [RO|EN]  │  ← magnifying glass icon
└────────────────────────────────┘
         │  user taps 🔍
         ▼
┌────────────────────────────────┐
│  [← Înapoi]                    │  ← back button
│  ─────────────────────────────  │
│  🔍 Caută asociația...         │  ← cmdk input, auto-focused
│  ─────────────────────────────  │
│  AJVPS Cluj              (46)  │
│  AJVPS Bihor             (32)  │
│  AJVPS Brașov            (28)  │
│  AJVPS Sibiu             (24)  │
│  Direcția Silvică Cluj   (18)  │
│  ...                            │
│  ─────────────────────────────  │
│  Toate asociațiile             │  ← clear selection
└────────────────────────────────┘
```

**Behavior:**
- Opens as a full-viewport overlay (z-2000, above everything including bottom sheet)
- Animate: slide down from top (200ms ease-out) or fade+scale (shadcn Command default)
- Input auto-focused on open — keyboard appears immediately
- Typing filters the list via cmdk's built-in fuzzy matching
- Selecting an association:
  1. Closes the overlay (slide up, 150ms)
  2. Calls `store.selectAssociation(slug)`
  3. Map recolors water features
  4. ColorLegend updates
  5. Bottom sheet stays in its current state (if open); if the selected water is no longer visible under the new association filter, the sheet dismisses
- Tapping "← Înapoi" or backdrop dismisses without changing selection
- Water count badge (e.g., "46") next to each association row
- "Toate asociațiile" at the bottom: clears selection → all waters shown in neutral blue

### 4.2 Tablet/Desktop (`≥ 768px`): Inline Dropdown

```
┌─────────────────────────────────────────────────────────────┐
│  Header                                                      │
│  [Logo]  [ 🔍 Caută asociația...           ▼ ]    [RO|EN]  │
└─────────────────────────────────────────────────────────────┘
                    │  user clicks / focuses
                    ▼
          ┌──────────────────────────────┐
          │ AJVPS Cluj             (46)  │
          │ AJVPS Bihor            (32)  │
          │ AJVPS Brașov           (28)  │
          │ ...                          │
          │ Toate asociațiile            │
          └──────────────────────────────┘
```

**Behavior:**
- Inline Command component in the header
- Opens as a popover/dropdown below the input (z-100, above header)
- Max height: 400px, scrollable if more items than fit
- Same cmdk filtering, same selection behavior
- Click outside / ESC closes the dropdown
- On tablet (768px-1023px): input max-width 280px; on desktop (≥1024px): max-width 480px
- Keyboard accessible: ↑ ↓ to navigate, Enter to select, Escape to close

---

## 5. Filter Placement

### 5.1 Mobile (`< 768px`): Horizontal Scrollable Row

```
┌──────────────────────────────────────────────────────┐
│  Județ: ← scroll → [Cluj] [Bihor] [Brașov] [Sibiu] → │
│  Tip:   [ Toate │ Lacuri │ Râuri ]                    │
└──────────────────────────────────────────────────────┘
```

**CountyFilter (top row):**
- Single row of chips, horizontally scrollable
- `overflow-x: auto; flex-wrap: nowrap; gap: 6px; padding: 8px 12px`
- Scrollbar hidden (`scrollbar-width: none` or `-webkit-scrollbar: none`)
- Scroll indicators: subtle gradient fade on right edge when more chips exist offscreen
- Each chip: `px-3 py-1.5 rounded-full text-sm` — selected: filled bg, deselected: outline
- "Toate județele" shown as a distinct chip at the start when nothing is selected
- Max ~6 chips visible at once; rest discovered by scrolling
- Tapping a chip: instant toggle via `store.toggleCounty(county)`
- CountyFilter is disabled (greyed out, chips not tappable) when `store.waters.length === 0`

**WaterTypeFilter (bottom row):**
- Segmented control: three pills in a single row
- `[ Toate │ Lacuri │ Râuri ]` — selected segment gets filled background
- Width: fits content, centered or left-aligned below the chips
- Calls `store.setWaterTypeFilter(type)`

**Interaction with map:**
- FilterBar is a fixed bar. It does NOT scroll with the map.
- Changing filters updates `useFilteredWaters()` → WaterFeatureLayer redraws
- If the currently selected water is filtered OUT by a new filter:
  - `selectWater(null)` is called automatically
  - Bottom sheet dismisses
  - Toast/notification: _"[N] ape afișate — apa selectată a fost filtrată"_

### 5.2 Tablet/Desktop (`≥ 768px`): Left Overlay Panel

```
┌─────────────────────────┐
│  Județ                  │
│  [Cluj] [Bihor] [Brașov]│  ← chips wrap to multiple rows
│  [Sibiu] [Mureș]        │
│                         │
│  Tip                    │
│  ○ Toate                │
│  ● Lacuri               │
│  ○ Râuri                │
└─────────────────────────┘
```

**Behavior:**
- Absolutely positioned top-left of the map viewport (z-1000)
- Background: white/glass-morphism (`bg-white/90 backdrop-blur-sm`)
- Border-radius: 12px, box-shadow: subtle
- County chips wrap to multiple rows (no horizontal scroll)
- Segmented control stacks vertically or horizontally depending on space
- Same instant toggle behavior as mobile
- Close/collapse button (chevron) to minimize the filter panel to a small icon (freeing map space)
- Collapse state persists in `localStorage`

---

## 6. ColorLegend Adaptation

### 6.1 Mobile (`< 768px`): Minimal, Collapsible

**Collapsed state (default on mobile):**

```
┌────────────┐
│ ■ ■ ▼      │  ← two colored dots + expand chevron (36×28px)
└────────────┘
```

- Bottom-right of map viewport, 8px from edges
- Semi-transparent background (`bg-black/60`), rounded
- Shows only colored dots (no labels) — compact, doesn't obscure map
- Tap to expand

**Expanded state (after tap):**

```
┌──────────────────┐
│ ■ Acoperit       │
│ ■ Neacoperit     │
│ ■ Vedere neutră  │  ← only when no association selected
│             [▲]  │  ← collapse
└──────────────────┘
```

- Shows colored squares + Romanian labels
- Semi-transparent background (`bg-black/70 text-white text-xs`)
- Auto-collapses after 5 seconds of no interaction
- Tap ▲ or tap outside to collapse

**Position when bottom sheet is open:**
- When sheet is at Peek state (35vh): legend moves UP so it sits just above the sheet's top edge (8px above sheet)
- When sheet is at Expanded state (65vh): legend is hidden (covered by backdrop + sheet)
- When sheet is at Collapsed state (10vh): legend stays at default position (bottom-right, 8px above the strip)

### 6.2 Tablet/Desktop (`≥ 768px`): Full, Always Visible

```
┌──────────────────┐
│ ■ Acoperit       │
│ ■ Neacoperit     │
│ ■ Vedere neutră  │  ← only when no association selected
└──────────────────┘
```

- Bottom-right of map viewport, 16px from edges
- White/glass-morphism background, subtle shadow
- Always shows labels (no collapse behavior needed — plenty of space)
- Font size: 14px
- When side panel is open, legend stays on the map side (doesn't overlap panel)

---

## 7. Interaction State Machine

### 7.1 Map Click → Sheet Update

```
Map click on water feature
   │
   ▼
store.selectWater(slug)
   │
   ├── Sheet currently Hidden ──→ animate to Peek (35vh), show content
   │
   ├── Sheet currently in any state ──→ stay at same height, crossfade content
   │
   └── No water at click point ──→ no-op (selectWater(null) NOT called — user may have
                                    mis-tapped; they can dismiss manually)
```

**Important:** Tapping an empty area of the map does NOT dismiss the sheet. This prevents accidental dismissal when the user intends to pan. The sheet only dismisses via:
- Drag down past threshold
- Close button (×)
- ESC key
- Selection/filter removing the current water

### 7.2 Filter Change → Sheet Update

```
User toggles a county chip or changes water type
   │
   ▼
Filter state changes → useFilteredWaters() recomputes
   │
   ├── Selected water still in filtered set ──→ WaterFeatureLayer redraws; sheet stays open
   │
   └── Selected water filtered OUT ──→ store.selectWater(null) called automatically
                                        Sheet animates to Hidden (250ms)
                                        Optional: brief toast notification
```

### 7.3 Association Change → Sheet Update

```
User selects new association in AssociationSearch
   │
   ▼
store.selectAssociation(newSlug)
   │
   ├── Selected water belongs to new association ──→ WaterFeatureLayer recolors (green);
   │                                                  sheet stays open
   │
   ├── Selected water does NOT belong to new association ──→ WaterFeatureLayer recolors
   │     (water turns grey); sheet stays open but shows the water as "Neacoperit"
   │
   └── "Toate asociațiile" selected ──→ WaterFeatureLayer shows all in blue (neutral);
                                          sheet stays open
```

### 7.4 Full Interaction Matrix

| Trigger | Current Sheet State | Result |
|---------|-------------------|--------|
| Tap water on map | Hidden | Open to Peek |
| Tap water on map | Collapsed / Peek / Expanded | Stay at current height, swap content |
| Tap empty map area | Any | No-op (no dismiss) |
| Drag sheet down (past threshold) | Collapsed | Dismiss to Hidden |
| Drag sheet down (past threshold) | Peek | Snap to Collapsed |
| Drag sheet down (small movement) | Expanded | Snap to Peek |
| Drag sheet up (past threshold) | Collapsed | Snap to Peek |
| Drag sheet up (past threshold) | Peek | Snap to Expanded |
| Tap × close button | Any | Dismiss to Hidden |
| Tap backdrop | Peek | No-op (map features still tappable) |
| Tap backdrop | Expanded | Collapse to Peek |
| Press ESC | Any | Dismiss to Hidden |
| Filter removes selected water | Any | Auto-dismiss to Hidden |
| "Toate asociațiile" selected | Any | Sheet stays open; water color resets |

---

## 8. Implementation Notes

### 8.1 Library Choice: vaul

The bottom sheet behavior is best implemented with **vaul** (the library that powers shadcn/ui's Sheet component), NOT a custom div. Reasons:

1. **Snap points** — vaul supports `snapPoints` prop natively: `snapPoints={[0.1, 0.35, 0.65]}` maps to Collapsed, Peek, Expanded.
2. **Drag handling** — vaul handles velocity-based snapping, threshold detection, and spring animations out of the box.
3. **Accessibility** — vaul manages focus trapping, ARIA attributes, and ESC-to-close.
4. **Already in node_modules** — shadcn/ui Sheet depends on vaul.

**Vaul snap points configuration:**

```typescript
// Conceptual — how vaul maps to our states
const SHEET_SNAP_POINTS = [0.1, 0.35, 0.65]; // Collapsed, Peek, Expanded
const SHEET_INITIAL_SNAP = 1;                 // index → Peek (0.35)

// vaul's activeSnapPoint index:
// 0 → Collapsed (10vh)
// 1 → Peek (35vh)
// 2 → Expanded (65vh)
```

**Backdrop opacity mapping to vaul's `activeSnapPoint`:**
- Index 0 (Collapsed): backdrop 0
- Index 1 (Peek): backdrop 0.20
- Index 2 (Expanded): backdrop 0.50

### 8.2 Detecting Breakpoints

Use Tailwind's responsive classes + a React hook for JavaScript-aware breakpoint logic:

```css
/* CSS-only: layout switching */
.map-shell {
  @apply relative h-[100dvh] w-full;
}
.sheet-container {
  @apply fixed inset-x-0 bottom-0 z-[1200]  /* mobile: bottom sheet */
         md:relative md:inset-auto md:z-auto; /* tablet+: side panel */
}
```

```typescript
// Hook for JS-aware breakpoint checks (e.g., vaul needs to know mobile vs desktop)
function useBreakpoint() {
  // tailwind responsive: md = 768px
  const [isMobile, setIsMobile] = useState(true);
  useEffect(() => {
    const mq = window.matchMedia('(max-width: 767px)');
    setIsMobile(mq.matches);
    const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);
  return { isMobile, isTablet: /* similar with 768-1023 */, isDesktop: /* >=1024 */ };
}
```

### 8.3 Avoiding Layout Shifts

- The bottom sheet uses `position: fixed; bottom: 0` + `transform: translateY(...)` — it does NOT affect the map's layout. The map always fills the viewport behind the sheet.
- The desktop side panel uses CSS Grid (`grid-template-columns: 1fr 380px`) — the map reacts to the panel's presence via a grid column, not via JS.
- Transitions between mobile and desktop layouts use `transition-all duration-300` on the grid.
- The ColorLegend position adjusts via CSS `bottom` value that accounts for the sheet height. On mobile, when a sheet is open at Peek (35vh), the legend's `bottom` becomes `calc(35vh + 8px)`. This is handled via a CSS custom property updated by vaul's `onSnapPointChange` callback.

### 8.4 Preventing Double-Tap Zoom

iOS Safari has a 300ms delay and double-tap-to-zoom behavior on un-styled elements. All interactive elements (chips, sheet, map features) must have:
- `touch-action: manipulation` on the map container (eliminates 300ms delay)
- `user-select: none` on filter chips and sheet handle
- The map itself needs `touch-action: pan-x pan-y pinch-zoom` to allow map gestures while preventing browser zoom on double-tap

### 8.5 Safe Area Insets (Notch / Home Indicator)

Modern iPhones have notches and home indicators that overlap the bottom sheet:

```css
.bottom-sheet {
  padding-bottom: env(safe-area-inset-bottom, 0px);
  /* Adds 34px on iPhone X+, 0 on devices without notch */
}
.filter-bar {
  padding-top: env(safe-area-inset-top, 0px);
  /* Prevents filters from being hidden behind notch on landscape iPhone */
}
```

---

## 9. CSS Custom Properties (Design Tokens)

To keep spacing and animation values consistent:

```css
:root {
  --sheet-collapsed-h: 10vh;
  --sheet-peek-h: 35vh;
  --sheet-expanded-h: 65vh;
  --sheet-z: 1200;
  --sheet-backdrop-z: 1100;
  --sheet-radius: 16px;
  --sheet-handle-width: 32px;
  --sheet-handle-height: 4px;
  --sheet-handle-color: #d4d4d8;      /* zinc-300 */
  --sheet-bg: #ffffff;
  --sheet-backdrop-color: #000000;
  --sheet-animation-duration: 250ms;
  --sheet-spring-stiffness: 300;
  --sheet-spring-damping: 30;

  --map-controls-z: 1000;
  --header-z: 50;
  --search-overlay-z: 2000;

  --mobile-header-h: 48px;
  --mobile-filter-h: 44px;
  --desktop-header-h: 56px;
  --desktop-panel-w: 380px;
  --tablet-panel-w: 320px;

  --legend-collapsed-size: 36px;
  --legend-bg: rgba(0, 0, 0, 0.6);
  --legend-text: #ffffff;
}
```

---

## 10. Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| **User rotates phone while sheet is at Peek** | Sheet stays at Peek. Heights are vh-based, so they scale. Content reflows. No state change. |
| **User opens AssociationSearch while sheet is open** | Search overlay covers everything (z-2000 > z-1200). Selecting association → overlay closes → sheet is still open behind it. |
| **User taps a water that has no association** (`asociatie: null`) | Sheet opens normally. Association section shows "Fără asociație" (No association). Contact fields hidden. Report button still visible. |
| **User taps a water that has no phone/address/website** | Those fields simply don't render. No "—" or "N/A" placeholder. |
| **User drags sheet while map is panning** | Sheet drag wins (vaul's gesture detection is stronger than Leaflet's). Map pan is cancelled. |
| **User opens sheet on a very short phone (320px height)** | Percentages still work: Peek = 35vh = 112px (still usable). Expanded = 65vh = 208px. Content scrolls. |
| **Data hasn't loaded yet and user taps map** | No-op. WaterFeatureLayer hasn't rendered. No click targets exist. |
| **User rapidly taps multiple water features** | Each tap calls `selectWater(newSlug)`. Sheet content updates to the last-tapped water. No animation queue buildup (use `useTransition` or debounce store updates at 50ms). |
| **Browser back button** | Should NOT dismiss the sheet. The sheet is UI state, not navigation. Use `history.replaceState` to avoid polluting browser history on sheet state changes. |
| **Offline / no JS** | Graceful degradation: map shows as a static image fallback (server-side). Sheet is a plain `<details>` element with water info from server-rendered data. Not part of this spec but noted for a11y. |

---

## 11. Verification Checklist

A reviewer should be able to confirm:

### Breakpoints & Layout
- [ ] Three clear breakpoints: mobile (<768px), tablet (768–1023px), desktop (≥1024px)
- [ ] Mobile: full-viewport map with bottom sheet + horizontal filter row
- [ ] Tablet: map + collapsible 320px side panel
- [ ] Desktop: map + 380px side panel
- [ ] `100dvh` used for viewport height; no layout jumps on mobile scroll

### Bottom Sheet States
- [ ] Four distinct states defined: Hidden, Collapsed, Peek, Expanded
- [ ] Heights: 0vh / ~10vh / ~35vh / ~65vh
- [ ] Each state has clear content rules (what's shown, what's truncated)
- [ ] Snap point thresholds documented
- [ ] Animation physics specified (spring, 250ms)

### Drag & Dismiss
- [ ] Drag up from Collapsed → Peek
- [ ] Drag up from Peek → Expanded
- [ ] Drag down from Expanded → Peek
- [ ] Drag down from Peek → Collapsed
- [ ] Drag down from Collapsed past threshold → Hidden (dismiss)
- [ ] Velocity-based snapping for fast flings
- [ ] × button, ESC, and backdrop-tap dismiss triggers defined

### Backdrop
- [ ] Backdrop opacity per state: 0 / 0 / 0.20 / 0.50
- [ ] Backdrop tap behavior per state (no-op, feature-tap, collapse)
- [ ] Backdrop transition: 200ms ease-out

### AssociationSearch
- [ ] Mobile: icon → fullscreen overlay (z-2000)
- [ ] Desktop: inline dropdown in header (z-100)
- [ ] cmdk filtering, water count badges, "Toate asociațiile" clear option
- [ ] Selecting association → map recolors, sheet stays open or dismisses if water filtered out

### Filters
- [ ] Mobile: horizontal scrollable chip row + segmented control
- [ ] Tablet/Desktop: left overlay panel with wrapping chips
- [ ] Filter change removes selected water → auto-dismiss sheet

### ColorLegend
- [ ] Mobile: collapsible (dots → labels), auto-collapse after 5s
- [ ] Position moves above sheet when sheet is open
- [ ] Tablet/Desktop: full labels, always visible

### Edge Cases
- [ ] Rotation: sheet stays at current state, vh scaling handles it
- [ ] Rapid taps: last-tapped water wins, no animation jank
- [ ] No-association water: graceful fallback
- [ ] Safe area insets accounted for
- [ ] Touch-action: manipulation on interactive elements

---

## 12. References to Other Design Docs

| Document | What it covers | How this doc relates |
|----------|---------------|---------------------|
| `ARCHITECTURE.md` | Tech stack, data model, routes | Uses same breakpoints and component names |
| `map-component-tree.md` | 12 components, file paths, z-index | This doc refines the responsive behavior summarized in Section 7 of that doc |
| `component_structure_plan.md` | Props, data flow, store design | This doc defines WHEN and HOW components appear/behave at each size |
| `data_model_proposal.md` | Water/Association types | Sheet content fields (sector, size, contact) come from the Water type |

---

## Appendix A: Quick Reference Card

```
MOBILE (<768px)
  Header:       48px, search=icon→overlay
  FilterBar:    44px, horizontal scroll chips + segmented control
  Map:          calc(100dvh - 48px - 44px)
  Sheet:        bottom sheet, 4 states (0/10/35/65vh)
  Legend:       collapsible dots, bottom-right, moves above sheet
  Backdrop:     only in Peek (0.20) and Expanded (0.50)

TABLET (768–1023px)
  Header:       48px, search=inline dropdown
  FilterBar:    left overlay panel, wrapping chips
  Map:          grid 1fr, side panel 320px (collapsible to 48px tab)
  Sheet:        right panel (not bottom sheet), scrollable
  Legend:       bottom-right, always visible, full labels

DESKTOP (≥1024px)
  Header:       56px, search=inline dropdown (wide)
  FilterBar:    left overlay panel
  Map:          grid 1fr, side panel 380px (persistent)
  Sheet:        right panel, scrollable
  Legend:       bottom-right, always visible, full labels
```
