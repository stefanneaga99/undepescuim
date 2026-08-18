# GitHub #44 — Pârâul Cușmed și Târnava Mică

## Goal

Determine whether the reported Mureș sector of Pârâul Cușmed (`anpa-anpa-0439`) and its receiving river, Târnava Mică, are represented with the correct confluence geometry and contractual association. Change data only if a source/geometry disagreement is proven; otherwise close the report with traceable evidence.

## Decision from investigation

**Current data is correct; no pipeline or published-data change is warranted.**

The report is about the Mureș contract, not the similarly named upstream Harghita contract:

| Water / sector | Published slug | Canonical source record | Contract association |
| --- | --- | --- | --- |
| Pârâul Cușmed, Mureș, `Limită jud. Mureș, loc. Sângeorzu de Pădure – conf. cu Târnava Mică` | `anpa-anpa-0439` | `anpa-0439`, source row 1001 | AJVPS MUREȘ, `40/24.10.2017` |
| Târnava Mică, Mureș, `Limită Jud. conf. cu pârâul Iuhod – comuna Adămuș sat Cornești` | `anpa-mures-tarnava-mica-96` | `anpa-0436`, source row 996 | AJVPS MUREȘ, `40/24.10.2017` |
| Târnava Mică, Harghita upstream sector | `anpa-harghita-tarnava-mica-5` | `anpa-0330`, source row 737 | AVPS TÂRNAVA MARE, `46/15.01.2018` |

### Evidence

1. The ANPA source is authoritative for contractual attribution:
   `data/raw/anpa_probe/Lista-habitatelor-acvatice-naturale-contractate-23.02.2026.txt`, lines 995–1002, lists both the Mureș Târnava Mică sector and Cușmed under the AJVPS MUREȘ block / contract `40/24.10.2017`.
2. Parsed, traceable records retain that provenance in `data/processed/anpa_waters.jsonl` (`anpa-0436`, `anpa-0439`), and `data/processed/traceability_report.json` resolves both published slugs to those rows with `contracts_seen: 1`.
3. `public/data/waters.json` correctly preserves `AJVPS MUREȘ` and its permit URL for both Mureș sectors. The two Târnava Mică contracts intentionally share `riverGroup: "tarnava-mica"`; the full course geometry is owned once by the Alba entry `hj594dti`, while the Harghita/Mureș sector records retain `course_frac` click targets. This is the project’s documented one-geometry-owner model, not a missing river.
4. The same published Cușmed geometry is used by `anpa-anpa-0320` (Harghita) and `anpa-anpa-0439` (Mureș): 45 OSM points from `[25.04643, 46.47725]` to `[24.84841, 46.43123]`. Its downstream endpoint agrees with the independent Fishsurfing listing (`46.431278, 24.848777`) and with the source limits.
5. The independent academic source, *Implicații social economice ale amenajării lacului de acumulare Bezid (Bazinul Târnavei Mici)* (Limnology.ro, p. 58), identifies Cușmed as a left tributary of Târnava Mică and locates the Bezid dam 1.5 km upstream of the confluence. This independently confirms the hydrographic relation.
6. `scripts/validate_geometry_county.py --json /tmp/geometry-county.json` classifies `anpa-anpa-0439` as `ok`: it crosses Harghita and Mureș and has 12 dense sampled points in its declared Mureș county. Its cross-county course is expected and does not indicate a same-name geometry collision.

## Architecture / data flow

```text
ANPA raw text
  -> data/processed/anpa_waters.jsonl (source row + contract data)
  -> scripts/merge_anpa_waters.py / targeted basin mapping
  -> public/data/waters.json
  -> riverGroup owner geometry + course_frac sector selection in UI
```

Contract attribution is per source sector, not inferred from the confluence. Sharing a river group/geometry does not merge association ownership across county/contract boundaries.

## Execution plan

### 1. Reconfirm only if the pinned source changes (2 min)

Files:
- `data/raw/anpa_probe/Lista-habitatelor-acvatice-naturale-contractate-23.02.2026.txt`
- `data/processed/anpa_waters.jsonl`
- `data/processed/anpa_contracts.jsonl`
- `data/processed/traceability_report.json`

Run a targeted read/query and assert:

```bash
python3 - <<'PY'
import json
from pathlib import Path
rows = [json.loads(x) for x in Path('data/processed/anpa_waters.jsonl').read_text().splitlines()]
for row_id in ('anpa-0436', 'anpa-0439'):
    row = next(x for x in rows if x['id'] == row_id)
    assert row['county'] == 'MUREȘ'
    assert row['association'] == 'AJVPS MUREȘ'
    assert row['contract_number'] == '40/24.10.2017'
print('ANPA Mureș attribution confirmed')
PY
```

Do not edit a contract merely because another upstream Târnava Mică sector belongs to AVPS TÂRNAVA MARE.

### 2. Verify geometry and sector-resolution invariant (3 min)

Files:
- `public/data/waters.json`
- `data/cache/osm_river_clusters.pkl` (geometry input only)
- `scripts/validate_geometry_county.py`

Confirm `anpa-anpa-0439` has the Cușmed course geometry, ends near `[24.8488, 46.4313]`, and the Mureș Târnava Mică entry is still a `tarnava-mica` group sector attributed to AJVPS MUREȘ. Confirm the owner entry `hj594dti` still carries the Târnava Mică course geometry.

