# SPIKE — audit național pe segmente de râu și validator permanent

## Verdict / GO-NO-GO

**GO condiționat pentru implementare, fără schimbare de date sau de contracte în acest card.** Repo-ul are deja blocuri utile, dar nu un guard care demonstrează că un curs contractat este complet pe fiecare segment:

- `scripts/audit_regions.py` are un grid 0.5° și clasifică 7.699 clustere OSM; snapshotul actual arată 936 `present`, 6 `present-hidden`, 1 `present-bbox`, 1 `anpa-missing` și 6.755 `uncontracted`.
- `scripts/audit_missing_rivers.py` preferă relații OSM și grupează ways, însă `cluster_parts(... max_gap_deg=0.06)` acceptă un gol de circa 6,7 km; este bun pentru matching, nu pentru a dovedi continuitatea unui râu.
- `scripts/build_uncontracted_rivers.py` și `scripts/sweep_uncontracted_overlay.py --gate` apără contra dublării contracted↔uncontracted, dar nu pot semnala o **bucată lipsă din geometria contractedă** dacă ea nu reapare ca overlay.
- `scripts/validate_geometry_county.py` este verde în snapshot (0 county flags, 0 gaps), dar validează județul unei geometrii deja atașate, nu completitudinea topologică față de relația/ways OSM.
- UI-ul calculează corect `fractionAtPoint` / `contractAtFraction` în `src/utils/river-course.ts`, însă contractele publicate folosesc `course_frac`, `sectorStart`, `sectorEnd`; nu există câmpul `contractAtFraction`. Noul validator trebuie să emită probe la fracții și să testeze funcția, nu să inventeze un câmp de date.

**NO-GO pentru auto-remediere:** orice `missing_contracted`, `ambiguous_relation`, `source_contract_conflict`, `sector_mismatch` sau `unresolved_no_osm_match` oprește publicarea/re-pin-ul, intră în review queue și nu modifică automat `waters.json`, `riverGroup`, asociația sau contractul. OSM este sursă geometrică; ANPA/arebaltapeste/Romsilva rămân sursele contractuale.

Skills solicitate de card (`osm-geodata-pipelines`, `live-map-qa`, `qa-strategy`) nu sunt instalate în profilul de lucru (`skill_view` a raportat lista disponibilă goală). Inventarul și planul de mai jos se bazează pe codul și testele din repo, fără a pretinde conținutul acelor skill-uri.

## Scop, arhitectură și surse de adevăr

```text
ANPA / arebaltapeste / Romsilva (contractual authority)
    -> data/processed/*.jsonl, sources.jsonl
    -> merge_anpa_waters.py -> public/data/waters.json

OSM snapshot pin-uit (geometrie, nu contract)
    data/raw/overpass_water_all.json + relation/way membership index
    -> data/cache/osm_river_segments_v1.jsonl.gz
    -> scripts/audit_river_segments.py
    -> data/processed/river_segment_audit.json
       + data/processed/river_segment_audit.md
       + data/processed/river_segment_audit_baseline.json

CI (offline, determinist)
    audit segmentar + assertions + manifest hashes
    -> block la regresie nouă; review queue pentru excepții declarate
```

### Separarea explicită a surselor

| Clasificare | Definiție | Comportament |
|---|---|---|
| `contracted_anpa` | rând trasabil din `anpa_waters.jsonl` / `anpa_contracts.jsonl` | trebuie să existe exact o apă publicată sau o excepție documentată |
| `contracted_arebaltapeste` | rând trasabil din `arebaltapeste_waters.jsonl` / asociație | aceeași regulă; nu se derivă din nume OSM |
| `managed_romsilva` | rând din `anpa_romsilva_waters.jsonl` | etichetat Romsilva, nu prezentat ca AJVPS/APS inventat |
| `uncontracted_osm` | cluster OSM numit fără match contractual confirmat | rămâne overlay `uncontracted:true`, fără `asociatie` / `referinta` fabricate |
| `unresolved` | match insuficient / date topologice incomplete / headwater ambiguu | nu se atașează automat; raport cu dovezi |

