# F1a — Permit link + type on water/association cards: implementation plan

**Task:** t_dcc1dcf5 (SPIKE F1a)
**Roadmap item:** F1a — rank #1, NOW, effort S
**Author:** plan-maker
**Date:** 2026-08-15
**Status:** Draft — awaiting review

---

## 1. Goal

Surface permit information on the water detail card and the association block:
the *where to buy a permit* URL (`permit_url`), the *issuing body* (ANADSPA national
agency vs. the water's own association vs. Romsilva), and — where known — the permit
*type* (annual / day / month). When a water has no known online permit store, show a
"verifică cu asociația" fallback instead of leaving the user with no answer.

This is a **data-plumbing + small UI** task. The permit URL already exists upstream but is
dropped before it reaches the frontend. The work is: (a) stop dropping it, (b) derive the
issuer from association type, (c) render a "Permis" row, (d) outline a backfill path for
the ~62 associations that have a website but no permit store.

---

## 2. Findings (verified against the repo, 2026-08-15)

### 2.1 Where the permit data lives today

| Layer | File | Field | Population |
|---|---|---|---|
| Upstream API | `api.arebaltapeste.ro/api/asociatii` | `link_permis` | **7 / 82** associations |
| Upstream API | `api.arebaltapeste.ro/api/search?type=ape` | `asociatie.link_permis` (embedded) | same 7 |
| Pipeline (Python) | `data/processed/arebaltapeste_associations.jsonl` | `permit_url` | **7 / 94** records |
| Refresh source (JS) | `scripts/sources/arebaltapeste.mjs` | `link_permis` (kept in `normalizeAssociation` + `normalizeWater`) | kept |
| **Frontend data** | `public/data/associations.json` | *(none)* | **0 / 94** — DROPPED |
| **Frontend data** | `public/data/waters.json` `[].asociatie` | *(none)* | **0 / 1013** — DROPPED |
| Frontend types | `src/types/data.ts` | *(none)* | n/a |

**The root cause:** the permit URL is captured by the pipeline (`fetch_arebaltapeste.py`
line 254 maps `link_permis` → `permit_url`) and by the refresh source, but the transform
that builds the frontend JSON does not pass it through:

- `scripts/extract-map-data.mjs` — `assocContact()` returns only `adresa`/`telefon`/`siteUrl`
  (no permit); the waters `asociatie` block likewise omits `link_permis`.
- `scripts/map_romsilva_rivers.py` line 373 — explicitly writes `"permit_url": None`.
- `scripts/merge_anpa_waters.py`, `scripts/fix_jiu_cerbul_associations.py` — build `asociatie`
  blocks with only `name`/`slug` (+ `name_long`), dropping all contact fields including permit.

### 2.2 The 7 associations with a permit URL

| Association | slug | permit_url | issuer (derived) |
|---|---|---|---|
| ANPA – Ape Necontractate | `anpa` | `https://permise.anpa.ro:12443/portal-public/permis` | **anadspa** (national) |
| Direcția Silvică Bihor | `directia-silvica-bihor` | `https://magazin-online.dsoradea.ro/categorie-produs/pescuit-recreativ/` | **romsilva** |
| FLY FISHING CLUB SIBIU | `fly-fishing-club-sibiu` | `https://flyfishingclubsibiu.ro/tarife/` | asociatie |
| AJVPS MUREȘ | `ajvps-mures` | `https://ajvpsmures.ro/plata-online.php` | asociatie |
| AVPS TÂRNAVA MARE | `avps-tarnava-mare-` | `https://vizpart.ro/ro/permise-cu-plata-online/` | asociatie |
| APS AQUA CRISIUS | `aps-aqua-crisius` | `https://www.aquacrisius.ro/tarif-permis-de-pescuit/` | asociatie |
| Pro Pescar | `pro-pescar` | `https://propescar.ro/membru-propescar/` | asociatie |

Water reach of these 7 (from `public/data/waters.json`): `fly-fishing-club-sibiu` 20,
`aps-aqua-crisius` 19, `ajvps-mures` 29, `pro-pescar` 15, `anpa` 13, `directia-silvica-bihor` 7,
`avps-tarnava-mare-` 0. → ~103 contracted waters would gain a live permit link today.

> **Data quirk to note:** the `anpa` association is the "Ape Necontractate" pseudo-row. Its
> `link_permis` points at the **national ANADSPA permit portal**, which is the *national*
> recreational-fishing permit required for **every** water — not just "necontractate". See §3.3.

### 2.3 Fields that do NOT exist anywhere upstream

`permit_type` (anual/zi/luna) and `permit_price` are **not present** in the arebaltapeste API
(verified: association keys are `name,name_long,slug,adresa,adrese,telefon,siteUrl,link_permis,
bbox,regulament`; water keys add `descriere,regulament` — no tariff/price/type field). The probe
report (`data/raw/arebaltapeste_probe_report.md` line 93) notes the *HTML* water-detail page
`/apa-<slug>-<name>` renders "permit info", so type/price *could* be scraped per-water later —
but that is 426 extra HTML fetches, out of scope for an S effort. See §7 (follow-ups).

`regulament` (fishing regulations text) also exists upstream and is currently unused — flagged
as a natural companion field, out of scope here.

### 2.4 Association `type` is the issuer source

The pipeline already classifies every association (`type`: `ajvps`/`avps`/`aps`/`ds`/`anpa`/`other`)
in `arebaltapeste_associations.jsonl` (36/13/7/26/1/11) and `locuri_associations.jsonl`. That field
is **not** copied into `public/data/associations.json`. It is a zero-cost, deterministic issuer source.

### 2.5 Related finding (flag, do not fix in this task)

`scripts/sources/arebaltapeste.mjs` (the monthly `npm run data:refresh` source) writes
`{generatedAt, count, items}` objects, but the app (`src/stores/map-store.ts` line 87-90) casts
`/data/associations.json` and `/data/waters.json` to flat arrays. If the refresh workflow is ever
run as-is it will emit a shape the app can't consume. The current on-disk files are flat arrays
built by the Python/`.mjs` transform chain. **Recommend** a separate follow-up to reconcile the
refresh source's output shape; the permit transform below targets the array-producing path.

---

## 3. Schema decision

### 3.1 Frontend types — `src/types/data.ts`

Add a `PermitIssuer` union and three optional fields. Naming follows the existing camelCase
convention (`siteUrl`, `telefon`, `adresa`).

```ts
/** Who issues the permit for a water. */
export type PermitIssuer = 'anadspa' | 'romsilva' | 'asociatie';

/** Permit duration type. NOT populated from upstream yet (see §7). */
export type PermitType = 'anual' | 'zi' | 'luna' | 'sezon' | 'altele';
```

`Association` gains:

```ts
export interface Association {
  slug: string;
  name: string;
  name_long: string;
  ape: number;
  adresa?: string;
  telefon?: string;
  siteUrl?: string;
  /** URL to buy the association's permit online (arebaltapeste `link_permis`). */
  permitUrl?: string;
  /** Issuing body derived from association type at transform time. */
  permitIssuer?: PermitIssuer;
  /** Permit duration type — reserved; empty until enrichment lands (§7). */
  permitType?: PermitType;
  bbox: BBox;
  id: string;
}
```

`Water.asociatie` (nested) gains the same three optional fields, so the card can render permit
info even when the water's association isn't in the 94-record directory (the fallback path in
`WaterDetailSheet.tsx` lines 45-55 builds the association object from `water.asociatie`):

```ts
asociatie: {
  name: string;
  name_long?: string | null;
  slug: string;
  telefon?: string;
  adresa?: string;
  siteUrl?: string;
  permitUrl?: string;
  permitIssuer?: PermitIssuer;
  permitType?: PermitType;
} | null;
```

**Decisions recorded:**
- `permit_price` — **NOT added.** Prices change frequently; a stale static price is worse than no
  price. The `permitUrl` leads to live pricing. Revisit only if a scrape+refresh of prices is built.
- `permit_type` — **type added, left unpopulated** for now (no upstream source). Populated by the
  §7 enrichment follow-up, not this task.
- `permit_issuer` — **added and populated now**, derived from association `type`
  (`anpa`→`anadspa`, `ds`→`romsilva`, everything else→`asociatie`).

### 3.2 Pipeline types — `src/pipeline/types.ts`

Already has `permit_url?: string` on `Association`. Add the same `permit_issuer` to stay consistent,
mirroring `data_model_proposal.md` §3.4 (single source of truth):

```ts
export type PermitIssuer = "anadspa" | "romsilva" | "asociatie";

export interface Association {
  // ... existing fields ...
  permit_url?: string;
  permit_issuer?: PermitIssuer;
  // ...
}
```

### 3.3 National permit (ANADSPA) — product decision to confirm

In Romania, fishing any contracted water legally requires **two** permits: the national
**permis de pescuit recreativ** (ANADSPA, `https://permise.anpa.ro/portal-public/permis`) **plus**
the association's own permit/abonament for that water. The plan therefore proposes a **constant
national-permit link** shown on every contracted water, alongside the association permit row.

Centralize the constant in one place so it's trivial to update:

```ts
// src/lib/permit.ts  (new)
export const NATIONAL_PERMIT_URL = 'https://permise.anpa.ro/portal-public/permis';
export const NATIONAL_PERMIT_LABEL = 'Permis național de pescuit (ANADSPA)';
```

**Default (recommended):** show the national-permit row on every contracted water, and the
association-permit row only when `permitUrl` is present (else the fallback). Flag this for the
user in review — it is the one product decision this task shouldn't silently assume.

---

## 4. Implementation plan — ordered steps (each 2–5 min)

### Step 1 — Frontend types

File: `src/types/data.ts`

1. Add `PermitIssuer` and `PermitType` unions near the existing type unions (top of file).
2. Add `permitUrl?`, `permitIssuer?`, `permitType?` to `Association`.
3. Add the same three to the `Water.asociatie` nested object.

Verify: `npm run lint` and `npm run build` (types must not break existing usages — all three
fields are optional, so nothing else changes).

### Step 2 — Pipeline types

File: `src/pipeline/types.ts`

Add `PermitIssuer` union + `permit_issuer?: PermitIssuer` to `Association`.

### Step 3 — Centralize the national-permit constant

File: `src/lib/permit.ts` (new) — content as in §3.3.

### Step 4 — Transform: pass `permitUrl` + `permitIssuer` through

This is the core fix. Apply to **every** array-producing transform so the field survives
regardless of which script regenerates the data.

**4a. `scripts/extract-map-data.mjs`**

```js
const ISSUER = { anpa: 'anadspa', ds: 'romsilva' };

function assocContact(a) {
  const addr = a.adrese?.[0]?.adresa ?? null;
  return {
    adresa: a.adresa ?? addr?.adresa ?? undefined,
    telefon: a.telefon ?? addr?.telefon ?? undefined,
    siteUrl: a.siteUrl ?? undefined,
    permitUrl: a.link_permis ?? undefined,
    permitIssuer: assocTypeToIssuer(a),   // see helper below
  };
}
// helper: derive issuer from name/type the same way fetch_arebaltapeste.py does
function assocTypeToIssuer(a) {
  const n = (a.name || '').toLowerCase();
  if (n.startsWith('anpa')) return 'anadspa';
  if (n.includes('silvica') || n.includes('romsilva')) return 'romsilva';
  return 'asociatie';
}
```

Also add `permitUrl: w.asociatie.link_permis ?? undefined` and the issuer to the waters
`asociatie` block (the nested `w.asociatie` already carries `link_permis` upstream).

**4b. `scripts/map_romsilva_rivers.py` (line ~373)**

Replace `"permit_url": None` with a real value when the association is a Romsilva district that
has one (Direcția Silvică Bihor → `https://magazin-online.dsoradea.ro/categorie-produs/pescuit-recreativ/`),
and add `"permit_issuer": "romsilva"` for Romsilva rows. At minimum, drop the hard `None` and let
the value come from the source association record if present.

**4c. `scripts/merge_anpa_waters.py` / `scripts/fix_jiu_cerbul_associations.py`**

These build `asociatie` blocks with only name/slug. They don't need a permit field added (ANPA
rows have no permit URL), but they MUST NOT *erase* one if a future merge feeds them association
records that carry it. Leave as-is but document.

