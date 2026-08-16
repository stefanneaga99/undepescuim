# UndePescuim.ro — Data Correctness Test Plan

**Task:** SPIKE QA-2 (t_cb05da47)
**Author:** plan-maker
**Date:** 2026-08-16
**User mandate:** data correctness is THE priority ("mai ales").

> This is a **test plan + per-file checklist + automation sketch** for end-to-end
> data correctness. It does not fix data — it defines *how we prove* the data is
> correct, which checks are cheap enough to run on every commit, and which need a
> scheduled full audit. All numbers in §2 are the **live baseline** measured on
> 2026-08-16 against `~/undepescuim`.

---

## 1. Sources of truth (the authority chain)

Correctness is only definable against a source. The project already stores its
canonical inputs in `data/processed/*.jsonl` + `data/raw/*`, each row tagged with
`source`, `file`, `source_row`, and a normalized join key `name_normalized`.

| # | Source of truth | Local artifact | Records | Key fields for traceability |
|---|---|---|---|---|
| S1 | **ANPA — Lista habitatelor acvatice naturale contractate 23.02.2026** | `data/processed/anpa_waters.jsonl` | 682 | `name_normalized`, `county`, `association`, `contract_number`, `contract_date`, `source_row` |
| S2 | **ANPA — contract registry** (association blocks) | `data/processed/anpa_contracts.jsonl` | ~90 | `association`, `contracts[]`, `water_ids[]` |
| S3 | **RNP-Romsilva — Lista habitatelor de munte (2013-07)** | `data/processed/anpa_romsilva_waters.jsonl` | 289 | `name_normalized`, `county`, `association`, `directia_silvica` |
| S4 | **arebaltapeste.ro API snapshot** (contracted + assoc) | `data/processed/arebaltapeste_waters.jsonl` (426) + `arebaltapeste_associations.jsonl` (94) | 426 / 94 | `name_normalized`, `slug`, `county`, `association_slug`, `referinta`, `coordinates`, `bbox` |
| S5 | **locuridepescuit.ro** (association contact + website) | `data/processed/locuri_associations.jsonl` | 64 | `name_normalized`, `slug`, `address`, `phone`, `email`, `website`, `counties_contract` |
| S6 | **Monitorul Oficial** (species min sizes) | `data/species.json` + `docs/species-min-sizes-verified.md` | 29 | `species`, `min_cm`, `source` (each row cites MO number + date) |
| S7 | **/permis & reguli 2026** | `src/content/permis-2026.ts` + `docs/permis-reguli-2026-sources.md` | n/a | `PERMIS_SOURCES` per-fact URLs, `PERMIS_LAST_UPDATED` |
| S8 | **OSM bulk geometry** (rivers/lakes) | `data/rivers_osm.geojson`, `data/raw/overpass_water_*.json` | n/a | geometry only (not a source of *facts*, only of shape) |

**Published (frontend) datasets — the *output* under test:**

| File | Records | Role |
|---|---|---|
| `public/data/waters.json` | 1013 | contracted + Romsilva + ProPescar waters (the map) |
| `public/data/associations.json` | 94 | association directory (contact + coverage) |
| `public/data/uncontracted_rivers.json` | 4166 | uncontracted river overlay |
| `public/data/uncontracted_lakes.json` | 5712 | uncontracted lake overlay |
| `public/data/counties.geojson` | 42 | county polygons for clipping/filtering |
| `public/data/reciprocity.json` | — | curated reciprocity registry (currently empty) |
| `data/species.json` | 29 | species min-size dataset (rendered by `/specii`) |

---

## 2. Live baseline (2026-08-16) — measured, not assumed

These are the numbers every check in §3–§7 starts from. Re-measure with the
commands in §9 and diff.

