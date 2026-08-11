# Probe report: locuridepescuit.ro contracted-waters listings

Date: 2026-08-11
Probe of https://locuridepescuit.ro/ape-contractate and linked county/association pages.
Scope: reconnaissance only. No DB writes, no full scraper.

## TL;DR counts

- Associations indexed: **64** association pages (`/asociatie-pescari/<judet>/<slug>/`) enumerated from the site's own `job_listing-sitemap.xml` (161 listings total on the site: 64 associations, 72 private waters, 12 shops, 11 lodging, 1 public place, 1 contest).
- Counties: **42** counties/Bucharest on the `/judete/` interactive map; **43** county-region pages (adds `delta-dunarii` as its own region); **39** counties have at least one association page. No association page exists for: Mehedinți, București, Tulcea (verified live).
- Waters (contracted, "Ape contractate (sau porțiuni din ele)"): **75 contracted waters in a 6-association sample** (range 1–29 per association; mean ~12.5). A full total requires crawling all 64 association pages — deliberately NOT done in this probe.
- Water→association reverse index (the site's own search, see AJAX below): "olt" → 17 listings, "mureș" → 15, "someș" → 6, "dunărea" → 3, "crișul" → 3.

## Data fields observed

### Association detail page (`/asociatie-pescari/<judet>/<slug>/`) — the data carrier
- **Name** (`<h1>`) — e.g. "AJVPS SIBIU"
- **County** — from URL slug; the page also has a `Județe în care Asociația are ape contractate` block (can list multiple counties)
- **Adresa** (address), **Telefon** (phone), **Email**, **Website** — optional; absent when the association did not fill them (e.g. AVPS DIANA TURNU ARAD has only address + county + waters)
- **Descriere** (free-text description)
- **Documente și Regulamente**, **Rețele Sociale**, **Galerie Foto**
- **Ape contractate (sau porțiuni din ele)** — the contracted-waters list; each item is a water name with a parenthesized location note, e.g. `Râul Olt (Limită jud. Brașov – limită Jud. Vâlcea pe teritoriu. Jud. Sibiu)`
- Related-listing carousel at the bottom (must be excluded when parsing the waters list)

### Sector / km info
- **No structured "sector" or "km" field exists.** `sector` appears 0 times across all 6 sampled association pages.
- Km info, when present, is embedded in the water name text itself, e.g. `Râul Cugir (Cugir 15 Km, de la loc. Cugir - conf. râul Mureș)` (AJVPS ALBA) or in private-water titles like `Balta Oltenitei Dn4 km 6`. Sector descriptions (reach limits, confluences) are embedded in the same parenthetical notes.
- Parsing implication: extract the parenthetical note per water and normalize later; do not expect a numeric km column.

## Site structure / pagination

WordPress 6.8.7 + WooCommerce + my-listing theme + Ajax Search Pro (ASP). Key pages:

| URL | Role |
|---|---|
| `/ape-contractate/` | Landing page; embeds an ASP search box ("Tastează numele apei...") that does water→association reverse lookup. No static listing, no pagination. |
| `/asociatii-pescari/` | Explore widget (`case27-explore-widget`) — a Vue grid that loads association cards via AJAX; no server-side cards in HTML. |
| `/judete/` | Interactive county map; county links are embedded in a JS `placestxt` config (42 counties). |
| `/in-judetul/<judet>/` | County landing pages (43 of them); thin static content, embed the same explore/map widgets. |
| `/asociatie-pescari/<judet>/<slug>/` | **Association detail pages — the actual data source** (64 pages). |
| `/locuri/` + `/locuri/page/N/` | Site-wide archive of all listing types; paginated (14 pages). Not needed for association data. |
| `sitemap_index.xml` → `job_listing-sitemap.xml` | Enumerates ALL listings (161) — best discovery vector found. |

### AJAX endpoints discovered
1. **ASP search** (water→association): `POST https://locuridepescuit.ro/wp-admin/admin-ajax.php` with form params `action=ajaxsearchpro_search`, `aspp=<water name>`, `asid=1`, `asp_inst_id=1`, `options=force_count=100`. Response: `___ASPSTART_HTML___<result cards>___ASPEND_HTML___<JSON with results_count / full_results_count / results[] {title, id, link, post_type, ...}>___ASPEND_DATA___`. GET returns 400; POST is required.
2. **my-listing explore/terms** (listing grid, county terms): `GET https://locuridepescuit.ro/?mylisting-ajax=1&action=<mylisting_quick_search|mylisting_list_terms|...>` with `security=CASE27.ajax_nonce`. Used by the explore widget and quick-search; full action set not reverse-engineered (follow-up for the real scraper).
3. WordPress REST: `wp-json/wp/v2/pages/1146` (the `/ape-contractate/` page) exists; listing REST endpoints not probed.

## Sample parsed entries (from saved raw HTML, see sample_parsed_entries.json)

1. **AJVPS SIBIU** (sibiu) — address: Strada Constituției 23, Sibiu; phone 0728138161; email ajvpssibiu@gmail.com; website apssibiu.ro; counties: Sibiu; **7 waters** (Lac acumulare Arpașu (limită jud. Brașov), Lac acumulare Avrig, Lac acumulare Racovița, Lac acumulare Scoreiu, Pârâul Hârtibaciu (Loc. Brădeni – conf. cu râul Olt), Râul Olt (Limită jud. Brașov – limită Jud. Vâlcea...), Râul Târnava Mare (limită jud. Mureș, Dumbrăveni – limită jud. Alba...))
2. **AJVPS ALBA** (alba) — address: Calea Moților 6, Alba Iulia; phone 0723354404; email ajvpsalba@yahoo.com; website ajvpsab.ro; counties: Alba; **20 waters** (Râul Arieș (Baia de Arieș – Vidolm), Râul Mureș (Stâna de Mureș- Băcăinți), Râul Cugir (Cugir 15 Km...), Râul Sebeș (acumulare Petrești- conf. râul Mureș), Râul Târnava Mare (Valea Lungă-conf. râul Mureș), ...)
3. **AJPS BRAȘOV** (brasov) — address: Strada Nicolae Bălcescu 14, Brașov; phone 0268414631; counties: Brașov; **12 waters** (Râul Olt (Lunca Câlnicului - Feldioara - Augustin), Râul Bârsa (Izvoare – conf. cu Bârsa Fierarului și toți afluenții), Râul Homorod (Izvoare - Vlădeni), ...)
4. **AJVPS TELEORMAN** (teleorman) — address: Strada Libertății, Slobozia; phone 0247317475; email ajvpsteleorman@gmail.com; counties: Teleorman; **6 waters** (Râul Olt (pe raza județului Teleorman), Râul Vedea, Râul Teleorman, Râul Călmățui, Râul Câlniștea, Râul Urlui)
5. **AJVPS VÂLCEA** (valcea) — address: Strada Regina Maria 5, Râmnicu Vâlcea; phone 0250737040; email ajvpsrmvl@yahoo.com; website ajvpsrmvl.wixsite.com; counties: Vâlcea; **29 waters** (Râul Olt (Râul Vadului-Gura Lotrului), Acumularea Govora cu bălțile adiacente, Râul Lotrul Inferior Baraj Brădișor-conf. Râul Olt, ...)
6. **AVPS DIANA TURNU ARAD** (arad) — address: Calea Aurel Vlaicu 150, Arad; **1 water** (Canalele din zona Turnu); no phone/email/website published.

Sample totals: 75 contracted waters across 6 associations.

## Blockers / caveats

1. **SSL certificate misconfiguration (must handle in the scraper):** the site serves a Let's Encrypt wildcard `*.locuridepescuit.ro` cert that does NOT cover the apex hostname, and every hostname 301-redirects to the apex (`https://www.locuridepescuit.ro/...` → `https://locuridepescuit.ro/...`). Straight requests fail with curl error 60. Workaround used here: `verify=False` (curl_cffi `Session(impersonate="chrome", verify=False)`). Document this; do not "fix" by pinning the broken cert.
2. **ASP search requires POST** — GET admin-ajax.php returns HTTP 400; the options payload must be the serialized settings form (empty is fine) plus `force_count=N`.
3. **No server-side listing on index pages** — `/ape-contractate/`, `/asociatii-pescari/`, county pages render no listing cards in HTML; the explore widget data comes from the `/?mylisting-ajax=1` endpoint (needs the my-listing nonce from `CASE27.ajax_nonce`, which is per-page and static in practice). The sitemap is the reliable discovery path.
4. **Total waters count is sample-based** (75 across 6 of 64 associations). A definitive count requires fetching all 64 association pages — that is the full scraper, out of scope for this probe.
5. **Path quirk:** this agent session's `$HOME` points at the Hermes profile dir, so `~/undepescuim` in the task body was interpreted as `/home/stefan/undepescuim` (the user's real home — matches the sibling arebaltapeste probe). Raw files live at `/home/stefan/undepescuim/data/raw/locuri_probe/`.
6. Listing data is user-contributed; water-name spelling is inconsistent (diacritics, abbreviations like "conf.", "Km"/"km"), so name normalization will be needed downstream.

