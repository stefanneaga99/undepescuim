# Unified Data Model Proposal — Contracted Fishing Waters (Romania)

**Date:** 2026-08-11  
**Author:** plan-maker (t_b05125bc)  
**Status:** Draft — awaiting user confirmation  
**Sources aggregated:** ANPA PDFs, arebaltapeste.ro API, locuridepescuit.ro HTML

---

## 1. Aggregate Volume Estimate

Counts from all three probes, with overlap estimates and the union projection.

### 1.1 Associations

| Source | Distinct associations | Notes |
|--------|----------------------|-------|
| ANPA (official) | **55–60** | County-level AJVPS + specialized clubs (CS, AVPS, APS) holding ANPA contracts |
| arebaltapeste.ro | **82** | 55 have waters; 27 listed with zero waters (directory-only); includes Romsilva forest districts and ProPescar |
| locuridepescuit.ro | **64** | User-contributed WP listings; 39 counties have ≥1 association page |

**Overlap:** Significant. All ~55-60 ANPA-contracted associations appear on at least one of the two websites. The arebaltapeste set adds Romsilva districts (14) which are forest-management entities, not angling associations per se. Locuri adds smaller clubs not captured in ANPA's list.

**Union estimate: ~90–100 unique entities.** Deduplication needed across name variants (AJVPS SIBIU / AJVPS Sibiu / Asociația Județeană a Vânătorilor și Pescarilor Sportivi Sibiu).

### 1.2 Contracted Waters (Habitats)

| Source | Count | Km rows | Ha rows | Data quality |
|--------|-------|---------|---------|-------------|
| ANPA (official, 23.02.2026) | **630** | 507 (~18,400 km) | 126 (~23,000 Ha) | Authoritative but PDF-only; multi-line parsing required |
| arebaltapeste.ro | **426** | 230 (with km) | 187 (with Ha) | Structured API; 9 rows have raw/unclear dimensions; georeferenced |
| locuridepescuit.ro | **~800 (est.)** | N/A | N/A | Embedded in text; mean 12.5 waters/assoc × 64 assoc = ~800; sector-km info in parenthetical notes |

**Overlap:** arebaltapeste.ro's 426 waters are a subset drawn from various ANPA list dates (01.01.2021 through 18.02.2025, plus Romsilva mountain waters). Most map 1:1 to ANPA's 630 rows — the difference (~200 rows) reflects: (a) ANPA rows not yet ingested by arebaltapeste, (b) Romsilva-only waters not in ANPA's contracted-habitats list (they're in a separate Romsilva document), and (c) contractual churn between list editions.

**Union estimate: ~650–700 unique water sections** when merging ANPA + Romsilva additions. Locuri may surface additional user-contributed entries not in official lists.

### 1.3 Counties

| Source | Counties with contracted waters | Total mapped |
|--------|-------------------------------|-------------|
| ANPA | 38 (of 42) | 38 |
| arebaltapeste.ro | 30 | 36 (balti) |
| locuridepescuit.ro | 39 | 42 + Delta Dunării |

**Missing from ANPA contracted list:** Cluj, Mehedinți, Tulcea, București. These have associations listed on the websites but zero ANPA-contracted habitats.

### 1.4 Sector-km / Sector-Ha Coverage

- **ANPA:** 18,398 km of river sections + 22,971 Ha of lake surfaces (authoritative, stable YoY)
- **arebaltapeste.ro:** 230 km records + 187 Ha records (subset; parsing required — mixed formats: "240 Ha", "35 km", "0,24 Ha")
- **locuridepescuit.ro:** No structured field; km/Ha values embedded in water-name parentheticals

**Recommendation:** ANPA is the canonical sector-km source. Enrich with arebaltapeste coordinates.

---

## 2. Data Quality Summary

