#!/usr/bin/env python3
"""Fix multi-contract river click resolution (task t_ac697770).

Root causes found in the audit:
1. assign_course_frac.py only used COUNTY SEATS (the geocode()/build_queries()
   code was never called) -> every contract in a county collapsed to one frac
   (all Olt contracts 0.0 or 1.0; Dâmbovița all 0.0; Argeș all 1.0; ...).
2. merge_anpa_waters.py deduped by water NAME ONLY, silently dropping
   same-name contracts from other counties (Olt Covasna/Făgăraș/Sibiu/
   Teleorman, Siret Suceava/Bacău/Neamț/Iași/Vrancea/Galați, Prut Iași,
   Argeș Călărași/Giurgiu, Ialomița-county, Mureș-county, Timiș, Someș
   Maramureș/Satu Mare).
3. Frontend groups contracts by a 5-char-prefix waterKey, which collides
   distinct rivers (Siret/Sirețel, Someș/Someșul Mic, Crișul Repede/Alb/
   Negru/Băița, Argeș/Argeșel, Bistrița/Bistra, ...) and misses 'oltul'
   ('Râul Oltul superior' != 'Râul Olt').
4. Non-owner members of multi-contract rivers carry PARTIAL/wrong geometry
   (3x identical 57-pt Vâlcea line attached to all three 'Râul Olt'
   contracts) — clicks on them compute fractions against the wrong geometry.

Fix:
- Add `riverGroup` to waters.json (exact group key, used by the frontend
  instead of the fuzzy waterKey) for every multi-contract river and every
  collision-prone singleton.
- Add the missing ANPA contracts (canonical assoc + limite + referinta).
- Designate ONE full-course geometry owner per river; strip geometry from
  other members; upgrade Jiu to the full OSM relation; build Someș/Prut
  courses from the OSM bulk-download ways.
- Recompute course_frac by GEOCODING each contract's limite places
  (Nominatim, cached) and projecting onto the owner's course.
"""
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import geocode_common as gc
from probe_buzau_places import fraction_at

WATERS = ROOT / "public" / "data" / "waters.json"
ANPA_FILE = ROOT / "data" / "processed" / "anpa_waters.jsonl"
OSM_FILE = ROOT / "data" / "rivers_osm.geojson"


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().split())


