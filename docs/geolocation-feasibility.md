# Geolocation Feature — Feasibility Spike

**Spike type:** PM feasibility (problem validation + technical feasibility + effort)
**Date:** 2026-08-16
**Author:** plan-maker
**Request:** "Online map showing data with the user's CURRENT POSITION — what water am I near, is it legal, which permit covers it."
**Consumes:** t_27c88f90 (fisherman-complaints-research.md — top JTBD list)
**Verdict:** **GO — scoped MVP** (small, additive, opt-in). "Live conditions" and external geocoding are explicitly **NO-GO**.

---

## TL;DR

- **JTBD fit:** geolocation is a *UX shortcut to JTBD #1* ("know where I can fish legally"), not a new job. Real need, not a gimmick — but it is an *enhancement*, and it must ship as an opt-in, non-default, additive button so it can't regress the existing map.
- **Technically trivial on the current stack.** All 10,904 waters (1,013 contracted + 9,891 uncontracted) are already loaded client-side with `coordinates` + `bbox` (+ 675 with full `geometry`). "Nearest waters" is a Haversine sort over in-memory points — no backend, no new dependency, <10 ms.
- **No reverse-geocoding service needed.** The nearest water already carries `judet` + `asociatie` + `permitIssuer`. Nominatim is explicitly avoided (1 req/s, ~2,500/day shared-resource limits make per-user client calls fragile and policy-violating).
- **Competitor bar is low.** No RO fishing tool auto-detects GPS position *and* answers the legality/permit question. Nearest rival (`locuridepescuit.ro`) requires typing a town + radius and has no legality layer. Auto-locate + legality is a white-space gap.
- **Effort: S** (~1–2 dev-days, 5–8 small sub-tasks, zero new services).

---

## 1. JTBD validation — real need vs nice-to-have vs gimmick

### 1.1 Trace to the complaints research

The #1 job (pain 5/5, freq 5/5, every source) is:

> "Help me know where I can fish **legally** — which water, which association covers it, what permit I need — so I don't get fined."

The evidence is concrete and mobile-shaped:

- r/Roumanie: a father took his kid to fish a city-edge river and was nearly fined — he had no idea the water required a permit or which one (the *at-the-water* moment).
- avocatnet.ro (5,633 views): a permit holder from Brașov could not tell whether his permit covered a water in another county — a *which-water/which-county* question he could not resolve on his own.
- Complaint #9: existing maps/apps answer "where is water", never "can I fish here legally".

### 1.2 Is "show me waters near my position" the right expression of that job?

**Yes, conditionally.** The angler's question at the water is *"is THIS water legal, and which permit covers it?"* Geolocation removes the three manual steps the current map requires (find my county → find my water → open the card) and, critically, resolves the **county-border ambiguity** that is rampant in RO fishing: rivers frequently form or cross county borders, and a stretch's association is not discoverable from where you are standing.

Two concrete friction points geolocation kills:

1. **"Which county am I even in?"** — non-obvious near borders; the association/permit answer depends on it.
2. **"Which of the ~10,000 mapped waters is this one?"** — a nearest-N list with distances answers it instantly.

### 1.3 The "say no" counter-reading (taken seriously)

The complaints never literally ask for GPS. A strict reading says geolocation is a *solution detail*, not a validated job. Mitigations that keep it honest:

- **Opt-in, non-default:** the feature is a "Locate me" button; it never fires automatically, never changes the default map view, and fully degrades to the existing browse flow on deny/timeout.
- **Additive:** it reuses the existing water card + association + permit data — no new data model, no new content pipeline.
- **Measure before expanding:** ship the MVP, instrument the button (tap → success → interaction rate), and only invest further (e.g. true geometry distance, sector-aware results) if usage justifies it.

