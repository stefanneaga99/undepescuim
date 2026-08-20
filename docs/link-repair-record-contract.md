# Link repair-record fixture contract

`tests/fixtures/link_validation/repair_records_cases.json` is a deterministic, minimal fixture bundle for the repair-record inventory. It is extracted from the committed live evidence files; it does not create replacement destinations.

## Fixture contents

- `derivedFrom.report` and `derivedFrom.repairs` identify the real source reports.
- `records` contains six source validation records: one already-correct URL, one client error, one redirect, one transient failure, one policy block, and a second occurrence of an already-correct URL.
- `repairs` contains one open repair record for each failed source record. The redirect has an explicitly reviewed first-party candidate; the client-error candidate is deliberately unconfirmed. The other failed records have no candidate.
- `expected` is the assertion contract for unit/integration tests: six input records, four repair records, one duplicate URL group, one actionable reviewed candidate, and one rejected unconfirmed candidate.

The source rows retain the real URL, source path, status, HTTP evidence, redirect chain, and retry history from `data/processed/link_validation_report.json`. The repair rows use the same SHA-256 key algorithm as `scripts/link_validation_lib.py`; `originalUrl` and evidence are never rewritten.

## Output contract (inventory schema v2)

Every generated output row must contain these fields:

- Identity: `schemaVersion`, `recordKey`, `associationSlug`, `field`, `sourcePath`, `sourceKind`, `originalUrl`.
- Classification: `errorCategory`, `observedStatus`.
- Immutable audit data: `attemptHistory`, `validationResults`, `repairHistory`.
- Evidence gate: `firstPartyEvidence` (`status`, `urls`, `reviewed`, `note`).
- Decision: `candidateUrl`, `reviewStatus`, `actionability`, `repairProposal`.
- Duplicate accounting: `duplicate` (`key`, `occurrence`, `total`, `isDuplicate`).

`attemptHistory` and `validationResults` are copied from the source record. A redirect destination is evidence only, never an automatic replacement. `candidateUrl` is emitted as actionable only when a repair history item has `firstPartyEvidence.reviewed == true` and the candidate is listed in `firstPartyEvidence.urls`; otherwise it must be `null`, `reviewStatus` must be `needs_first_party_review`, and `actionability` must be `non_actionable`. Successful (`ok`) rows are `not_in_repair_scope` and have no repair proposal.

## Scenario/count matrix

| Scenario | Input records | Repair records | Actionable output | Expected handling |
|---|---:|---:|---:|---|
| Already correct URL | 1 | 0 | 0 | Preserve URL; no repair |
| Client error | 1 | 1 | 0 | Reject unconfirmed proposal |
| Redirect | 1 | 1 | 1 | Only explicit reviewed first-party destination |
| Transient result | 1 | 1 | 0 | Keep retry/attempt history; do not repair automatically |
| Blocked/policy | 1 | 1 | 0 | Policy block is not a destination |
| Duplicate already-correct URL | 1 | 0 | 0 | Keep the record; count duplicate, do not collapse it |
| **Total** | **6** | **4** | **1** | **No automatic replacements** |

The live report currently has no separate `server_error` status; server-side failures are represented by the transient/error evidence available in the report. If a future report adds that taxonomy value, it must be added as a real report-derived row rather than invented in this fixture.
