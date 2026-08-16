# Offline / PWA Feasibility & Implementation Plan (F6)

**Date:** 2026-08-16
**Author:** plan-maker (t_9a813772 — SPIKE)
**Parent:** F6 roadmap item (LATER); follows E2E spike t_30cc75ff which flagged PWA as out-of-scope (no SW exists)
**Status:** Feasibility verdict + implementation plan — NO implementation done (spike only)

---

## 0. Verdict

**FEASIBLE — recommend "PWA light" (installable + offline data + cached visited tiles), with one hard scope correction to ARCHITECTURE §8.**

- **Service worker:** Serwist (`@serwist/next` 9.5.12). `next-pwa` is abandoned (last publish 2022-08-23, no Next 16 support). Serwist peer-depends on `next >=14` — Next 16.3 is covered.
- **Data JSON (≈6 MB gzip):** fully cacheable, network-first. No blocker.
- **Map tiles:** OSM policy explicitly **prohibits offline/prefetch use** of `tile.openstreetmap.org`. Only *re-visits of tiles the user actively viewed* may be served from cache (≥7-day TTL). A "download area for offline" button is **not permitted**. True full-offline maps require a self-hosted/vector provider (Protomaps `.pmtiles`), which is a separate LATER item.
- **Installability:** standard `manifest` + icons + iOS meta; no blockers.
- **Effort: S** (≈1 session / 1–2 h) for the compliant "PWA light"; the full-offline tile tier is a separate M.

Everything below is grounded in the live repo (`~/undepescuim`) and primary sources (OSM Tile Usage Policy, Serwist 9.5.12 type definitions, npm registry).

---

## 1. Current state (measured)

| Fact | Value | Implication |
|------|-------|-------------|
| Framework | Next.js 16.3.0 app router, React 19.2.8, serverless on Vercel | Serwist supported; **not** static export (`/api/report` needs serverless) |
| Data load | `MapShell` → `useMapStore.loadData()` → 5× `fetch()` in `Promise.all` | SW intercepts these fetches cleanly; no bundling changes needed |
| Files fetched | `associations.json` (44 KB), `waters.json` (37 MB / 5.6 MB gz), `uncontracted_rivers.json` (2.3 MB / 0.5 MB gz), `uncontracted_lakes.json` (3.2 MB / 0.7 MB gz), `counties.geojson` (224 KB / 0.1 MB gz) | ≈ **6.9 MB gzip** total — comfortably under Cache Storage quota |
| Tile URL | `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png` (legacy subdomains) | Policy §1 now wants the single host, no subdomain — minor fix |
| SW / manifest / icons | none (`public/` has no manifest.json, no /icons/, no sw.ts) | greenfield |
| Freshness source | none — `refresh-data.mjs` writes data but no timestamp file | must add one (see §6) |
| Routes | `/` (map), `/specii`, `/permis` + `POST /api/report` | app shell = 3 documents; `/api/report` must be excluded from SW |
| CDN headers | `vercel.json`: `/data/*` max-age=86400; `/_next/static/*` immutable | SW data revalidation is bounded by 1-day CDN cache; sw.js needs its own no-cache rule |

Measured OSM tile response headers (2026-08-16): `cache-control: max-age=524522` (~6 d) + `stale-while-revalidate=604800` (7 d) + `stale-if-error=604800`; ETag present.

---

## 2. Findings that correct ARCHITECTURE §8

1. **next-pwa → Serwist.** §8 already said "via serwist" as a footnote; this confirms it. `next-pwa` 5.6.0 is dead (2022). Serwist is the maintained successor.
2. **30-day tile TTL is wrong.** §8.3 proposed `maxAgeSeconds: 30 days` for tiles. The OSM policy §3.2 requires *honouring server caching headers* (the server sends ~6 d + 7 d stale-while-revalidate). A 30-day client TTL both violates "honour headers" and risks serving stale tiles past what OSM authorises. **Use 7 days.**
3. **No "download for offline" / bulk prefetch.** §8.7's "pre-cache area" framing and any "Save area" feature are **prohibited** by policy §4 on `tile.openstreetmap.org` (enforced by blocking). Offline map = cache of what the user *already browsed*, nothing more.
4. **The `globDirectory: "out"` config in §8.6 is the static-export path** and no longer applies. `@serwist/next` on a serverless build precaches from the Next build manifest automatically — no `globDirectory`/`globPatterns` needed.
5. **`manifest.json` → `src/app/manifest.ts`.** Next 16 app-router idiom is `MetadataRoute.Manifest` (typed, works with `metadata`/`viewport` exports), rather than a hand-written `public/manifest.json`. Either works; the typed route is preferred.
6. **Drop the `{s}.` subdomain** in `MapView.tsx` (policy §1: "other subdomains … may be slower or withdrawn"). Also consider adding a "Report a map issue" link and a published contact email (policy "should" items).
7. **Serwist `runtimeCaching.handler` must be a strategy *instance*** (`new CacheFirst({…})`), not a string name — verified against Serwist 9.5.12 `RuntimeCaching` type (`handler: RouteHandler`, where `Strategy implements RouteHandlerObject`).

