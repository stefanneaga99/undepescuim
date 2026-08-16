# Dark Mode — Feasibility Verdict & Implementation Plan

**Task:** t_4fa4be4a (spike) · **Date:** 2026-08-16 · **Author:** plan-maker
**Status:** PLAN — awaiting review (review-required block)

---

## 0. Verdict (TL;DR)

**FEASIBLE. LOW RISK. Effort = S (small) for the core; the only open product decision is map tiles.**

The codebase is already ~80% wired for dark mode — it just has no switch:

- Tailwind **v4 class strategy** is already configured: `@custom-variant dark (&:is(.dark *))` in `globals.css:5`.
- The **`.dark` CSS-variable block is already fully written** (`globals.css:86-118`, all `oklch` values).
- **`dark:` utility classes already exist** across the app (`specii/page.tsx`, `permis/page.tsx`, and every shadcn/ui component: `button`, `badge`, `switch`, `input`, `textarea`, `tabs`, `select`, `checkbox`, `dropdown-menu`, `sheet-grabber`, `input-group`).
- **ARCHITECTURE.md §Layout Hierarchy already anticipates** `ThemeProvider? (optional: light/dark)` (line 387).

What's missing is only the *mechanism* to flip `.dark` on `<html>`: a theme provider, a toggle, and persistence. That is a well-trodden, ~1-file-ish change using **next-themes** (the standard for Next.js app router).

The **only genuinely open decision** is map tiles (Leaflet). Recommendation: ship dark UI over the existing light OSM tiles first, and treat a dark-tile variant as an optional phase 2.

---

## 1. Current state audit (verified in repo)

| Concern | State |
|---|---|
| Tailwind version | v4 (`@import "tailwindcss"`, `@tailwindcss/postcss` in `postcss.config.mjs`) |
| Dark variant | `@custom-variant dark (&:is(.dark *))` — **class strategy** (matches `.dark` ancestor) |
| Dark palette | `.dark { --background … --sidebar-ring }` fully populated (`globals.css:86-118`) |
| shadcn/ui | `radix-nova` style, `cssVariables: true` — all components use CSS vars + `dark:` fallbacks |
| `dark:` classes in app code | `specii/page.tsx` (badges + amber/teal callouts), `permis/page.tsx`, `sheet-grabber` — already present |
| ThemeProvider / toggle | **NONE** (`next-themes` not installed; `layout.tsx` has no provider) |
| `layout.tsx` | Server component, `LayoutProps<"/">` typed, static `html` className, **no `suppressHydrationWarning`** |
| Map tiles | OSM light: `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png` (`MapView.tsx:63`) |
| Map overlay panels (hardcoded light) | `FilterBar.tsx:60` `bg-white/90` · `ColorLegend.tsx:89` `bg-white/90` |
| Map feature colors (hardcoded hex) | `src/utils/colors.ts` (blue/green/grey/orange/teal/violet) — tuned for light tiles |
| E2E assertion to flip | `docs/e2e-test-plan.md:152` "assert **no** theme toggle is rendered" |

### 1.1 Hardcoded surfaces that need attention (grep of `bg-white|bg-black|bg-zinc|bg-slate|bg-gray|#fff`)

| File:line | Class | Dark handling |
|---|---|---|
| `map/FilterBar.tsx:60` | `bg-white/90` (desktop filter panel) | **needs** `dark:bg-neutral-900/90` (or `dark:bg-card/90`) |
| `map/ColorLegend.tsx:89` | `bg-white/90` (desktop legend) | **needs** dark variant |
| `map/ColorLegend.tsx:59` | `bg-black/60 text-white` (mobile pill) | OK in both (semi-transparent black) |
| `ui/sheet.tsx:40`, `ui/dialog.tsx:42` | `bg-black/10` (scrim) | OK; optional deepen to `/30` in dark |
| `waters/WaterDetailSheet.tsx:117`, `associations/AssociationDetailSheet.tsx:90` | `bg-black` (scrim) | OK |
| `ui/sheet-grabber.tsx:25` | `bg-zinc-300 dark:bg-zinc-600` | **already dark-aware** ✓ |
| `waters/WaterDetailCard.tsx:65` | `bg-slate-100 text-slate-600` badge | minor — add `dark:bg-slate-800 dark:text-slate-300` |
| `specii/page.tsx:51` | `bg-slate-100 … dark:bg-slate-800 dark:text-slate-300` | **already dark-aware** ✓ |