### Step 5 — Backfill script (outline)

File: `scripts/backfill_permit_urls.py` (new, ~60 lines)

Inputs → outputs:

1. Read `data/processed/arebaltapeste_associations.jsonl` → the 7 authoritative `permit_url`
   (+ derived `permit_issuer` from `type`).
2. Read `data/processed/locuri_associations.jsonl` → 26 associations with `website` (candidate
   fallback permit-info pages, NOT auto-assigned — human confirms each is actually a permit page).
3. Emit `data/processed/permit_enrichment.json`:
   ```json
   {
     "known":  [ {"slug": "...", "permit_url": "...", "permit_issuer": "..."}, ... ],   // 7
     "website_no_permit": [ {"slug": "...", "website": "..."}, ... ],                    // ~62
     "no_website": [ "slug", ... ]                                                       // dead-ends
   }
   ```
4. Emit `data/processed/permit_overrides.json` (empty template) — a human-paste list of manually
   curated `{slug, permit_url, permit_issuer}` that the transform merges **on top of** the
   `known` list (overrides win).

The transform (Step 4) merges `known` + `overrides` into the frontend JSON. The 7 known URLs land
immediately; the `website_no_permit` list becomes the manual-curation queue for the §7 follow-up.

### Step 6 — Regenerate frontend data