`source_detail` rămâne doar proveniență tehnică. Pentru fiecare verdict, raportul va purta `source_row_ids`, `source_kind`, `osm_relation_ids`, `osm_way_ids`, scor și coordonate; astfel nu confundă o potrivire OSM cu un contract.

## Inventar verificat

- Pipeline canonic: `scripts/rebuild_data.py`; `FULL_STEPS` rulează merge, audit/matching, overlay, county clips și simplificare. Manifestul curent are 54 intrări/8 ieșiri, dar exclude snapshotul liniar `data/raw/overpass_water_all.json` și viitorul index segmentar.
- Intrare OSM existentă: `data/raw/overpass_water_all.json` (258.6 MB, nepinuită în manifest), `data/rivers_osm.geojson`, plus `data/cache/osm_river_clusters.pkl` (cache neversionat). Fișierul public nu va servi snapshotul brut.
- Date publice: 1.013 ape contractate în `public/data/waters.json`, 473 cu geometrie liniară; 4.140 râuri OSM necontractate în `public/data/uncontracted_rivers.json`.
- Logica de grup/sector: `src/utils/river-course.ts`; renderer/click: `src/components/map/WaterFeatureLayer.tsx`; overlay: `src/components/map/UncontractedWaterLayer.tsx`.
- QA existent: `audit_integrity.py`, `audit_source_trace.py`, `validate_geometry_county.py`, `sweep_uncontracted_overlay.py`, `audit_regions.py`, `audit_multicontract.py`; CI: `.github/workflows/data-integrity.yml`; Playwright: config cu proiecte mobile/tablet/desktop și tier `@data` nightly.
- Teste existente relevante: `tests/test_mapping_common.py`, `tests/test_county_validator.py`, `tests/test_sweep_uncontracted_overlay.py`, `tests/test_parity_vs_frontend.py`, `src/utils/river-course.test.ts`, `tests/e2e/specs/regression/map-segment-qa.spec.ts`.

## Designul noului audit

### A. Artefact OSM pin-uit și index topologic

Fișiere noi:

- `scripts/build_osm_river_segment_index.py`
- `data/cache/osm_river_segments_v1.jsonl.gz` (artefact mare, cache versionat/reprodus conform deciziei de repo)
- `data/processed/osm_river_snapshot_manifest.json`
- `data/processed/osm_relation_overrides.json`

1. Snapshotul este descărcat doar de un job explicit `data refresh`, nu în PR CI. Salvează exact query/source URL, timestampul, sha256, bbox/polygon RO, versiunea indexerului și toate OSM relation/way/node IDs.
2. Parsează OSM în `way_id -> {node_ids, coordinates, tags}`; relation members păstrează rolul, secvența și `relation_id`. Nu pierde ways fără `name`: un way membru într-o relație numită este parte a cursului.
3. Produce o înregistrare normalizată per `relation` și un fallback per cluster de ways: `osm_id`, `kind`, `all_way_ids`, `named_aliases`, `geometry`, `node_degree`, `endpoints`, `components`, `length_m`, `county_ids`, `h3/grid cells`.
4. Pentru fiecare relation verifică membership incomplet: member way absent, geometrie sub 2 puncte, duplicate way, self-loop, multiple componente. Acestea sunt `osm_source_incomplete`, nu geometrie completă inventată.
5. Pin: `osm_river_snapshot_manifest.json` include sha256 pentru snapshot brut și index, numărul de nodes/ways/relations și `schema_version`. `rebuild_data.py --check` verifică aceste hash-uri în loc să ignore un cache neversionat.

Praguri propuse (configurabile): `NODE_JOIN_EPS_M=25`, `SNAP_EPS_M=35`, `MAX_INTERNAL_GAP_M=100`, `MAX_TERMINAL_GAP_M=250`, `MIN_REPORT_SEGMENT_M=250`, `COVERAGE_SAMPLE_SPACING_M=100`. Distanțele se calculează în CRS metric local/UTM, nu în grade.

