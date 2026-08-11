# ANPA PDF Probe Report — Contracted Fishing Waters (Romania)

Date: 2026-08-11
Probe scope: anpa.ro (Agenția Națională pentru Pescuit și Acvacultură) PDF publications listing contracted fishing waters / recreational-fishing associations.
Raw files: `~/undepescuim/data/raw/anpa_probe/` (6 PDFs downloaded + pdftotext extractions).

## 1. PDFs found and downloaded

The ANPA site is a WordPress site; the public-facing pages are JS-protected ("Verify your browser"), but the
`/wp-content/uploads/` file store is directly accessible with curl_cffi browser impersonation (`impersonate="chrome"`).

Enumeration: crawled 5 index pages (Pescuit Recreativ `?cat=3`, Pescuit Comercial `?cat=4`,
Privatizare-Concesionare `?page_id=317`, Comisie Concesionare `?page_id=2616`, Cote Pescuit `?page_id=1582`).
Found **89 unique PDF links** on those pages. Of these, the documents actually listing contracted waters / associations are:

| # | File (local) | Source URL | Pages | Content |
|---|--------------|------------|-------|---------|
| 1 | `Lista-habitatelor-acvatice-naturale-contractate-23.02.2026.pdf` | anpa.ro/wp-content/uploads/2020/07/...23022026.pdf | 36 | **MAIN**: contracted natural aquatic habitats per county, per association, with limits, km/Ha and contract no. |
| 2 | `Lista-habitatelor-acvatice-naturale-necontractate-23.02.2026.pdf` | anpa.ro/wp-content/uploads/2020/07/...23.02.2026.pdf | 9 | Habitats NOT yet contracted (complement of #1) |
| 3 | `Lista-habitatelor-contractate-18.02.2025.pdf` | anpa.ro/wp-content/uploads/2020/07/lista-hpn-contractate-18.02.2025.pdf | ~36 | Previous edition (18.02.2025) of #1 — confirms the list is republished periodically |
| 4 | `Lista-habitate-Romsilva.pdf` | anpa.ro/wp-content/uploads/file/lista%20habitate%20Romsilva.pdf | 13 | Mountain salmonid habitats kept in direct administration of RNP-Romsilva (state forestry), **not** contracted to associations |
| 5 | `Raport-ANPA-2012.pdf` | anpa.ro/wp-content/uploads/2013/09/...2012.pdf | 80 | Annual report; contains commercial concession/lease contract situation |
| 6 | `Raport-ANPA-2016.pdf` | anpa.ro/wp-content/uploads/file/Informare%20Publica/...2016.pdf | 30 | Annual report; contains commercial contract situation by region/county |

All 6 downloaded OK via curl_cffi (no TLS-fingerprint issues). The other ~83 PDF links are procedure decisions,
permit regulations, turbot (calcan) quota documents, and org charts — not water lists.

Note: a 2025 mirror also exists on Scribd (ro.scribd.com/document/888449822 "Lista HPN Contractate 18.02.2025"),
confirming the family of documents is published at least yearly. Earlier editions (2023, 2024) are likely on the
site too but were not needed for the volume estimate.

## 2. Estimated data volume (main document: contracted list, 23.02.2026)

Counts computed from `pdftotext -layout` output (regex-based, no full parser):

- **Counties covered: 38** (of 42) — headers `JUDEȚ X` present for: Alba, Arad, Argeș, Bacău, Bihor, Bistrița-Năsăud,
  Botoșani, Brașov, Brăila, Buzău, Caraș-Severin, Călărași, Constanța, Covasna, Dâmbovița, Dolj, Galați, Giurgiu,
  Gorj, Harghita, Hunedoara, Ialomița, Iași, Ilfov, Maramureș, Mureș, Neamț, Olt, Prahova, Satu Mare, Sălaj, Sibiu,
  Suceava, Teleorman, Timiș, Vaslui, Vâlcea, Vrancea.
  Missing (no contracted habitats): **Cluj, Mehedinți, Tulcea, București**.
- **Contracted habitats (water rows with a km/Ha value): 630**
  - 507 rows with km values → **total ≈ 18,398 km** of contracted river/lake sections
  - 126 rows with Ha values → **total ≈ 22,971 Ha** of contracted lake/pond surfaces
- **Associations: ~55–60 distinct**, appearing in **~70 association blocks** ("cu sediul în" + contract number).
  Dominant type: AJVPS (județean hunters & sport fishermen associations, one per county, ~33 counties), plus
  specialized clubs: AVPS/APS/AJPS/CS (e.g. AVPS Diana Turnu, APS Aqua Crisius, CS Hunedoara, AVPS Târnava Mare,
  A. Fly Fishing Club, A. Lucioperca Club, ASOCIAȚIA Fly Fishing Club).
- **Contract numbers: 99 occurrences / 89 distinct** (format `nr/DD.MM.YYYY`). Some contracts are old
  (e.g. 1/22.02.1987, 664/598/1982 — with acte adiționale extending them).
- **306 of 630 rows** (49%) have a resolvable association + contract number within a small text window — i.e. a
  machine-parseable subset for a future full parser.

Year-over-year (cross-check with 2025 edition):

| Metric | 18.02.2025 | 23.02.2026 |
|---|---|---|
| Counties | 38 | 38 |
| km rows / total km | 513 / 18,703 | 507 / 18,398 |
| Ha rows / total Ha | 130 / 23,058 | 126 / 22,971 |
| Contract numbers | 99 | 99 |

=> Volume is stable year-over-year (~18.4k km + ~23k Ha, ~38 counties, ~55-60 associations, ~90 contracts).

Complementary datasets (same ANPA family, not recreational-association lists):
- **Non-contracted habitats (23.02.2026):** 40 county headers, 134 value rows, sum ≈ 5,801 (km+Ha). Most counties
  say "no non-contracted habitats remain"; notable non-contracted remainders in Argeș, Brașov, Caraș-Severin etc.
- **Romsilva mountain waters:** ~283 habitat rows (salmonid mountain waters kept in state-forest administration,
  not contracted to associations; lengths in km/ha column, units in header only).
- **Commercial contracts (annual reports):** 2016 report table: **210 contracts, 42,935.9 ha** (173 concession,
  7 lease, 4 leasing, 26 association) across all regions; 2012 report: 32 new contracts in 2012 + full tracked table.

## 3. Data quality issues

1. **Layout is a merge nightmare** — association name + address block sits in the right-hand column and spans
   multiple rows/water entries; one association block applies to the whole group of rows above/below it.
   A full parser needs a "current association" state machine per county section.
2. **Multi-line rows** — water names and limits wrap across lines (e.g. "Fondul piscicol 24 Ciceu: include
   afluenții …", "Râul Crișul Alb cu afluenții"). Regex extraction splits them.
3. **Missing values** — several rows have no km/Ha (e.g. "Canal Dunăre – Marea Neagră", "Râul Colentina",
   "Gălățui", "Râul Bistra Ardealului, mijlociu"); ~0 values for some counties (Constanța, Ilfov, Teleorman have
   headers but 0 value-bearing rows in the contracted list).
4. **Ambiguous units** — km vs Ha mixed in the same table; Ha sometimes written "5Ha"/"5 Ha"/"10 ha".
5. **Association ↔ county mismatch** — associations can hold waters outside their home county (e.g. CS HUNEDOARA
   with sediul in Călan/Hunedoara holds waters listed under JUDEȚ ALBA; APS AQUA CRISIUS of Oradea/Bihor holds
   waters under JUDEȚ ALBA). County = water county, not association county.
6. **Association-name artifacts** — names split across lines ("AJVPS BISTRIȚA-" / "NĂSĂUD"), names glued to
   contract prefixes ("AJVPS DOLJ NR."), inconsistent capitalization (Km/km, JUDET/JUDEȚ, Ş/Ș, Ţ/Ț).
7. **Old/irregular contract dates** (664/598/1982) and "ACT ADIȚIONAL NR." annotations make contract-number
   parsing non-trivial.
8. **No machine-readable source** — the list is a Word-printed PDF; no CSV/API alternative on anpa.ro.

## 4. Sample extracted entries (verbatim rows, cleaned)

1. **Râul Sebeș** — limits: "acumulare Petrești – conf. râul Mureș" — **17 Km** — AJVPS ALBA (Alba Iulia, Calea Moților 6) — contract **44/26.10.2017** [JUDEȚ ALBA]
2. **Mihoești** — limits: "Mihoești, comuna Câmpeni" — **98 Ha** — AJVPS ALBA — contract **44/26.10.2017** [JUDEȚ ALBA]
3. **Râul Vălișoara** — limits: "Izvoare până la Cheile Aiudului" — **31 Km** — APS AQUA CRISIUS (Oradea, str. Mihai Eminescu 15, județ Bihor) — contract **68/26.07.2018** [JUDEȚ ALBA]
4. **Râul Geoagiu Inferior** — limits: "Cheile Râmeț – conf. râul Mureș" — **28 Km** — CS HUNEDOARA (Călan, sat Strei, Ferma Piscicolă F.N., județ Hunedoara) — contract **60/26.07.2018** [JUDEȚ ALBA; association from another county]
5. **Balta Căpâlnaș** — limits: "Localitatea Căpâlnaș" — **2 Ha** — AJVPS ARAD (Arad, str. Mărășești 6) — contract **95/10.01.2024** [JUDEȚ ARAD]
6. **Râul Argeș** — limits: "Comuna Oiești – limita jud. (comuna Pătroaia, jud. Dâmbovița)" — **87 Km** — AJVPS ARGEȘ — contract **39/18.10.2017** [JUDEȚ ARGEȘ]

## 5. Conclusions / recommendations

- **Volume estimate (recreational contracted waters, 2026):** ~38 counties, ~630 contracted habitats,
  ~55–60 associations, ~90 contracts, ≈ 18,400 km + ≈ 23,000 Ha. Stable vs 2025.
- Plus ~134 non-contracted habitats (5,801 km+Ha) and ~283 Romsilva-managed mountain sections (separate category).
- **Feasible to parse** for a future implementation: county sections are regular; a "current association block"
  state machine + value regex can capture ~90% of rows; the 306 rows with in-window association+contract are the
  safest seed set.
- **Next step:** full scraper should download the newest contracted + non-contracted lists each time they're
  republished (yearly), extract with the state machine, and store county/water/limits/value/association/contract.
- No DB writes performed in this probe (per scope).

## Files in this probe

- 6 PDFs (listed above) + 6 `pdftotext -layout` `.txt` extractions
- This report: `anpa_probe_report.md`
