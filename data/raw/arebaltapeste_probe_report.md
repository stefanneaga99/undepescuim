# arebaltapeste.ro Reconnaissance Probe Report

Date: 2026-08-11
Source: https://arebaltapeste.ro/ape (+ linked pages + backend API)
Method: curl_cffi (impersonate chrome124) + BeautifulSoup. Raw HTML saved; full JSON snapshot pulled via the site's own backend API (discovered during probe).

## Executive summary

The site publishes structured data on Romanian public fishing waters ("ape publice") contracted to
angling associations, plus a separate catalogue of private ponds/lakes ("balti"). The frontend is a
Vue 3 SPA whose pages embed the full dataset in `window.__INITIAL_STATE__` JSON and paginate via a
REST backend at `https://api.arebaltapeste.ro`. The contracted-waters dataset (426 records) is small
enough to fetch completely in ~5 requests.

## Concrete counts

| Entity | Count |
|---|---|
| Associations (asociatii) | **82** |
| Contracted public waters (ape, type=ape) | **426** |
| — lakes (subtype=lac) | 193 |
| — rivers (subtype=rau) | 233 |
| Private ponds/lakes (balti, separate category) | 201 |
| Counties covered by ape (of 42 RO counties) | **30** |
| Counties covered by balti | 36 |
| Associations that actually administer >=1 water on site | 55 (27 listed assoc. have no waters) |

### County distribution of contracted waters (ape)

Vâlcea 54, Hunedoara 39, Cluj 35, Sibiu 33, Bihor 30, Argeș 24, Alba 23, Bacău 19,
Bistrița-Năsăud 19, Caraș-Severin 17, Gorj 15, Arad 14, Dâmbovița 14, Olt 13, Prahova 13,
Botoșani 12, Brașov 10, Maramureș 7, Neamț 6, Suceava 5, Harghita 5, Timiș 5, Ialomița 3,
Brăila 3, Sălaj 2, Ilfov 2, Buzău 1, Dolj 1, Mureș 1, Mehedinți 1.

Note: 30 counties present; no contracted waters found for Teleorman, Tulcea, Constanța, Galați,
Giurgiu, Iași, Vaslui, Vrancea, Satu Mare, Sălaj (partial), Călărași, Covasna, București,
Bistrița-Năsăud (has 19), etc. Some of these counties have associations listed but zero waters on
this site.

### Association type breakdown (by name pattern)

- AJVPS/AJPS (county-level hunters & fishers associations): 30
- APS / other local angling associations: 21
- AVPS (local hunters/fishers): 16
- Direcția Silvică / Romsilva (state forest districts): 14
- ANPA (national agency): 1

## Data fields observed

### Water ("ape") record — all 426 records have:
- `name` — water name (e.g. "Lacul Tarnița", "Valea Răcătăului")
- `judet` — county (Romanian diacritics preserved, e.g. "Argeș")
- `subtype` — "lac" | "rau" (lake vs river)
- `dimensiune` — size: "240 Ha" for lakes, "35 km" for rivers (230 km entries, 187 ha entries, 9 raw numeric/unclear)
- `limite` — sector boundaries (e.g. "De la Steaua - la Pârâul Alb")
- `referinta` — source document string (see below)
- `asociatie` — embedded association object: name, name_long, slug, telefon, adresa, siteUrl, link_permis, adrese[] (with coordinates), bbox, id
- `pescuit_interzis` — bool (3 records flagged)
- `bbox`, `coordinates`, `driving` — geo data (all 426 have coordinates)
- `slug` — short id used in URL (e.g. "q2agyhcl")
- `id` — MongoDB ObjectId
- `createdAt` / `updatedAt` — timestamps

### Association record — 82 records have:
- `name` (short, e.g. "D.S. Cluj"), `name_long` (full legal name)
- `slug`, `id` (ObjectId)
- `adresa`, `telefon`, `siteUrl`, `link_permis` (permit purchase URL)
- `adrese[]` — array of {adresa, coordinates, id} (permit sales points)
- `bbox`, `createdAt`, `updatedAt`

### Data provenance (`referinta` field on waters)
- ANPA "Lista habitatelor piscicole naturale contractate ... la data 01.02.2024" — 186
- Same list dated 01.08.2021 — 58
- RNP-ROMSILVA mountain waters (Protocol 12935/LAV/17.09.2013) — 56
- Same ANPA list dated 26.04.2024 — 40
- ROMSILVA mountain waters (undated) — 25
- ANPA list dated 01.01.2021 — 18 + 13
- "Lista ... necontractate ... la data 01.08.2021" (uncontracted) — 13
- ANPA list dated 18.02.2025 — 8
- "Ape administrate de ProPescar" — 6 (+1)
- Association-specific URLs — 2

So the dataset is a mix of contracted and Romsilva-administered waters from several ANPA list
versions; the `referinta` string is the per-record provenance tag.

## Site structure

