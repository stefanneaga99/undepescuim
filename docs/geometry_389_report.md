# GEOMETRY 389 — final merge report

Merge task `t_1b7c95a7` (parent `t_bebd7e7f`), 2026-08-13.
All six geometry batches (t_21fd2a04 → t_3fc96b80) committed to `main`; this task
merged their results, reconciled, rebuilt, deployed to Vercel production and
verified the live app.

## Final counts (public/data/waters.json)

| metric | before | after |
|---|---|---|
| total contracted waters | 1015 | 1015 |
| with OSM geometry | 626 | **691** |
| with bbox | 439 | 504 |
| neither geometry nor bbox | 354 | 292 (188 group members sharing a course + 104 documented unmatchable) |

Of the 389 contracted waters that had NO geometry at the start of the sweep:

| outcome | count |
|---|---|
| geometry attached (river/lake/owner-reattach) | **98** (incl. 40 sector-interval members whose group owner got a full-course geometry) |
| group-shared (member of an existing multi-contract riverGroup; course drawn by the group owner) | 124 |
| documented unmatchable — no OSM candidate in the declared county; keep bbox fallback | 175 |
| covered by t_f4ff3853 (Doftana Superioară, Prahova) outside the batches | 1 |
| **total** | **398** (389 targets + 9 already-geometry waters upgraded to full courses) |

Validator `scripts/validate_geometry_county.py`: **0 flags** (691 waters, 42 county
polygons). `npm run build` passes. Deployed to https://undepescuim.vercel.app
(production alias confirmed live).

## Per-county totals (fixed / group-shared / documented-unmatchable)

| judet | fixed | group_shared | unmatchable | total |
|---|---|---|---|---|
| Alba | 5 | 7 | 10 | 22 |
| Arad | 5 | 0 | 13 | 18 |
| Argeș | 5 | 2 | 1 | 8 |
| Bacău | 1 | 3 | 0 | 4 |
| Bihor | 3 | 2 | 13 | 18 |
| Bistrița-Năsăud | 5 | 2 | 5 | 12 |
| Botoșani | 0 | 1 | 13 | 14 |
| Brașov | 5 | 3 | 4 | 12 |
| Brăila | 1 | 0 | 3 | 4 |
| Buzău | 1 | 6 | 1 | 8 |
| Caraș-Severin | 5 | 5 | 4 | 14 |
| Cluj | 7 | 6 | 3 | 16 |
| Constanța | 1 | 0 | 2 | 3 |
| Covasna | 1 | 5 | 3 | 9 |
| Călărași | 2 | 0 | 7 | 9 |
| Dolj | 0 | 1 | 8 | 9 |
| Dâmbovița | 3 | 2 | 1 | 6 |
| Galați | 0 | 2 | 0 | 2 |
| Giurgiu | 2 | 0 | 1 | 3 |
| Gorj | 3 | 2 | 4 | 9 |
| Harghita | 2 | 12 | 4 | 18 |
| Hunedoara | 6 | 6 | 7 | 19 |
| Ialomița | 0 | 1 | 2 | 3 |
| Iași | 0 | 3 | 1 | 4 |
| Ilfov | 2 | 0 | 0 | 2 |
| Maramureș | 5 | 4 | 14 | 23 |
| Mehedinți | 1 | 1 | 0 | 2 |
| Mureș | 4 | 6 | 4 | 14 |
| Neamț | 1 | 8 | 2 | 11 |
| Olt | 3 | 1 | 0 | 4 |
| Prahova | 1 | 0 | 0 | 1 |
| Satu Mare | 0 | 3 | 3 | 6 |
| Sibiu | 2 | 4 | 6 | 12 |
| Suceava | 2 | 11 | 10 | 23 |
| Sălaj | 3 | 2 | 4 | 9 |
| Teleorman | 0 | 1 | 0 | 1 |
| Timiș | 3 | 2 | 7 | 12 |
| Vaslui | 0 | 1 | 1 | 2 |
| Vrancea | 0 | 5 | 3 | 8 |
| Vâlcea | 8 | 4 | 11 | 23 |
| **TOTAL** | **98** | **124** | **175** | **397** |