### B. Relație completă, ways și continuitate

Fișiere noi:

- `scripts/river_segment_audit_lib.py` — I/O, reproiecție, graph, linear referencing, raport.
- `scripts/audit_river_segments.py` — CLI strict read-only implicit.
- `tests/test_river_segment_audit.py`.

Algoritm pe `riverGroup` / proprietar de geometrie:

1. Formează `contract_units`: toate apele cu asociație, grupate strict după `riverGroup`; pentru singleton folosește `slug`, niciodată prefixul fuzzy de 5 litere. Membrii fără geometrie sunt sectoare valide doar dacă owner-ul de grup are curs liniar și `sectorStart/End` sau `course_frac` justificat.
2. Leagă unitatea de OSM prin ordine de încredere: override pin-uit `{riverGroup|slug: relation_id}` → `osm_relation_ids` deja cunoscute → exact alias+overlap spațial → candidate review. O potrivire după nume singur nu poate trece ca `PASS` când există collision.
3. Pentru relation: construiește graph pe node IDs; pentru fallback: graph pe endpointuri snap-uite la `SNAP_EPS_M`. Raportează componente, noduri cu degree >2 (braid/tributar), capete și toate muchiile/ways.
4. Alege main stem determinist: maximul drum ponderat cu lungime între două terminale, constrâns de relation order când acesta există. Brațele/lateralele sunt păstrate în evidence, nu concatenate arbitrar prin PCA.
5. Compară owner geometry cu main stem OSM folosind probe echidistante în ambele direcții:
   - `osm_to_published_coverage`: proporția probe OSM la <= `COVERAGE_TOL_M=125` de geometry publicată;
   - `published_to_osm_coverage`: proporția probe publicate la <=125 m de OSM;
   - detectează intervale consecutive neacoperite >=250 m ca `missing_segment`, cu `[start_fraction,end_fraction]`, lungime, midpoint, coordinates și way IDs;
   - capetele publicate la >250 m de un terminal OSM devin `truncated_head` / `truncated_mouth` (sau `ambiguous_orientation` dacă direcția nu este demonstrabilă).
6. Un `PASS` de continuitate cere: un singur main-stem component sau excepție aprobată, niciun internal gap >100 m, acoperire OSM→publicată >=98%, publicată→OSM >=98%, niciun segment lipsă >=250 m. Râurile foarte scurte folosesc minimum 2 probe și prag procentual, nu un fals PASS.

Aceasta previne regresia Târnava: auditul nu acceptă faptul că există „un râu Târnava” și nici o singură geometrie lungă; inspectează toate ways ale relation, construiește axa principală și marchează orice interval neacoperit dintre două porțiuni corecte.

### C. Audit de coverage național / grid × segment

Extinde `scripts/audit_regions.py` sau, preferabil, migrează logica reutilizabilă în `river_segment_audit_lib.py`; noul CLI devine sursa unică pentru raport, iar vechiul script este wrapper compatibil.

1. Folosește H3 resolution 7 (sau un grid EPSG:3035 de 10 km fixat în config) pentru geometriile segmentizate; păstrează și intersecția cu județe din limitele cache locale. Evită centroidul „nearest county” pentru clasificarea de segment.
2. Pentru fiecare celulă/județ × segment OSM, emite o singură stare cu `segment_id`, `source_osm_id`, fracție, lungime, județe reale și evidence coordinate:
   - `PASS_CONTRACTED`
   - `MISSING_CONTRACTED` (există rând contractual/sursă dar nu row publicat ori nu sector reprezentabil)
   - `UNCONTRACTED_EXPECTED` (OSM fără contract confirmat; trebuie să apară numai ca overlay, dacă trece pragurile de afișare)
   - `UNRESOLVED_NO_OSM_MATCH`
   - `UNRESOLVED_AMBIGUOUS_MATCH`
   - `EXEMPT_DOCUMENTED` (canal/japșă sau sector fără geometrie, cu reason ID)