def norm_flat(s: str) -> str:
    """norm() without collapsing whitespace (matches ANPA name_normalized)."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


# ---------------------------------------------------------------------------
# riverGroup: exact group key per normalized water name.
# 'raul X' / 'Xul superior' style variants of the SAME river share a key;
# distinct rivers that collide under the old 5-char prefix get their own key.
# ---------------------------------------------------------------------------
RIVER_GROUP: dict[str, str] = {}


def rg(name: str, key: str) -> None:
    RIVER_GROUP[norm_flat(name)] = key


def rg_many(key: str, *names: str) -> None:
    for n in names:
        rg(n, key)


# --- audit rivers ---
rg_many("olt", "Râul Olt", "Râul Olt și afluenții săi", "Râul Oltul superior")
rg_many("mures",
        "Râul Mureș", "Râul Mureș I", "Râul Mureș II", "Râul Mureș III",
        "Râul Mureș IV", "Râul Mureș, cu afluenții", "Râul Mureș, cu afluenții săi")
rg_many("siret", "Râul Siret")
rg("Râul Sirețel", "siretel")
rg_many("prut", "Râul Prut", "Râul Prut și revărsări", "Prut– fără lacul Stânca", "Râul Prut și revărsările")
rg_many("somes", "Râul Someș")
rg_many("somesul-mare", "Râul Someșul Mare", "Râul Someșul Mare inferior")
rg_many("somesul-mic", "Râul Someșul Mic")
rg_many("somesu-rece", "Someșu Rece Mijlociu", "Someșu Rece Superior", "Someșul Rece Inferior")
rg_many("somesul-cald", "Someșul Cald Mijlociu", "Someșul Cald Superior", "Lacul Someșul Cald")
rg_many("crisul-repede", "Râul Crișul Repede", "Râul Crișul Repede inferior",
        "Râul Crișul Repede Mijlociu", "Crișul Repede Superior", "Crișul Repede Mijlociu")
rg_many("crisul-alb", "Râul Crișul Alb", "Râul Crișul Alb, cu afluenții")
rg_many("crisul-negru", "Râul Crișul Negru", "Râul Crișul Negru inferior", "Râul Crișul Negru mijlociu")
rg("Râul Crișul Băița", "crisul-baita")
rg_many("arges", "Râul Argeș")
rg_many("argesel", "Râul Argeșel inferior", "Râul Argeșel Superior")
rg_many("ialomita", "Râul Ialomița")
rg_many("dambovita", "Râul Dâmbovița", "Râul Dâmbovița mijlocie", "Râul Dâmbovița mijlociu",
        "Râul Dâmbovița Superioară", "Râul Dâmbovița superioară")
rg_many("jiu", "Râul Jiu", "Râul Jiu și afluenții săi")
rg_many("jiul-de-est", "Râul Jiul de est Inferior")
rg_many("jiul-de-vest", "Râul Jiul de vest – superior cu afluenții", "Râul Jiul de vest mijlociu")
rg("Râul Jiul Inferior", "jiul-inferior")

# --- other multi-contract rivers / collision fixes ---
rg_many("buzau", "Râul Buzău", "Râul Buzăul superior cu afluenții săi",
        "Râul Buzăul inferior", "Pârâu Buzăul Mijlociu", "Valea Buzăului superior", "Valea Buzăului inferior")
rg_many("oltet", "Râul Olteț")
rg_many("moldova", "Râul Moldova", "Râul Moldova I", "Râul Moldova II", "Râul Moldova III", "Râul Moldova IV")
rg_many("jijia", "Râul Jijia", "Râul Jijia curs principal")
rg_many("tarnava-mare", "Târnava Mare", "Râul Târnava Mare superior", "Râul Târnava Mare mijlocie", "Râul Târnava Mare inferior")
rg("Râul Târnava Mică", "tarnava-mica")
rg_many("cibin", "Râul Cibin", "Râul Cibinul Inferior")
rg("Râul Cibinul Mare", "cibinul-mare")
rg("Râul Cibinul Mic", "cibinul-mic")
rg_many("negru", "Râul Negru I", "Râul Negru II")
rg_many("homorod", "Râul Homorod")
rg("Râul Homorodul Mare", "homorodul-mare")
rg("Râul Homorod Mic", "homorod-mic")
rg("Râul Homorodul Nou", "homorodul-nou")
rg_many("iza", "Râul Iza", "Râul Iza superioară")
rg_many("iuhod", "Râul Iuhod", "Râul Iuhodul Praidului")
rg_many("lotru", "Râul Lotru mijlociu", "Râul Lotrul Inferior")
rg_many("ramnicu-sarat", "Râul Râmnicu Sărat")
rg_many("salauta", "Râul Sălăuța Inferioară", "Râul Sălăuța Superioară")
rg_many("streiul", "Râul Strei, cu afluenții", "Râul Streiul montan inferior")
rg_many("steiul", "Râul Steiul montan inferior", "Râul Steiul montan mijlociu")
rg_many("susita", "Râul Șușița")
rg("Râul Șușița Seacă", "susita-seaca")
rg("Râul Șușița Verde", "susita-verde")
rg_many("talna", "Râul Talna", "Râul Talna Mare superioara")
rg_many("teleajen", "Râul Teleajen inferior", "Râul Teleajen inferior - Bucov",
        "Râul Teleajen superior", "Râul Teleajenul inferior")
rg_many("timis", "Râul Timiș", "Râul Timișul inferior")
rg("Raul Timișu Mort", "timisu-mort")
rg_many("tur", "Râul Tur", "Râul Tur superior", "Râul Tur mijlociu")
rg_many("uzul", "Râul Uzul", "Râul Uzul superior")
rg_many("doamnei", "Râul Doamnei inferior", "Râul Doamnei Superior")
rg_many("targului", "Râul Târgului inferior", "Râul Târgului mijlociu", "Râul Târgului superior")
rg_many("prahova", "Râul Prahova inferioară", "Râul Prahova mijlocie", "Râul Prahova superioară")
rg_many("zabala", "Râul Zăbala mijlocie", "Râul Zăbala inferioara")
rg("Râul Zăbăluța", "zabaluta")
rg_many("colentina", "Râul Colentina")
rg_many("calmatui", "Râul Călmățui", "Râul Călmățui cu afluenții săi")
rg_many("barzava", "Râul Bârzava", "Râul Bârzava inferioară")
rg_many("budacul", "Râul Budacul inferior", "Râul Budacul superior")
rg("Râul Casinul inferior", "casinul")
rg("Râul Cașin", "casin")
rg_many("colibita", "Râul Colibița superioară", "Râul Colibița inferioară")
rg_many("geoagiu", "Råul Geoagiu Inferior", "Râul Geoagiu Superior")
rg("Râul Oituz", "oituz")
rg("Râul Oituzul Moldovenesc", "oituzul-moldovenesc")
rg("Râul Cerna", "cerna")
rg("Râul Cerna superioară Obârșia", "cerna-superioara")
rg_many("bistrita", "Râul Bistrița", "Râul Bistrița I Zugreni", "Râul Bistrița II",
        "Râul Bistrița V", "Râul Bistrița VI", "Râul Bistrița Aurie I",
        "Râul Bistrița Aurie II", "Râul Bistrița Aurie III", "Bistra Aurie II")
rg_many("bistra", "Râul Bistra", "Râul Bistra Ardealului, mijlociu")
rg("Râul Bistricioara", "bistricioara")
rg("Râul Cricov", "cricov")
rg("Râul Cricovul Dulce", "cricovul-dulce")
rg("Râul Cricovul Sărat", "cricovul-sarat")
rg("Râul Sebeș", "sebes")
rg("Râul Sebeșul de Jos", "sebesul-de-jos")
rg("Râul Sebeșul de Sus", "sebesul-de-sus")
rg("Râul Tazlău", "tazlau")
rg("Râul Tazlăul Sărat", "tazlaul-sarat")
rg_many("sadu", "Râul Sadu Inferior", "Sadu V")
rg("Râul Șomuzul Mare și afluenții", "somuzul-mare")
rg("Râul Șomuzul Mic și afluenții", "somuzul-mic")
rg("Râul Geamăna", "geamana")
rg("Râul Geamărtălui", "geamartalui")
rg("Râul Topolog", "topolog")
rg("Lacul Topolovățul", "topolovatul")
rg("Râul Rudărie", "rudarie")
rg("Râul Rudăreasa", "rudareasa")
rg("Balta Potcoava", "potcoava")
rg("Potcoava Bordușani", "potcoava-bordusani")
rg("Izvorul Mureș", "izvorul-mures")
rg("Izvorul Izei", "izvorul-izei")
rg("Lacul Izvorul (Măgurii)", "izvorul")
rg("Lacul Izvorul(Măgurii)", "izvorul")
rg_many("malaia", "Lacul Malaia", "Lacul Mălaia", "Râul Malaia")
rg("Râul Baranca Hudești", "baranca-hudesti")
rg("Râul Baranca Nouă", "baranca-noua")
rg("Râul Bâsca Rozilei", "basca-rozilei")
rg("Râul Bâsca Chiojdului", "basca-chiojdului")
rg("Râul Olănești", "olanesti")
rg("Râul Olănești cu pâraiele Cheia, Baciului și Pârâul de sub Stână", "olanesti")
rg("Râul Boia", "boia")
rg("Râul Boia Mică", "boia-mica")
rg("Râul Arieș", "aries")
rg_many("doamnei", "Râul Doamnei inferior", "Râul Doamnei Superior")
rg("Râul Măieruș", "maierus")
rg("Râul Cormoș", "cormos")
rg("Râul Fișag", "fisag")
rg("Râul Mădărașul Mare", "madarasul-mare")
rg("Pârâul Minei", "minei")
rg("Pârâul Mare", "paraul-mare-harghita")
rg("Pârâul Mic", "paraul-mic-harghita")
rg("Râul Avrigul Mare", "avrigul-mare")
rg("Râul Lotrioara", "lotrioara")
rg("Pârâul Tălmăcuț", "talmacut")
rg("Pârâul Valea Rîndiboului", "valea-rundiboului")
rg("Pârâul Valea Strâmbii", "valea-strambii")
rg("Râul Uria", "uria")
rg("Valea Robești", "valea-robesti")
rg("Valea Călinești cu pâraiele Călinești, Sulița și Zănoaga", "valea-calinesti")
rg("Râul Luncavăț", "luncavat")
rg("Râul Topolog", "topolog")

# ---------------------------------------------------------------------------
# Missing ANPA contracts to ADD (dropped by name-only dedupe in the merge).
# key: riverGroup, anpa id, anchor query (geocoded, cached).
# ---------------------------------------------------------------------------
MISSING: list[dict] = [
    # --- Olt ---
    {"id": "anpa-0250", "group": "olt", "anchor": "Piatra Găurită, Covasna, România",
     "anchor_fb": "Baraolt, Covasna, România"},
    {"id": "anpa-0192", "group": "olt", "anchor": "Veneția de Jos, Brașov, România",
     "anchor_fb": "Feldioara, Brașov, România"},
    {"id": "anpa-0519", "group": "olt", "anchor": "Avrig, Sibiu, România",
     "anchor_fb": "Tălmaciu, Sibiu, România"},
    {"id": "anpa-0581", "group": "olt", "anchor": "Turnu Măgurele, Teleorman, România",
     "anchor_fb": "Islaz, Teleorman, România"},
    # --- Mureș ---
    {"id": "anpa-0426", "group": "mures", "anchor": "Târgu Mureș, România",
     "anchor_fb": "Chețani, Mureș, România"},
    {"id": "anpa-0584", "group": "mures", "anchor": "Periam, Timiș, România",
     "anchor_fb": "Sânnicolau Mare, Timiș, România"},
    # --- Siret ---
    {"id": "anpa-0552", "group": "siret", "anchor": "Siret, Suceava, România",
     "anchor_fb": "Dolhasca, Suceava, România"},
    {"id": "anpa-0066", "group": "siret", "anchor": "Bacău, România",
     "anchor_fb": None},
    {"id": "anpa-0469", "group": "siret", "anchor": "Roman, Neamț, România",
     "anchor_fb": None},
    {"id": "anpa-0390", "group": "siret", "anchor": "Lespezi, Iași, România",
     "anchor_fb": "Pașcani, Iași, România"},
    {"id": "anpa-0674", "group": "siret", "anchor": "Suraia, Vrancea, România",
     "anchor_fb": "Mărășești, Vrancea, România"},
    {"id": "anpa-0296", "group": "siret", "anchor": "Buciumeni, Galați, România",
     "anchor_fb": "Galați, România"},
    # --- Prut ---
    {"id": "anpa-0389", "group": "prut", "anchor": "Gorban, Iași, România",
     "anchor_fb": "Tabăra, Iași, România"},
    # --- Someș ---
    {"id": "anpa-0402", "group": "somes", "anchor": "Seini, Maramureș, România",
     "anchor_fb": "Țicău, Maramureș, România"},
    {"id": "anpa-0496", "group": "somes", "anchor": "Satu Mare, România",
     "anchor_fb": None},
    # --- Argeș ---
    {"id": "anpa-0230", "group": "arges", "anchor": "Oltenița, Călărași, România",
     "anchor_fb": None},
    {"id": "anpa-0298", "group": "arges", "anchor": "Hotarele, Giurgiu, România",
     "anchor_fb": "Ghimpați, Giurgiu, România"},
    # --- Ialomița ---
    {"id": "anpa-0388", "group": "ialomita", "anchor": "Dridu, Ialomița, România",
     "anchor_fb": "Urziceni, Ialomița, România"},
]

# ---------------------------------------------------------------------------
# course_frac anchors for EXISTING waters: (matcher, anchor query, fallback)
# matcher: dict matched by name (norm_flat) — use the full water name.
# ---------------------------------------------------------------------------
ANCHORS: list[dict] = [
    # --- Olt ---
    {"group": "olt", "name": "Râul Oltul superior", "anchor": "Bălan, Harghita, România", "anchor_fb": None},
    {"group": "olt", "name": "Râul Olt și afluenții săi", "anchor": "Augustin, Brașov, România", "anchor_fb": None},  # AVPS RUPEA
    {"group": "olt", "name": "Râul Olt", "judet": "Brașov", "anchor": "Feldioara, Brașov, România", "anchor_fb": None},  # AJPS Brașov
    {"group": "olt", "name": "Râul Olt", "judet": "Vâlcea", "anchor": "Gura Lotrului, Vâlcea, România", "anchor_fb": "Brezoi, Vâlcea, România"},
    {"group": "olt", "name": "Râul Olt", "judet": "Olt", "anchor": "Izbiceni, Olt, România", "anchor_fb": None},
    # --- Mureș (verify existing) ---
    {"group": "mures", "name": "Râul Mureș I", "anchor": "Subcetate, Harghita, România", "anchor_fb": None},
    {"group": "mures", "name": "Râul Mureș II", "anchor": "Sălard, Mureș, România", "anchor_fb": None},
    {"group": "mures", "name": "Râul Mureș IV", "anchor": "Deda, Mureș, România", "anchor_fb": None},
    {"group": "mures", "name": "Râul Mureș, cu afluenții", "anchor": "Deva, Hunedoara, România", "anchor_fb": None},
    {"group": "mures", "name": "Râul Mureș", "judet": "Arad", "anchor": "Lipova, Arad, România", "anchor_fb": None},
    # --- Siret ---
    {"group": "siret", "name": "Râul Siret", "judet": "Botoșani", "anchor": "Tudora, Botoșani, România", "anchor_fb": "Bucecea, Botoșani, România"},
    # --- Prut ---
    {"group": "prut", "name": "Prut– fără lacul Stânca", "anchor": "Bădărăi, Botoșani, România", "anchor_fb": "Ștefănești, Botoșani, România"},
    {"group": "prut", "name": "Râul Prut și revărsări", "anchor": "Drânceni, Vaslui, România", "anchor_fb": "Cârja, Vaslui, România"},
    {"group": "prut", "name": "Râul Prut", "judet": "Galați", "anchor": "Vădeni, Galați, România", "anchor_fb": "Galați, România"},
    # --- Someș ---
    {"group": "somes", "name": "Râul Someș", "anchor": "Dej, Cluj, România", "anchor_fb": None},
    # --- Crișul Repede ---
    {"group": "crisul-repede", "name": "Crișul Repede Superior", "anchor": "Valea Drăganului, Cluj, România", "anchor_fb": "Huedin, Cluj, România"},
    {"group": "crisul-repede", "name": "Crișul Repede Mijlociu", "anchor": "Huedin, Cluj, România", "anchor_fb": None},
    {"group": "crisul-repede", "name": "Râul Crișul Repede Mijlociu", "anchor": "Bucea, Cluj, România", "anchor_fb": "Bratca, Bihor, România"},
    {"group": "crisul-repede", "name": "Râul Crișul Repede inferior", "anchor": "Vadu Crișului, Bihor, România", "anchor_fb": "Bratca, Bihor, România"},
    {"group": "crisul-repede", "name": "Râul Crișul Repede", "anchor": "Oradea, Bihor, România", "anchor_fb": None},
    # --- Argeș ---
    {"group": "arges", "name": "Râul Argeș", "judet": "Argeș", "anchor": "Pitești, Argeș, România", "anchor_fb": None},
    {"group": "arges", "name": "Râul Argeș", "judet": "Dâmbovița", "anchor": "Potlogi, Dâmbovița, România", "anchor_fb": "Valea Mare, Dâmbovița, România"},
    # --- Ialomița ---
    {"group": "ialomita", "name": "Râul Ialomița", "anchor": "Fieni, Dâmbovița, România", "anchor_fb": None},
    # --- Dâmbovița ---
    {"group": "dambovita", "name": "Râul Dâmbovița Superioară", "anchor": "Dragoslavele, Argeș, România", "anchor_fb": "Rucăr, Argeș, România"},
    {"group": "dambovita", "name": "Râul Dâmbovița mijlocie", "anchor": "Malul cu Flori, Argeș, România", "anchor_fb": "Stoenești, Argeș, România"},
    {"group": "dambovita", "name": "Râul Dâmbovița", "judet": "Dâmbovița", "anchor": "Brezoaele, Dâmbovița, România", "anchor_fb": "Târgoviște, România"},
    {"group": "dambovita", "name": "Râul Dâmbovița", "judet": "Ilfov", "anchor": "Cernica, Ilfov, România", "anchor_fb": "București, România"},
    # --- Jiu ---
    {"group": "jiu", "name": "Râul Jiu", "anchor": "Țânțăreni, Gorj, România", "anchor_fb": "Bumbești Jiu, Gorj, România"},  # Gorj
    {"group": "jiu", "name": "Râul Jiu și afluenții săi", "anchor": "Bâlta, Dolj, România", "anchor_fb": "Bechet, Dolj, România"},
    # --- Olteț ---
    {"group": "oltet", "name": "Râul Olteț", "judet": "Olt", "anchor": "Dobriceni, Olt, România", "anchor_fb": "Slatina, România"},
]

# ---------------------------------------------------------------------------
# Olt EXACT sector intervals: [start_query, end_query] per contract slug.
# start=None -> source (0.0); end=None -> mouth (1.0). When start >= end
# (projection degeneracy) the sector is skipped and Voronoi on course_frac
# is used instead. Overlapping intervals (AJPS Brașov is county-wide) resolve
# to the SMALLEST containing interval — sub-club contracts win their stretch.
# ---------------------------------------------------------------------------
OLT_SECTORS: list[tuple] = [
    # slug, start_query, end_query
    ("anpa-anpa-0339", None, "Bălan, Harghita, România"),                                # Gheorghieni: source -> Bioxid/Bălan
    ("anpa-anpa-0250", "Piatra Găurită, Covasna, România", "Augustin, Brașov, România"),  # Covasna
    ("ehwpvgwh", "Augustin, Brașov, România", "Veneția de Jos, Brașov, România"),        # Rupea
    ("anpa-anpa-0192", "Veneția de Jos, Brașov, România", "Arpașu de Jos, Sibiu, România"),  # Făgăraș
    ("anpa-anpa-0519", "Arpașu de Jos, Sibiu, România", "Câineni, Vâlcea, România"),     # Sibiu
    ("3e8t20hn", "Câineni, Vâlcea, România", "Drăgășani, România"),                      # Vâlcea (extends to county border)
    ("y6i6nikh", "Izbiceni, Olt, România", "Lița, Teleorman, România"),                   # Olt county -> Teleorman border
    ("anpa-anpa-0581", "Lița, Teleorman, România", None),                                 # Teleorman: border -> mouth
]
OLT_SECTOR_FALLBACKS: dict[str, list[str]] = {
    "Piatra Găurită, Covasna, România": ["Bățanii Mari, Covasna, România", "Baraolt, Covasna, România"],
    "Arpașu de Jos, Sibiu, România": ["Arpașu de Sus, Sibiu, România"],
    "Câineni, Vâlcea, România": ["Câinenii Mici, Vâlcea, România"],
    "Drăgășani, România": ["Drăgășani, Vâlcea, România"],
    "Lița, Teleorman, România": ["Lița, România"],
}

# ---------------------------------------------------------------------------
# Geometry ownership: river -> slug that carries the FULL course.
# Non-owners get their geometry stripped (they render via the shared course).
# ---------------------------------------------------------------------------
COURSE_OWNER: dict[str, str] = {
    "olt": "ehwpvgwh",          # Râul Olt și afluenții săi (AVPS RUPEA) — full relation
    "mures": "hmd3pa0v",        # Râul Mureș (Arad) — full relation 89325
    "siret": "9m2irr6m",        # Râul Siret (Brăila) — full relation 7689581
    "prut": "o4sf1fah",         # Prut– fără lacul Stânca — built from OSM ways
    "somes": "lagsqhtl",        # Râul Someș (Cluj) — built from OSM ways
    "crisul-repede": "xzrr6do0",  # Râul Crișul Repede (Bihor) — relation 89339
    "arges": "3614s8es",        # Râul Argeș (Dâmbovița) — full relation 5815028
    "ialomita": "3ek8e82l",     # Râul Ialomița (Dâmbovița) — full relation 6153744
    "dambovita": "fo3h8cp6",    # Râul Dâmbovița (Ilfov) — full relation 6213935
    "jiu": "qrjybswm",          # Râul Jiu (Gorj) — UPGRADE to relation 7691863
    "oltet": "dvhkx2a2",        # Râul Olteț (Vâlcea) — full course
    "moldova": "anpa-anpa-0391",  # Râul Moldova (Iași) — full course
}

# ---------------------------------------------------------------------------
# Geometry upgrades: slug -> (source, name/type) from rivers_osm.geojson.
# ---------------------------------------------------------------------------
GEOM_UPGRADE: dict[str, dict] = {
    "qrjybswm": {"kind": "relation", "name": "Jiu"},   # full Jiu course
}


def load_osm_geometries() -> dict:
    """Return {('relation'|'way', name_norm): geometry} from the bulk download."""
    data = json.loads(OSM_FILE.read_text(encoding="utf-8"))
    nodes = {
        el["id"]: (el.get("lat"), el.get("lon"))
        for el in data.get("elements", [])
        if el["type"] == "node" and "lat" in el
    }
    ways: dict[int, list] = {}
    for el in data.get("elements", []):
        if el["type"] != "way":
            continue
        coords = [[nodes[n][1], nodes[n][0]] for n in el.get("nodes", []) if n in nodes]
        if len(coords) >= 2:
            ways[el["id"]] = coords
    rel_geoms: dict[str, dict] = {}
    way_geoms: dict[str, dict] = {}
    for el in data.get("elements", []):
        if el["type"] == "relation":
            coords = [ways[m["ref"]] for m in el.get("members", []) if m["type"] == "way" and m["ref"] in ways]
            if coords:
                rel_geoms[norm(el.get("tags", {}).get("name", ""))] = {
                    "type": "MultiLineString", "coordinates": coords}
        elif el["type"] == "way":
            n = norm(el.get("tags", {}).get("name", ""))
            if n and n not in way_geoms:  # first way per name
                way_geoms[n] = {"type": "LineString", "coordinates": ways[el["id"]]}
    return {**way_geoms, **rel_geoms}


def build_course_from_ways(geoms: dict, name_norm: str) -> dict:
    """Build a MultiLineString from ALL ways with the given name (ordered by PCA at
    fraction-time; we just need every segment present)."""
    data = json.loads(OSM_FILE.read_text(encoding="utf-8"))
    nodes = {
        el["id"]: (el.get("lat"), el.get("lon"))
        for el in data.get("elements", [])
        if el["type"] == "node" and "lat" in el
    }
    parts = []
    seen_ids = set()
    for el in data.get("elements", []):
        if el["type"] != "way":
            continue
        if norm(el.get("tags", {}).get("name", "")) != name_norm:
            continue
        eid = el["id"]
        if eid in seen_ids:
            continue
        seen_ids.add(eid)
        coords = [[nodes[n][1], nodes[n][0]] for n in el.get("nodes", []) if n in nodes]
        if len(coords) >= 2:
            parts.append(coords)
    return {"type": "MultiLineString", "coordinates": parts}


def geocode_cached(db, query: str):
    row = db.execute(
        "SELECT result_json FROM geocode_cache WHERE query_string = ?", (query,)
    ).fetchone()
    if row is not None:
        if row[0]:
            try:
                data = json.loads(row[0])
                if data:
                    return [float(data[0]["lon"]), float(data[0]["lat"])]
            except Exception:
                pass
        return None
    results = gc.nominatim_search(query, countrycodes="ro")
    if results:
        first = results[0]
        db.execute(
            "INSERT OR REPLACE INTO geocode_cache (query_string, water_name, water_type, result_json, osm_type, osm_id, geometry_type, bbox, source, confidence) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (query, "fix_river_contracts", "rau", json.dumps(results, ensure_ascii=False),
             first.get("osm_type"), str(first.get("osm_id")),
             first.get("geojson", {}).get("type") if isinstance(first.get("geojson"), dict) else None,
             json.dumps(first.get("boundingbox")), "nominatim", "medium"),
        )
        db.commit()
        return [float(first["lon"]), float(first["lat"])]
    db.execute(
        "INSERT OR REPLACE INTO geocode_cache (query_string, water_name, water_type, result_json, source) VALUES (?,?,?,NULL,?)",
        (query, "fix_river_contracts", "rau", "nominatim_negative"),
    )
    db.commit()
    return None


def geocode_any(db, queries):
    for q in queries:
        if not q:
            continue
        pt = geocode_cached(db, q)
        if pt:
            return pt, q
    return None, None


def main() -> None:
    waters = json.loads(WATERS.read_text(encoding="utf-8"))
    by_slug = {w["slug"]: w for w in waters}
    anpa = {json.loads(l)["id"]: json.loads(l)
            for l in ANPA_FILE.read_text(encoding="utf-8").splitlines() if l.strip()}
    db = gc.get_db()

    print("== geometry upgrades ==")
    osm = load_osm_geometries()
    # Upgrade Jiu to the full relation
    for slug, spec in GEOM_UPGRADE.items():
        key = norm(spec["name"])
        g = osm.get(key)
        if g:
            old = by_slug[slug].get("geometry")
            by_slug[slug]["geometry"] = g
            print(f"  {slug} geometry upgraded: {old and old.get('type')} -> {g['type']} ({sum(len(p) for p in g['coordinates'])} pts)")
        else:
            print(f"  !! {slug}: relation {spec['name']!r} not found in OSM download")
    # Build Someș / Prut courses from ways
    for slug, name_norm in (("lagsqhtl", "somes"), ("o4sf1fah", "prut")):
        g = build_course_from_ways(osm, name_norm)
        npts = sum(len(p) for p in g["coordinates"])
        lats = [p[1] for part in g["coordinates"] for p in part]
        print(f"  {slug}: built {name_norm} course from {len(g['coordinates'])} ways, {npts} pts, lat {min(lats):.2f}-{max(lats):.2f}")
        if npts >= 10:
            by_slug[slug]["geometry"] = g
        else:
            print(f"  !! {slug}: too few points, keeping existing")

    print("\n== anchors ==")
    # resolve anchor points -> frac per (group, name)
    fracs: dict[tuple, float] = {}
    groups: dict[str, list] = {}
    for w in waters:
        g = w.get("riverGroup") or RIVER_GROUP.get(norm_flat(w.get("name", "")))
        if g:
            groups.setdefault(g, []).append(w)
    for g, members in groups.items():
        owner_slug = COURSE_OWNER.get(g)
        if not owner_slug:
            continue
        owner = by_slug.get(owner_slug)
        if not owner or not owner.get("geometry"):
            print(f"  [skip] {g}: no owner geometry ({owner_slug})")
            continue
        parts = owner["geometry"]["coordinates"]
        for a in ANCHORS:
            if a["group"] != g:
                continue
            # find the matching water(s) by name (+ county when given)
            targets = [w for w in members
                       if norm_flat(w.get("name")) == norm_flat(a["name"])
                       and (not a.get("judet") or norm_flat(w.get("judet")) == norm_flat(a["judet"]))]
            if not targets:
                print(f"  [warn] {g}: no water named {a['name']!r} {a.get('judet') or ''}")
                continue
            pt, used_q = geocode_any(db, [a["anchor"], a["anchor_fb"]])
            if not pt:
                print(f"  [warn] {g}/{a['name']}: NO geocode for {a['anchor']!r}")
                continue
            frac, dist = fraction_at(parts, pt)
            if frac is None:
                print(f"  [warn] {g}/{a['name']}: fraction failed")
                continue
            for t in targets:
                fracs[(g, t["slug"])] = frac
                print(f"  {g:14} {a['name'][:34]:36} ({pt[0]:.4f},{pt[1]:.4f}) -> frac {frac:.4f} [via {used_q}]")

    print("\n== missing contracts ==")
    added = 0
    for m in MISSING:
        slug = f"anpa-anpa-{m['id'].replace('anpa-', '')}"
        if slug in by_slug:
            print(f"  [skip] {slug} already exists")
            continue
        row = anpa[m["id"]]
        assoc = (row.get("association") or "").strip()
        # canonical association name/slug (ANPA carries 'A. ' prefixes and
        # trailing spaces for the same association)
        ASSOC_OVERRIDES = {
            "A. Centrul Regional de Ecologie Bacău": "Centrul Regional de Ecologie Bacău",
            "A. Centrul Regional de Ecologie BACĂU": "Centrul Regional de Ecologie Bacău",
        }
        assoc = ASSOC_OVERRIDES.get(assoc, assoc)
        entry = {
            "slug": slug,
            "name": row["water_name"],
            "judet": row["county"].title(),
            "type": "ape",
            "subtype": "rau" if row.get("water_type") == "river" else "lac",
            "limite": row.get("limits_text") or "",
            "dimensiune": row.get("sector_raw") or "",
            "pescuit_interzis": False,
            "referinta": f"Contract {row.get('contract_number')} ({row.get('contract_date')})",
            "coordinates": None,
            "driving": None,
            "bbox": None,
            "asociatie": {
                "name": assoc,
                "slug": norm(assoc).replace(" ", "-"),
            },
            "geometry": None,
            "riverGroup": m["group"],
        }
        # anchor frac
        owner_slug = COURSE_OWNER.get(m["group"])
        if owner_slug and by_slug.get(owner_slug, {}).get("geometry"):
            parts = by_slug[owner_slug]["geometry"]["coordinates"]
            pt, used_q = geocode_any(db, [m["anchor"], m["anchor_fb"]])
            if pt:
                frac, dist = fraction_at(parts, pt)
                if frac is not None:
                    entry["course_frac"] = round(frac, 4)
                    print(f"  {slug:16} {entry['name'][:40]:42} [{entry['judet']}] frac={frac:.4f} [via {used_q}]")
        waters.append(entry)
        by_slug[slug] = entry
        groups.setdefault(m["group"], []).append(entry)
        added += 1
    print(f"  added {added} missing contracts")

    print("\n== applying riverGroup + course_frac ==")
    n_group = 0
    for w in waters:
        g = RIVER_GROUP.get(norm_flat(w.get("name", "")))
        if g:
            w["riverGroup"] = g
            n_group += 1
    # strip geometry/bbox from non-owner members of multi-contract rivers
    stripped = 0
    for g, members in groups.items():
        owner_slug = COURSE_OWNER.get(g)
        if not owner_slug:
            continue
        for w in members:
            if w["slug"] == owner_slug:
                continue
            if w.get("geometry"):
                w.pop("geometry", None)
            # never render a bbox rectangle for a river sector (it is a
            # click-resolution target only; the shared course renders)
            if w.get("bbox"):
                w.pop("bbox", None)
            stripped += 1

    # exact Olt sector intervals (sectorStart/sectorEnd)
    olt_parts = by_slug["ehwpvgwh"]["geometry"]["coordinates"]
    for slug, start_q, end_q in OLT_SECTORS:
        w = by_slug.get(slug)
        if not w:
            print(f"  [warn] OLT sector: missing water {slug}")
            continue
        def _frac(query, fb_key):
            if query is None:
                return 0.0 if fb_key == "start" else 1.0
            qs = [query] + OLT_SECTOR_FALLBACKS.get(query, [])
            pt, used = geocode_any(db, qs)
            if not pt:
                print(f"  [warn] OLT sector {slug}: no geocode for {query!r}")
                return None
            f, _d = fraction_at(olt_parts, pt)
            return f
        s = _frac(start_q, "start")
        e = _frac(end_q, "end")
        if s is None or e is None or s >= e:
            print(f"  [warn] OLT sector {slug}: skipped (start={s}, end={e}) — Voronoi fallback")
            continue
        w["sectorStart"] = round(s, 4)
        w["sectorEnd"] = round(e, 4)
        print(f"  OLT sector {slug:16} [{w['name'][:28]:30}] -> [{s:.4f}, {e:.4f}]")
    # set course_frac from anchors
    n_frac = 0
    for (g, slug), frac in fracs.items():
        w = by_slug[slug]
        w["course_frac"] = round(frac, 4)
        n_frac += 1
    # mouth-sector contracts keep 1.0 (Siret Brăila)
    for slug in ("9m2irr6m",):
        if slug in by_slug:
            by_slug[slug]["course_frac"] = 1.0

    # normalize association names (ANPA carries trailing spaces / title-case
    # variants of the same association)
    ASSOC_OVERRIDES = {
        "A. Centrul Regional de Ecologie Bacău": "Centrul Regional de Ecologie Bacău",
        "A. Centrul Regional de Ecologie BACĂU": "Centrul Regional de Ecologie Bacău",
    }
    assoc_fixed = 0
    for w in waters:
        a = w.get("asociatie")
        if not a or not a.get("name"):
            continue
        name = (a["name"] or "").strip()
        name = ASSOC_OVERRIDES.get(name, name)
        if name != a["name"]:
            a["name"] = name
            assoc_fixed += 1
        expected_slug = norm(name).replace(" ", "-")
        if a.get("slug") and a["slug"].strip() != expected_slug and a["slug"].strip() != name.lower().replace(" ", "-"):
            # keep existing slugs stable; only fix trailing-whitespace slugs
            if a["slug"].strip() != a["slug"]:
                a["slug"] = a["slug"].strip()
    print(f"  normalized {assoc_fixed} association names")
    print(f"  riverGroup applied to {n_group} waters; stripped {stripped} non-owner geometries; set {n_frac} course_fracs")

    # remove arebaltapeste dupe of 'Râul Dâmbovița mijlociu' (same contract as anpa-anpa-0056)
    dup = next((w for w in waters if w.get("slug") == "f5tx309y"), None)
    if dup:
        waters = [w for w in waters if w.get("slug") != "f5tx309y"]
        print(f"  removed dupe f5tx309y ({dup.get('name')}) — same contract as anpa-anpa-0056")

    # Gorj Jiu association: ANPA canonical = AJVPS GORJ (was A.CERBUL CARPATIN from arebaltapeste)
    jiu_gorj = by_slug.get("qrjybswm")
    if jiu_gorj:
        jiu_gorj["asociatie"] = {"name": "AJVPS GORJ", "slug": "ajvps-gorj"}
        print("  Râul Jiu (Gorj) association updated to AJVPS GORJ (ANPA canonical)")

    WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n[done] {len(waters)} waters written")


if __name__ == "__main__":
    main()