## 3. Recommended architecture — cache tiers (concrete)

Three tiers + one exclusion, all in `src/app/sw.ts`:

| Tier | What | Strategy | Cache name | Limits |
|------|------|----------|-----------|--------|
| App shell | precached build assets (JS/CSS/fonts/HTML) | Precache (revisioned) | `serwist-precache` | auto |
| Data | `/data/*.json`, `/data/*.geojson` | Network-first (4 s timeout) → cache fallback | `app-data` | 20 entries, 7 d |
| Map tiles | `tile.openstreetmap.org` (visited only) | Cache-first | `osm-tiles` | 1000 entries, 7 d |
| — | `POST /api/report` | **not cached** (excluded) | — | — |

Full `sw.ts` (verified against Serwist 9.5.12 exports):

```ts
// src/app/sw.ts
import { defaultCache } from "@serwist/next/worker";
import type { PrecacheEntry, SerwistGlobalConfig } from "serwist";
import {
  CacheFirst, NetworkFirst, ExpirationPlugin,
  CacheableResponsePlugin, Serwist,
} from "serwist";

declare global {
  interface WorkerGlobalScope extends SerwistGlobalConfig {
    __SW_MANIFEST: (PrecacheEntry | string)[] | undefined;
  }
}
declare const self: ServiceWorkerGlobalScope;

const DAY = 24 * 60 * 60;

const serwist = new Serwist({
  precacheEntries: self.__SW_MANIFEST,
  skipWaiting: true,
  clientsClaim: true,
  navigationPreload: true,
  disableDevLogs: true,
  runtimeCaching: [
    {
      // OSM raster tiles — ONLY tiles the user already viewed. Cache-first,
      // 7-day TTL to honour OSM Tile Usage Policy §3.2 (server sends ~6d + 7d
      // stale-while-revalidate). DO NOT extend past 7d; no prefetch/offline
      // download (policy §4 prohibits it).
      matcher: ({ url }) => url.hostname === "tile.openstreetmap.org",
      handler: new CacheFirst({
        cacheName: "osm-tiles",
        plugins: [
          new ExpirationPlugin({ maxEntries: 1000, maxAgeSeconds: 7 * DAY }),
          new CacheableResponsePlugin({ statuses: [200] }),
        ],
      }),
    },
    {
      // Static data — fresh-first, fall back to cache when offline.
      matcher: ({ url, sameOrigin }) =>
        sameOrigin && url.pathname.startsWith("/data/"),
      handler: new NetworkFirst({
        cacheName: "app-data",
        networkTimeoutSeconds: 4,
        plugins: [
          new ExpirationPlugin({ maxEntries: 20, maxAgeSeconds: 7 * DAY }),
          new CacheableResponsePlugin({ statuses: [200] }),
        ],
      }),
    },
    ...defaultCache,
  ],
  fallbacks: {
    entries: [
      {
        url: "/",
        matcher({ request }) {
          return request.mode === "navigate";
        },
      },
    ],
  },
});

serwist.addEventListeners();
```

`/api/report` is a POST → the default handler (network-only for non-GET) leaves it untouched; no explicit rule needed, but do not add a broad `/api/` cache rule.

### next.config.ts

```ts
import type { NextConfig } from "next";
import withSerwistInit from "@serwist/next";

const withSerwist = withSerwistInit({
  swSrc: "src/app/sw.ts",
  swDest: "public/sw.js",
  // serverless build: precache manifest comes from the Next build manifest.
  // (ARCHITECTURE §8.6's globDirectory:"out" was the static-export path —
  // not used here because /api/report requires serverless.)
});

const nextConfig: NextConfig = {
  transpilePackages: ["react-leaflet"],
  allowedDevOrigins: ["172.17.0.1", "*.172.17.0.1"],
  // NOTE: still NO `output: "export"` — see existing comment (F3 report route).
};

export default withSerwist(nextConfig);
```

Add to `.gitignore`: `public/sw.js`, `public/sw.js.map`, `public/swe-worker*.js` (Serwist build artifacts are generated, not committed).

`tsconfig.json`: add `"webworker"` to `compilerOptions.lib`, `"@serwist/next/typings"` to `compilerOptions.types`, and `"public/sw.js"` to `exclude`.

### SW registration (client)

Serwist needs a client-side registration. Minimal approach in the root layout's body (client component):

