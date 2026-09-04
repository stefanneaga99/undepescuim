# Deterministic river/lake geometry ledger

Locked `origin/main`: `62974d0f050b265a27dcc7ea30c6b356eb3a3454`.

## Scope and semantics

- Canonical waters: **1013** (761 rivers, 252 lakes).
- Canonical geometry: **714 present**, **299 absent**.
- Unresolved inventory: **312**; classes `{"2": 163, "3": 13, "4": 6, "5": 12, "6": 118}`.
- Class2 physical source: **148 records / 168 candidates / 76 all-candidate `(riverGroup, geometryHash)` keys**.
- Current runtime consumes candidate index 0 and deduplicates those to **69 representatives**; Production exposes only the first Buzău alias, as recorded below.
- `repaired` means render-ready canonical geometry in the frozen dataset; it does not claim this audit changed or newly proved the legal sector.
- `preview-only` is a neutral physical course and never legal ownership/association/endpoint evidence.
- `selected-focus` is runtime-only and is deliberately absent from persisted geometry variants.

## Immutable legal surfaces

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
- Buzău renders neutral teal `#14b8a6`, weight 3, dash `7 5`; its click opens the canonical AJVPS card without the physical-preview disclosure.
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
