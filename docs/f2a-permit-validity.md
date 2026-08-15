# F2a — Permit Validity Statement (contracts + reciprocity) — Implementation Plan

**Date:** 2026-08-15
**Author:** plan-maker (t_f46082ba)
**Parent roadmap item:** F2a (from t_a3c4c042, rank #4, NOW, effort M)
**Status:** Draft — review required before execution
**Related specs:** `docs/ARCHITECTURE.md`, `docs/map-state-data-flow.md`, `docs/component_structure_plan.md`, `docs/mobile-layout-spec.md`, `data/raw/data_model_proposal.md`

---

## 0. Goal

Make the existing "coverage highlight" (green/grey map coloring) **legally explicit** by
surfacing, in the UI, a statement of the form:

> **"Permisul de la {asociație} este valabil pe {N} ape în județele: {județ1, județ2, …}."**

…on two surfaces:
1. **Association detail view** (new — does not exist today) triggered from the association search.
2. **Water detail card** — a "validity" line under the resolved association for a clicked water.

Reciprocity partners (other associations whose waters a permit *also* covers) are marked
**"reciprocitate neconfirmată"** by default, because no public per-pair reciprocity registry exists
(see §2).

---

## 1. Findings — Data (what we already have)

### 1.1 Frontend datasets (consumed by the Next.js app)

| File | Shape | Contents |
|------|-------|----------|
| `public/data/associations.json` | `Association[]` (94 rows) | `slug, name, name_long, ape, adresa, telefon?, siteUrl?, bbox?, id` |
| `public/data/waters.json` | `Water[]` (1013 rows) | `slug, name, judet, type, subtype, limite, dimensiune, pescuit_interzis, referinta, coordinates, driving, bbox, asociatie{slug,name,name_long,adresa,siteUrl,telefon?}, geometry, course_frac, …` |
| `public/data/uncontracted_rivers.json` / `uncontracted_lakes.json` | `Water[]` | OSM waters with no contract (`uncontracted: true`) |

### 1.2 Pipeline datasets (source of truth, not shipped to FE)

| File | Rows | Key fields |
|------|------|-----------|
| `data/processed/anpa_waters.jsonl` | 682 | `county, county_id, association, water_name, sector_km/ha, contract_number, contract_date, is_contracted:true` |
| `data/processed/anpa_romsilva_waters.jsonl` | 289 | Romsilva mountain waters, `admin:romsilva`, `is_contracted:false`, `gestionar_ocol` |
| `data/processed/locuri_associations.jsonl` | 64 | `name, slug, county_id, counties_contract` (space-separated multi-county string!) |
| `data/processed/locuri_waters.jsonl` | 626 | `association, association_slug, water_name, is_contracted:false` |
| `data/processed/sources.jsonl` | 68 | provenance (`source_name, raw_file_path, source_date, record_count`) |

### 1.3 Key aggregation facts (computed this spike)

- **Every** of the 1013 waters has a non-null `asociatie.slug` + `judet` → the association→county
  coverage graph is fully derivable from `waters.json` alone.
- `associations.json` **`ape` field is already exactly equal** to the computed water count
  (0 mismatches across 94 rows). So the "N waters" half of the statement already exists; only the
  **counties** dimension is missing.
- **92 distinct association slugs** appear in `waters.json`; 6 associations are directory-only
  (`ape: 0`): `acvps-fagetel-mortonca-`, `ajvps-campina`, `app-filiala-suceava`, `aps-hunedoara`,
  `aps-salmo-carpatica-lupeni-`, `a-p-s--sovata-2008`.
- **4 waters reference slugs absent from `associations.json`** (slug-mismatch legacy): `aps-pro-pescar`
  (5 waters), `a.fly-fishing-club-sibiu` (3), `asociatia-fly-fishing-rarau` (1), `cs-hunedoara` (2).
  → the validity statement must tolerate a missing association (fall back to the water's embedded
  `asociatie` object, exactly like `WaterDetailSheet` already does).
- **Multi-county associations** (the only cases where "counties Y" is plural):
  | slug | waters | counties |
  |------|-------|----------|
  | `aps-aqua-crisius` | 19 | Alba, Argeș, Brașov, Sibiu, Suceava |
  | `ajvps-botosani` | 42 | Botoșani, Suceava |
  | `anpa` (agency pseudo-association) | 13 | 10 counties — **special-case** (see §4.3) |
- **40 distinct counties** appear in `waters.json` (missing: Tulcea — Delta Dunării is a separate
  ARBDD permit — and București).
- `referinta` already holds a per-water legal reference string (135 distinct values, e.g.
  *"Lista habitatelor piscicole naturale contractate … la data 01.02.2024"* and
  *"Contract 44/26.10.2017 (2017-10-24)"*). This is the natural anchor for the "contract" clause.

### 1.4 Design decision — validity aggregation

```
validity(association A) =
  { count:     |{ w ∈ waters.json : w.asociatie.slug == A.slug }|          // == A.ape
    counties:  sorted(distinct w.judet for those waters)                   // NEW — add to associations.json
    contract:  optional contract ref (from anpa_waters.jsonl by association) }
```

- `count` is already persisted as `ape` — reuse it, do not recompute.
- Add **`counties: string[]`** to `associations.json` (sorted, diacritics preserved, display-ready).
- Add **`reciprocity: "neconfirmată"`** to every association (constant for now — see §2).
- (Optional, cheap) add **`contract_ref?: string`** = the most recent `contract_number` seen in
  `anpa_waters.jsonl` for that association, to back the "under contract …" clause.

---

## 2. Findings — Reciprocity (research)

**Conclusion: there is NO public, structured, per-pair list of reciprocity agreements between
AJVPS/AVPS associations.** Reciprocity exists as a *statutory default*, not as a published
pairwise matrix. Therefore the plan is the **"reciprocitate neconfirmată" label path**: default
every association to *neconfirmată* and surface the legal context, reserving a manual-curation
file for future confirmations.

### 2.1 Legal basis (primary)

- **Legea nr. 176/2024** (privind pescuitul și protecția resursei acvatice vii — successor of
  OUG 23/2008). The permit clause, quoted on `avocatnet.ro` forum (thread 615033):
  > *"Permisul de pescuit recreativ este valabil atât pentru zonele pentru care asociația al cărei
  > membru este a încheiat contracte de utilizare în scop recreativ a resurselor acvatice vii, cât
  > și pentru zonele pentru care alte asociații au încheiate contracte, **pe bază de reciprocitate**…"*
  → **A single permit is, in law, valid on ALL contracted waters "on the basis of reciprocity".**

### 2.2 The reciprocity mechanism (AGVPS umbrella)

- **AGVPS** (*Asociația Generală a Vânătorilor și Pescarilor Sportivi din România*) governs
  reciprocity for its affiliated associations:
  - **Statut AGVPS, Art. 9** (published MO Partea I nr. 705/21.09.2015) — the AGVPS Congress sets
    reciprocity principles.
  - **Hotărârea nr. 1/30.05.2015 (Sibiu), Art. 6 + Anexa 5** — *"Condițiile acordării dreptului de
    reciprocitate"*: a member of an affiliated association, with the current-year cotizație paid,
    fishing at **another affiliated association** pays a **reduced ½ cotizație**.
    Source: `https://www.agvps.ro/pescuitul_in_romania/dreptul_de_reciprocitate.html`,
    PDF: `agvps.ro/docs/reciprocitate.pdf`.
  - **Circulara AGVPS 29.01.2018** — clarifies that affiliated associations are **obligated** to honor
    reciprocity, and that attempts to sign *"acorduri/contracte de reciprocitate"* only with SOME
    associations *"excede prevederilor statutare"*. Source:
    `https://www.info-delta.ro/circulara-agvps-despre-acordarea-reciprocitatii-intre-asociatiile-afiliate-pe-linie-de-pescuit/`.

### 2.3 Practical reality (why we default to "neconfirmată")

- **Reciprocity applies to AGVPS-affiliated associations only.** The 2018 circular explicitly names
  *"asociațiile neafiliate din jud. Cluj și Alba"* as outside the system. Affiliated ≠ all.
- **Not uniformly honored.** `avocatnet.ro` and the `info-delta.ro` comment threads document
  anglers fined on a neighbour county's water because the local association refused the reciprocity
  "viză"; the mechanism is a *per-association reduced-fee endorsement*, not an automatic right.
- **No registry.** Neither ANPA (`anpa.ro`) nor AGVPS publishes a machine-readable list of which
  pairs of associations currently honor reciprocity. `ajvpsmures.ro/regulament-pescuit.php` phrases it
  as *"protocol de reciprocitate, vizat la zi"* — confirming it is a live per-association status we
  cannot verify from any single public source.

### 2.4 What the label means (copy)

| Label | Meaning | When shown |
|-------|---------|------------|
| `reciprocitate confirmată` | A citable source proves this association honors another association's permit. | **Only** if a source is entered in `reciprocity.json` (manual curation). Currently none. |
| `reciprocitate neconfirmată` (default) | No public source confirms a reciprocity protocol for this association. | Always, until curated. |

**Display copy (RO):** *"Reciprocitate: neconfirmată — nu am găsit o sursă publică care să confirme
că permisul acestei asociații este acceptat și de alte asociații. Legea prevede valabilitatea pe
bază de reciprocitate între asociațiile afiliate AGVPS; verifică cu asociația înainte de a pescui."*

---

## 3. Architecture / Approach

- **No backend.** Static JSON (existing pattern). Add two fields to `associations.json` via a small
  pipeline script (extend `scripts/recompute_assoc_counts.py` pattern).
- **Association detail view = in-app panel/sheet**, NOT a new route. Matches the existing decision
  ("no deep links for waters", single-page map, `ARCHITECTURE.md §5`). Selecting an association
  already flies the map to its bbox and green-lights its waters; we add a **persistent association
  info chip + expandable detail sheet** that carries the validity statement.
- **Water card** gets a small "validity" block under the association section.

---

## 4. Implementation steps (each ~2–5 min)

### Step 1 — Data: add `counties` + `reciprocity` to `associations.json`

Extend the existing recompute script (new file so `ape` logic stays untouched):

`scripts/recompute_assoc_validity.py`:
```python
#!/usr/bin/env python3
"""Add per-association `counties` and default `reciprocity` to associations.json (F2a)."""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
waters = json.loads((ROOT / "public/data/waters.json").read_text(encoding="utf-8"))
assocs = json.loads((ROOT / "public/data/associations.json").read_text(encoding="utf-8"))

counties = defaultdict(set)
for w in waters:
    a = w.get("asociatie") or {}
    if a.get("slug"):
        counties[a["slug"]].add(w["judet"])

for a in assocs:
    a["counties"] = sorted(counties.get(a["slug"], ()))
    a["reciprocity"] = "neconfirmată"          # constant until curated (§2)

(ROOT / "public/data/associations.json").write_text(
    json.dumps(assocs, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"associations.json: {len(assocs)} entries, counties + reciprocity added")
```
Run: `python3 scripts/recompute_assoc_validity.py`

**Expected:** 94 rows gain `counties: [...]` and `reciprocity: "neconfirmată"`. `aps-aqua-crisius`
→ 5 counties; `ajvps-botosani` → 2; directory-only 6 → `counties: []` (statement must handle empty).

### Step 2 — Data: (optional) `reciprocity.json` curation seed

`public/data/reciprocity.json` (empty seed, schema documented):
```json
{ "version": 1,
  "confirmed": [],
  "note": "Asociații cu reciprocitate confirmată prin sursă publică. Fiecare intrare: { slug, partners: [slug...], source_url, source_date }. Empty = nimic confirmat încă." }
```
This is the forward-compatible hook; UI reads it but renders "neconfirmată" until an entry exists.
**Decision point for reviewer:** ship the empty seed now (cheap) or defer the file entirely until a
real source surfaces. Recommended: ship it — it makes the "confirmată" path real without scope creep.

### Step 3 — TypeScript: extend the `Association` type

`src/types/data.ts` (add to the `Association` interface):
```typescript
/** County names whose contracted waters this association manages (sorted, display-ready). */
counties: string[];
/** Reciprocity status. 'neconfirmată' unless a public source confirms otherwise (F2a). */
reciprocity?: 'confirmată' | 'neconfirmată';
/** Optional contract reference (most recent ANPA contract_number). */
contract_ref?: string;
```
Note: keep `reciprocity` and `counties` optional-friendly so the FE tolerates a stale
`associations.json` during the transition (guard with `?? []` / `?? 'neconfirmată'` in components).

### Step 4 — UI: association validity statement component (new)

`src/components/associations/AssociationValidity.tsx` (pure presentational):
```tsx
'use client';
import { Badge } from '@/components/ui/badge';
import type { Association } from '@/types/data';

export function AssociationValidity({ association }: { association: Association }) {
  const n = association.ape ?? 0;
  const counties = association.counties ?? [];
  if (n === 0) {
    return <p className="text-sm text-muted-foreground">Asociația nu are ape contractate afișate pe site.</p>;
  }
  return (
    <div className="flex flex-col gap-2 text-sm">
      <p>
        Permisul <strong>{association.name}</strong> este valabil pe{' '}
        <strong>{n} {n === 1 ? 'apă' : 'ape'}</strong>
        {counties.length > 0 && (
          <> în județele: <strong>{counties.join(', ')}</strong></>
        )}.
      </p>
      {association.contract_ref && (
        <p className="text-xs text-muted-foreground">Contract: {association.contract_ref}</p>
      )}
      <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
        Reciprocitate: <strong>neconfirmată</strong> — nu am găsit o sursă publică care să confirme
        că permisul acestei asociații este acceptat și de alte asociații. Legea prevede
        valabilitatea pe bază de reciprocitate între asociațiile afiliate AGVPS; verifică cu
        asociația înainte de a pescui.
      </div>
    </div>
  );
}
```

### Step 5 — UI: association detail sheet (new)

`src/components/associations/AssociationDetailSheet.tsx` — reuse the **vaul Drawer** pattern from
`WaterDetailSheet.tsx` (mobile bottom sheet `<1024px`, desktop right panel ≥1024px, same snap points
[0.1, 0.35, 0.65] and × / ESC / drag-dismiss). Content:
- Header: association `name` + `name_long` (secondary).
- `AssociationValidity` (Step 4).
- Contact block (telefon / adresa / siteUrl — same icons+links as `WaterDetailCard`).
- Water-count `ape` badge.
- **Open trigger:** when `selectedAssociationSlug` is non-null, render a persistent **association
  chip** on the map (top-center, below FilterBar) showing the association name + `ape`; tapping the
  chip opens the sheet. This gives desktop + mobile an explicit entry point without a new route.

### Step 6 — Wire the association chip + sheet into `MapShell`

`src/components/map/MapShell.tsx` — add the chip and sheet alongside `WaterDetailSheet`:
```tsx
<AssociationChip />                 // new, top overlay; hidden when no selection
<WaterDetailSheet />
<AssociationDetailSheet />          // new, rendered last so it layers above the water sheet
```
`AssociationChip` reads `selectedAssociationSlug` + `associations` from the store, renders nothing
when `null`. Selection/clear already flows through `store.selectAssociation` — no store change
needed (the chip is purely derived).

### Step 7 — UI: water card validity line

`src/components/waters/WaterDetailCard.tsx` — inside the existing "Asociație" block (after the
contact links), add a one-line validity statement for the **resolved association**:
```tsx
{association && !isUncontracted && (
  <p className="mt-1 border-t pt-2 text-xs text-muted-foreground">
    Permisul {association.name} este valabil pe acest sector.
  </p>
)}
```
(Full per-association "N ape în județele…" sentence lives in the association detail sheet; the water
card only asserts *this* water is covered — it is, because the map already resolved the contract.)

### Step 8 — i18n note (deferred)

Text is hardcoded RO (matches the current single-language app — `Header` shows a "RO" badge and
next-intl is a documented follow-up milestone). Add a `// TODO(i18n)` comment so the strings are
caught when localization lands. Do **not** build the i18n plumbing in this task.

### Step 9 — Verify

- `python3 scripts/recompute_assoc_validity.py` → re-open `associations.json`, confirm
  `counties`/`reciprocity` present and `ape` unchanged.
- `npm run build` (or `pnpm build`) → type-checks the new `Association` fields.
- Manual: `npm run dev` → select `APS AQUA CRISIUS` → chip appears; open sheet → statement reads
  *"…valabil pe 19 ape în județele: Alba, Argeș, Brașov, Sibiu, Suceava"* + reciprocity note.
  Click a water in that association → card shows *"Permisul APS AQUA CRISIUS este valabil pe acest
  sector."* Select a directory-only association (`ajvps-campina`) → empty-count branch renders.
  Click a water whose slug is missing from the directory (e.g. `aps-pro-pescar`) → no crash,
  card falls back to the embedded `asociatie`.

---

## 5. Risks & tradeoffs

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| "Reciprocitate neconfirmată" on every card reads as *negative* to users | Medium | Low–Med | Frame as *"verifică cu asociația"* guidance, not a warning; cite the legal default (§2.1). Reviewer may soften copy. |
| `anpa` pseudo-association (10 counties) makes an odd statement | Low | Low | Special-case `slug === 'anpa'` → show *"administrate direct de ANPA / necontractate"* instead of a county list. |
| 4 waters reference slugs missing from `associations.json` | Low | Low | Water card + sheet already fall back to `water.asociatie` (existing pattern in `WaterDetailSheet`). |
| `counties` list drifts from reality on next data refresh | Medium | Medium | `recompute_assoc_validity.py` is idempotent and wired into the same CI refresh that runs `recompute_assoc_counts.py` (`data-refresh.yml`). |
| Reciprocity is a *live* per-association status (protocol "vizat la zi") | High | Med | Never assert "confirmată" without a dated source in `reciprocity.json`; default stays "neconfirmată". |
| New sheet competes with the water sheet for the bottom sheet slot | Low | Low | Both use vaul; association sheet opens from the chip only, water sheet from map clicks — only one selected at a time (opening the chip clears `selectedWaterSlug`, mirroring existing selection rules). |

---

## 6. Verification checklist

- [ ] `associations.json` gains `counties` (sorted) + `reciprocity` for all 94 rows; `ape` unchanged.
- [ ] `src/types/data.ts` `Association` extended; build passes.
- [ ] Association chip + detail sheet render the validity sentence for multi-county (`aps-aqua-crisius`), single-county, and empty (`ape:0`) associations.
- [ ] Water card shows the per-water validity line under the resolved association; uncontracted waters unaffected.
- [ ] Missing-association-slug waters (4 known) do not crash.
- [ ] Reciprocity note shown everywhere, "neconfirmată", with the legal caveat.

---

## 7. Files touched (summary)

| File | Action |
|------|--------|
| `scripts/recompute_assoc_validity.py` | NEW — compute `counties` + stamp `reciprocity` |
| `public/data/associations.json` | REGENERATED — +`counties`, +`reciprocity` |
| `public/data/reciprocity.json` | NEW (empty seed) — future "confirmată" curation |
| `src/types/data.ts` | `Association` += `counties`, `reciprocity?`, `contract_ref?` |
| `src/components/associations/AssociationValidity.tsx` | NEW — validity statement + reciprocity note |
| `src/components/associations/AssociationDetailSheet.tsx` | NEW — detail sheet (vaul) |
| `src/components/associations/AssociationChip.tsx` | NEW — persistent selection chip |
| `src/components/map/MapShell.tsx` | EDIT — mount chip + sheet |
| `src/components/waters/WaterDetailCard.tsx` | EDIT — per-water validity line |

---

## 8. Reciprocity source index (for the record)

| # | Source | URL | What it establishes |
|---|--------|-----|---------------------|
| 1 | Legea 176/2024 (permit clause, via avocatnet) | `https://www.avocatnet.ro/forum/discutie_615033/Valabilitate-permis-de-pescuit.html` | Legal default: permit valid on other associations' waters "pe bază de reciprocitate" |
| 2 | AGVPS — Condiții de reciprocitate | `https://www.agvps.ro/pescuitul_in_romania/dreptul_de_reciprocitate.html` | Hotărârea 1/30.05.2015, Art.6 + Anexa 5; ½ cotizație rule |
| 3 | AGVPS — reciprocitate PDF | `http://agvps.ro/docs/reciprocitate.pdf` | Conditions of the reciprocity right |
| 4 | Circulara AGVPS 29.01.2018 | `https://www.info-delta.ro/circulara-agvps-despre-acordarea-reciprocitatii-intre-asociatiile-afiliate-pe-linie-de-pescuit/` | Affiliated associations obligated; non-affiliated (Cluj, Alba) excluded |
| 5 | Info-Delta — tipuri de permise | `https://www.info-delta.ro/care-sunt-tipurile-de-permise-de-pescuit/` | Practical: reciprocity needs a signed per-association agreement + ½ cotizație |
| 6 | AJVPS Mureș — Regulament | `https://ajvpsmures.ro/regulament-pescuit.php` | "protocol de reciprocitate, vizat la zi" phrasing |
| 7 | Claumar Pescar — ghid 2025 | `https://claumarpescar.ro/blog/ghid-permise-de-pescuit-2025` | Permit valid on other associations' waters "pe bază de reciprocitate până la finele anului" |
| 8 | Crapmania — ghid ANPA | `https://www.crapmania.ro/articole/legislatie-pescuit/permis-pescuit-anpa-1` | "pe bază de reciprocitate, este suficient un singur permis" |

**Confirmed-absent:** no ANPA/AGVPS public, structured, per-pair reciprocity list exists.