```tsx
// src/components/pwa/ServiceWorkerRegister.tsx
"use client";
import { useEffect } from "react";

export function ServiceWorkerRegister() {
  useEffect(() => {
    if ("serviceWorker" in navigator && process.env.NODE_ENV === "production") {
      navigator.serviceWorker.register("/sw.js", { updateViaCache: "none" });
    }
  }, []);
  return null;
}
```

Render `<ServiceWorkerRegister />` in `src/app/layout.tsx` `<body>`. `updateViaCache: "none"` forces the browser to revalidate `sw.js` itself (critical so a new deploy's SW is picked up).

**Vercel header for sw.js:** add to `vercel.json` headers a `source: "/sw.js"` with `Cache-Control: no-cache` (do NOT let it inherit any immutable rule). Optionally also `/sw.js` -> `Service-Worker-Allowed: /`.

## 4. Offline UX promise (realistic)

**What works offline after one online visit (the "PWA light" promise):**

1. **App shell** — the whole UI (header, filters, sheets, `/specii`, `/permis`) boots offline from precache.
2. **All data** — associations, waters, uncontracted, counties load from `app-data` cache. The entire national dataset (all 41 counties, ~426+ waters + uncontracted) is already loaded in one shot, so filters/search/detail cards/geolocation *all* work offline.
3. **Visited map tiles** — areas the user panned/zoomed while online render from `osm-tiles` cache for up to 7 days. **Unvisited areas show blank/grey tiles** (Leaflet's default for a failed tile) — this is expected and policy-compliant; add a graceful `tileerror` handler to dim the tile instead of erroring.

**What does NOT work offline (by design, not omission):**

- Fetching tiles for areas never viewed (grey tiles until back online).
- The `/api/report` form (submission needs network; queue/retry is out of scope for F6 — note in UX copy that reports need connectivity).

**Explicit non-goal:** "Download region for offline" / full-country offline tiles. This requires a provider that allows prefetch — **Protomaps `.pmtiles`** (self-host a single ~100 MB `.pmtiles` for Romania via Vercel/static host) or MapTiler free tier. That is a **separate LATER item**; ARCHITECTURE §8.7 already gestures at it. Document it as the upgrade path, don't build it now.

Offline states to handle (mirrors §8.4):
- **Online, fresh** — network-first data; cache tiles+data.
- **Offline, cached** — banner: "Fără conexiune — date din <date>" (offline, data as of <date>).
- **Offline, never visited** — app shell still loads (data cache may be empty on first-ever offline launch): show empty-state "Prima utilizare necesită conexiune la internet."

Detect offline via `navigator.onLine` + `online`/`offline` events, and via SW `fetch` fallback (data actually served from cache). The banner is a small client component in the Header.

## 5. Installability (manifest + icons + iOS)

**Manifest** via `src/app/manifest.ts`:

```ts
import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "UndePescuim",
    short_name: "UndePescuim",
    description: "Harta apelor de pescuit din România — Romanian fishing waters map",
    start_url: "/",
    scope: "/",
    display: "standalone",
    background_color: "#ffffff",
    theme_color: "#3b82f6",
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
      { src: "/icons/icon-512-maskable.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  };
}
```

**Icons** (generate from the existing fish logo concept, one-off):
- `public/icons/icon-192.png`, `icon-512.png`, `icon-512-maskable.png` (safe-zone padded), `apple-touch-icon.png` (180×180).
- No icons exist today; a tiny `scripts/gen-icons.mjs` using `sharp` (already a transitive dep of Next) can produce all four from one source SVG.

**Metadata** in `src/app/layout.tsx`: add `export const viewport: Viewport = { themeColor: "#3b82f6" }` and `appleWebApp: { capable: true, statusBarStyle: "default", title: "UndePescuim" }` on the `Metadata` object.

**iOS caveat:** no `beforeinstallprompt` on Safari/iOS — install is "Share → Add to Home Screen". The custom install banner (ARCHITECTURE §8.5) only fires on Android/Chromium; gate it accordingly (`beforeinstallprompt` event, dismiss for 7 days via localStorage).

## 6. "Last updated" indicator (data freshness — F6 acceptance)

Add a build-time freshness file so the UI can show when the data was last updated, and the offline banner can say "data as of <date>".

**Primary (build-time, recommended):** `scripts/gen-meta.mjs` runs as a `prebuild` step and writes `public/data/meta.json`:

```js
// scripts/gen-meta.mjs  (run via `node scripts/gen-meta.mjs` in "prebuild")
import { execSync } from "node:child_process";
import { writeFileSync } from "node:fs";

const iso = (() => {
  try {
    return execSync('git log -1 --format=%cI -- public/data', { encoding: "utf8" }).trim();
  } catch { return new Date().toISOString(); }
})();
writeFileSync("public/data/meta.json", JSON.stringify({ generatedAt: new Date().toISOString(), dataUpdatedAt: iso }));
```

`package.json`: `"prebuild": "node scripts/gen-meta.mjs"`.

Why build-time: it's always in sync with whatever is actually deployed (data changes land via git → Vercel deploy), and `git log -- public/data` is the single source of truth across the manual `fix_*.py` edits *and* the `refresh-data.mjs` workflow. Fallback to `Date.now()` when git is unavailable.

**Optional (refresh-time):** also have `refresh-data.mjs` write `last-refreshed.json` (ISO + source run) as a "when the scraper last actually ran" signal for the workflow log. Not required for the UI.

**UI:** fetch `/data/meta.json` in the same `loadData()` pass (already network-first via SW). Render "Date actualizate: 12 aug 2026" in the Header (or a Footer). Reuse the value for the offline banner.

## 7. Effort estimate & risks

**Effort: S** (one executioner session, ~1–2 h). Rationale: Serwist is a documented drop-in, the app is a single-page map, data is already `fetch()`-based, and each tier is a ~10-line rule. The only genuinely new surface is icons + two small UI components + a build-time meta script. A full manual Android + iOS + DevTools-offline test pass adds ~30–45 min and is what separates "works on paper" from "shipped".

| Risk | Impact | Mitigation |
|------|--------|------------|
| **OSM tile policy violation** (HIGH) | OSM blocks the app's tile requests | Only cache visited tiles; 7-day TTL; no prefetch/download button; single-host tile URL; valid attribution |
| **SW update strategy / stale shell** | users stuck on old UI/data | `skipWaiting`+`clientsClaim` for this app size; `updateViaCache:"none"` on register; `no-cache` on sw.js |
| **Stale data** | wrong info shown offline | network-first data + 7-day cap + "last updated" indicator |
| **iOS cache eviction** | iOS purges SW/Cache Storage after ~7 days of non-use and under storage pressure | acceptable for a "revisit" app; revisit re-populates; use 180px apple-touch-icon |
| **Cache Storage quota** | heavy panners accumulate tiles | `maxEntries: 1000` cap on `osm-tiles`; data is 6.9 MB fixed |
| **Next 16 + Serwist edge cases** | build/type friction | Serwist peer-dep `next >=14`; pin versions; smoke-test `next build` first |
| **tileerror flood on offline pan** | console errors / ugly map | add `tileerror` handler to render a neutral grey tile |

---

## 8. Step-by-step implementation tasks (executioner)

Each step is small and independently verifiable.

1. **Install:** `npm i @serwist/next && npm i -D serwist` (dev). Pin `@serwist/next@9.5.12`, `serwist@9.5.12`.
2. **SW source:** create `src/app/sw.ts` (content in §3). Fix the tile matcher to single host `tile.openstreetmap.org`.
3. **Wire config:** wrap `next.config.ts` with `withSerwist` (swSrc/swDest as in §3); update `tsconfig.json` (webworker lib, `@serwist/next/typings`, exclude `public/sw.js`); update `.gitignore`.
4. **Registration + headers:** add `ServiceWorkerRegister` component, render in `layout.tsx`; add `/sw.js` `no-cache` header to `vercel.json`.
5. **Manifest + icons + meta:** add `src/app/manifest.ts`, `viewport.themeColor` + `appleWebApp` in `layout.tsx`; generate icons via `scripts/gen-icons.mjs`; drop the `{s}.` subdomain in `MapView.tsx`.
6. **Freshness:** add `scripts/gen-meta.mjs` + `prebuild` script; fetch `/data/meta.json` in `loadData()`.
7. **Offline UX:** add offline banner + "last updated" chip in Header (client component using `navigator.onLine` + `online/offline` events + the meta timestamp); add `tileerror` grey-tile handler in `MapView.tsx`.
8. **Test + verify:** `npm run build` passes; Lighthouse PWA audit ≥ 90; install on Android + iOS; DevTools "Offline" → reload → map+data render, unvisited tiles grey; confirm `/api/report` still 200s (not intercepted).

## 9. Verification checklist (reviewer)

- [ ] `next build` succeeds with Serwist; `public/sw.js` generated (gitignored).
- [ ] `curl -I https://…/sw.js` returns `Cache-Control: no-cache` (not immutable).
- [ ] Lighthouse: PWA installable (manifest + SW + icons all resolve), performance not regressed.
- [ ] Offline (DevTools): reload → app shell + data render; "data as of <date>" banner shows.
- [ ] Visited tiles render offline; unvisited tiles grey (no console error flood).
- [ ] No "download for offline"/prefetch button exists anywhere.
- [ ] `/api/report` POST works online and is not served from cache.
- [ ] Tile URL is `https://tile.openstreetmap.org/...` (no `{s}.`), attribution visible.