**Verdict: real need (shortcut to the #1 job), gimmick-risk low and guarded. Enhancement, not a new product pillar.**

---

## 2. Technical feasibility (current stack: Next.js 16 static + Leaflet/OSM + Vercel free, no backend)

### 2a. Browser Geolocation API on mobile

| Concern | Finding | Status |
|---|---|---|
| HTTPS required (secure context) | Vercel provides TLS on `*.vercel.app` **and** the custom `undepescuim.ro` domain. `localhost` is exempt in dev. | ✅ |
| Permission flow | `navigator.geolocation.getCurrentPosition()` triggers a one-shot native browser prompt per origin. Must handle deny/timeout/`PERMISSION_DENIED` gracefully. | ✅ standard |
| iOS Safari | Works over HTTPS; accuracy is "reduced" only for `requestPermission`-gated fuzzed APIs, not `getCurrentPosition`. One caveat: after a hard deny, iOS does not re-prompt — must surface a "enable Location in Settings" hint. | ⚠️ handle deny UX |
| Reverse geocoding to county/locality | **Not needed.** Derive locality from the nearest water's `judet`. Nominatim is off the table (1 req/s, ~2,500 req/day soft limit, shared resource — per-user client calls at any real traffic volume would breach policy). | ✅ avoided by design |

**Decision:** no external geocoding service. County/locality label comes from the nearest water's own `judet` (and optionally its `name`). Zero API keys, zero rate-limit risk, zero latency.

### 2b. "Nearest waters" computation — client-side, no spatial index required

Measured facts (2026-08-16):

| Dataset | Count | Has `coordinates` | Has `bbox` | Has `geometry` |
|---|---|---|---|---|
| `waters.json` (contracted) | 1,013 | 1,013 | 1,013 | 675 |
| `uncontracted_rivers.json` | 4,179 | 4,179 | 4,179 | 4,179 |
| `uncontracted_lakes.json` | 5,712 | 5,712 | 5,712 | 5,712 |

All of it is already in the Zustand store after `loadData()` — the map renders it today. "Nearest waters" is a distance sort over in-memory records:

- **Haversine** from user `[lat, lon]` to each water's `coordinates` (centroid). 1,013 contracted → <1 ms. All ~10,900 → <10 ms with a naive loop. Re-sorting on a single position fix is negligible.
- **Accuracy note for rivers:** a river's centroid can be far from a user standing on its bank. Cheap upgrade: compute distance to the water's `bbox` (axis-aligned box distance) for rivers, which reflects "how close is this water's course to me" far better than its centroid. True nearest-point-on-polyline (via `geometry`) is possible for the 675 geocoded contracted waters but is a v2 nicety — **not needed for MVP**.
- **Spatial index (R-tree/grid):** over-engineering at 11k points. A single `sort` per fix wins. Explicitly out of scope.

### 2c. Map interaction

All primitives exist or are one-liners:

- **Center on user:** `map.flyTo([lat, lon], 12–13)` — the existing `FlyToController` already shows the pattern.
- **Radius circle:** react-leaflet `<Circle center={...} radius={maxKm * 1000} />` (meters) — zero new deps.
- **User marker:** Leaflet's default marker images break under bundlers; the codebase currently renders **no markers at all** (only GeoJSON shapes). Use a CSS `divIcon` (blue pulsing dot) — no assets, no bundler hack.
- **Nearby list:** a bottom-sheet (mobile, `vaul` already in deps) / side panel (desktop) reusing the `WaterDetailSheet` visual language. Tapping an entry calls the existing `selectWater(slug)` → opens the existing card with association + permit + permit-issuer badge.

### 2d. Data freshness — honest framing

- The **position is live** (sub-second); the **water/legal data is annual** (per-season contracts).
- That combination is **correct for coverage** ("which contracted water covers where I'm standing") and **wrong for live conditions** (open today? stocked? weather? current ANPA→ANADSPA rule state). The latter is a data-freshness problem independent of geolocation and is **not** solved by this feature.
- **Honest UI copy** is mandatory: label results "Ape în apropiere — date 2026" and never imply live availability. This matches the existing site's "date 01.02.2024" legal-reference framing.

---

## 3. Competitor bar

| Tool | Auto-GPS position | "Near me" | Legality/permit layer | Map |
|---|---|---|---|---|
| **locuridepescuit.ro** | ✗ (type a town + radius "20 km", sort "cele mai apropiate") | partial (manual) | ✗ (mentions "ce permis îți trebuie" only as prose) | Mapbox (paid) |
| **baltipescuit.ro** | ✗ | ✗ (search/filter by location) | ✗ | directory |
| **fishingmaps.eu / Fish Deeper** | ✅ ("Localizare GPS") | ✅ | ✗ (bathymetric/lake-depth, premium) | proprietary |
| **iPescuit** | ✗ | ✗ | ✗ (spot map) | app |

**The bar:** nobody auto-detects GPS *and* answers the legality question. Geolocation alone is commodity; **geolocation + the legality/permit layer is unique** — and the legality layer is exactly UndePescuim's existing differentiator (complaints #1, #8, #9). This feature multiplies the value of the core asset rather than competing on a commodity.

---

## 4. User story

> **As a recreational angler** standing at (or driving toward) a river or lake, **I want** to tap "Locate me" and see the waters nearest to my current position together with the association and permit that cover each, **so that** I know immediately whether I can fish here legally and what permit I need — without hunting for my county or guessing across county borders.

Out-of-scope (explicitly rejected): live conditions, weather/solunar, reverse-geocoded street address, auto-tracking the user's movement (`watchPosition`), and re-plumbing the data pipeline.

---

## 5. Acceptance criteria

1. A visible "Locate me" button (FAB) is present on both mobile and desktop; it is **opt-in** and never fires on load.
2. Tapping it requests geolocation once (`getCurrentPosition`, `enableHighAccuracy: true`, 10 s timeout). First tap shows the native permission prompt.
3. **Success:** the map centers on the user (`zoom ≥ 12`), draws a radius circle, drops a user marker, and opens a "Nearby waters" list showing the **N nearest contracted waters within the radius** (default 25 km), each with: name, distance (km, 1 decimal), county, association name, and permit-issuer badge (anadspa / romsilva / asociatie).
4. **Adaptive radius:** if fewer than 3 contracted waters are within 25 km, expand to 50 km; always show at least the nearest few regardless of radius.
5. Tapping a nearby-water entry calls `selectWater(slug)` and opens the existing detail card (no new detail UI).
6. **Deny / timeout / unavailable:** the button shows a graceful, localized message and leaves the map in the default view; the rest of the app is unaffected. On iOS hard-deny, the message links the user to the OS Settings.
7. A clear, honest "date 2026" data-freshness label is shown on the nearby list; nothing implies live availability.
8. The feature is fully client-side: no new backend, no new external service, no new runtime dependency (a ~10-line Haversine lives in `src/utils/geo.ts`).
9. Existing behavior is untouched when the feature is not used (default Romania view, filters, association select all unchanged).
10. i18n: all new strings exist in both `ro` and `en`.

---

## 6. Effort estimate

**S (small).** ~1–2 dev-days, 5–8 focused sub-tasks. Breakdown:

| Sub-task | Size |
|---|---|
| `use-geolocation` hook (permission/state machine + deny UX) | XS |
| Haversine + `nearestWaters()` util in `src/utils/geo.ts` | XS |
| Store slice (`userPosition`, `nearbyWaters`, actions) | XS |
| `LocateButton` FAB | XS |
| `UserPositionLayer` (marker `divIcon` + radius `<Circle>` + flyTo) | S |
| `NearbyWatersSheet` list (mobile `vaul` / desktop panel) | S |
| i18n strings (ro/en) + fresh-label copy | XS |
| E2E/manual QA across iOS + Android + desktop deny/allow paths | S |

No new dependency; optionally `turf` distance could be added but a hand-rolled Haversine is cleaner for one function.

---

## 7. Implementation sketch

### 7.1 Files (new / modified)

```
src/hooks/use-geolocation.ts          NEW — wraps getCurrentPosition + permission state
src/utils/geo.ts                      EDIT — add haversineKm() + nearestWaters()
src/stores/map-store.ts               EDIT — add userPosition / nearbyWaters slice
src/components/map/LocateButton.tsx   NEW — FAB, triggers locate
src/components/map/UserPositionLayer.tsx NEW — marker + radius circle + flyTo
src/components/waters/NearbyWatersSheet.tsx NEW — nearest-N list
src/components/map/MapShell.tsx       EDIT — mount the three new components
messages/ro.json · messages/en.json   EDIT — strings
src/types/data.ts                     EDIT — (optional) NearbyWater type
```

### 7.2 Core snippets

```ts
// src/utils/geo.ts — ADD
export function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371, toRad = (d: number) => (d * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1), dLon = toRad(lon2 - lon1);
  const a = Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// Distance to a water: bbox (axis-aligned) for rivers AND lakes — a lake's
// bbox reflects its EXTENT (the stored centroid can be stale — t_6c2ac870 —
// and is a poor proxy for a user on a big reservoir's shore); centroid
// haversine only as a no-bbox fallback.
export function distanceToWaterKm(lat: number, lon: number, w: Water): number {
  const [minLon, minLat, maxLon, maxLat] = w.bbox ?? [NaN, NaN, NaN, NaN];
  if (!Number.isNaN(minLon)) {
    const dLon = Math.max(minLon - lon, 0, lon - maxLon);
    const dLat = Math.max(minLat - lat, 0, lat - maxLat);
    // approximate km using mid-latitude scaling for longitude
    const kLon = 111.32 * Math.cos((toRad(lat)));
    return Math.hypot(dLat * 111.32, dLon * kLon);
  }
  const [clon, clat] = w.coordinates ?? [NaN, NaN];
  return Number.isNaN(clon) ? Infinity : haversineKm(lat, lon, clat, clon);
}

export function nearestWaters(lat: number, lon: number, waters: Water[], opts: { limit: number; maxKm: number }) {
  return waters
    .map((w) => ({ water: w, km: distanceToWaterKm(lat, lon, w) }))
    .filter((e) => e.km <= opts.maxKm)
    .sort((a, b) => a.km - b.km)
    .slice(0, opts.limit);
}
```

```ts
// src/hooks/use-geolocation.ts — NEW (state machine)
type GeoState =
  | { status: 'idle' }
  | { status: 'requesting' }
  | { status: 'granted'; lat: number; lon: number; accuracy: number }
  | { status: 'denied' }        // PERMISSION_DENIED → iOS Settings hint
  | { status: 'error' };        // timeout / unavailable / unsupported

export function useGeolocation() {
  const [state, setState] = useState<GeoState>({ status: 'idle' });
  const locate = useCallback(() => {
    if (!('geolocation' in navigator)) return setState({ status: 'error' });
    setState({ status: 'requesting' });
    navigator.geolocation.getCurrentPosition(
      (p) => setState({ status: 'granted', lat: p.coords.latitude, lon: p.coords.longitude, accuracy: p.coords.accuracy }),
      (e) => setState({ status: e.code === e.PERMISSION_DENIED ? 'denied' : 'error' }),
      { enableHighAccuracy: true, timeout: 10_000, maximumAge: 60_000 },
    );
  }, []);
  return { state, locate };
}
```

```tsx
// src/components/map/UserPositionLayer.tsx — NEW
// inside <MapContainer>: user marker (divIcon) + radius circle + one-shot flyTo
const icon = L.divIcon({ className: 'user-position-dot', iconSize: [16, 16] });
// ...
{position && (
  <>
    <Marker position={[position.lat, position.lon]} icon={icon} />
    <Circle center={[position.lat, position.lon]} radius={maxKm * 1000} pathOptions={{ color: '#2563eb', weight: 1, fillOpacity: 0.06 }} />
  </>
)}
```

### 7.3 Store slice

```ts
// src/stores/map-store.ts — ADD
userPosition: LngLat | null;          // [lon, lat] or null
nearbyWaters: { slug: string; km: number }[];
setUserPosition: (p: LngLat | null) => void;
setNearbyWaters: (list: { slug: string; km: number }[]) => void;
```

`nearbyWaters` is computed once per successful fix (over the contracted `waters` pool — that is where the association/permit data lives) and consumed by `NearbyWatersSheet`.

### 7.4 UX copy (ro)

- Button: "Localizează-mă" / "Locate me"
- Nearby sheet title: "Ape în apropiere (date 2026)"
- Denied: "Accesul la locație este blocat. Activează-l din setările browserului." (iOS: link to Settings)
- Error/timeout: "Nu am putut determina locația. Continuă să explorezi harta manual."

---

## 8. Risks & tradeoffs

| Risk | Severity | Mitigation |
|---|---|---|
| **iOS hard-deny can't re-prompt** | M | Detect `PERMISSION_DENIED`, show Settings link; never nag. |
| **Battery/privacy hesitation** (anglers wary of location) | L | Opt-in button only, one-shot fix, no `watchPosition` (no tracking). |
| **Centroid distance misleads for long rivers** | M | Use bbox-distance for rivers in v1; true polyline distance is a v2 upgrade. |
| **"Live" expectations** (user assumes real-time availability) | M | Explicit "date 2026" label + copy that never implies live conditions. |
| **Scope creep** (watchPosition, weather, address) | M | Enforced out-of-scope list (Section 4). |
| **Nominatim policy breach** if someone later adds reverse geocoding | L | Design decision documented (Section 2a); county comes from water data. |
| **37 MB `waters.json` already on first paint** (pre-existing) | note | Not caused by this feature; nearest-waters reuses the already-loaded data. |

---

## 9. Recommendation

**GO — scoped MVP.** Build the opt-in "Locate me" button + nearest-contracted-waters list on the existing static stack (S effort, no backend, no new services, no new dependency). It is a genuine, complaint-backed shortcut to the #1 job ("where can I fish legally") that no RO competitor currently offers, and it multiplies the value of the site's existing legality layer.

**Revisit only after usage data:** if tap→success→interaction rates are strong, promote v2 (true geometry distance, sector-aware river results, `watchPosition` follow-me). If they are weak, the feature costs nothing to keep and nothing has been over-built.

**Explicitly not approved:** live conditions, weather/solunar, reverse-geocoded address, automatic location on page load.