3. Compară overlay-ul publicat cu segmentele `uncontracted`: fiecare cluster OSM eligibil trebuie ori să aibă geometrie overlay în aceeași celulă, ori un reason explicit (`too_short`, outside RO, duplicate contracted, manual exclusion). Nu promova un stream la contractat.
4. Normalizează județele cu `canonical_county` existent/centralizat; cazul curent `TIMIȘ` vs `Timiș` din `audit_regions_summary.json` devine test de regresie.

### D. Contracte multi-sector și granițe de județ

În `audit_river_segments.py`, pentru fiecare grup cu >=2 contracte:

1. Alege geometry owner; mapează toate segmentele pe fracția source→mouth validată topologic.
2. Construiește puncte obligatorii: `0.01`, `0.50`, `0.99`; fiecare limită de `sectorStart`, `sectorEnd` ± epsilon; și fiecare intersecție main-stem × county boundary ± 50 m.
3. Calculează expected contract:
   - interval explicit: cel mai îngust `[sectorStart,sectorEnd)` care conține proba — aceeași regulă ca `contractAtFraction`;
   - fără interval: Voronoi din `course_frac`, marcat `derived_voronoi`/review, nu contractual exact.
4. Rulează implementarea Python echivalentă și funcția TS în fixture golden: pentru fiecare punct, `expected_slug == contractAtFraction(...).slug`. Un overlapping interval fără regula „smallest wins”, gap între sectoare, fracție în afara [0,1], ordine ne-monotonă sau cross-county fără justificare este `sector_mismatch` hard fail.
5. Raportul include `fraction`, coordinate, county actual, `expected_slug`, `actual_ui_slug`, `association`, `contract reference`, `selection_mode`.

### E. Nume, headwaters și duplicate

Fișiere:

- `data/processed/river_name_aliases.json` — aliasuri verificabile, fiecare cu motiv și provenance; nu `MANUAL_OVERRIDES` opac în cod.
- `data/processed/river_segment_exceptions.json` — excepții limitate, owner, `expires_on`, reason/evidence; CI eșuează pentru intrare expirată/nefolosită.

Reguli:

1. Indexează `name`, `alt_name`, `old_name`, `loc_name`, aliases din relație și numele ways. Generează candidates de headwater/tributar doar dacă au continuitate topologică la main stem sau confluence verificabil.
2. `same_name_collision`: același core name în componente disjuncte / județe diferite. Niciun candidat nu devine match fără `relation_id` sau overlap spațial + sursă/county confirmată.
3. `contracted_uncontracted_duplicate`: overlay ≥90% pe un sector contractat; păstrează clasificarile `DUPLICATE` / `PARTIAL_DUPLICATE`, dar raportează fracția segmentară și exact way IDs. CI rămâne block pentru aceste două clase.
4. `headwater_variant`: o relație cu alt nume conectată la contract; raportată ca `requires_alias_review`, nu absorbită automat. Numai intrare explicită în alias registry poate ridica la PASS.

## Contractul raportului

`data/processed/river_segment_audit.json` (format determinist: chei sortate, array-uri sortate după `river_group, osm_id, segment_id`) va include:

```json
{
  "schema_version": 1,
  "snapshot_sha256": "...",
  "thresholds": {"coverage_tol_m": 125, "min_report_segment_m": 250},
  "summary": {"PASS_CONTRACTED": 0, "MISSING_CONTRACTED": 0},
  "rivers": [{
    "river_group": "tarnava-mica",
    "owner_slug": "...",
    "source_rows": ["anpa-..."],
    "osm": {"relation_ids": [0], "way_ids": [0], "match_status": "confirmed"},
    "topology": {"components": 1, "internal_gaps": []},
    "coverage": {"osm_to_published": 1.0, "published_to_osm": 1.0},
    "segments": [{"segment_id": "...", "status": "PASS_CONTRACTED", "fraction": [0.2,0.3], "length_m": 1000, "midpoint": [0,0], "counties": ["..."]}],
    "sector_probes": [{"fraction": 0.5, "expected_slug": "...", "ui_slug": "...", "status": "PASS"}],
    "findings": []
  }],
  "cells": [{"cell_id": "...", "county": "...", "counts": {}, "evidence": []}]
}
```