| Metric | Value | Status |
|---|---|---|
| waters.json | 1013 | — |
| associations.json | 94 | — |
| uncontracted rivers / lakes | 4166 / 5712 | — |
| species.json | **29** (not "21" as in the ticket) | ⚠️ ticket stale — 21 inland + 8 fully-protected |
| waters with geometry / point / bbox | 714 / 550 / 609 | — |
| waters with **none** of geometry/point/bbox | **166** | ⚠️ see anomaly A5 |
| waters with no `asociatie` | 0 | ✅ invariant holds |
| water slug uniqueness | 1013/1013 unique | ✅ |
| association slug uniqueness | 94/94 unique | ✅ |
| **uncontracted duplicate slugs** | **4 rivers + 9 lakes** | 🔴 anomaly A1 |
| water→assoc slugs missing from directory | **4 orphan slugs** | 🔴 anomaly A2 |
| directory assoc slugs never referenced by a water | 6 (incl. 2 trailing-dash) | ⚠️ anomaly A3 |
| assoc `telefon` / `siteUrl` / `permitUrl` coverage | 66 / 69 / 7 of 94 | ⚠️ anomaly A4 |
| waters whose `referinta` cites a source list vs a contract | 321 list / ~350 "Contract N/d" / 208 Romsilva | — |

### Anomalies already visible (feed directly into the checklist)

- **A1 — duplicate `slug`s in uncontracted overlays.** 4 rivers (`unc-67f997e7ef`
  Galbena/Hunedoara, `unc-fec867f72e` Ghimbășel/Brașov, `unc-fe58a4c246` Râșca
  Mare/Cluj, `unc-b5aac05bef` Бирда/Timiș) and 9 lakes (mostly "Iaz neidentificat"
  Iași + Lacul Dobroești + Lacul Neptun I). Slugs are derived from a name hash, so
  identical `(name, county)` pairs collide. **Also note the Cyrillic "Бирда"** — a
  non-Latin name in a Romanian river list is itself a data-quality flag.
- **A2 — 4 orphan association slugs.** Waters reference `a.fly-fishing-club-sibiu`,
  `aps-pro-pescar`, `asociatia-fly-fishing-rarau`, `cs-hunedoara` but none exists in
  `associations.json` → those water cards resolve to a broken association link.
- **A3 — 6 directory slugs never referenced** (incl. trailing-dash artifacts
  `acvps-fagetel-mortonca-`, `aps-salmo-carpatica-lupeni-`). Legit if `ape:0`, but
  the trailing dash is a normalization bug, not a real slug.
- **A4 — association contact coverage is thin.** 66/94 phone, 69/94 website,
  **7/94 `permitUrl`**. The reachability check (§4) is exactly what catches stale
  placeholders here.
- **A5 — 166 waters with no geometry/point/bbox.** 139 of them carry a `riverGroup`
  (the legitimate "one geometry owner per group, sector copies stay geometry-free"
  pattern). **27 have neither a `riverGroup` nor any geometry** — these are
  undocumented gaps that need either a geometry, a point, or an explicit fallback.

---

## 3. Test plan — Layer 1: data vs source-of-truth (the critical ones)

**Goal:** every row in `waters.json` traces to a row in S1/S3/S4/S5; no orphans, no
fabrications; contract numbers/dates match.

### 3.1 Traceability (no orphans, no fabrications)

For each water, re-normalize its name with the project's own `norm()` /
`name_normalized` (see `scripts/audit_missing_rivers.py:norm`) and join against
`name_normalized` + `county` + `association` in the source jsonl.

```python
# scripts/audit_source_trace.py  (sketch)
# For every water in waters.json, find >=1 source row in
#   anpa_waters.jsonl | anpa_romsilva_waters.jsonl | arebaltapeste_waters.jsonl
# matching (name_normalized, county_id, association). Emit:
#   traced      -> {source, file, source_row, contract_number, contract_date}
#   untraced    -> water has no source row  (FABRICATION / merge artifact risk)
#   ambiguous   -> >1 source row with DIFFERENT contract numbers (merge conflict)
```

**Pass criteria (full audit):** `untraced == 0`. `ambiguous` must be human-reviewed
(counts as a finding, not a pass).

Note: `waters.json` currently has no `source_row`/`source_file` back-pointer — only
the human-readable `referinta`. **Recommended fix:** add a `provenance` object
(`{source, file, source_row}`) to each water at merge time, so traceability becomes
a cheap index lookup instead of a fuzzy re-join. Until then the check re-normalizes.