| Issue | Source(s) | Severity | Mitigation |
|-------|-----------|----------|------------|
| Association blocks span multiple rows in PDF | ANPA | High | State-machine parser with "current association" context |
| Multi-line water names/limits | ANPA | Medium | Coalesce wrapped lines before regex matching |
| Mixed km vs Ha units ("240 Ha", "35 km", "5Ha") | ANPA, arebaltapeste | Medium | Parse with unit-aware regex; store numeric + unit separately |
| Missing km/Ha values on some rows | ANPA | Low | Nullable fields; flag for manual review |
| Diacritics / case / abbreviation inconsistencies | All | Medium | Store name_normalized column (strip diacritics, lowercase) for dedup |
| Cross-county associations | ANPA | Medium | County = water county; association has a separate home county |
| arebaltapeste `dimensiune` raw formats ("12,4", "234.5", "-") | arebaltapeste | Low | Try-parse numeric; store raw string as fallback |
| Locuri SSL cert requires verify=False | locuri | Low | Document in scraper; do not fix upstream |
| Locuri ASP search is POST-only | locuri | Low | Use POST with form-encoded params |
| No km/Ha structure in locuri | locuri | Medium | Extract from parenthetical notes; cross-reference ANPA |
| User-contributed data (locuri) | locuri | High | Treat as enrichment; never as primary authority |
| Old/irregular contract dates (1982, 1987) | ANPA | Low | Store as-is; flag pre-2000 contracts |

---

## 3. Unified Data Model

### 3.1 Design Principles

1. **ANPA is canonical** — the official government list is the source of truth for water identity, limits, km/Ha, and contract status. Other sources enrich it.
2. **Source attribution per row** — every record carries a `source` field and a `source_row` reference so data lineage is traceable back to the raw file.
3. **Normalize for dedup, preserve for display** — store both `name` (raw, with diacritics) and `name_normalized` (ASCII-folded, lowercase, whitespace-collapsed) for matching.
4. **Pre-compute for the static site** — the pipeline produces flat JSON files (`associations.json`, `waters.json`) that the Next.js static export consumes directly. No database at runtime.
5. **Idempotent ingestion** — re-running the pipeline on updated sources (e.g., new ANPA yearly PDF) produces the same canonical IDs for unchanged records.

### 3.2 Entity-Relationship Diagram

```
┌──────────────┐       ┌──────────────────────┐       ┌──────────────┐
│   counties   │       │  water_associations  │       │ associations │
│──────────────│       │──────────────────────│       │──────────────│
│ id (PK)      │──1:N──│ water_id (FK)        │──N:1──│ id (PK)      │
│ name         │       │ association_id (FK)  │       │ name         │
│ name_ascii   │       │ contract_number      │       │ name_long    │
│ region       │       │ contract_date        │       │ type         │
│ has_contracts│       │ is_primary           │       │ home_county  │
│ anpa_order   │       │ source               │       │ address      │
└──────────────┘       │ source_row           │       │ phone        │
                       └──────┬───────────────┘       │ email        │
                              │                       │ website      │
                              │ N:1                   │ source_ids[] │
                       ┌──────┴───────────────┐       │ raw_files[]  │
                       │       waters         │       └──────────────┘
                       │──────────────────────│
                       │ id (PK)              │
                       │ name                 │       ┌──────────────────┐
                       │ name_normalized      │       │ source_references │
                       │ name_alt[]           │       │──────────────────│
                       │ county_id (FK)       │──N:1──│ id (PK)          │
                       │ water_type           │       │ source_name      │
                       │ sector_description   │       │ raw_file_path    │
                       │ sector_km            │       │ raw_file_url     │
                       │ sector_ha            │       │ source_date      │
                       │ sector_unit          │       │ record_count     │
                       │ limits_text          │       │ schema_version   │
                       │ coordinates (lat/lon)│       └──────────────────┘
                       │ bbox                 │
                       │ is_contracted        │
                       │ prohibition_flag     │
                       │ canonical_source     │
                       │ source_ids[]         │
                       │ raw_files[]          │
                       └──────────────────────┘
```

### 3.3 Table Schemas

