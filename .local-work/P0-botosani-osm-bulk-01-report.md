# P0-botosani-osm-bulk-01 geometry repair report

- Batch: `P0-botosani-osm-bulk-01`
- County: Botoșani
- Source/type lock: `osm_bulk`
- Inventory records: 2
- Records: `anpa-anpa-0166` (Râul Baranca Hudești), `anpa-anpa-0167` (Râul Baranca Nouă)

## Result

Completed as a verified no-op. Both locked records already have source-backed Botoșani river geometry with the expected `type: ape` / `subtype: rau` shape. No geometry, source/type, county, ownership, or contract data was changed. No Class 2–6 record was touched.

Canonical geometry SHA-256 values before execution:

- `anpa-anpa-0166`: `a6342678e5c4ebf4835e0480992ae2234008e999c9eafa07f1548cf8d4731e92`
- `anpa-anpa-0167`: `a6342678e5c4ebf4835e0480992ae2234008e999c9eafa07f1548cf8d4731e92`

Both records currently carry the same five-part MultiLineString for the Baranca locality; this is retained unchanged because the batch provides no source evidence for a different course.

## Verification

- Target/source/type/county check: passed; report in `P0-botosani-osm-bulk-01-record-check.json`.
- `python3 scripts/audit_integrity.py --json /home/stefan/undepescuim-local-work/.local-work/integrity_report.json`: passed, 0 violations (143 review findings are pre-existing source-data findings).
- `python3 scripts/rebuild_data.py --verify`: passed; deterministic derivations reproduced committed outputs byte-for-byte.
- `python3 -m pytest -q tests/test_same_day_geometry.py tests/test_ialomita_geometry_regression.py tests/test_parity_vs_frontend.py`: passed, 7 tests.
- Git working tree before report-only artifacts: clean; canonical data files unchanged.
- GitHub push and production promotion: not performed, per task constraints.