(40 counties; totals dedupe slugs listed in more than one batch category.)

## Batch summary

| batch | counties | waters | fixed | group | unmatch | commit |
|---|---|---|---|---|---|---|
| 1 (t_21fd2a04) | Suceava/Vâlcea/Maramureș/Alba | 88 | 15+5s | 26 | 45 | f742841 |
| 2 (t_0d20d433) | Hunedoara/Arad/Bihor/Harghita | 73 | 10+6s | 20 | 37 | a38b4f1 |
| 3 (t_0683d54e) | Cluj/Botoșani/Caraș-Severin/Mureș | 57 | 13+2s | 18 | 24 | 3b3c370 |
| 4 (t_8d2e4541) | Timiș/Sibiu/Brașov/Neamț/B-N | 58 | 12+5s | 19 | 24 | 631d4f7 |
| 5 (t_a15dac21) | Gorj/Călărași/Covasna/Dolj/Argeș/Buzău/Sălaj | 60 | 18+4s | 18 | 28 | 6b226d2 |
| 6 (t_3fc96b80) | Vrancea/Satu Mare/Dâmbovița/Bacău/Olt/Iași/rest | 53 | 9 | 26 | 17 | 8f28285 |

(`+Ns` = sector-interval members counted in `fixed` above; batch reports live in
`data/processed/batch{1..6}_geometry_report.json`.)

## Merge-task changes (this commit 3de184a)

1. **Degenerate lake rings stripped** — `anpa-anpa-0643` (Acumularea Râmnicu
   Vâlcea), `anpa-anpa-0645` (Acumularea Râureni), `romsilva-cluj-lacul-gilau`
   (Lacul Gilău) carried a 2–3-point sub-meter sliver ring as a second
   MultiPolygon part (lake-merge artifact); shapely's LinearRing rejects
   <4-point rings, which broke `build_uncontracted_lakes.py`. Dropped the slivers
   (script `scripts/fix_degenerate_lake_rings.py`).
2. **Identical-geometry double-draws collapsed** — `lotru` (rw5qqi3t +
   teziodii, same 1939-pt course) and `doamnei` (5pomav1f + d5xhbhta, same
   2824-pt course) each drew the full course twice; kept one owner per group,
   stripped the duplicate (script `scripts/fix_merge_double_draws.py`).
   Click resolution unchanged (sectors/Voronoi intact).
3. **Uncontracted-lakes overlay rebuilt** — `build_uncontracted_lakes.py`
   re-run against the merged waters.json: **Lacul Snagov dropped** (now
   contracted as Râul Snagov, anpa-anpa-0397) plus 6 other newly-contracted
   lakes (Pângărați, Hortop, Bucecea, Olt reservoir, Rogojești 2, unnamed
   Pângărați pond); 5719 → 5712, 0 added.

## Reconciliation checks (acceptance #2)

- `git pull --rebase origin main` — up to date; all six batch commits present
  (f742841 → 8f28285) plus the interleaved Doftana fix (1c36826).
- No lost fixes: every baseline geometry water keeps geometry, except the two
  documented somesul-cald fragment clears (batch3) and the two intentional
  merge double-draw strips (above) — all recorded.
- No bbox regressions beyond the somesul-cald documented clears.
- No NEW multi-owner riverGroups introduced by the batches (the 13 remaining
  multi-owner groups are all pre-existing; somesul-cald went 3→2 owners).
- All 22 sector_fixed members carry riverGroup + sectorStart/sectorEnd
  (geometry:null by design — the group owner draws the course).
- Round-trip serialization verified (indent=1, ensure_ascii=False, no trailing
  newline); semantic diff = exactly the 5 intended entries.

## Live verification

- Production deploy: `vercel --prod` → https://undepescuim-4kchcxrp6-stefan-a190.vercel.app
  aliased to **https://undepescuim.vercel.app**.