#### `counties` — Romanian county registry (static lookup)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` (slug) | ✓ | Lowercase ASCII slug, e.g. `"cluj"`, `"bistrita-nasaud"` |
| `name` | `string` | ✓ | Romanian name with diacritics, e.g. `"Cluj"`, `"Bistrița-Năsăud"` |
| `name_ascii` | `string` | ✓ | ASCII-folded, e.g. `"Cluj"`, `"Bistrita-Nasaud"` |
| `region` | `string` | | Historical region / macroregion (e.g. `"Transilvania"`, `"Muntenia"`) |
| `has_contracted_waters` | `boolean` | ✓ | True if ANPA lists contracted habitats in this county |
| `anpa_section_order` | `int` | | 1-based order in the ANPA PDF (null if not in ANPA list) |

**Population:** 42 rows (all Romanian counties + Bucharest). Static. Requires no scraping.

#### `associations` — angling associations and water-managing entities

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` (UUID) | ✓ | Pipeline-generated stable ID |
| `name` | `string` | ✓ | Short display name with diacritics, e.g. `"AJVPS CLUJ"` |
| `name_long` | `string` | | Full legal name, e.g. `"Asociația Județeană a Vânătorilor și Pescarilor Sportivi Cluj"` |
| `name_normalized` | `string` | ✓ | Lowercase, diacritics-stripped, whitespace-collapsed for dedup |
| `type` | `enum` | ✓ | `ajvps` (county hunters+fishers), `avps` (local), `aps` (specialized club), `ds` (Romsilva forest district), `anpa` (agency), `other` |
| `home_county_id` | `string` (FK→counties) | | County where the association is headquartered (may differ from water county) |
| `address` | `string` | | Physical address |
| `phone` | `string` | | Phone number (raw format) |
| `email` | `string` | | Email address |
| `website` | `string` | | Website URL |
| `permit_url` | `string` | | URL for purchasing permits (arebaltapeste field) |
| `slug` | `string` | ✓ | URL-safe slug for frontend routing |
| `bbox` | `[float×4]` | | `[minLon, minLat, maxLon, maxLat]` from arebaltapeste |
| `source_ids` | `[string]` (FK→source_references) | ✓ | Which raw sources contributed this record |
| `raw_data` | `JSON` | | Full source record(s) preserved as JSON blob for debugging |

**Population:** ~90-100 rows. Pipeline merges ANPA + arebaltapeste + locuri by `name_normalized` + `home_county_id`.

#### `waters` — contracted water sections (habitats)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` (UUID) | ✓ | Pipeline-generated stable ID |
| `name` | `string` | ✓ | Water name with diacritics, e.g. `"Râul Olt"`, `"Lacul Tarnița"` |
| `name_normalized` | `string` | ✓ | Lowercase, diacritics-stripped for dedup |
| `name_alt` | `[string]` | | Alternative names/spellings (e.g. `"Raul Olt"`, `"Olt River"`) |
| `county_id` | `string` (FK→counties) | ✓ | County where the water section is physically located |
| `water_type` | `enum` | ✓ | `river`, `lake`, `canal`, `stream`, `pond`, `accumulation` |
| `sector_description` | `string` | | Human-readable sector identifier, e.g. `"Lunca Câlnicului - Feldioara - Augustin"` |
| `sector_km` | `float` | | Numeric km value (null if sector is in Ha) |
| `sector_ha` | `float` | | Numeric Ha value (null if sector is in km) |
| `sector_unit` | `enum` | | `km` or `ha` — which unit this record uses |
| `limits_text` | `string` | | Full boundary description, e.g. `"De la Steaua - la Pârâul Alb"` |
| `coordinates_lat` | `float` | | Latitude (WGS84) from arebaltapeste |
| `coordinates_lon` | `float` | | Longitude (WGS84) from arebaltapeste |
| `bbox` | `[float×4]` | | `[minLon, minLat, maxLon, maxLat]` |
| `is_contracted` | `boolean` | ✓ | True if ANPA confirms a contract exists (vs Romsilva-administered or user-reported) |
| `prohibition_flag` | `boolean` | | Fishing is temporarily or permanently prohibited (arebaltapeste field) |
| `contract_number` | `string` | | ANPA contract number, e.g. `"44/26.10.2017"` |
| `contract_date` | `string` (ISO) | | Contract date extracted from ANPA, e.g. `"2017-10-26"` |
| `canonical_source` | `enum` | ✓ | Which source is authoritative for this row: `anpa`, `arebaltapeste`, `locuri` |
| `source_ids` | `[string]` (FK→source_references) | ✓ | All source records that contributed to this water |
| `raw_data` | `JSON` | | Full source record(s) preserved as JSON blob |

