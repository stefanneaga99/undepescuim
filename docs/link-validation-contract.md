# Offline link validation contract

`python3 scripts/link_validation.py --mode fixtures --report /tmp/link-report.json --repairs /tmp/link-repairs.jsonl` runs the deterministic, network-free URL policy fixtures. It never resolves DNS, opens sockets, changes source data, or follows redirects. CI uses this command plus `python3 -m pytest tests/test_link_validation.py -q`.

The report is schema version 1:

- `schemaVersion`, `generatedAt`, `mode`, and `policyVersion` identify the run.
- `summary` contains `total`, `ok`, `failed`, and stable `byStatus` counts.
- `records` are ordered by source kind, association slug, field, and source path. Each record has the source identity, sanitized `originalUrl`/`finalUrl`, status, enum `failureReason`, redirect evidence, and retry evidence. Query values named token/key/secret/password/auth/signature/session/code/email/phone are replaced with `REDACTED`.

Statuses are `ok`, `redirected`, `client_error`, `server_error`, `transient_error`, `blocked`, and `unsupported`. Failures generate idempotent manual-review JSONL records keyed by SHA-256; the validator never repairs URLs.

Supported runtime and curated fields include association site/permit URLs, embedded water association URLs, `association_locations` contact/source URLs, and provenance URL fields. The fixture registry is intentionally explicit so a new URL-bearing field requires a test update. Live reachability belongs in the scheduled/manual audit, not pull-request CI.

For a local live audit, use the separate reviewed live transport runner when available; do not change fixture mode to make network calls in CI.