### 3.2 Contract number/date exactness

For waters whose `referinta` is `"Contract NN/DD.MM.YYYY"` (the ANPA-merged rows),
assert `contract_number` + `contract_date` equal the source row's values. Cross-check
the association's `anpa_contracts.jsonl` block: the water must be a member of
`water_ids[]` of exactly one contract that the association actually holds.

### 3.3 County correctness (extend `validate_geometry_county.py` into an audit)

`scripts/validate_geometry_county.py` already computes, per water with locatable
points: centroid distance to the declared county seat, polygon-membership counts
across all 41 county polygons, and a `wrong-county` / `outside-romania` /
`multi-county-share` / `ok` classification. **Turn it into a full audit with a
persisted report + a non-zero exit on flags:**

```bash
.venv/bin/python scripts/validate_geometry_county.py \
    --json data/processed/county_audit_report.json
# expected today: 0 FLAGGED (wrong-county + outside-romania)
```

Extensions to add to the audit script:
1. **Exit code 1 when `len(flagged) > 0`** (so it can gate CI) — today it exits 0.
2. Emit the flagged list as machine-readable `data/processed/county_audit_flags.json`.
3. Add the "no-locatable-points" waters (the 166) as a third section of the report:
   each must be justified (riverGroup sector copy) or listed as a gap.

### 3.4 `pescuit_interzis` correctness

3 waters carry `pescuit_interzis: true`. Confirm each against the source
(`arebaltapeste_waters.jsonl` preserves the flag) and against the species / season
rules in `data/species.json` (e.g. waters on a year-round-prohibited species).

### 3.5 Species (S6) — re-verify as a test fixture

`docs/species-min-sizes-verified.md` already resolved the six discrepancies against
the consolidated annex of **Ordin MADR 342/2008 (as amended by 304/2023)** and the
prohibition windows of **Ordin 23/297/2025 (consolidat 27.10.2025)**. The test plan:

- **Fixture:** a small `data/test/species_fixture.json` pinning the 21 inland
  values (poz. + `min_cm`) + the 8 protected-species flags, each with its MO
  citation. A CI test asserts `data/species.json` matches the fixture byte-for-byte
  on `(species, latin, min_cm)`.
- **Re-verify cadence:** annually before the season + immediately when MADR publishes
  a new size-table amendment or prohibition order (see `last_updated` per row).
- **Guard:** `min_cm` must be numeric > 0 for every non-protected species; protected
  species carry `min_cm: null` + a `retention: interzis` derivation. Assert the
  `/specii` page renders "interzis" for the 8 protected, never a number.

### 3.6 /permis & reguli (S7) — facts vs sources, last-updated discipline

`src/content/permis-2026.ts` already links every fact to `docs/permis-reguli-2026-sources.md`
(which itself carries a per-source confidence level HIGH/MED/PENDING). The check:

- **last-updated gate:** `PERMIS_LAST_UPDATED` must be within the re-verify window
  (≤ 3 months). Today `2026-08-15` ✅.
- **MED/PENDING facts must not render as settled:** a CI check greps
  `permis-2026.ts` for the four "re-verificat înainte de publicare" gate items
  (§5 of the sources doc) and fails if any PENDING fact is presented without a
  "proiect/în curs" qualifier.
- **URL liveness:** `PERMIS_PORTAL_URL` (and any other hardcoded URLs) must return
  HTTP 200 in a scheduled audit (reachability, §4).

---

## 4. Test plan — Layer 2: association/contact data reachability

**Goal:** association `name`, `telefon`, `adresa`, `siteUrl`, `permitUrl` are real,
reachable, and not stale placeholders.

### 4.1 Static shape

- `slug` + `name` + `name_long` present on 94/94 (already true).
- `permitIssuer` present on 94/94 (already true — `anadspa`/`romsilva`/`asociatie`).
- `telefon` and/or `siteUrl` present — target **≥ 90/94**; the 4–5 with neither get a
  "no public contact" note, never a fake placeholder.

