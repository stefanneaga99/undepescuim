# Confirmed rendering execution-batch manifest

**JSON is authoritative:** `.local-work/river-geometry-confirmed-batches.json`.

## Decision

**Blocked; zero confirmed execution batches.** This is a manifest-only result. No river record is fixed, approved, or scheduled.

The strict gate is not met: the parent Phase-1 audit identifies four `RENDERING_FIX` classifications, but every one has `reproduction.status: NOT_REPRODUCED`; there are no two clean reproducible root-cause observations and no recorded reviewer acceptance.

## Locked parent evidence

| Item | Value |
|---|---|
| Parent audit SHA-256 | `98c0d40bf327eaa69e2242c80ddd3f24224dde34fcf6fc7bb9fed287476d2bae` |
| Parent manifest SHA-256 | `e61cdc90f29e67725c77d0938385191da84fea0fa8388a300faee10d98ffa029` |
| Parent report SHA-256 | `0a9e8c487e9ca3c5d99443b9f7bb241a944b9a74c640832886aedd528d469017` |
| Selected river records | 295 |
| Record-slug-set SHA-256 | `873c0b0acb14ccb13cdf4e9771bb683e978b835958b90aa898c57383e753c91a` |
| Rejected/non-river or missing joins | 17 (identities not exposed by parent artifact) |

Canonical before/after hashes in the parent audit are identical for waters, county clips, segment audit, and render provenance. The missing Class-2 physical preview artifact remains unavailable evidence; it is not substituted.

## Rendering candidates rejected from batching

| Slug | County | River group | Canonical geometry hash | Reproduction | Reason |
|---|---|---|---|---|---|
| `romsilva-bacau-barzauta` | Bacău | `barzauta` | `33c87ab3f0c73fe554a05bd798d10f2efbabe29ac7df6ce83cd1bd6f94d4f882` | `NOT_REPRODUCED` | requires two clean reproducible root-cause observations; parent audit marks reproduction NOT_REPRODUCED |
| `romsilva-covasna-sugo` | Covasna | `sugo` | `02ce3e2c49f7857bb41b6ec06633f8bf3601829cc3bf9a42b286a207e9f9c6b4` | `NOT_REPRODUCED` | requires two clean reproducible root-cause observations; parent audit marks reproduction NOT_REPRODUCED |
| `romsilva-maramures-crasna-frumusaua` | Maramureș | `crasna` | `72296fcead3dcd206ab1cdbae03e20c86e5a021c275f31b9ed0c72c10bfdd03a` | `NOT_REPRODUCED` | requires two clean reproducible root-cause observations; parent audit marks reproduction NOT_REPRODUCED |
| `vb2p0152` | Olt | `geamartalui` | `4b556411ff5991cf37c2b5b7521214697d31c3aa11cabafdb6d70c56f5d0ce33` | `NOT_REPRODUCED` | requires two clean reproducible root-cause observations; parent audit marks reproduction NOT_REPRODUCED |

All 295 audited record hashes are retained in the JSON. The four rows above are the only candidates with the parent classification `RENDERING_FIX`; the remaining 291 records are ineligible by classification precedence. No rows are packed because the two-pass reproduction gate fails before county/source partitioning.

## Safety and sequencing

- `confirmedExecutionBatches` is empty.
- No implementation cards are created.
- Any future batch must contain 10–20 eligible rivers, one normalized county and source family, no duplicate slug/riverGroup/geometry hash, a fresh isolated worktree rooted at the locked commit, and one active executioner.
- Physical geometry is not contractual or legal-sector geometry. No legal endpoints, ownership, association, contract, or deployment facts were inferred or changed.
- This output is local-only and does not approve or schedule a repair.