**Population:** ~650-700 rows. ANPA is the seed (630 rows); arebaltapeste enriches with coordinates, subtype, and limits. Locuri adds user-reported entries not in ANPA.

#### `water_associations` — junction table: which association manages which water

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `water_id` | `string` (FK→waters) | ✓ | |
| `association_id` | `string` (FK→associations) | ✓ | |
| `contract_number` | `string` | | ANPA contract number (may differ from water-level contract if multiple associations share a water) |
| `contract_date` | `string` (ISO) | | |
| `is_primary` | `boolean` | ✓ | True for the primary managing association |
| `source` | `enum` | ✓ | Which source established this link: `anpa`, `arebaltapeste`, `locuri` |
| `source_row` | `int` | | Line number or record index in the source file |

**Population:** ~630+ rows (one per ANPA water, plus locuri water→association links). Many-to-many: a water can be managed by multiple associations (rare), and an association manages many waters.

#### `source_references` — provenance tracking for every ingested file

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` (UUID) | ✓ | |
| `source_name` | `enum` | ✓ | `anpa`, `arebaltapeste`, `locuri` |
| `raw_file_path` | `string` | ✓ | Relative path to raw file in `data/raw/`, e.g. `anpa_probe/Lista-habitatelor-...2026.pdf` |
| `raw_file_url` | `string` | | Original URL where the file was fetched |
| `source_date` | `string` (ISO) | | Date the source document was published/effective, e.g. `"2026-02-23"` |
| `ingested_at` | `string` (ISO8601) | ✓ | Timestamp when the pipeline ingested this source |
| `record_count` | `int` | | Number of records extracted from this file |
| `schema_version` | `string` | ✓ | Pipeline schema version at ingest time, e.g. `"1.0.0"` |

**Population:** One row per raw file fetched. Provides full data lineage.

### 3.4 TypeScript Interfaces (pipeline layer)

These mirror the SQL schemas above but in the TypeScript types used by the pipeline scripts before transforming to the frontend format defined in `ARCHITECTURE.md §3`.

```typescript
// src/pipeline/types.ts

export type WaterType = "river" | "lake" | "canal" | "stream" | "pond" | "accumulation";
export type SectorUnit = "km" | "ha";
export type AssociationType = "ajvps" | "avps" | "aps" | "ds" | "anpa" | "other";
export type CanonicalSource = "anpa" | "arebaltapeste" | "locuri";
export type SourceName = "anpa" | "arebaltapeste" | "locuri";

export interface County {
  id: string;
  name: string;
  name_ascii: string;
  region?: string;
  has_contracted_waters: boolean;
  anpa_section_order?: number;
}

export interface Association {
  id: string;
  name: string;
  name_long?: string;
  name_normalized: string;
  type: AssociationType;
  home_county_id?: string;
  address?: string;
  phone?: string;
  email?: string;
  website?: string;
  permit_url?: string;
  slug: string;
  bbox?: [number, number, number, number];
  source_ids: string[];
  raw_data?: Record<string, unknown>;
}

export interface Water {
  id: string;
  name: string;
  name_normalized: string;
  name_alt?: string[];
  county_id: string;
  water_type: WaterType;
  sector_description?: string;
  sector_km?: number;
  sector_ha?: number;
  sector_unit?: SectorUnit;
  limits_text?: string;
  coordinates_lat?: number;
  coordinates_lon?: number;
  bbox?: [number, number, number, number];
  is_contracted: boolean;
  prohibition_flag?: boolean;
  contract_number?: string;
  contract_date?: string;
  canonical_source: CanonicalSource;
  source_ids: string[];
  raw_data?: Record<string, unknown>;
}