### 4.2 HTTP reachability (scheduled audit, not CI)

For every `siteUrl` and `permitUrl` (94+ URLs), a cron-style audit does a
`HEAD`/`GET` with a browser UA and records `{slug, url, status, final_url,
checked_at}` to `data/processed/url_audit.jsonl`:

```python
# scripts/audit_urls.py  (sketch)
# for each association: GET siteUrl + permitUrl (timeout 10s, UA=Chrome)
#   ok(2xx/3xx) | redirect_to | soft_fail(4xx) | dead(5xx/DNS/timeout)
# writes data/processed/url_audit.jsonl; non-zero exit if any `dead`.
```

**Classification rule:** a 4xx/5xx for a `permitUrl` is a **P1** (users can't buy the
permit the card advertises); a dead `siteUrl` is a **P2** (stale contact). A URL that
moved (301) is auto-followed and the final URL recorded for a one-line fix.

### 4.3 Telephone shape

`telefon` must be a plausible Romanian number (regex: optional `+40`/`00 40`, 9–10
digits) — catches placeholder strings like "00 000 0000". Addresses must be
non-empty, no "TBD"/"n/a" strings.

---

## 5. Test plan — Layer 3: uncontracted overlay integrity

**Goal:** the 4166 rivers + 5712 lakes that render as "uncontracted" are (a) actually
uncontracted, (b) non-overlapping with contracted waters, (c) internally
de-duplicated.

### 5.1 Overlap sweep (already a script — make it a gate)

`scripts/sweep_uncontracted_overlay.py` runs the STRtree sweep and classifies each
hit as DUPLICATE / PARTIAL_DUPLICATE / AMBIGUOUS / TRIBUTARY / NAME_COLLISION, and
writes `data/sweep_overlay_report.json` + `.md`.

```bash
.venv/bin/python scripts/sweep_uncontracted_overlay.py
# Pass criteria: 0 DUPLICATE + 0 PARTIAL_DUPLICATE remaining.
# AMBIGUOUS / NAME_COLLISION are review queues, not gates.
```

The report already supports `--with-fixed` to append a "removed vs git HEAD" section
— keep that so each run is auditable.

### 5.2 Duplicate-slug gate (fixes A1)

Add to the invariant script (§7): slugs must be unique within each overlay. Today:
**13 duplicates** (A1) — this is a hard fail, not a warning. Fix is either
regenerating the slug with a county discriminator or de-duping the source.

### 5.3 Cross-overlay duplicate names

287 rivers and 80 lakes share a name within their own overlay (mostly legitimate:
same river name in different counties). The check must distinguish:
- same name + **different county** → OK (distinct feature);
- same name + **same county** → DUPLICATE candidate → STRtree distance confirms.
- Non-Latin names (Cyrillic "Бирда") → flag for transliteration (Romanian water
  names are Latin-script by law).

---

## 6. Test plan — Layer 4: derivation integrity (determinism)

**Goal:** the pipeline is reproducible — running it twice on the same inputs produces
byte-identical `public/data` files.

### 6.1 Canonical rebuild sequence

The pipeline is currently a loose set of scripts with no orchestrator. Define the
canonical order (inputs → outputs) in `scripts/rebuild_data.py`:

```
merge_anpa_waters.py        (anpa + romsilva + abp -> waters.json)
audit_missing_rivers.py     (attach OSM geometry to fixable rows)
build_uncontracted_rivers.py / build_uncontracted_lakes.py
sweep_uncontracted_overlay.py  (dedupe overlay vs contracted)
recompute_assoc_validity.py / recompute_assoc_counts.py
backfill_permit_urls.py
build_locality_assignment.py
build_counties_geojson.py
```

### 6.2 Hash check

```bash
scripts/rebuild_data.py --to data/_rebuild_check/   # rebuild into a scratch dir
sha256sum public/data/*.json data/_rebuild_check/*.json | diff
```

**Pass criteria:** every rebuilt file is byte-identical to the committed file.
Known non-determinism sources to fix first: (a) `merge_anpa_waters.py` fuzzy OSM
matching must be made stable (deterministic tie-breaks — `best_score` ties currently
break on dict iteration order), (b) any `set`-based iteration in slug generation.

