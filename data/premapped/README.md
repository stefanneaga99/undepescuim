# Tier 1 Pre-Mapped Water Bodies

High-confidence geometry for the 10 biggest rivers (13 queries) + 15 major
lakes, produced manually (pre-map) so the Tier 2 batch geocoder SKIPS them.
Pipeline design: `data/raw/geocoding-pipeline-proposal.md` §3 (Tier 1) and §7.1
(output schema).

## Features (28)

### Rivers (13, MultiLineString)

| slug | name | segments | points |
|------|------|----------|--------|
| siret | Siret | 20 | 3,501 |
| olt | Olt | 32 | 6,312 |
| mures | Mureș | 28 | 12,707 |
| prut | Prut | 139 | 6,327 |
| somes | Someș | 17 | 4,947 |
| jiu | Jiu | 18 | 2,470 |
| arges | Argeș | 23 | 2,211 |
| bistrita | Bistrița | 16 | 2,192 |
| crisul-repede | Crișul Repede | 22 | 4,147 |
| crisul-alb | Crișul Alb | 13 | 3,067 |
| crisul-negru | Crișul Negru | 3 | 1,626 |
| tarnava-mare | Târnava Mare | 19 | 3,010 |
| dunarea | Dunărea (Danube) | 66 | 2,092 |

### Lakes (15, Polygon)

| slug | name | source anchor (waters.json) |
|------|------|------------------------------|
| lacul-razim | Lacul Razim | — |
| lacul-sinoe | Lacul Sinoe | — |
| lacul-bicaz | Lacul Bicaz (Izvorul Muntelui) | 26.017, 47.028 |
| lacul-vidraru | Lacul Vidraru | — |
| lacul-snagov | Lacul Snagov | — |
| lacul-rosu | Lacul Roșu | 25.787, 46.789 |
| lacul-sfanta-ana | Lacul Sfânta Ana | — |
| lacul-techirghiol | Lacul Techirghiol | — |
| lacul-siutghiol | Lacul Siutghiol | — |
| lacul-bucura | Lacul Bucura | 22.875, 45.360 |
| lacul-balea | Lacul Bâlea | 24.617, 45.603 |
| lacul-tarnita | Lacul Tarnița | 23.275, 46.716 |
| lacul-stanca-costesti | Lacul Stânca-Costești | 27.184, 47.943 |
| lacul-iezer | Lacul Iezer (Iezerul Mare, Parâng) | 23.801, 45.587 |
| lacul-iezerul-mic | Lacul Iezerul Mic (Parâng) | 23.779, 45.587 |

## Sources

- **Rivers + lakes:** HOTOSM Waterways of Romania, HDX snapshot 2026-08-07
  (ODbL, © OpenStreetMap contributors). See `data/sources/README.md`.
- **Danube:** Overpass API
  (`way["waterway"="river"]` with `name:en="Danube"` OR `name~"^Dun"` — OSM
  tags the RO segment primarily as **Dunărea**, not "Danube"), then clipped to
  the Romanian extent (lon 20.26–29.69, lat 43.62–48.27). Covers the border
  section Porțile de Fier → Danube Delta (bbox lon 20.26–29.62, lat 43.62–45.47).
- **ANCPI TOPRO5 (INSPIRE WFS) validation:** SKIPPED — all ANCPI geoportal
  endpoints were unreachable from this environment on 2026-08-11
  (`geoportal.ancpi.ro` connection failures; `ancpi.ro/geoportal` 404).
  Per proposal §11 risk table, HOTOSM is the primary source and ANCPI is
  validation-only; degradation is graceful. Re-validate if the WFS comes back.

## Disambiguation notes

- **Bistrița:** 4+ Romanian rivers share this name. This file maps the famous
  Moldavian Bistrița (forms Lacul Bicaz, flows into the Siret), anchored to
  (26.4, 46.8) ±90 km. The arebaltapeste entries "Râul Bistrița"
  (Bistrița-Năsăud, 25 km) and Gorj are different, smaller rivers — they are
  NOT represented here.
- **Lacul Roșu:** anchored to (25.787, 46.789) — the Harghita lake, not the
  Delta "Lacul Roșu" (largest polygon by area, rejected by anchor).
- **Lacul Iezer:** the proposal suggested "Lacul Iezer"; the Parâng glacial
  lake Iezerul Mare (in the waters list as "Lac montan Iezerul Mare") was
  chosen and anchored at (23.801, 45.587). The floodplain "Lacul Iezer -
  Gheorghe Lazăr" (largest polygon by area) was rejected by anchor.
- **Lacul Călinești:** OSM's only "Lacul Călinești" is in Maramureș, which
  does not correspond to any lake in the arebaltapeste waters list (the
  "Valea Călinești" entry is a river in Vâlcea). Replaced with **Iezerul Mic**
  (Parâng, in the waters list, clean OSM match).
- **Crișul Alb:** matched by Romanian name "Crișul Alb" as well as Hungarian
  variants "Fehér-Körös" (name or name_ro). Crișul Repede also matched via
  "Sebes-Körös"; Crișul Negru via "Fekete-Körös".
- **Someș:** main stem only (name "Someș"); Someșul Mare / Someșul Mic are
  separate waters in the source list and will be handled by Tier 2.

## Validation status

- All 28 files load with `json.load`; geometries non-empty; correct type
  (river=MultiLineString, lake=Polygon).
- Name matching is diacritic-tolerant (`Mures` → `Mureș` etc.).
- Danube clipped to RO bbox, covers the expected border course.
- ANCPI validation skipped (unreachable) — see above.

## Regeneration

```bash
python3 scripts/sources/premap-tier1.py
```

Requires `data/sources/waterways.geojson` (see `data/sources/README.md`).
