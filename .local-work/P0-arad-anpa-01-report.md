# P0-arad-anpa-01 geometry repair report

- Batch: `P0-arad-anpa-01`
- County: Arad
- Source/type lock: `anpa`
- Inventory records: 2
- Records: `anpa-anpa-0034` (Lac Mortărel), `anpa-anpa-0035` (Lac Hortop)

## Result

Completed as a verified no-op. Both locked records already have source-backed Arad lake geometry, valid bboxes/coordinates, and the expected `type: ape` / `subtype: lac` shape. No geometry or source/type/ownership data was changed. No Class 2–6 record was touched.

Canonical geometry SHA-256 values before execution:

- `anpa-anpa-0034`: `3768c6684dfb058c455776d6fcfa0513613e90448b184bcfc2d72d219661ada4`
- `anpa-anpa-0035`: `4d8c5f28e40fb3866852c02d932a37ced8777145ba55de9176920e19dbb772e2`

The prior batch evidence records `anpa-anpa-0034` as an intentionally retained bbox fallback and `anpa-anpa-0035` as a county-validated `Hortop` lake match; the current committed dataset already contains valid geometry for both, so no new attachment was justified.

## Verification

- Target/source/type/integrity check: passed; report in `P0-arad-anpa-01-record-check.json`.
- `python3 scripts/audit_integrity.py --json .local-work/integrity_report.json`: passed, 0 violations (143 review findings are pre-existing source-data findings).
- `python3 scripts/rebuild_data.py --verify`: passed; deterministic derivations reproduced committed outputs byte-for-byte.
- `python3 -m pytest -q tests/test_same_day_geometry.py tests/test_ialomita_geometry_regression.py`: passed, 3 tests.
- Git diff before report-only artifacts: no tracked files changed.
