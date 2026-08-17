# UndePescuim.ro — Data-QA known gaps & residual review items

**Task:** t_45a0beae (IMPL QA-DATA, plan `docs/data-correctness-test-plan.md`)
**Updated:** 2026-08-17

This file documents the *residual* data-quality items that remain after the
A1–A5 anomaly fixes. Each item below is either (a) a documented, by-design
state, or (b) a review item flagged by the automated gates that needs a human
who can read the underlying source. **The gates themselves are green** — run
them with:

```bash
.venv/bin/python scripts/audit_integrity.py            # Layer 5 invariants
.venv/bin/python scripts/audit_source_trace.py         # Layer 3.1 traceability
.venv/bin/python scripts/validate_geometry_county.py --json data/processed/county_audit_report.json
.venv/bin/python scripts/sweep_uncontracted_overlay.py # Layer 5.1 overlap
```

The machine-readable output of the first is
`data/processed/integrity_report.json` (findings = review items, not failures).

---

## 1. A1 — non-Latin / legacy-orthography names (flagged, not fatal)

### 1.1 Cyrillic river names in the uncontracted overlay (52 rivers)

The overlay comes from OSM bulk geometry; border-area rivers are tagged in
their local script. The integrity audit flags **52 river names containing
Cyrillic letters** (`overlay.rivers.non_latin_name`), e.g. `Апшиця`,
`Бољетинска река`, `гирло Мусура – Brațul Musura`. These are genuinely
non-Latin-script OSM names (Ukraine/Serbia border) and are **flagged for
transliteration**, not auto-translated — a transliteration would require a
verified Romanian name from OSM or a gazetteer, which is manual work.

The specific A1 anomaly, the Cyrillic `Бирда` (Timiș), was **fixed** in the A1
pass (`scripts/fix_duplicate_slugs_overlay.py` transliterates it; 0 hits
remain in the published overlay).

### 1.2 Legacy orthography (cedilla `ş ţ`, a-ring `å`) — 34 published names

`waters.json` (22), `uncontracted_rivers.json` (5) and `uncontracted_lakes.json`
(7) carry pre-1993 Romanian forms: `ş`/`ţ` (s/t with cedilla) and `å`
(mis-rendered `â`, e.g. `Råul Geoagiu Inferior`). These are **flagged** as
`*.legacy_orthography` review items (distinct from the Cyrillic check). They
are not a correctness violation of the gates — normalizing them would require
updating the source jsonl (`data/processed/anpa_romsilva_waters.jsonl` etc.)
**and** re-running the full canonical rebuild, which the B5 determinism
manifest then re-pins. Deferred as a display-level polish item (owner: data
task, low priority).

---

## 2. A4 — association contact coverage (best-effort backfill done)

After the A4 backfill (`scripts/backfill_assoc_contacts.py`, sources:
`locuri_associations.jsonl` scrape + association public sites):

| Field | Coverage | Note |
|---|---|---|
| `telefon` | **74/96** | +8 since baseline (66/94) |
| `siteUrl` | **73/96** | +4 since baseline (69/94) |
| `permitUrl` | **7/96** | at source-parity — all 7 `permit_url` values present in `arebaltapeste_associations.jsonl` are already published |
| telefon **and/or** siteUrl | **89/96** | plan §4.1 target ≥90/94; the residual gap is the 7 below |

The 7 associations with **no public contact** (kept contact-free on purpose —
plan §4.1: "no public contact note, never a fake placeholder"):

- `ap-banatul` — AP BANATUL (address on file; no public phone/site found;
  Reșița relocation covered by radioresita.ro but no contact published)
- `aps-hunedoara` — APS HUNEDOARA (registry address only)
- `aps-salmo-carpatica-lupeni` — APS SALMO CARPATICA LUPENI (registry
  address only; president named in local press, no public phone)
- `a-p-s-sovata-2008` — APS SOVATA 2008 (registry address only)
- `av-vida-surducel-dobresti` — AV VIDA SURDUCEL DOBREȘTI (registry address only)
- `avps-bradul-piatra-neamt` — AVPS BRADUL PIATRA NEAMȚ (registry address only)
- `cs-hunedoara` — CS HUNEDOARA (registry address only)

`permitUrl`: only 7/96 associations publish a permit-purchase page. The rest
sell permits in person / via ANPA, or publish no public purchase page — each
missing permitUrl is a potential P1 (users can't buy the permit the card
advertises), tracked by the weekly URL audit
(`.github/workflows/url-audit.yml` → `data/processed/url_audit.jsonl`).

---

## 3. A5 — waters without geometry (documented, by design)

166 waters have no `geometry`/`point`/`bbox`:

- **139** are sector copies of a `riverGroup` — the group's single geometry
  owner carries the shape; sector copies stay geometry-free by design
  (validated by the county audit: "166 documented, 0 gaps").
- **27** carry an explicit `fallback: "no_geometry"` marker (added by
  `scripts/mark_no_geometry_fallback.py`, committed in b086805). These are
  ANPA contract rows (canals, irrigation channels, japșa) for which no OSM
  geometry or point exists and no authoritative coordinate was found. They
  render in lists/filters; the marker documents that the map cannot place
  them. List (slugs):

```
anpa-anpa-0011 anpa-anpa-0015 anpa-anpa-0018 anpa-anpa-0019 anpa-anpa-0023
anpa-anpa-0024 anpa-anpa-0026 anpa-anpa-0040 anpa-anpa-0203 anpa-anpa-0205
anpa-anpa-0206 anpa-anpa-0228 anpa-anpa-0229 anpa-anpa-0231 anpa-anpa-0236
anpa-anpa-0249 anpa-anpa-0287 anpa-anpa-0387 anpa-anpa-0415 anpa-anpa-0418
anpa-anpa-0435 anpa-anpa-0464 anpa-anpa-0499 anpa-anpa-0530 anpa-anpa-0559
anpa-anpa-0574 anpa-anpa-0623
```

Resolving them needs either a new authoritative source (ANPA sector maps) or
manual geocoding of each canal/japșa — follow-up candidate, not a gate.

---

## 4. Other documented review items

- **Traceability `AMBIGUOUS`** (3 waters): `Râul Bicaz`, `Râul Suceava`,
  `Râul Bistrița` each match 2 source rows with **different contract numbers**
  (e.g. Bicaz: `32/10.10.2017` vs `67/26.07.2018`). These are real ANPA
  multi-contract waters; a human should confirm which contract is current.
  Reported by `audit_source_trace.py` (review queue, not a hard fail).
- **Overlap sweep review queues** (from `data/sweep_overlay_report.json`):
  303 AMBIGUOUS + 36 NAME_COLLISION hits need human map-reading. The gate
  only blocks on DUPLICATE/PARTIAL_DUPLICATE (0 remaining).
- **`waters.contract_blank`** (46): ANPA canal/japșa rows carry no
  `limite`/`dimensiune` — a source gap (sector_raw null in the authoritative
  parser output), not a pipeline bug.
- **`assoc.placeholder`** (11): address fields holding "TBD"/"n/a"-style
  values instead of real addresses — flagged for manual cleanup.
- **A3**: 6 directory associations with `ape: 0` (no contracted waters in the
  current dataset) are kept in the directory — legitimate per plan §2
  (association exists; currently holds no contracted waters). The 2
  trailing-dash slug artifacts from the baseline are gone.