export interface WaterAssociation {
  water_id: string;
  association_id: string;
  contract_number?: string;
  contract_date?: string;
  is_primary: boolean;
  source: CanonicalSource;
  source_row?: number;
}

export interface SourceReference {
  id: string;
  source_name: SourceName;
  raw_file_path: string;
  raw_file_url?: string;
  source_date?: string;
  ingested_at: string;
  record_count?: number;
  schema_version: string;
}
```

---

## 4. Deduplication Strategy

### 4.1 Association Deduplication

Association names vary across sources — the same entity appears as:
- ANPA: `"AJVPS ALBA"` (in PDF body text, upper/mixed case)
- arebaltapeste: `"AJVPS ALBA"`, name_long `"Asociația Județeană a Vânătorilor și Pescarilor Sportivi Alba"`
- locuri: `"AJVPS ALBA"` (user-entered)

**Algorithm:**
1. Compute `name_normalized` for each incoming record: lowercase, strip diacritics, collapse whitespace.
2. Group by `(name_normalized, home_county_id)` as the primary dedup key.
3. For each group, pick the longest `name_long` from all sources; use the most complete contact info (merge address, phone, email, website from whichever source has them).
4. If a source-only association has no `home_county_id` match in any group, create a new row.
5. Manual review queue: flag any group where `name_normalized` is ambiguous (e.g., "ajvps" without a county qualifier).

**Precedence for contact fields:** ANPA > arebaltapeste > locuri (ANPA is official; arebaltapeste has structured fields; locuri is user-contributed).

### 4.2 Water Deduplication

Water names overlap heavily between ANPA and arebaltapeste but with variations:

ANPA: `"Râul Sebeș"` — limits `"acumulare Petrești – conf. râul Mureș"` — 17 Km — jud. Alba
arebaltapeste: `"Râul Sebeș"` (possibly same or different section) — subtype=rau — dimensiune `"17 km"` — jud. Alba

**Algorithm:**
1. Compute `name_normalized`.
2. Match by `(name_normalized, county_id, sector_km, sector_ha)` — require all four to match for a confident merge.
3. If km/Ha values differ (or one source is missing them), fall back to `(name_normalized, county_id)` + fuzzy match on `limits_text`.
4. ANPA is always `canonical_source = "anpa"` for its records; arebaltapeste records that map to ANPA get `canonical_source = "anpa"` with arebaltapeste as enrichment.
5. Locuri waters that do not match any ANPA or arebaltapeste row are added as new rows with `canonical_source = "locuri"` and `is_contracted = false` (user-reported, unconfirmed).
6. Manual review: flag waters where `limits_text` suggests the same water but km/Ha differ significantly (>20%), or where the same water name appears in two counties (likely the same river crossing county borders — these are legitimate distinct sections, not duplicates).

### 4.3 Cross-Source Reconciliation Table

| ANPA record | arebaltapeste record | Match confidence | Action |
|------------|---------------------|-----------------|--------|
| Râul Sebeș (17 Km, Alba) | Râul Sebeș (subtype=rau, Alba) | High (name + county + km match) | Merge: ANPA as canonical, arebaltapeste supplies coords + subtype |
| Râul Olt (Sibiu section) | Râul Olt (Brașov section) | Low (same name, different counties — legitimate distinct sections) | Keep separate; different `county_id` |
| No match | Valea Răcătăului (Romsilva, Cluj) | N/A (Romsilva water not in ANPA contracted list) | Add as new row; canonical_source = arebaltapeste; is_contracted = false |

---

## 5. High-Level Implementation Plan

### Phase 1: Foundation (static data + pipeline scaffold)

Duration: ~1 session each

| Step | Task | Input | Output | Who |
|------|------|-------|--------|-----|
| 1.1 | Create `counties.json` with all 42 counties | Manual (Wikipedia/ANCPI) | `data/raw/counties.json` (42 rows) | executioner |
| 1.2 | Create `src/pipeline/types.ts` from §3.4 above | This proposal | TS interfaces for pipeline | executioner |
| 1.3 | Scaffold pipeline directory: `src/pipeline/`, `data/processed/` | — | Directory structure | executioner |

### Phase 2: ANPA PDF Parser (primary source)

Duration: 1-2 sessions

| Step | Task | Input | Output | Who |
|------|------|-------|--------|-----|
| 2.1 | Build ANPA state-machine parser | `anpa_probe/Lista-...2026.pdf` (pdftotext) | `src/pipeline/parse_anpa.py` | executioner |
| 2.2 | Extract counties, waters, associations, contracts | pdftotext output | `data/processed/anpa_waters.jsonl` (~630 lines) | executioner |
| 2.3 | Validate against probe counts: 38 counties, ~630 habitats, ~18,400 km, ~23,000 Ha | parsed output | Test assertions pass | executioner |
| 2.4 | Write `source_references` row for each ingested ANPA PDF | parser output | `data/processed/sources.jsonl` | executioner |

### Phase 3: arebaltapeste API Ingest (secondary source)

Duration: 1 session

| Step | Task | Input | Output | Who |
|------|------|-------|--------|-----|
| 3.1 | Fetch full dataset via `GET /api/search?type=ape&limit=100&skip=N` | API | `data/raw/arebaltapeste_probe/snapshot_full.json` (426 records) | executioner |
| 3.2 | Normalize fields: parse `dimensiune`, extract subtype, map to pipeline types | snapshot JSON | `data/processed/arebaltapeste_waters.jsonl` | executioner |
| 3.3 | Fetch association list via `/api/asociatii?limit=100` | API | `data/processed/arebaltapeste_associations.jsonl` (82 rows) | executioner |
| 3.4 | Write `source_references` rows | fetcher output | `data/processed/sources.jsonl` (append) | executioner |

### Phase 4: locuridepescuit Scraper (enrichment source)

Duration: 1-2 sessions

| Step | Task | Input | Output | Who |
|------|------|-------|--------|-----|
| 4.1 | Crawl all 64 association pages (verify=False, polite delay) | `association_urls.json` | 64 HTML files in `locuri_probe/` | executioner |
| 4.2 | Parse each page: extract association name, contact info, water list with parenthetical notes | HTML files | `data/processed/locuri_associations.jsonl`, `locuri_waters.jsonl` | executioner |
| 4.3 | Extract km/Ha from parenthetical notes where possible | water name strings | Enriched `sector_km` / `sector_ha` fields | executioner |
| 4.4 | Write `source_references` rows | scraper output | `data/processed/sources.jsonl` (append) | executioner |

### Phase 5: Merge & Deduplicate

Duration: 1 session

| Step | Task | Input | Output | Who |
|------|------|-------|--------|-----|
| 5.1 | Normalize all names (strip diacritics, lowercase, collapse whitespace) | All JSONL files | Normalized records | executioner |
| 5.2 | Merge associations by `(name_normalized, home_county_id)` | All association files | `data/processed/associations.json` (~90-100 rows) | executioner |
| 5.3 | Merge waters by `(name_normalized, county_id, sector_km, sector_ha)` | All water files | `data/processed/waters.json` (~650-700 rows) | executioner |
| 5.4 | Build `water_associations` junction from ANPA contract blocks + arebaltapeste `asociatie` field | Merged records | `data/processed/water_associations.json` | executioner |
| 5.5 | Write merge report: how many matched, how many new, how many flagged | Merger output | `data/processed/merge_report.md` | executioner |

### Phase 6: Transform to Frontend Format

Duration: 1 session

| Step | Task | Input | Output | Who |
|------|------|-------|--------|-----|
| 6.1 | Map pipeline types → frontend types per `ARCHITECTURE.md §3` | `data/processed/waters.json` | `public/data/waters.json` (386 for pilot; full set for production) | executioner |
| 6.2 | Map association types → frontend `Association` | `data/processed/associations.json` | `public/data/associations.json` | executioner |
| 6.3 | Generate `counties.json` with pilot flags (4 counties enabled) | `data/raw/counties.json` | `public/data/counties.json` | executioner |

### Phase 7: Pipeline orchestration script

Duration: 1 session

| Step | Task | Input | Output | Who |
|------|------|-------|--------|-----|
| 7.1 | Write `src/pipeline/run_all.py` that orchestrates phases 2-6 | All phase scripts | Single-command pipeline | executioner |
| 7.2 | Add `--pilot` flag for pilot-filtered output (4 counties) | CLI args | Pilot JSON subset | executioner |
| 7.3 | Wire into `data-refresh.yml` CI workflow | Pipeline script | Annual auto-refresh on Vercel | executioner |

---

## 6. Risks & Tradeoffs

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| ANPA updates the PDF format/layout in future editions | Medium | High — parser breaks | Version-detect from first-page headers; keep regex patterns configurable |
| ANPA PDF is merged-table layout requiring human review for ~10% of rows | High | Medium | Flag ambiguous rows; build a manual-review queue (JSON file of flagged rows) |
| arebaltapeste API goes down or changes schema | Low | Medium | Snapshot the JSON as static backup; the site has been stable for 3+ years |
| locuridepescuit SSL cert never gets fixed | Medium | Low | `verify=False` is a documented workaround; not a blocker |
| locuri user-contributed data has inaccurate water names / missing entries | High | Medium | Treat as enrichment only; never override ANPA canonical data from locuri |
| Name normalization collisions (different waters with same normalized name) | Low | Medium | Require `(name_normalized + county_id + sector_km)` for confident match; flag single-name+county collisions |
| Pipeline takes too long on first run (64 locuri pages × polite delay) | Medium | Low | Parallelize locuri crawl (3-5 workers); acceptable as one-time cost |
| Contract dates from 1982/1987 imply the data is stale for some waters | Medium | Medium | Store as-is with a `contract_date_quality` flag; surface in merge report |

---

## 7. Verification Checklist

Before marking this proposal as confirmed:

- [ ] Volume estimates (§1) are realistic — user confirms ~650-700 waters and ~90-100 associations feel right
- [ ] Schema (§3) covers all fields observed in the three probes
- [ ] Dedup strategy (§4) handles the cross-source reconciliation cases correctly
- [ ] Frontend-compatible: pipeline output maps cleanly to the `Water` and `Association` types in `ARCHITECTURE.md`
- [ ] Source attribution (`source_ids`, `source_references`) provides full lineage for every record
- [ ] Implementation plan (§5) phases are clear and assignable to downstream workers

---

## 8. Files Referenced

| File | Role |
|------|------|
| `/home/stefan/undepescuim/data/raw/anpa_probe_report.md` | Primary source probe report |
| `/home/stefan/undepescuim/data/raw/arebaltapeste_probe_report.md` | Secondary source probe report |
| `/home/stefan/undepescuim/data/raw/locuri_probe_report.md` | Enrichment source probe report |
| `/home/stefan/undepescuim/data/raw/arebaltapeste_probe/snapshot_waters.json` | 426 reference water records |
| `/home/stefan/undepescuim/data/raw/arebaltapeste_probe/snapshot_asociatii.json` | 82 reference association records |
| `/home/stefan/undepescuim/data/raw/locuri_probe/sample_parsed_entries.json` | 6-association sample (75 waters) |
| `/home/stefan/undepescuim/data/raw/locuri_probe/association_urls.json` | 64 locuri association URLs |
| `/home/stefan/undepescuim/docs/ARCHITECTURE.md` | Frontend types to align pipeline output with |
| `/home/stefan/undepescuim/data/raw/anpa_probe/Lista-habitatelor-acvatice-naturale-contractate-23.02.2026.pdf` | Canonical ANPA water list |