### 6.3 Source file pinning

Determinism only holds if inputs are pinned. `sources.jsonl` already records
`raw_file_path` + `source_date` + `record_count` for every source. Add a
`data/processed/pipeline_manifest.json` that records the SHA-256 of every input the
rebuild reads, so a "changed input" can be detected before a rebuild silently
diverges.

---

## 7. Test plan — Layer 5: consistency invariants (CI gate)

One script, runnable in seconds, gates every commit. `scripts/audit_integrity.py`:

```python
# For waters.json:
#   - slug unique; slug matches ^[a-z0-9-]+$ (no uppercase/space/underscore)
#   - every water: name, judet, subtype in {lac,rau}, type == "ape"
#   - every contracted water (asociatie present) has: asociatie.slug resolving to
#     associations.json, plus limite + dimensiune non-empty
#   - every water has geometry OR coordinates OR bbox OR a documented fallback
#     (riverGroup membership counts as documented)
#   - bbox is [minLon,minLat,maxLon,maxLat] with min<=max and all in valid ranges
#     (lon in [-180,180], lat in [-90,90])
#   - coordinates is [lon, lat] in range
# For associations.json:
#   - slug unique; name+name_long+permitIssuer present
#   - ape == count of waters whose asociatie.slug == this slug (assert recompute
#     matches, or mark as stale-count finding)
#   - counties[] == sorted distinct judet of its waters (recompute_assoc_validity)
# For species.json:
#   - matches the fixture (§3.5)
# For uncontracted overlays:
#   - slug unique; uncontracted == true; lengthKm/areaHa numeric > 0
# Exit 0 iff no violation; print a machine-readable violations list.
```

**Pass criteria today:** run it and triage A1–A5 into "fixed now" vs "documented
known issue with owner". The gate only goes green once A1 (13 dup slugs) and A2
(4 orphan assoc slugs) are fixed; A5's 27 undocumented gaps are either filled or
moved to an explicit `fallback` marker.

---

## 8. Sample-vs-full policy

| Trigger | Mode |
|---|---|
| Data files changed (`public/data/*.json`, `data/*.json`, `data/processed/*`) | **FULL audit** — run all Layer 1–5 checks |
| Source re-ingest (new ANPA list, arebaltapeste re-scrape, Romsilva update) | **FULL audit** + determinism rebuild |
| UI-only change (components, styles, i18n, no data touched) | **SAMPLED** — Layer 5 invariants + Layer 3.1 trace spot-check only |
| Scheduled (weekly cron) | **FULL** reachability audit (§4.2) + county audit (§3.3) + overlap sweep (§5.1); traceability full |
| Scheduled (monthly cron) | **FULL** source-vs-published reconciliation (§3.1, §3.2) + species/permis re-verify reminder |

Rule of thumb: **data changes → full; UI-only → sampled.** The trigger is the diff,
not the calendar: a commit touching `public/data/` never skips the full run.

---

## 9. Automation sketch — what becomes CI vs cron

There is currently **no `.github/workflows` and no `test` script** (verified). This
is greenfield.

### 9.1 CI (every PR / push to `main`) — fast, deterministic, no network except geoms

`.github/workflows/data-integrity.yml`:

```yaml
name: data-integrity
on: [push, pull_request]
jobs:
  integrity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install shapely==2.1.2
      - name: Consistency invariants (Layer 5)
        run: python3 scripts/audit_integrity.py
      - name: Source traceability (Layer 3.1)
        run: python3 scripts/audit_source_trace.py
      - name: County audit (Layer 3.3)
        run: python3 scripts/validate_geometry_county.py --json data/processed/county_audit_report.json
      - name: Overlap sweep gate (Layer 5.1)
        run: python3 scripts/sweep_uncontracted_overlay.py
      - name: Species fixture (Layer 3.5)
        run: python3 - <<'PY'
import json
fixture = json.load(open("data/test/species_fixture.json"))
data = {(s["species"], s["latin"]) : s["min_cm"] for s in json.load(open("data/species.json"))}
assert all(data.get(k) == v for k, v in fixture.items()), "species drift"
PY
```

