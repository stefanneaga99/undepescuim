# Link review inventory

`scripts/build_link_review_inventory.py` produces the deterministic JSONL artifact
`data/processed/link_review_inventory.jsonl` from the validator report and repair
proposals. Each row retains the original URL and has:

- `validationResults`: the complete validator record, including confidence,
  HTTP outcome, redirect chain, and retry history.
- `repairHistory`: the complete matching repair-proposal record(s), including
  action and state. An empty array means the URL passed validation and is not in
  repair scope.
- `firstPartyEvidence`: evidence URLs plus the explicit `reviewed` gate.
- `candidateUrl`: null unless a reviewer marked first-party evidence as
  reviewed and the candidate URL is one of those evidence URLs.
- `reviewStatus`: `needs_first_party_review` for failed rows (kept for
  compatibility), `reviewed_repair_ready` only after the evidence gate, or
  `not_in_repair_scope` for successful rows.
- `actionability`: `non_actionable`, `actionable`, or `not_applicable`.

Redirect destinations remain observations in `validationResults`; they are
never copied into `candidateUrl` automatically. Rows without reviewed
first-party evidence remain in the inventory and are never discarded.
