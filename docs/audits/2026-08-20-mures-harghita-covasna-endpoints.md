# Mureș–Harghita–Covasna endpoint audit (2026-08-20)

## Conclusion

This was an evidence-bounded, read-only audit. The fresh production payload is byte-identical to the checked-out local payload (`56380740bbc6a9f91a49b1f4f57ee8465821e9d144eaa39822e9d19d8caab7c0`). The fresh iPhone 14 reproduction produced 181 non-transparent blue contracted feature slugs in the reproduced unfiltered view and 356 terminal rows with exact slug, geometry, endpoint, contract, render, and pinned-source fields.

No renderer-only defect was proven, and no water data, ownership, association, county, contractual range, or source claim was changed. The ledger conservatively classifies 170 terminal rows as `legitimate_contract_endpoint` and 186 as `insufficient_provenance`; the latter require a unique relation/way ordering plus matching contract evidence before any geometry patch. There is no approved repair proposal.

## Fresh production identity

- URL: `https://undepescuim.vercel.app/data/waters.json`
- HTTP: 200; `x-vercel-cache: HIT`; `last-modified: Thu, 20 Aug 2026 17:30:33 GMT`; `etag: "b100e1c8df76beb7f14e1a9d682461b2"`
- Production SHA-256: `56380740bbc6a9f91a49b1f4f57ee8465821e9d144eaa39822e9d19d8caab7c0`
- Local SHA-256: `56380740bbc6a9f91a49b1f4f57ee8465821e9d144eaa39822e9d19d8caab7c0`
- Payload: JSON array, 1,013 waters
- Full headers: `test-results/mures-harghita-covasna-production/waters.headers.txt`
- Downloaded payload: `test-results/mures-harghita-covasna-production/waters.production.json`

## Reproduction

The probe used a fresh browser context with service workers blocked and iPhone 14 emulation (`390×664`, DPR 3). It set the map to the incident area at `[46.49, 24.88]`, zoom 9, then captured controls at zooms 7, 8, 10, and 11, plus Mureș, Harghita, and Covasna county controls and the unfiltered desktop/mobile smoke baseline.

Unfiltered zoom-9 bounds were exactly:

```json
{"west":24.345703125,"south":46.07132518308111,"east":25.4168701171875,"north":46.90712199744462}
```

Observed unfiltered blue contracted paths: 181. County control counts at the same center/bounds: Mureș 19, Harghita 45, Covasna 62. Unfiltered path counts changed with zoom (z7 812, z8 1086, z9 374, z10 640, z11 440); this is consistent with viewport/LOD changes and is not evidence of a truncated published geometry by itself.

Feature-to-DOM mapping used `window.__UNDEPESCUIM_MAP__`, `layer.feature.properties.slug`, and `layer._path`; transparent paths were excluded. All mapped blue base features were in `overlayPane`. The capture also stored the SVG `d` hash, so screenshot pixels were not used as source provenance. Focus, association, and invisible hit paths were not conflated with the blue base inventory.

Screenshots and JSON bundles:

- `test-results/mures-harghita-covasna-production/screenshot.png`
- `screenshot.json`, `screenshot-feature-paths.json`
- `z7.json`/`.png`, `z8.json`/`.png`, `z10.json`/`.png`, `z11.json`/`.png`
- `screenshot-Mureș.json`/`.png`, `screenshot-Harghita.json`/`.png`, `screenshot-Covasna.json`/`.png`
- `production-repro-summary.json`

## Exact endpoint ledger

`data/processed/mures_harghita_covasna_endpoint_audit.json` is the machine-readable ledger. It contains one row per `(slug, partIndex, terminal)` and includes:

- exact slug, published name, association, county, and `riverGroup`;
- geometry type and canonical geometry SHA-256;
- endpoint coordinate and sector/course interval;
- county-clip loaded/type/hash fields where the control payload supplied one;
- render bundle, pane, and canonical SVG path hash;
- nearest same-group published terminal and geodesic distance;
- nearest name-matched pinned-index relation/way and geodesic endpoint distance;
- classification and evidence list.

The incident ledger has 181 unique unfiltered blue slugs and 356 endpoint rows. All 356 rows have an SVG path hash. The source snapshot and generated index are immutable local artifacts:

- OSM snapshot: `data/raw/overpass_water_all.json`, SHA-256 `f7ba218227f49611cf59611f896c03effebf7bfc933c753cc56bab80e0b2bce9`
- OSM index: `test-results/mures-harghita-covasna-production/osm-index.jsonl.gz`, SHA-256 `a6f13fd420f5ea6f451a31d77b2890a49f64cd45e55cc7dcc1acc8626525e4d4`
- Index manifest: `test-results/mures-harghita-covasna-production/osm-index.manifest.json`

## Topology and classification evidence

The no-network segment audit was run against the pinned local snapshot/index and reported 19 named river relations. Its complete output is retained at:

- `test-results/mures-harghita-covasna-production/river-segment-audit.json`
- `test-results/mures-harghita-covasna-production/river-segment-audit.md`

The endpoint ledger uses geodesic distances, not longitude/latitude degree deltas. A terminal is considered legitimate only when the published contract carries a sector boundary or a name-matched pinned OSM endpoint is within the audit tolerance; otherwise it remains `insufficient_provenance`. No visual continuation was inferred. The county runs are counterfactual controls: the unfiltered reproduction has no loaded county clip, while the separate county captures record the loaded clip state where available.

## Verification

- `LIVE_PROD=1 LIVE_URL=https://undepescuim.vercel.app npm run test:e2e:live` — **8 passed (18.6s)**, four desktop and four mobile live smoke tests. Output: `test-results/mures-harghita-covasna-production/live-smoke.log`.
- Fresh production probe — **completed**, no browser console/page errors, screenshots and JSON saved above.
- Offline pinned OSM index build — **completed**, no network path used.
- Existing segment audit — **completed**, no repository data changed.

No TypeScript, unit, build, or new regression test was added because the audit did not establish a deterministic renderer defect or an approved data repair; adding a repair assertion would encode an unproven source claim. The existing live smoke suite passed on both mobile and desktop.