## Files saved (`/home/stefan/undepescuim/data/raw/locuri_probe/`)

- `ape-contractate_p1.html` — landing/search page (463 KB)
- `asociatii-pescari_p1.html` — associations explore page
- `judete.html`, `locuri.html` — county map page + archive page
- `in-judetul_alba.html`, `in-judetul_hunedoara.html` — county pages
- `asociatie_{sibiu,arad,alba,brasov,teleorman,valcea}_*.html` — 6 association detail pages
- `sitemap_index.xml`, `sitemap_job_listing.xml`, `sitemap_pages.xml`, `sitemap_regions.xml`, `sitemap_job_categories.xml` — WP sitemaps (listing/region discovery)
- `county_links.json` — 42 counties with URLs
- `association_urls.json` — 64 association URLs
- `asp_search_{olt,mures,dunarea,somes,crisul}.json` — ASP search endpoint responses
- `sample_parsed_entries.json` — parsed sample entries
- `probe_locuri.py`, `parse_association.py` — probe/parse scripts (also in workspace)
- `mylisting_frontend.js`, `asp-core.js` — JS bundles inspected for AJAX endpoints

## Recommended follow-up (for the full scraper task)

1. Enumerate all 64 association URLs from `association_urls.json`; fetch each page (verify=False, polite delay).
2. Parse per `parse_association.py`; normalize water names and extract the parenthetical sector/location notes into separate columns.
3. Optionally use the ASP search endpoint per water name to build the water→association reverse map (matches the site's own UX).
4. Cross-check the association list against the ASP index (broad searches returned up to 89 matches) to catch listings missing from the sitemap.