`river_segment_audit.md` este sumarul auditabil: totaluri pe stare, tabel per râu, tabel per județ/celulă, top blockers și link/ID la coordonate. JSON-ul, nu textul, este intrarea CI. Raportul nu include PII.

## Plan de implementare (pași mici)

1. **Definește schema/config-ul și fixtures (3 min).**
   - Adaugă `data/processed/river_segment_audit_baseline.json`, `river_name_aliases.json`, `river_segment_exceptions.json` cu schema/version goale și exemple Târnava sintetice, fără schimbarea datasetului.
   - Adaugă `tests/fixtures/osm_segment_cases.geojson` și `tests/fixtures/osm_relation_members.json`: chain complet, gol intern, două componente, same-name collision, headwater alias, border crossing.
   - Test: `.venv/bin/python -m pytest tests/test_river_segment_audit.py -q`.

2. **Construiește indexerul OSM offline (5 min).**
   - Creează `scripts/build_osm_river_segment_index.py` cu `--input`, `--out`, `--manifest`, `--no-network`; refuză să descarce implicit.
   - Indexează relation membership și way/node graph, cu stable sort și sha256.
   - Test: `.venv/bin/python scripts/build_osm_river_segment_index.py --input data/raw/overpass_water_all.json --out /tmp/osm-index.jsonl.gz --manifest /tmp/osm-index-manifest.json --no-network` și repetă; `sha256sum` trebuie identic.

3. **Extrage biblioteca topologică testabilă (5 min).**
   - Creează `scripts/river_segment_audit_lib.py`: reproiecție metrică, graph, main-stem, gap scan, sample coverage, county intersection, report sorting.
   - Nu reutiliza `cluster_parts` cu `0.06` grade pentru validare; acesta poate rămâne matching fallback.
   - Teste unit: gaps la 99/101 m, terminal cut, relation cu way lipsă, branch, reproducibilitate a ordinii.

4. **Implementează auditul contractual/segmentar read-only (5 min).**
   - Creează `scripts/audit_river_segments.py --osm-index ... --out-json ... --out-md ... --baseline ... --gate`.
   - Încarcă source rows înainte de `waters.json`, aplică strict grupurile/owner-ul și alias/exceptions registries; nu scrie `public/data`.
   - Test: `.venv/bin/python scripts/audit_river_segments.py --osm-index data/cache/osm_river_segments_v1.jsonl.gz --out-json /tmp/river-segments.json --out-md /tmp/river-segments.md --baseline data/processed/river_segment_audit_baseline.json --gate`.

5. **Adaugă audit grid/județ și overlay (5 min).**
   - Extinde același CLI cu `--cells h3-r7` (sau grid 10 km configurat) și verificarea `uncontracted_rivers.json`.
   - Refactorizează `scripts/audit_regions.py` să consume biblioteca/raportul nou ori marchează-l deprecated; nu păstra două clasificatoare divergente.
   - Teste: county normalization `TIMIȘ`→`Timiș`, segment care traversează două celule/județe, OSM uncontracted care rămâne uncontracted.

6. **Validează multi-sectorul în Python și TS (5 min).**
   - Adaugă `tests/test_river_segment_sector_resolution.py` cu golden fixtures; include upstream/midstream/downstream, county-boundary și smallest-interval-wins.
   - Extinde `src/utils/river-course.test.ts`; dacă se introduce helper pur pentru probes, păstrează API-ul UI.
   - Extinde `tests/test_parity_vs_frontend.py` astfel încât Python și TS produc aceleași rezultate pentru golden fixtures.
   - Teste: `.venv/bin/python -m pytest tests/test_river_segment_sector_resolution.py tests/test_parity_vs_frontend.py -q && npm test -- src/utils/river-course.test.ts`.