These run in seconds (STRtree sweep over ~10k geoms ≈ a few seconds), so they are
legitimate commit gates.

### 9.2 Cron audit (weekly) — slow / network-dependent / world-state checks

- **URL reachability** (`scripts/audit_urls.py`) → writes
  `data/processed/url_audit.jsonl`, opens GitHub issues (reuse the existing
  `/api/report` → `report` label mechanism, or a dedicated `data-audit` label) for
  each dead/redirected URL.
- **Source re-publication watcher:** fetch the ANPA "Lista habitatelor … contractate"
  page and compare the date in the filename to the pinned `sources.jsonl` date;
  alert when a newer edition exists (annual republish cadence confirmed in
  `anpa_probe_report.md`).
- **Species/permis re-verify reminder:** when `last_updated` / `PERMIS_LAST_UPDATED`
  exceeds 3 months, emit a reminder (this is a *prompt to re-verify against MO*, not
  an auto-update — values are legal facts, never auto-changed).

### 9.3 What stays manual

- Resolution of `AMBIGUOUS` / `NAME_COLLISION` sweep hits (needs a human who can read
  a map).
- `reciprocity.json` curation (no public registry exists — each entry needs a cited
  source; the file documents this).
- Legal re-verification of species sizes / permit rules (the checks *compare to the
  fixture*, a human re-derives the fixture from Monitorul Oficial).

---

## 10. Per-file checklist (the executable contract)

### `public/data/waters.json` (1013)
- [ ] slug unique, `^[a-z0-9-]+$` (Layer 5)
- [ ] every row: name, judet, subtype∈{lac,rau}, type="ape"
- [ ] every row traces to a source row (S1/S3/S4) — untraced == 0 (Layer 3.1)
- [ ] contract rows: contract_number+date == source (Layer 3.2)
- [ ] `asociatie.slug` resolves in associations.json (Layer 5) — fix A2
- [ ] geometry centroid/bbox inside declared county (Layer 3.3) — flags == 0
- [ ] geometry OR coordinates OR bbox OR documented fallback (Layer 5) — fix A5
- [ ] bbox/coordinates numeric + in range (Layer 5)
- [ ] no duplicate name+judet that maps to distinct geometries (Layer 5.3)
- [ ] `pescuit_interzis` matches source (Layer 3.4)

### `public/data/associations.json` (94)
- [ ] slug unique (Layer 5)
- [ ] name, name_long, permitIssuer present (Layer 4.1)
- [ ] `ape` == recomputed water count (Layer 7)
- [ ] `counties[]` == recomputed distinct judet (Layer 7)
- [ ] telefon plausible / siteUrl reachable (Layer 4.2–4.3) — improve A4
- [ ] permitUrl reachable, non-placeholder (Layer 4.2) — improve A4
- [ ] no stale "TBD"/"n/a" placeholders

### `public/data/uncontracted_rivers.json` (4166) / `uncontracted_lakes.json` (5712)
- [ ] slug unique (Layer 5.2) — fix A1
- [ ] `uncontracted == true`, lengthKm/areaHa numeric > 0 (Layer 5)
- [ ] no DUPLICATE/PARTIAL_DUPLICATE vs contracted (Layer 5.1)
- [ ] same-name+same-county pairs resolved (Layer 5.3)
- [ ] no non-Latin names (Layer 5.3)

### `data/species.json` (29)
- [ ] matches `species_fixture.json` (Layer 3.5)
- [ ] non-protected species: numeric min_cm > 0
- [ ] protected species: min_cm null + interzis flag
- [ ] `last_updated` within re-verify window (≤ 3 months)

### `src/content/permis-2026.ts`
- [ ] `PERMIS_LAST_UPDATED` within window (Layer 3.6)
- [ ] every fact has a source in `PERMIS_SOURCES`
- [ ] MED/PENDING facts carry a qualifier, not asserted as settled (Layer 3.6)
- [ ] portal/URLs live (Layer 4.2, cron)