Leaflet's own controls (zoom `+/-`, attribution) come from `leaflet/dist/leaflet.css` and stay white in dark mode — a cosmetic 3-line override covers it (see §5.5). Not blocking.

---

## 2. Approach: next-themes vs manual

### Recommendation: **next-themes v0.4.6** (latest)

| | next-themes | manual (Zustand/useState + inline script) |
|---|---|---|
| SSR/hydration safety | built-in (`suppressHydrationWarning` + auto-injected head script) | you write the no-FOUC script yourself |
| No-FOUC | **auto-injects** a minified script into `next/head` that sets `.dark` on `<html>` before first paint | hand-rolled inline script |
| Persistence | localStorage (`theme` key) + `prefers-color-scheme` via `enableSystem` + `defaultTheme="system"` | you implement + test |
| `attribute="class"` | native — drops `.dark` on `<html>`, exactly matching the existing variant | you implement |
| Size / maintenance | ~1 KB minzip, MIT, 6.3k★, React 19 / Next 16 compatible | n/a |

Rationale: next-themes is the de-facto standard, it matches the existing `@custom-variant dark (&:is(.dark *))` + `.dark` block one-to-one (`attribute="class"`), and it eliminates the two hard parts (hydration mismatch + theme flash) that a hand-rolled provider would have to re-solve. The project already uses Zustand for *map state*, but theme is a different problem (must mutate `<html>` before hydration); next-themes is purpose-built for it.

**Note on the task's "no-FOUC inline script" point:** with next-themes there is *no manual inline script to write* — the `ThemeProvider` injects it automatically (confirmed in the README: "ThemeProvider automatically injects a script into next/head … the page will not flash"). In `next dev` a flash may still appear; production builds do not flash.

---

## 3. Tailwind v4 dark variant — already correct

`globals.css:5`:

```css
@custom-variant dark (&:is(.dark *));
```

This is the **class strategy** (`dark:` variants match when an ancestor has `.dark`), not the `prefers-color-scheme` media strategy. next-themes with `attribute="class"` toggles `.dark` on `<html>`, so every existing `dark:` utility and the `.dark` variable block activate with zero CSS changes. **No Tailwind config change needed** (v4 has no `tailwind.config`; the variant is declared in CSS, which is already done).

---

## 4. Theme surfaces — coverage matrix

| Surface | Mechanism | Work needed |
|---|---|---|
| Header / filter bars | `bg-background/95` (CSS var) | none (auto) |
| Hamburger menu / sheets / dialogs / popovers / dropdowns | shadcn `radix-nova` CSS vars + `.dark` block | none (auto) |
| `/specii` + `/permis` pages | `dark:` classes already present | none (auto) |
| Report form (Dialog + inputs + radios) | shadcn vars | none (auto) |
| Map overlay panels (FilterBar desktop, ColorLegend desktop) | hardcoded `bg-white/90` | **edit 2 files** (add `dark:` variant) |
| WaterDetailCard "type" badge | `bg-slate-100` | minor 1-line edit |
| Leaflet zoom/attribution controls | library CSS (white) | optional 3-line CSS override |
| **Map tiles** | OSM light tiles | **decision — see §7** |

Conclusion: UI chrome is essentially free; the only real work is the provider+toggle and the two map-overlay panels.

---

## 5. Implementation plan (step-by-step, exact files)

### Step 1 — Install next-themes

```bash
cd /home/stefan/undepescuim && npm install next-themes
```

