# Feasibility Spike — Minimum Fish Retention Sizes (dimensiuni minime de reținere) + Species Search

**Spike type:** PM feasibility (problem validation → JTBD → impact vs effort → plan)
**Date:** 2026-08-16
**Author:** plan-maker profile
**Status:** VERDICT = FEASIBLE & RECOMMENDED (low effort, P2 "nice-to-have", high SEO/trust value)
**Consumes:** t_27c88f90 (fisherman complaints research) — complaint #10 + reinforcement of #1/#3.

---

## TL;DR verdict

Integrating **minimum retention sizes, searchable by species**, is **feasible and recommended** — but it is a **companion feature, not a core priority**.

- **Need:** real but the *weakest* complaint signal found (JTBD #10, pain 2/5, frequency 2/5). It does, however, directly reinforce the top job ("fish legally — avoid a fine") and plugs a gap in our own `/permis` page, which already cites the sub-size fine (300–600 lei) but ships **no size table**.
- **Data:** an **official structured list exists** (annex to Ordin MADR nr. 342/2008, ~45 species, amended by Ordin 304/2023). It is **not machine-readable** → manual entry, one time. **Critical risk:** the two main secondary sources *disagree* on several values (somn 50 vs 60 cm, avat 30 vs 40, clean 25 vs 28, scobar 20 vs 25, lipan 25 vs interzis) — the dataset **must be verified against Monitorul Oficial** before publishing.
- **Form:** standalone `/specii` page, static & server-rendered (same pattern as `/permis`), with a `cmdk` Command search (the *existing* search pattern — note: the task said "Fuse.js" but the repo actually uses **cmdk**, already a dependency). Link out from `/permis` and from water cards.
- **Effort:** ~1.5–2 dev-days (S/M t-shirt). No new dependencies, no backend.

---

## 1. Data source

### 1.1 What the legal basis is (as of 2026)

| Layer | Instrument | Role |
|---|---|---|
| Framework law | **Legea nr. 176/2024** a pescuitului și protecției resursei acvatice vii | Replaces OUG 23/2008 as the framework; delegates the size table to ministerial order. |
| Size table (the actual list) | **Ordin MADR nr. 342/2008** — anexa "dimensiunile minime individuale ale resurselor acvatice vii" | The canonical species→min-size list (~45 rows incl. marine fish + crayfish + shellfish). |
| 2023 amendment | **Ordin nr. 304/2023** (MO 785/2023) | Changed: **caras 15 → 20 cm**, **crap 35 → 40 cm**. |
| Annual prohibition periods | **Ordin MADR/MMAP nr. 23/297/2025** (and yearly successors) | Seasonal no-fishing windows per species/zone (știucă 1 feb–20 mar, șalău 20 mar–7 iun, general 9 apr–7 iun, etc.). |

> Note: minimum sizes themselves are set by ministerial order (the 342/2008 annex, amended), **not** by the framework law. The annual "ordin de prohibiție" (23/297/2025) sets *periods*, not sizes. The permit page already captures this correctly ("dimensiunile minime se schimbă anual prin ordin de ministru").

### 1.2 Is there a structured official source?

- **Yes, semi-structured.** The annex is published as an HTML table / PDF in Monitorul Oficial and mirrored by association sites. There is **no official JSON/CSV/API** — it is a legal annex, so the values must be **manually transcribed** (one-time), same as the F5 permit guide content.
- Two usable secondary mirrors that reproduce the annex:
  - **eDelta.ro** (reproduces Ordin 342/2008 + 2023 update, ~45 rows): https://www.edelta.ro/articole/info-pescar/pescuit/180-dimensiunile-minime-legale-pentru-pestii-retinuti
  - **pescuit365.ro** (a "2026" recreational table, ~20 freshwater species + protected species): https://www.pescuit365.ro/articole/dimensiuni-legale-pesti-2026.html

### 1.3 ⚠️ CRITICAL — source disagreement (must resolve before shipping)

The two main secondary sources disagree on several flagship values. This is exactly the class of risk the F5 `/permis` "last-updated + sources" honesty pattern exists to handle. **Do not publish until a human verifies against the current Monitorul Oficial text.**

| Species | eDelta (Ordin 342/2008 + 2023) | pescuit365 ("2026") | Flag |
|---|---|---|---|
| **Somn** (*Silurus glanis*) | **50 cm** | **60 cm** | 🔴 flagship — resolve |
| **Avat** (*Aspius aspius*) | 30 cm | 40 cm | 🔴 resolve |
| **Clean** (*Leuciscus cephalus*) | 25 cm | 28 cm (as *Squalius cephalus*) | 🟠 resolve |
| **Scobar** (*Chondrostoma nasus*) | 20 cm | 25 cm | 🟠 resolve |
| **Lipan** (*Thymallus thymallus*) | 25 cm | **INTERZIS** (protected) | 🔴 resolve |
| **Oblete** (*Alburnus alburnus*) | 12 cm | "—" (no limit, live bait) | 🟠 resolve |
| Caras (*Carassius gibelio*) | 20 cm | 20 cm (invaziv, no prohibition) | ✅ agree |
| Crap (*Cyprinus carpio*) | 40 cm | 40 cm | ✅ agree |
| Șalău / Știucă | 40 / 40 cm | 40 / 40 cm | ✅ agree |
| Biban | 12 cm | 12 cm | ✅ agree |
| Mreană / Plătică / Roșioară | 27 / 25 / 15 | 27 / 25 / 15 | ✅ agree |

**Recommendation:** before data entry, pull the official annex text from **legislatie.just.ro / Monitorul Oficial** (the current anexa to Ordin 342/2008 as amended, plus any 2025/2026 order) and use **that** as the single source of truth. The ANPA site (`www.anpa.ro/?p=39`, "acte normative aprobate") is JS-walled and could not be scraped in this spike.

### 1.4 Species coverage relevant to UndePescuim

- The 342/2008 annex covers **~45 taxa**, but many are marine/Delta/shellfish irrelevant to the inland map.
- The **~20 freshwater recreational species** that matter for our map: crap, caras, caracudă, șalău, știucă, somn, biban, mreană, clean, avat, plătică, scobar, văduviță, roșioară, lin, morunaș, oblete, păstrăv (indigen + curcubeu), lipan, + fully-protected list (sturioni, lostriță, asprete).
- Per-species **daily bag limits** also exist (5 kg/zi total, somn 1 ex/zi, știucă 2 ex/zi) and belong in the same dataset.

---

## 2. JTBD — does this trace to the complaints research?

Traces to **complaint #10** in t_27c88f90:

> **"When I catch a fish, help me know what it is and whether I can legally keep it (size/limit/season)."** — pain 2/5, frequency 2/5. *Weakest direct signal of the 10.*

It also **reinforces the top jobs**:

- **#1 "fish legally — avoid a fine"** (5/5 pain): the single most frequent complaint is fear of the fine; a sub-size retention carries a 300–600 lei fine (already stated on `/permis`). A species→size lookup is the cheapest "don't get fined at the water's edge" answer.
- **#3 "stay current when rules change"** (5/5 pain): sizes *did* change (2023: caras/crap) and the annual prohibition order moves windows; a `lastUpdated + sources` block matches the existing honesty discipline.

**Verdict on need:** real but **low urgency** — a "nice-to-have" that opportunistically fills a gap in our own content and earns search/trust, **not** a core map problem. Position it as the *companion* to `/permis`, not a headline feature. It is cheap precisely because it is a static content page, not new data plumbing.

---

## 3. Product form — options & recommendation

| Option | What | Effort | Value / fit |
|---|---|---|---|
| **(a) Species encyclopedia page + search** | `/specii` page, species→size+season, searchable | Low | ✅ best fit: static, searchable, SEO-rich |
| **(b) Per-water / per-association display** | show sizes on each water/association card | **Heavy** | ❌ sizes are **national**, not per-water → wrong granularity, large data + UI cost for zero added legality info |
| **(c) Standalone `/specii` + cmdk search + links** | (a) + links from `/permis` & water cards | Low–Med | ✅ **recommended** |
| **(d) Mobile-first / app-like** | dedicated species flow | Med | ↕ already covered by the mobile-layout-spec bottom-sheet pattern |

**Recommendation: (c).** A standalone `/specii` page:
- **Static & server-rendered** (mirrors `/permis`): SEO-friendly, zero runtime data.
- **cmdk Command search** for species (the *existing* pattern in `AssociationSearch.tsx`) — the task context said "Fuse.js", but the repo actually uses **cmdk** (already in `package.json`; no Fuse.js anywhere). Reuse cmdk, don't add a dependency.
- **Links in** from `/permis` (a "Dimensiuni minime pe specii" section/card) and from water cards (a small "Vezi dimensiunile legale" hint) — cheap cross-links, high discoverability.
- **Honesty block**: `SPECIES_LAST_UPDATED` + `SPECIES_SOURCES` at the bottom, same as `permis-2026.ts`, plus an explicit "valori naționale — bălțile private pot impune limite mai mari, niciodată mai mici" caveat.
- **No per-water join.** Minimum sizes are national; associating them to water records adds data-entry burden with no real value.

---

## 4. Data model

New file `src/content/species.ts` (pattern: `src/content/permis-2026.ts`). Types live alongside, mirroring existing style.

```ts
// src/content/species.ts
export const SPECIES_LAST_UPDATED = '2026-08-16'; // bump when re-verified

export type RetentionStatus = 'min-size' | 'interzis' | 'fara-limita';

export interface Species {
  slug: string;                 // 'crap', 'somn', 'salau' ...
  nameRo: string;               // 'Crap'
  nameScientific: string;       // 'Cyprinus carpio'
  category: 'rapitor' | 'pasnic' | 'salmonid' | 'invaziv' | 'protejat';
  minSizeCm: number | null;     // null when 'interzis' or 'fara-limita'
  retention: RetentionStatus;   // 'min-size' | 'interzis' | 'fara-limita'
  prohibition?: string;         // '9 apr – 7 iun' (null = none)
  dailyLimit?: string;          // '1 exemplar / pescar / zi' etc.
  notes?: string;               // 'specie invazivă, fără prohibiție'
  sourceRef: string;            // label matching SPECIES_SOURCES entry
}

export const SPECIES: Species[] = [ /* ~20 rows, one per species */ ];

export const SPECIES_PROTECTED: Species[] = [ /* sturioni, lostriță, asprete — 'interzis' */ ];

export const SPECIES_DAILY_LIMIT = '5 kg/zi total, sau un singur exemplar dacă depășește 5 kg; somn 1 ex/zi; știucă 2 ex/zi.';

export const SPECIES_SOURCES: { label: string; url: string; note: string }[] = [
  /* Ordin 342/2008 (legislatie.just.ro), Ordin 304/2023 (MO 785/2023),
     Legea 176/2024, Ordin 23/297/2025 — same honesty shape as PERMIS_SOURCES */
];
```

Key properties that make this maintainable:
- **`sourceRef` per species** — every value is attributable, matching the "no invented data" rule in `permis-2026.ts`.
- **`retention` enum** — distinguishes "has a size" from "fully protected" (lipan/sturions) and "no limit" (oblete), which is what a search result must communicate first.
- **`SPECIES_LAST_UPDATED`** — one date, shown at top + bottom, same as `/permis`.

---

## 5. Implementation sketch

| Step | File | What |
|---|---|---|
| 1 | `src/content/species.ts` | Transcribe the verified dataset (~20 species + protected list) with `sourceRef` per row. |
| 2 | `src/app/specii/page.tsx` | Server component (mirror `permis/page.tsx`): hero, `SpeciesSearch`, grouped table (pașnici / răpitori / salmonizi / protejate), daily-limit box, sources footer. |
| 3 | `src/components/species/SpeciesSearch.tsx` | `'use client'` cmdk `Command` (clone the `AssociationSearch` mobile overlay + desktop dropdown pattern, simplified — no store, just `open` state + `onSelect` scroll-to). |
| 4 | `src/components/species/SpeciesCard.tsx` (or inline) | Result card: name, scientific, big min-size number, status badge, prohibition, daily limit. |
| 5 | `src/components/layout/Header.tsx` | Add a `Specii` nav link next to `Permis 2026`. |
| 6 | `src/app/permis/page.tsx` | Add a § linking to `/specii` ("Dimensiunile minime de reținere, pe specii"). |
| 7 | `src/components/waters/WaterDetailCard.tsx` | Small "Vezi dimensiunile legale pe specii →" link (where the `/permis` link already renders). |
| 8 | `scripts/_e2e_specii.mjs` | Playwright check (repo already has `_e2e_*.mjs` scripts): page loads, search narrows, a species shows its size, sources block present. |

No new dependencies. cmdk, the UI primitives, and the `@/content/*` convention already exist.

---

## 6. Effort estimate

| Component | Estimate |
|---|---|
| Data verification vs Monitorul Oficial (human gate) | 2–4 h (one-off; the real cost) |
| `species.ts` content + sources | 1–2 h |
| `/specii` page + search + cards | 4–6 h |
| Cross-links (header / permis / water cards) | 1 h |
| e2e + lint + build | 1 h |
| **Total** | **~1.5–2 dev-days (S/M)** |

T-shirt: **S/M**. Risk is concentrated in the **data-verification gate**, not the code.

---

## 7. Acceptance criteria

1. `/specii` renders server-side; no client-side data fetch; passes `next build`.
2. Searching "somn" returns the somn row with its verified min size + prohibition + daily limit; searching "pike"/"știucă" also matches (diacritic-insensitive — cmdk handles this, verify).
3. Every species row shows a non-empty `sourceRef`, and the page footer lists `SPECIES_SOURCES` with `SPECIES_LAST_UPDATED`.
4. Protected species (sturioni, lostriță, asprete, lipan if applicable) render a distinct "interzis" state, not a number.
5. The "valori naționale / bălțile private pot fi mai stricte" caveat is visible.
6. Header shows a `Specii` link; `/permis` and water cards link to `/specii`.
7. Mobile (<768px): search opens the fullscreen cmdk overlay (same UX as association search); desktop: inline dropdown.
8. `_e2e_specii.mjs` passes.

---

## 8. Risks & tradeoffs

- **Legal accuracy is the whole product.** A wrong size (e.g. publishing somn 50 when the current rule is 60, or vice-versa) is worse than no page — it could cause a user to keep an illegal fish. Mitigation: the mandatory Monitorul Oficial verification gate; `sourceRef` + `lastUpdated`; "informații sensibile la timp, re-verifică trimestrial" footer (same as `/permis`).
- **Values change annually / by order.** Mitigation: `SPECIES_LAST_UPDATED` + a documented quarterly re-verify cadence (already the repo norm).
- **Delta / marine divergence.** The 342/2008 annex mixes inland + Delta + marine. Mitigation: scope v1 to **inland freshwater recreational species only**; note Delta (ARBDD) may differ.
- **Weak underlying demand (JTBD #10).** This is the tradeoff to accept: we're building it because it's *cheap and high-trust*, not because it's the most-requested feature. Do **not** let it displace the #1–#3 jobs (legality, reciprocity, rule-change currency).

---

## 9. Verification steps (for the spike itself + implementer)

1. Human: open the current anexa to Ordin 342/2008 (as amended) on legislatie.just.ro / Monitorul Oficial and confirm every `minSizeCm` and `retention` before code ships.
2. `cd /home/stefan/undepescuim && npm run build` — no type/lint errors.
3. `node scripts/_e2e_specii.mjs` — smoke: page renders, search narrows, sources present.
4. Manual: open `/specii`, search "somn" and "știucă"; confirm values match the verified source.

---

## 10. Sources

- Ordin MADR nr. 342/2008 (anexa dimensiuni minime) — mirrored: https://www.edelta.ro/articole/info-pescar/pescuit/180-dimensiunile-minime-legale-pentru-pestii-retinuti
- Ordin nr. 304/2023 (caras 15→20, crap 35→40) — MO 785/2023 (see eDelta "Actualizat 4 Septembrie 2023" + info-delta.ro)
- Legea nr. 176/2024 (framework) — https://legislatie.just.ro/public/DetaliiDocument/283479
- Ordin nr. 23/297/2025 (prohibition periods) — https://legislatie.just.ro/Public/DetaliiDocumentAfis/294196
- pescuit365.ro "Dimensiuni legale pești 2026" (recreational table, disputed values) — https://www.pescuit365.ro/articole/dimensiuni-legale-pesti-2026.html
- info-delta.ro "Noile dimensiuni minime 2023" — https://www.info-delta.ro/noile-dimensiuni-minime-legale-pentru-pestii-retinuti-2023/
- In-repo precedent: `src/content/permis-2026.ts`, `src/app/permis/page.tsx`, `src/components/associations/AssociationSearch.tsx` (cmdk pattern).

---

## Handoff / next step

- **This spike is complete** (verdict + plan delivered). It does **not** create implementation tasks yet — the data-verification gate and scope (inland-freshwater-only vs full annex) should be confirmed with a human first.
- After approval, spawn a **child implementation task** assigned to an engineer profile with this doc as the spec, and a small **data-verification task** (or fold it into implementation) for the Monitorul Oficial check.