### `public/data/counties.geojson` (42) + `reciprocity.json`
- [ ] 42 county polygons, each a valid Polygon/MultiPolygon (shapely `is_valid`)
- [ ] reciprocity entries each carry `slug`, `partners[]`, `source_url`, `source_date`

---

## 11. Risks & tradeoffs

1. **Fuzzy re-join vs explicit provenance.** Re-normalizing names to trace rows can
   false-negative (name drift) and false-positive (two same-name waters). Until the
   `provenance` back-pointer is added (§3.1), the trace check reports
   `untraced`/`ambiguous` as *review items*, not hard fails — but the **goal** is to
   make them hard fails by adding provenance at merge time.
2. **Determinism is only as good as the inputs.** The rebuild hash test will fail on
   any unpinned OSM re-download. Pin inputs with `pipeline_manifest.json` (§6.3)
   before treating a hash diff as a real regression.
3. **Reachability is world-state, not code-state.** A dead URL can be the association
   going offline, not our bug — hence cron (alert + issue) rather than CI (block).
4. **County polygon fidelity.** `validate_geometry_county.py` uses cached Nominatim
   boundaries; border-attribution artifacts (Romsilva lakes on the Făgăraș crest) are
   real and already handled via `KEEP_GEOMETRY`. Don't "fix" those — they're
   documented, correct behavior.
5. **Overlap sweep thresholds are empirical** (`EPS_DEG`, `SEARCH_DEG`, `frac_near`).
   Any threshold change re-classifies hits — version the thresholds in the report.
6. **Ticket says "21 species"; reality is 29** (21 inland + 8 protected). The fixture
   must encode 29 or the CI test will be wrong out of the gate.

---

## 12. Verification steps (run these now, in order)

```bash
cd ~/undepescuim

# 0. baseline (confirm §2 numbers)
python3 - <<'PY'
import json, collections
w=json.load(open("public/data/waters.json")); a=json.load(open("public/data/associations.json"))
r=json.load(open("public/data/uncontracted_rivers.json")); l=json.load(open("public/data/uncontracted_lakes.json"))
print(len(w), len(a), len(r), len(l), len(json.load(open("data/species.json"))))
PY

# 1. county audit (Layer 3.3)
.venv/bin/python scripts/validate_geometry_county.py --json data/processed/county_audit_report.json

# 2. overlap sweep (Layer 5.1)
.venv/bin/python scripts/sweep_uncontracted_overlay.py

# 3. determinism (Layer 6 — after adding rebuild_data.py)
#    scripts/rebuild_data.py --to data/_rebuild_check/ && diff hashes

# 4. invariants (Layer 5 — after adding audit_integrity.py)
#    python3 scripts/audit_integrity.py

# 5. species fixture (Layer 3.5)
#    python3 -c "assert json.load(open('data/species.json')) == json.load(open('data/test/species_fixture.json'))"
```

**Acceptance for this spike:** this document + the five audit scripts (§3.1, §7,
§4.2, §6.1) exist and run cleanly modulo the documented anomalies A1–A5, each of
which is either fixed or owned in a follow-up task.

---

## 13. Proposed follow-up tasks (hand-off, not scope creep)

| # | Task | Assignee | Gate |
|---|---|---|---|
| F1 | Fix A1 (13 dup slugs) + A2 (4 orphan assoc slugs) + A3 trailing-dash slugs | executioner | data |
| F2 | Add `provenance` back-pointer to waters.json + write `audit_source_trace.py` | executioner | data |
| F3 | Write `audit_integrity.py` (Layer 5) + wire `.github/workflows/data-integrity.yml` | executioner | data |
| F4 | Write `audit_urls.py` + weekly reachability cron | executioner | data |
| F5 | Write `rebuild_data.py` orchestrator + `pipeline_manifest.json` determinism | executioner | data |
| F6 | Build `species_fixture.json` from `species-min-sizes-verified.md` | executioner | data |
| F7 | Resolve A5 (27 undocumented no-geometry waters): geometry / point / fallback | executioner | data |