Adds `"next-themes": "^0.4.6"` to `dependencies`.

### Step 2 — ThemeProvider in root layout

`src/app/layout.tsx` (server component stays server — `ThemeProvider` is a client component and can be imported directly):

```tsx
import type { Metadata } from "next";
import { ThemeProvider } from "next-themes";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

// ... fonts + metadata unchanged ...

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="ro"
      suppressHydrationWarning   // ← REQUIRED: next-themes mutates <html> class
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <ThemeProvider
          attribute="class"          // matches @custom-variant dark (&:is(.dark *))
          defaultTheme="system"      // first visit → prefers-color-scheme
          enableSystem               // allow "system" as an explicit choice
          disableTransitionOnChange  // avoid theme-change color "morph" animation
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
```

> `attribute="class"` + `defaultTheme="system"` + `enableSystem` give the persistence + system-preference behaviour requested in the task with no extra code. localStorage key defaults to `theme` (override with `storageKey` if desired).

### Step 3 — ThemeToggle component (new file)

`src/components/layout/ThemeToggle.tsx`:

```tsx
'use client';

import { useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';
import { useTheme } from 'next-themes';
import { Button } from '@/components/ui/button';

/**
 * Sun/Moon toggle in the header (near the RO badge). Uses next-themes
 * resolvedTheme (not theme) so "system" renders the correct icon.
 * Mounted guard prevents the server/client icon mismatch (next-themes
 * returns undefined until mount).
 */
export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const isDark = resolvedTheme === 'dark';

  return (
    <Button
      variant="ghost"
      size="icon-sm"
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
      aria-label={isDark ? 'Treci la tema luminoasă' : 'Treci la tema întunecată'}
      title={isDark ? 'Tema luminoasă' : 'Tema întunecată'}
      suppressHydrationWarning
    >
      {mounted ? (isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />) : (
        <Moon className="h-5 w-5" />
      )}
    </Button>
  );
}
```

> Decision: a two-state toggle (light ⇄ dark, "system" as the initial default) rather than a 3-way menu, to keep the header minimal (the RO badge is small). If a "System" option is wanted later, swap `Button` for a `DropdownMenu` with Light/Dark/System.

### Step 4 — Mount the toggle in the header

`src/components/layout/Header.tsx` — insert `<ThemeToggle />` in the right-side `<nav>` (or next to the RO badge). Suggested placement: immediately before the RO badge `<span>`:

```tsx
      <nav className="flex shrink-0 items-center gap-1.5">
        {/* ... existing Permis/Specii links ... */}
      </nav>

      <ThemeToggle />   // ← add here (shrink-0, sits left of RO badge)

      <span
        className="shrink-0 rounded-md border px-2 py-0.5 text-xs font-semibold text-muted-foreground"
        title="Limba site-ului — EN în curând"
      >
        RO
      </span>
```

Import: `import { ThemeToggle } from '@/components/layout/ThemeToggle';`

### Step 5 — Surface polish (the only 3 real edits)

**5.1** `src/components/map/FilterBar.tsx:60` — desktop filter panel:

```tsx
className="absolute left-3 top-3 z-[1000] hidden max-h-[calc(100dvh-80px)] max-w-[280px] flex-col gap-2.5 overflow-y-auto rounded-xl border bg-white/90 p-3 shadow-md backdrop-blur-sm md:flex dark:bg-neutral-900/90"
```

**5.2** `src/components/map/ColorLegend.tsx:89` — desktop legend:

```tsx
className="hidden flex-col gap-1.5 rounded-lg border bg-white/90 px-3 py-2 text-xs shadow-md backdrop-blur-sm md:flex dark:bg-neutral-900/90"
```

**5.3** `src/components/waters/WaterDetailCard.tsx:65` — type badge:

```tsx
<Badge variant="outline" className="bg-slate-100 text-[10px] uppercase tracking-wide text-slate-600 dark:bg-slate-800 dark:text-slate-300">
```