Run:

```bash
.venv/bin/python scripts/validate_geometry_county.py \
  --json /tmp/github-44-county-audit.json
python3 scripts/audit_source_trace.py
```

Pass condition: `anpa-anpa-0439` is classified `ok` or an explicitly supported multi-county variant; traceability resolves it to only `anpa-0439`; `anpa-mures-tarnava-mica-96` resolves to only `anpa-0436`.

### 3. Add a regression only if an implementation/data edit becomes necessary (5 min)

No test change is required for the current no-change resolution. If a future source refresh, mapping change, or geometry repair touches this relationship, add a focused snapshot assertion to `tests/test_county_validator.py` (or a new `tests/test_cusmed_tarnava_mica.py` if it needs geometry helpers).

The test must load committed `public/data/waters.json` and assert:

```python
by_slug = {water['slug']: water for water in waters}
cusmed = by_slug['anpa-anpa-0439']
tarnava_mures = by_slug['anpa-mures-tarnava-mica-96']
owner = by_slug['hj594dti']

assert cusmed['asociatie']['slug'] == 'ajvps-mures'
assert cusmed['referinta'] == 'Contract 40/24.10.2017 (2017-10-24)'
assert cusmed['geometry']['type'] in {'LineString', 'MultiLineString'}
assert tarnava_mures['asociatie']['slug'] == 'ajvps-mures'
assert tarnava_mures['riverGroup'] == 'tarnava-mica'
assert owner['riverGroup'] == 'tarnava-mica'
assert owner['geometry']['type'] in {'LineString', 'MultiLineString'}
```

If geometry is changed, extend the assertion with a stable downstream endpoint tolerance around the independent Fishsurfing coordinate rather than exact full-coordinate equality, so simplification does not create false failures.

Run the mandatory pipeline tests for any script/data-pipeline change:

```bash
.venv/bin/python -m pytest tests/test_county_validator.py tests/test_merge_anpa_waters.py
.venv/bin/python -m pytest
python3 scripts/rebuild_data.py --check
npm test
```

If public data is intentionally regenerated, re-pin only after the full rebuild/gates pass:

```bash
python3 scripts/rebuild_data.py --to data/_rebuild_check
python3 scripts/rebuild_data.py --manifest
python3 scripts/rebuild_data.py --check
```

Do not treat the current `--check` drift as evidence against #44: the working tree already contains unrelated uncommitted rebuild work (`public/data/waters.json` and `scripts/rebuild_data.py`). Isolate/stash it before a clean verification.

### 4. Close the user report with sources (2 min)

Post this concise conclusion to GitHub #42, then close #44 as no-change:

> Verificat: Pârâul Cușmed din raport (`anpa-anpa-0439`) se varsă în Târnava Mică, iar relația este corectă în date. ANPA listează atât Cușmed (10 km), cât și sectorul Mureș al Târnavei Mici (96 km) sub AJVPS MUREȘ, contractul 40/24.10.2017 (Lista habitatelor contractate 23.02.2026, rândurile 996 și 1001). Geometria Cușmed ajunge la confluență în zona Sângeorgiu de Pădure; o sursă hidrologică independentă confirmă Cușmed ca afluent stâng al Târnavei Mici. Târnava Mică are și un sector distinct în Harghita, contractat separat de AVPS Târnava Mare — acesta nu schimbă atribuirea sectorului Mureș. Nu este necesară corectare de date/pipeline.

Include URLs:
- `https://github.com/neagastefan99/undepescuim/blob/main/data/raw/anpa_probe/Lista-habitatelor-acvatice-naturale-contractate-23.02.2026.txt`
- `https://www.limnology.ro/water2010/Proceedings/58.pdf`
- `https://www.fishsurfing.com/sv/map/paraul-cusmed-1304662703/`

## Correct / change decision rule

Close as **correct / no change** only when all are true:

1. ANPA source rows `anpa-0436` and `anpa-0439` still name AJVPS MUREȘ and contract `40/24.10.2017`.
2. Published Mureș sector entries preserve that association/contract and source trace.
3. Cușmed’s downstream geometry remains at the Târnava Mică confluence and passes the county validator without a wrong-county/outside-Romania flag.
4. The shared `tarnava-mica` geometry owner plus Mureș sector target still exists, so the river is both visible and contract-selectable.

Make a **data change** only if a newer authoritative ANPA record changes the Mureș association/contract, the source-trace join becomes ambiguous/untraced, or geometry no longer reaches/represents the documented Cușmed–Târnava Mică confluence. A change must include the regression test and the full pipeline gates above.

## Risks / tradeoffs

- Cușmed has two contracts: the Harghita 20 km portion (AVPS HUBERTUS) and the Mureș 10 km portion (AJVPS MUREȘ). Name-only matching would incorrectly collapse them; always use slug/county/limits/contract together.
- The Târnava Mică geometry is intentionally shared under an Alba owner. Copying it onto every contract sector would increase payload and defeat the river-group model.
- Source downloads can change between runs. Record the source date and row IDs in the GitHub response; do not use secondary fishing-directory pages as contractual authority.