Run the array-producing chain and confirm the field survives:

```bash
node scripts/extract-map-data.mjs
# then re-apply the repo's merge/fix chain as documented in the task history, ending with:
python3 scripts/recompute_assoc_counts.py
```

Verify with a data-integrity check (see §6).

### Step 7 — UI: "Permis" row in `WaterDetailCard`

File: `src/components/waters/WaterDetailCard.tsx`

Add a permit block inside the association section (after the existing `telefon`/`adresa`/`siteUrl`
rows), plus the national-permit row. Sketch:

```tsx
import { Ticket, ShieldCheck } from 'lucide-react';
// import { NATIONAL_PERMIT_URL, NATIONAL_PERMIT_LABEL } from '@/lib/permit';

const permitUrl = association?.permitUrl ?? water.asociatie?.permitUrl;
const permitIssuer = association?.permitIssuer ?? water.asociatie?.permitIssuer;

// inside the association block (before the closing of the !isUncontracted section):
{permitUrl ? (
  <a href={permitUrl} target="_blank" rel="noopener noreferrer"
     className="flex items-center gap-2 text-primary hover:underline">
    <Ticket className="h-3.5 w-3.5 shrink-0" />
    {permitIssuer === 'anadspa' ? 'Permis ANADSPA' :
     permitIssuer === 'romsilva' ? 'Permis Romsilva' : 'Cumpără permis online'}
  </a>
) : (
  <p className="flex items-start gap-2 text-xs text-muted-foreground">
    <Ticket className="mt-0.5 h-3.5 w-3.5 shrink-0" />
    Permis: verifică cu asociația
  </p>
)}
```