**5.4 (optional)** `src/app/globals.css` — Leaflet control dark override (append after the Leaflet block):

```css
.dark .leaflet-bar a,
.dark .leaflet-control-attribution {
  background: oklch(0.205 0 0);
  color: oklch(0.985 0 0);
  border-color: oklch(1 0 0 / 10%);
}
```

### Step 6 — Flip the E2E assertion

`docs/e2e-test-plan.md:152` (and the summary at lines 19-20, and §495) — change:

```markdown
| Dark mode | assert **no** theme toggle is rendered (dark mode not implemented) |
```

to:

```markdown
| Dark mode | theme toggle rendered in header; clicking it toggles `.dark` on `<html>` and persists across reload (localStorage `theme`) |
```

The spec itself lives in `tests/e2e/specs/` (currently empty — the plan doc is the source of truth until the specs are written). Suggested Playwright assertions for when the spec lands:

```ts
// toggle exists and is reachable on all three viewports
const toggle = page.getByRole('button', { name: /tema/i });
await expect(toggle).toBeVisible();
// clicking toggles the class on <html>
await toggle.click();
await expect(page.locator('html')).toHaveClass(/dark/);
// persisted: reload keeps dark
await page.reload();
await expect(page.locator('html')).toHaveClass(/dark/);
```

---

## 6. Persistence + system preference (how it's satisfied)

| Requirement | Mechanism |
|---|---|
| Persist user's choice | next-themes writes `theme` to `localStorage` (`storageKey` default) |
| Respect system pref on first visit | `defaultTheme="system"` + `enableSystem` → reads `prefers-color-scheme` when no stored value |
| No flash on reload | next-themes auto-injected `<head>` script sets `.dark` before first paint |
| Hydration safety | `suppressHydrationWarning` on `<html>`; `mounted` guard in toggle |

No manual localStorage reads/writes or `matchMedia` listeners are required anywhere in app code.

---

## 7. Map tiles — the one real tradeoff

The Leaflet base layer is light OSM tiles. Dark tiles would look cohesive but carry real cost.

| Option | Effort | Pros | Cons |
|---|---|---|---|
| **A. Keep light OSM tiles + dark UI** (recommended for phase 1) | 0 | Zero work; feature colors (`colors.ts`) stay legible; maps are conventionally light | Bright map inside dark chrome at night; not fully "dark" |
| **B. CartoDB Dark Matter tiles** (`dark_all`) | M (2-4 h) | Truly dark, free raster tiles | Feature colors in `colors.ts` are tuned for light tiles and **must be re-tuned** (brightened) for dark; tile URL must be theme-aware; extra CARTO attribution; needs contrast verification |
| C. CSS invert filter on tiles | S | One-liner | Produces wrong/muddy colors (water→orange), breaks semantic color coding — **rejected** |

### CartoDB Dark Matter facts (verified)

- Free public raster basemap (CARTO), attribution required (`© OpenStreetMap, © CARTO`).
- URL: `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png`, subdomains `abcd`.
- Variants available: `dark_all`, `dark_nolabels`, `dark_only_labels` (label separation useful if markers must stay legible).

### If dark tiles are adopted (phase 2 — optional, M)

1. Make the `TileLayer` theme-aware in `src/components/map/MapView.tsx` — read theme via a small `useTheme()` call (MapView is already `'use client'`) and swap the `url` + `attribution`:

```tsx
import { useTheme } from 'next-themes';
// inside MapView:
const { resolvedTheme } = useTheme();
const url = resolvedTheme === 'dark'
  ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
  : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
const attribution = resolvedTheme === 'dark'
  ? '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
  : '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';
```

> `useTheme` returns `undefined` on first render → guard against a flash of wrong tiles, or keep the light URL until `resolvedTheme` resolves (same `mounted` pattern as the toggle). The `TileLayer` `key`/`url` change forces react-leaflet to swap tiles.

