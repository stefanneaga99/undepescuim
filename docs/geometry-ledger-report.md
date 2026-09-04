# Deterministic river/lake geometry ledger

Locked `origin/main`: `62974d0f050b265a27dcc7ea30c6b356eb3a3454`.

## Scope and semantics

- Canonical waters: **1013** (761 rivers, 252 lakes).
- Canonical geometry: **714 present**, **299 absent**.
- Unresolved inventory: **312**; classes `{"2": 163, "3": 13, "4": 6, "5": 12, "6": 118}`.
- Class2 physical source: **148 records / 168 candidates / 76 all-candidate `(riverGroup, geometryHash)` keys**.
- Current runtime validates every exact candidate identity and deduplicates all candidates to **76 representatives**.
- `repaired` means render-ready canonical geometry in the frozen dataset; it does not claim this audit changed or newly proved the legal sector.
- `preview-only` is a neutral physical course and never legal ownership/association/endpoint evidence.
- `selected-focus` is runtime-only and is deliberately absent from persisted geometry variants.

## Immutable legal surfaces

- `data/processed/anpa_contracts.jsonl`: `e49b90f7d9c2d2faa214eef7d2d75ce92c4ef32ec325c615fec23a61253eb27b` (before = after)
- `data/processed/anpa_romsilva_waters.jsonl`: `e9f9e48edf79c24b54f7baf6beea3328972d3f41346b4bc42ff528e301749c6b` (before = after)
- `data/processed/anpa_waters.jsonl`: `af1311584384ae75290b43a442e6b78cb9067924a506c3c4bc6eb93033215a9d` (before = after)
- `data/processed/arebaltapeste_associations.jsonl`: `757ad07257cf42fa8c28b99ed74cd5a9c529973409a265a58cd7bf0cb236eb8a` (before = after)
- `data/processed/arebaltapeste_waters.jsonl`: `88e479305d3cb9b19ae51363328091a32f72e8ea0b79bdf077ce9fd22529b87a` (before = after)
- `data/processed/mures_harghita_covasna_endpoint_audit.json`: `065872997c7c05b0a96b33637e39fe7053bd034c79b34c48eff0faa9ec2e8dae` (before = after)
- `data/processed/permit_enrichment.json`: `e7035af369c726b1f24b32d5041814742aec2ed4ca00ce02da3e70d006110d75` (before = after)
- `data/processed/permit_overrides.json`: `4d25281bc7b3cbf7b254a235aaf77f4a05c843da4e565e92fd2da0de36f015fa` (before = after)
- `data/processed/river_segment_audit.json`: `9232fbadaa9ee3c80b0718cb9ea49eef61e1cab954c5c25b0eed0d8a2093ef35` (before = after)
- `public/data/association_locations.json`: `bc54ab5ce74c07e282ac2d1f51b16247180d2d5bfd5e3389f2c11735a9c6b9a7` (before = after)
- `public/data/associations.json`: `388ff8ef7efc267914d3a67a20f2f5a9230dd6bc0a0fdf9b87188b8f2fbaafa9` (before = after)
- `public/data/waters.json`: `56380740bbc6a9f91a49b1f4f57ee8465821e9d144eaa39822e9d19d8caab7c0` (before = after)
- `public/data/waters_county_clips.json`: `4bf26bb9d352bc112782f5dc2bc9950e5c341ee369493d39b7b84ebe2eda5e92` (before = after)

## Historical audit refs

- `origin/agent/t_6465ebb8` → `8e416fc81d469e64dc03645682a9ddf4e0a79f66`
- `origin/wt/t_86659d07` → `e6edd3e5dc83077be5303fe9b40c3a912d366e6b`

The four prior `RENDERING_FIX` rows remain `NOT_REPRODUCED` and ineligible in the confirmed-batch audit; this ledger does not approve those historical repairs.

## Pipeline manifest reconciliation

- STALE `public/data/waters_county_clips.json`: manifest `feb35105be12c8d6f85367f041d4354fb8355354919c2c3f484ccd15ef982fbc`, actual `4bf26bb9d352bc112782f5dc2bc9950e5c341ee369493d39b7b84ebe2eda5e92`

## Production browser evidence

- `390x844` / `block`: `https://unde-pescuim.ro/`; HTTP `200`; evidence `docs/evidence/production-390x844-sw-block.png`.
- `390x844` / `allow`: `https://unde-pescuim.ro/`; HTTP `200`; evidence `docs/evidence/production-390x844-sw-allow.png`.
- `1280x800` / `block`: `https://unde-pescuim.ro/`; HTTP `200`; evidence `docs/evidence/production-1280x800-sw-block.png`.
- `1280x800` / `allow`: `https://unde-pescuim.ro/`; HTTP `200`; evidence `docs/evidence/production-1280x800-sw-allow.png`.
- Limitation: Vercel inspect verified deployment ID, URL, aliases and creation time but did not expose a git commit field; commit mapping is therefore not asserted.
- Limitation: Physical-preview aliases share one deduplicated feature; clicking that feature opens its representative source card, so non-representative alias card text is not independently observable from the map layer.
- Limitation: Browser observations describe rendering only and are never legal ownership, association or endpoint evidence.
- Buzău Production feature aliases are `["anpa-anpa-0207"]` at all probes, while the source-backed ledger group has six exact aliases.
- Frozen Production baseline: Buzău renders neutral teal `#14b8a6`, weight 3, dash `7 5`; its click opened the canonical AJVPS card without the physical-preview disclosure before this runtime fix.
- Mobile probes use the Vaul bottom sheet at `35vh`; desktop probes use the right aside. All four probes reported zero console/page errors.
- Historical candidate click-resolution: Bacău Bărzăuța opens the Covasna sector card; Maramureș Crasna (Frumușaua) opens the Satu Mare Crasna card. Șugo and Geamărtălui resolve to matching-county cards.
- Per-target feature properties, styles, card text, culling-before/after-fit and visible filter controls are retained in `docs/evidence/geometry-ledger-production-observations.json`.

## Classification totals

- `preview-only`: 148
- `repaired`: 712
- `unresolved`: 153

## Source-backed render repair provenance

- County clip transition: `feb35105be12c8d6f85367f041d4354fb8355354919c2c3f484ccd15ef982fbc` → `4bf26bb9d352bc112782f5dc2bc9950e5c341ee369493d39b7b84ebe2eda5e92`; 243 entries.
- No legal/ownership/association/endpoint surface was mutated by this generator.