7. **Consolidează guard-ul de integritate și manifestul (4 min).**
   - Actualizează `scripts/rebuild_data.py`: introduce explicit indexul/manifestul OSM ca input pin-uit; nu consideră artefactul neversionat „skip” în CI când auditul este activ.
   - Actualizează `scripts/audit_integrity.py` pentru schema de `riverGroup`, `course_frac`, `sectorStart/End` (finite, 0..1, start<end), registry expirations și consistența raportului.
   - Teste: `.venv/bin/python -m pytest tests/test_rebuild_data.py tests/test_data_gates.py -q` și `python3 scripts/rebuild_data.py --check` într-un checkout curat.

8. **Wire CI cu niveluri corecte (3 min).**
   - Actualizează `.github/workflows/data-integrity.yml`:
     1. PR: index existent + audit `--gate`, unit tests, integrity, trace, county, sweep, manifest.
     2. `main`/nightly: același audit plus raport artifact upload de fiecare dată.
     3. manual `workflow_dispatch` cu `refresh_osm=true`: download controlat, index rebuild, full audit; nu mută baseline fără aprobare.
   - Adaugă `.github/workflows/osm-snapshot-refresh.yml` dacă refresh-ul trebuie separat; păstrează artefactele 30 zile și PR-ul de date explicit.

9. **Adaugă QA browserless/Playwright cu eșantion geografic (5 min).**
   - Creează `tests/e2e/specs/data-contract/river-segment-samples.spec.ts` tag `@data @river-segments`.
   - Creează `tests/e2e/fixtures/river-segment-samples.json` derivat determinist din audit: max. 12 PASS (minim 1/celulă/județ disponibil), toate Târnava/headwater/multi-sector/finding fixtures, cu slug, fracție, lat/lon, expected association/contract.
   - Extinde `tests/e2e/helpers/map.ts` cu `panAndClickFraction(page, ownerSlug, fraction)` care alege path/hit layer și face click real cu `page.mouse.click`, apoi verifică sheet/card, nu bridge-only.
   - Desktop/mobile: probele la zoom >=10 (hit layer există); la zoom național verifică vizibilitatea, nu click individual deoarece componentele o dezactivează intenționat sub zoom 10.

10. **Rulează și re-pin-uiește numai după review (5 min).**
    - Rulează full baseline, compară raportul cu baseline; orice finding nou e blocker sau excepție documentată cu expirare.
    - Abia după toate gates green: `python3 scripts/rebuild_data.py --manifest`, apoi `--check`; include raportul/manifestul în PR.

## Matrice de teste

| Nivel | Caz | Așteptare |
|---|---|---|
| Python unit | relation cu toate ways conectate | PASS, lungime și fracții stabile |
| Python unit | gol intern >100 m / segment neacoperit >=250 m | `missing_segment`, coordonate + way IDs |
| Python unit | cap OSM la >250 m de cursul publicat | `truncated_head` sau `truncated_mouth` |
| Python unit | 2 componente / way relation absent | `osm_source_incomplete`, nu PASS |
| Python unit | nume identic în bazine diferite | `same_name_collision`, fără auto-match |
| Python unit | alias/headwater | `requires_alias_review` până la registry verificat |
| Python snapshot | toate contractele ANPA/areba/Romsilva | exact una din stările prescrise, niciun contract inventat |
| Python snapshot | grid × county | toate segmentele eligibile clasificate, județe canonicalizate |
| Python/TS parity | upstream/mid/downstream, granițe județ | Python expected = `contractAtFraction` UI |
| Python snapshot | Târnava multi-way cu gol injectat | fail determinist; aceasta este regresia obligatorie |
| Existing gate | overlay duplicate/partial duplicate | 0, păstrează `sweep_uncontracted_overlay.py --gate` |
| Playwright `@data` | 12 probe segmentare reale | cardul potrivit după click fizic, nume/asociație/sector ne-goale |
| Playwright `@data` | Târnava 3 probe + frontieră județ | fiecare click rezolvă contractul așteptat |
| Playwright | mobile 390×844 | tap pe probe; sheet și contract corecte |
| Playwright | tablet 768×1024 / desktop 1280×800 | click real; fără dead zones, fără console error |