2. Re-tune `src/utils/colors.ts` for dark tiles: the palette is a set of `const` hex strings consumed by `getFeatureStyle` etc. Refactor to a `getPalette(isDark)` (or two exported palettes) so neutrals/feature colors are brightened on dark tiles. Verify orange focus (`#f97316`), violet bbox dots (`#8b5cf6`), teal uncontracted (`#14b8a6`) contrast on `dark_all`.

3. Add a `dark:` override for the user-position dot if its `#fff` border/blue pulse reads poorly on dark tiles.

**Recommendation:** ship **Option A** in phase 1. Dark UI + light map is an accepted, common pattern (Google Maps, Citymapper keep light base layers in dark UIs), and it defers the only M-sized chunk. Revisit Option B only if a dark map is explicitly wanted after the theme system lands.

---

## 8. Effort estimate

| Chunk | Size | Est. | Notes |
|---|---|---|---|
| next-themes install + provider + `suppressHydrationWarning` | S | 15 min | ~2 files |
| ThemeToggle + header mount | S | 30 min | 2 files |
| Surface polish (FilterBar, ColorLegend, WaterDetailCard, Leaflet CSS) | S | 30 min | 3-4 tiny edits |
| E2E doc flip (+ spec when written) | S | 15 min | 1 doc edit |
| **Phase 1 total (dark UI, light tiles)** | **S** | **~1-2 h** | + review/QA |
| Phase 2: dark map tiles (tiles + palette + contrast) | **M** | 2-4 h | optional, separate task |

---

## 9. Risks & mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Hydration mismatch (theme undefined on server) | Low | `suppressHydrationWarning` on `<html>`; `mounted` guard in toggle (next-themes standard pattern) |
| Theme flash (FOUC) | Low | next-themes auto-injected head script (dev may flash; prod does not) |
| Map tile/UI inconsistency | Low (phase 1) | Defer dark tiles; light map over dark chrome is acceptable and preserves feature-color semantics |
| Map feature colors illegible if dark tiles added naively | Med (phase 2 only) | Separate phase-2 task: theme-aware palette + contrast test |
| shadcn components not dark-ready | **None** | All use CSS vars + `.dark` block already present; `dark:` fallbacks already in source |
| Leaflet controls stay white | Cosmetic | Optional 3-line CSS override (§5.4) |
| E2E regression | Low | Flip the single "no toggle" assertion; toggle name stable via `aria-label` |
| `disableTransitionOnChange` flashes on page load (React hydration of class) | Low | Standard; if a flash on first client nav appears, keep prop or accept — cosmetic |

---

## 10. Verification steps

```bash
cd /home/stefan/undepescuim

# type-check + lint
npx tsc --noEmit
npm run lint

# unit tests (should be unaffected)
npm run test

# build (catches the next-themes server/client split)
npm run build

# manual smoke
npm run dev   # then: toggle in header → html.dark flips; reload → persists;
              # filter panel + legend flip to dark; /specii + /permis render dark
```

E2E (once the flipped spec lands): `npm run test:e2e:smoke` on all three viewports (mobile 390, tablet 768, desktop 1280).

---

## 11. Files touched (summary)

| File | Change |
|---|---|
| `package.json` | add `next-themes` |
| `src/app/layout.tsx` | add `suppressHydrationWarning` + `<ThemeProvider>` |
| `src/components/layout/ThemeToggle.tsx` | **new** |
| `src/components/layout/Header.tsx` | mount `<ThemeToggle />` |
| `src/components/map/FilterBar.tsx` | `dark:` variant on desktop panel |
| `src/components/map/ColorLegend.tsx` | `dark:` variant on desktop legend |
| `src/components/waters/WaterDetailCard.tsx` | `dark:` variant on type badge |
| `src/app/globals.css` | (optional) Leaflet control dark override |
| `docs/e2e-test-plan.md` | flip the dark-mode assertion |

*(Phase 2, if approved: `src/components/map/MapView.tsx` + `src/utils/colors.ts`.)*
