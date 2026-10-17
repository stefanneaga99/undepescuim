# River geometry v2 — handoff to a local Claude Code session (2026-10-17)

Read first: `AGENTS.md` (QA gate: logic changes ship tests), `docs/plans/river-geometry-v2.md` (the plan), this file.
Owner: Stefan (stefan.neaga99@icloud.com), GitHub `stefanneaga99/undepescuim`. Work autonomously; merge a PR when its core checks are green
(`ts`, `py`, `integrity`, `Data payload budgets`). `Audit & static gates`, `Dependency review`, Lighthouse, Playwright, e2e are pre-existing reds and do not block. No branch protection on `main`.

## State
- Merged: P0, Track A (extract, graph, courses, LR, QA, `build`), Track B (`limite` parser, matcher, resolvers, sectors, report, review page), `publish` core (shadow/write), first real run (#19).
- Open: PR #20 (matcher endpoint evidence + confluence base-name fallback + refreshed data). Merge it first if green.
- Pinned input: release `osm-extract-20261017` (OSM 2026-10-16), sha256 in `data/rivernet/input_manifest.json`. Download with `gh release download osm-extract-20261017 -p water-extract.jsonl.gz`.
- Pipeline (all `PYTHONPATH=scripts python -m rivernet ...`): `build` -> `parse` -> `match --extract` -> `resolve --extract` -> `report` -> `review-page --all` -> `publish --mode shadow`. Build takes ~10 min (use `--waters ''`-free default).
- Result on 761 river waters: 104 resolved / 97 review / 560 unresolved. Alba: 3/41 resolved. Causes: 235 waters have no OSM course under that name (small streams); endpoints that are not mappable features ("Cheile Râmeț", "uzina…"); tributary confluences with no OSM course.
- `public/data/waters.json` is untouched. Never run `publish --mode write` or commit changes to `public/data/` without the owner's explicit approval (cutover = T4.4, owner step O5).

## Your goals, in order
1. **Second geometry source for the unresolved small streams** (the biggest lever).
   - Open https://data.gov.ro/dataset/hidrografie in a browser; the "Cursuri de apa rauri" and "Confluente si izvoare" resources are the candidates. Record format, size, scale, licence in `docs/data-sources/hidrografie.md`. If open (OGL-ROU-1.0 or similar), download, normalise to the extract schema (§3.3 of the plan: ways with `waterway`, name, coords; node `place`/spring for sources and confluences), and add an adapter in `scripts/rivernet/` that merges it as a *fallback* layer: OSM stays primary, the new layer only fills courses OSM lacks. Keep licences/attribution (extend `public/data/osm-lineage.json` + `MapAttribution.tsx` only at cutover).
   - If it is not usable, check the EEA WISE WFD2022 centrelines (CC BY 4.0, ArcGIS service `WISE_WFD/WFD2022_SurfaceWaterBodyCentreline_WM/MapServer/0`, RO ≈ 12,190 features, names in `geographicalNameText`, codes `RORW…`/`ROLW…`) and EU-Hydro v1.3. Measure: of the 235 `no_candidate` + 30 `no_county_match` waters in `data/sectors/matches.jsonl`, how many get a course. Report the number before building more.
   - Draft the Law 544/2001 request to ANAR for the cadastral river network (Romanian, ready to send) in `docs/data-sources/anar-request-ro.md`.
2. Re-run the pipeline, aim to lift `resolved` materially; inspect `data/sectors/progress.json` top reasons. Typical fixes: endpoint forms the parser misses, tributary confluences, county-border rivers (alternating county intervals), course fragments that are too short (e.g. Siriu 8 km vs 38 km contract).
3. **T4.1 frontend pre-cut support** (see plan; needs local `npm ci`, `npm test`, a dev server, and a look at the map in a browser).
4. **T4.2 tail** (simplify skip, county clips, ledger `resolved-limite`, class-2 preview, `rebuild_data` step) with tests.
5. T4.3 evidence file + card UI. Stop before T4.4 cutover and ask the owner: spot-check of review pages (O4) and go/no-go (O5).

## Rules that bit before
- D8: a multi-contract `riverGroup` switches only if every member resolves; unresolved waters keep legacy geometry ("never worse").
- Ledger embeds the manifest hash: changing `data/rivernet/input_manifest.json` requires regenerating the 4 geometry-ledger outputs and `tests/test_geometry_ledger.py` expectations.
- Local tests: `pip install -r requirements-dev.txt` then `python -m pytest`; vitest via `npm test`. Do not hit the network in tests. Fixtures are hand-labelled (`tests/fixtures/rivernet/limits_cases.json` is never generated from parser output).
- One branch + one PR per task; PR bodies end with the attribution lines the harness gives you.
- Update the project doc `claude/river-geometry-v2-status.md` (Projects tool) after each merged milestone.