## Praguri CI și baseline

- **Hard fail imediat:** snapshot/index hash inconsistent; source trace lipsă; `MISSING_CONTRACTED`; `missing_segment` >=250 m; `truncated_*`; `sector_mismatch`; duplicate/partial duplicate; excepție expirată; `PASS` fără evidence OSM.
- **Fail la regresie față de baseline:** creștere în `UNRESOLVED_*`, `present-hidden`, `same_name_collision`, `headwater_variant`, sau reduceri de coverage. Baseline-ul nu poate masca hard failures.
- **Review-only (nu auto-fail dacă numărul nu crește):** headwater variant, OSM relation incompletă, OSM stream foarte scurt, contract fără geometrie cu `fallback` valid. Raportul trebuie să conțină reason/evidence.
- **Nu re-pin-ui manifest/baseline:** când auditul nu a rulat cu snapshotul exact, când un report este non-determinist, ori când a apărut un blocker neaprobat.

## Cost / runtime estimat

| Operație | Mediu | Estimare |
|---|---|---|
| Citește index pin-uit + audit 473 owner courses/7.699 clustere | CI 2 vCPU | 2–6 min, RAM țintă <1 GB |
| Unit + parity + integrity existent | CI | 1–3 min |
| Playwright `@data` 12 probe × 3 viewports | CI Chromium | 6–12 min, rulat nightly/main sau doar dacă se schimbă datele/harta |
| Descărcare/normalizare OSM + index rebuild | manual/nightly separat | 10–30 min, dependent de Overpass; niciodată PR default |

Optimizează cu STRtree/H3, pre-projection și probe spațiate; nu face N×M Shapely brute force. CI trebuie să consume artefactul index deja pin-uit și să nu aibă apel HTTP.

## Comenzi de verificare finală

```bash
cd /home/stefan/undepescuim
.venv/bin/python -m pytest \
  tests/test_river_segment_audit.py \
  tests/test_river_segment_sector_resolution.py \
  tests/test_parity_vs_frontend.py \
  tests/test_rebuild_data.py \
  tests/test_data_gates.py -q

.venv/bin/python scripts/audit_river_segments.py \
  --osm-index data/cache/osm_river_segments_v1.jsonl.gz \
  --out-json /tmp/river-segment-audit.json \
  --out-md /tmp/river-segment-audit.md \
  --baseline data/processed/river_segment_audit_baseline.json \
  --gate

.venv/bin/python scripts/audit_integrity.py
.venv/bin/python scripts/audit_source_trace.py
.venv/bin/python scripts/validate_geometry_county.py --json /tmp/county-audit.json
.venv/bin/python scripts/sweep_uncontracted_overlay.py --gate
python3 scripts/rebuild_data.py --check
npm test
npx playwright test --grep '@data.*river-segments|river-segments.*@data'
```

## Risc / decizii tehnice

1. Nu adopta PCA/latitudine ca dovadă universală de direcție: o folosește UI-ul istoric, dar auditul trebuie să raporteze orientare ambiguă atunci când graph-ul/relația nu poate demonstra source→mouth.
2. Nu schimba public schema `Water` pentru a păstra relation IDs decât dacă UI-ul are un consum real; păstrează provenance auditabilă în raport/index. Dacă ulterior e necesară, adaugă opțional `osmRelationIds?: number[]` cu migrare/test de schemă.
3. Nu face fallback automat de la relation la toate ways cu același nume când relation există, deoarece poate uni râuri omonime. Fallback-ul este doar candidate `unresolved`/review.
4. Excepțiile trebuie să fie rare, explicite și expirabile; o listă hardcoded fără evidence repetă problema `MANUAL_OVERRIDES` și ascunde regresiile.
5. Lucrul curent are schimbări necomise în `scripts/rebuild_data.py` și artefacte `.hermes`/`data/_rebuild_check`; implementarea trebuie făcută într-un worktree/PR curat și nu trebuie să le absoarbă accidental.