- **/ape** — contracted public waters listing (React/Vue SPA; first page renders 15; backend total 426). No server-side pagination links — "load more" calls the API.
- **/asociatii** — all 82 associations (name + "Vezi Asociație" links to /asociatie-<slug>). Static state contains full 82-item list.
- **/judete** — county index; links to /<county-slug> pages (e.g. /cluj).
- **/<judet>** — per-county listing pages (filter type + judet).
- **/asociatie-<slug>** — association detail: contact info, addresses, "N habitate piscicole în administrare", water list (paginated 15, "Vezi mai multe rezultate").
- **/apa-<slug>-<name>** — water detail: name, admin association, county, SUPRAFAȚĂ/DIMENSIUNI, prohibition flag, permit info, shop products (unrelated merch).
- **/balti** — private ponds (separate category, own schema: facilitati, pesti, tarife, telefon, suprafata, etc.).

### Backend API (discovered from JS bundle `assets/index-DfRb4_86.js`)
- Base: `https://api.arebaltapeste.ro`
- `GET /api/search?type=ape[&judet=X][&asociatie=<ObjectId>]&limit=N&skip=S`
  → `{metadata:{count}, items:[{type, item:{...}}]}` — THE primary listing endpoint, supports county + association filters.
- `GET /api/ape?limit&skip` → mongoose-style `{docs, totalDocs, totalPages, ...}` (426 totalDocs).
- `GET /api/asociatii?limit&skip` → 82 docs.
- Tiles: `https://api.mapcherry.io/tiles/arebaltapeste/{z}/{x}/{y}.png?key=...`

## Blockers / caveats

1. **None blocking.** All pages fetched with 200; no CAPTCHA, no Cloudflare, no rate limiting observed at probe volumes.
2. County names contain Romanian diacritics in the API (`Argeș`) but ASCII slugs in URLs (`/arges`) — normalize for joins.
3. `dimensiune` mixes units and formats ("240 Ha", "35 km", "12,4", "234.5", "-"); needs parsing/normalization in the full scraper.
4. 27 of 82 associations have zero waters listed on this site — they may contract waters not published here, or hold no contracts.
5. The site embeds data for the *current* page only; full dataset requires the API pagination loop (15/page, 29 pages for 426) or `limit=100` (~5 calls).
6. Ponds (/balti) are a different schema and likely out of scope for "contracted waters" — confirmed separate `type` in the API.

## Sample parsed entries (5, exact values from snapshot)

1. **Lacul Tarnița** — subtype=lac, jud. Cluj — dimensiune "240 Ha" — limite "zona de acumulare" — admin: Direcția Silvică Cluj - Romsilva (D.S. Cluj, tel 0264 420 908, site cluj.rosilva.ro) — referinta: ROMSILVA mountain-waters list — coords [23.2745, 46.71585].
2. **Valea Răcătăului** — subtype=rau, jud. Cluj — dimensiune "35 km" — limite "De la Steaua - la Pârâul Alb" — admin: D.S. Cluj — referinta: ROMSILVA mountain-waters list — coords [23.0471345, 46.5833747].
3. **Lac montan Podragu mic** — subtype=lac, jud. Sibiu — dimensiune "0,24 Ha" — limite "Lac glaciar" — admin: APS AQUA CRISIUS (tel 0752270142, site aquacrisius.ro) — referinta: ANPA contracted list 01.08.2021 — coords [24.690080668462187, 45.610518108539736].
4. **Lacul de acumulare Beliș-Fântânele** — subtype=lac, jud. Cluj — dimensiune "800 ha" — limite "judetul Cluj" — admin: D.S. Cluj — referinta: ROMSILVA mountain-waters list — coords [23.0234, 46.659].
5. **Râul Someș** — subtype=rau, jud. Cluj — admin: AJVPS CLUJ (Asociația Județeană a Vânătorilor și Pescarilor Sportivi Cluj, tel 0264596578, Str. Cuza Vodă, Cluj-Napoca) — 1 of 4 habitate in administration — from /asociatie-ajvps-cluj page.

## Files saved

Directory: `/home/stefan/undepescuim/data/raw/arebaltapeste_probe/`
- 33 raw HTML pages (`ape.html`, `asociatii.html`, `judete.html`, `balti.html`, 16 `apa-*` water pages, 7 `asociatie-*` association pages, `index.html`, misc pages) + per-page `.meta.json` (url/status/size)
- `manifest.json` — link inventory & fetch log
- `snapshot_waters.json` — all 426 contracted water records (API)
- `snapshot_asociatii.json` — all 82 association records (API)
- `snapshot_balti.json` — all 201 pond records (API, for reference)
- `arebaltapeste_probe_report.md` — this report

## Recommendation for the full scraper (next step)

Use `GET https://api.arebaltapeste.ro/api/search?type=ape&limit=100&skip=N` in a ~5-request loop
(plus `/api/asociatii` for the association table) instead of HTML parsing — the API returns the
complete normalized schema (name, judet, subtype, dimensiune, limite, referinta, asociatie,
coordinates, id). HTML pages remain useful for per-water detail enrichment (prohibition, permit
procedures) and as an independent cross-check. No blockers to scale.