And above/below the association block, for contracted waters only:

```tsx
<a href={NATIONAL_PERMIT_URL} target="_blank" rel="noopener noreferrer"
   className="flex items-center gap-2 text-primary hover:underline">
  <ShieldCheck className="h-3.5 w-3.5 shrink-0" />
  {NATIONAL_PERMIT_LABEL}
</a>
```

Note: the existing `association` fallback object in `WaterDetailSheet.tsx` (lines 45-55) must also
copy `permitUrl`/`permitIssuer` from `water.asociatie` so the row renders even for waters whose
association isn't in the directory.

### Step 8 — Verify + lint + build

```bash
npm run lint
npm run build
npm run dev   # manual check: open a water under APS Aqua Crisius / Fly Fishing Club Sibiu
```

---

## 5. Acceptance criteria

1. `public/data/associations.json` — the 7 known associations carry `permitUrl` and a correct
   `permitIssuer`; `grep -c '"permitUrl"' public/data/associations.json` ≥ 7.
2. `public/data/waters.json` — waters under the 7 associations carry `permitUrl` in `asociatie`
   (~103 waters); all other waters have no `permitUrl` (fallback path renders).
3. `WaterDetailCard` renders a tappable "Cumpără permis online"/issuer-specific permit link when
   `permitUrl` is present, and "verifică cu asociația" when absent.