- Live `waters.json`: 1015 waters, 691 with geometry, 504 with bbox; Râul Snagov
  (anpa-anpa-0397) live as MultiPolygon.
- Live `uncontracted_lakes.json`: 5712, Snagov absent.
- E2E (`scripts/_e2e_merge_sample.mjs` via local chromium + libasound
  workaround): **64/64 sampled waters across 31 counties rendered** (lines,
  polygons, multipolygons) and opened a detail card with the correct county +
  association. Spot cards verified: Râul Mogoș-Cotu (AJVPS Alba), Râul Salane
  (Direcția Silvică Alba), Lac Hortop (AJVPS Arad), Râul Vl. Finiș (D.S. Bihor),
  Lacul Gilău (D.S. Cluj), Valea Lonei (AJPS Cluj), Lac acumulare Izbiceni /
  Frunzaru (AJVPS Olt), Acumularea Râmnicu Vâlcea (AJVPS Vâlcea), etc.
- Association click (`scripts/_e2e_merge_snagov.mjs`): selecting **AVPS ACVILA**
  highlights Râul Snagov (green covered stroke, 24px), clicking opens the card
  "Râul Snagov — Periș – Gruiu — AVPS ACVILA". PASSED.

### E2E harness notes (this merge)

- The app server was restarted after `npm run build` — the pre-existing
  `next start` served a STALE build manifest (missing Tailwind v4 classes, map
  container collapsed to 0px height). Kill `next-server` before `next start`.
- Local chromium (instead of the shared browserless window): extract
  `libasound2t64` into /tmp and run with
  `LD_LIBRARY_PATH=/tmp/asound/usr/lib/x86_64-linux-gnu`. The shared
  browserless window gets closed by concurrent consumers mid-run.
- Leaflet zoom under automation: `page.mouse.wheel` and zoom-control clicks are
  unreliable; a synthetic `WheelEvent(deltaY: ±60)` on `.leaflet-container` =
  exactly one zoom level (wheelPxPerZoomLevel 60). Keyboard '+' accumulates
  zoom across samples — use `setZoom()` clamps instead.
- County filter chips are DOM toggles; click via `el.click()` in page context
  (Playwright hit-test is intercepted by the z-1000 filter panel).
- With an association selected, contracted waters turn GREEN (#22c55e) and
  non-covered GREY — path finders must accept the coverage color.

## Known follow-ups (deferred, NOT fixed here)

1. **romsilva-bihor-dragan** (Drăgan, Bihor): subtype `lac` (source: 200 ha
   artificial lake) but geometry is a 24-part river course (7313 pts) — source
   data mismatch, pre-existing; no OSM lake polygon named 'Drăgan' exists in
   the water dump. Needs human decision: rename/flip subtype vs re-attach a
   reservoir polygon.
2. **sadu group** (Sibiu): ug8h7f1s full course + gff3cbfy headwater lake
   polygon (Sadu V) — lake polygon is exempt from slicing (FE pitfall #51);
   coexistence is cartographically correct, left as-is.
3. **Pre-existing identical-geometry double-draws** in groups argesel, budacul,
   crisul-negru (4 owners), malaia, prahova (3), somesu-rece, targului (3),
   teleajen, valea-robesti — all pre-date this sweep; candidates for a
   dedicated one-owner-per-group cleanup.
4. **m19ue32m/nwa37i1j == romsilva-cluj-1/2** (Someșul Cald): duplicate
   contracts with identical sector intervals — dedup candidate for the
   contract-merge task (batch3 note).
5. Botoșani 13 unmatchable: no OSM named rivers exist in-county — all listed in
   `batch3_geometry_report.json` with per-water notes.

## Artifacts

- `data/processed/batch{1..6}_geometry_report.json` — per-water detail.
- `scripts/fix_degenerate_lake_rings.py`, `scripts/fix_merge_double_draws.py`.
- `scripts/_e2e_merge_sample.mjs`, `.e2e/r_merge_snagov.png`.