4. National-permit row renders on every contracted water (pending the §3.3 review decision).
5. `npm run lint` and `npm run build` pass; no type regressions.
6. `scripts/backfill_permit_urls.py` runs and emits `permit_enrichment.json` + `permit_overrides.json`
   with the counts above.

---

## 6. Verification commands (exact)

```bash
# 1. Data-integrity check (after regeneration)
python3 - <<'PY'
import json
a = json.load(open('public/data/associations.json'))
w = json.load(open('public/data/waters.json'))
pa = [x for x in a if x.get('permitUrl')]
pw = [x for x in w if (x.get('asociatie') or {}).get('permitUrl')]
issuers = {x.get('permitIssuer') for x in a if x.get('permitIssuer')}
print('assoc with permitUrl:', len(pa))
print('waters with permitUrl:', len(pw))
print('issuers seen:', issuers)
assert len(pa) >= 7
assert set(issuers) <= {'anadspa','romsilva','asociatie'}
PY

# 2. Lint + type-check + build
npm run lint
npm run build

# 3. Backfill script
.venv/bin/python scripts/backfill_permit_urls.py
```

---

## 7. Follow-ups (NOT this task — spawn separately if approved)

- **Permit type/price enrichment (F1a-part2):** scrape `/apa-<slug>-<name>` HTML for the 7+62
  associations' permit type (anual/zi/luna) and price; populate `permitType` + a fresh
  `permitPrice`-with-`asOf` field. S/M effort.
- **`regulament` field surfacing:** regulations text already in the API, unused — cheap add, same
  card section.
- **Reconcile `scripts/sources/arebaltapeste.mjs` output shape** with the app's array consumption
  (latent refresh bug noted in §2.5).
- **Standalone association detail panel:** currently there is no association detail view — the
  "association block" lives only inside the water card. If a dedicated association page is wanted,
  that's a separate UI task.

---

## 8. Risks & tradeoffs

| Risk | Impact | Mitigation |
|---|---|---|
| `link_permis` URLs rot (arebaltapeste is a 3rd-party site) | Low–Med | Annual refresh re-pulls them; treat as best-effort links, always `target=_blank` |
| The `anpa` pseudo-association's `link_permis` is the *national* portal, not a per-water permit | Med (mislabel) | Special-case `anpa`→`anadspa` issuer + national-permit row, so it never reads as a water-specific store |
| Two distinct permit regimes (national vs association) may confuse users | Med | Label each row explicitly ("Permis național" vs "Permis asociație") |
| Multi-script transform chain can re-drop the field later | Med | Apply the passthrough in **all** array-producing scripts + add the §6 data-integrity assertion to CI |
| `permit_type`/`permit_price` have no upstream source → empty fields | Low | Types are optional; UI renders nothing when absent; enrichment is a tracked follow-up |
| Refresh source shape mismatch (§2.5) could surface when `data:refresh` runs | Med | Out of scope here but flagged; fix in a dedicated follow-up |

---

## 9. Files touched (summary)

- `src/types/data.ts` — add permit fields to `Association` + `Water.asociatie` + unions
- `src/pipeline/types.ts` — add `permit_issuer` (consistency with data model)
- `src/lib/permit.ts` — **new** national-permit constant
- `src/components/waters/WaterDetailCard.tsx` — "Permis" rows
- `src/components/waters/WaterDetailSheet.tsx` — copy `permitUrl`/`permitIssuer` into the fallback association object
- `scripts/extract-map-data.mjs` — pass `permitUrl`/`permitIssuer` through
- `scripts/map_romsilva_rivers.py` — stop nulling `permit_url`; set issuer
- `scripts/backfill_permit_urls.py` — **new** enrichment/backfill script
- `public/data/associations.json`, `public/data/waters.json` — regenerated
