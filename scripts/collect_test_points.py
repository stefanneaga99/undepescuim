#!/usr/bin/env python3
"""Collect geocoded test points for the river click-resolution verification.

Reads the geocode cache (geocoding any missing query), then writes
Legacy point collector retained for data investigation; reusable course-math
assertions now live in the shared parity fixtures under tests/fixtures/.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import geocode_common as gc
from probe_buzau_places import geocode_cached

# river -> [(label, query, expected_assoc_name)]
TEST_POINTS: dict[str, list[tuple]] = {
    "olt": [
        ("Bălan (source)", "Bălan, Harghita, România", "AVPS GHEORGHIENI"),
        ("Sf. Gheorghe", "Sfântu Gheorghe, Covasna, România", "AJVPS COVASNA"),
        ("Augustin (Rupea)", "Augustin, Brașov, România", "AVPS RUPEA"),
        ("Veneția de Jos", "Veneția de Jos, Brașov, România", "AVPS FĂGĂRAȘ"),
        ("Feldioara", "Feldioara, Brașov, România", "AVPS FĂGĂRAȘ"),
        ("Avrig (Sibiu)", "Avrig, Sibiu, România", "AJVPS SIBIU"),
        ("Râmnicu Vâlcea", "Râmnicu Vâlcea, România", "AJVPS VÂLCEA"),
        ("Drăgășani", "Drăgășani, Vâlcea, România", "AJVPS VÂLCEA"),
        ("Slatina", "Slatina, România", "AJVPS OLT"),
        ("Izbiceni", "Izbiceni, Olt, România", "AJVPS OLT"),
        ("Turnu Măgurele (vărsare)", "Turnu Măgurele, Teleorman, România", "AJVPS TELEORMAN"),
    ],
    "mures": [
        ("Subcetate (Mureș I)", "Subcetate, Harghita, România", "AVPS TÂRNAVA MARE"),
        ("Deda (Mureș IV)", "Deda, Mureș, România", "AJVPS MUREȘ"),
        ("Târgu Mureș", "Târgu Mureș, România", "AJVPS MUREȘ"),
        ("Deva (Hunedoara)", "Deva, Hunedoara, România", "AJVPS HUNEDOARA"),
        ("Periam (Timiș)", "Periam, Timiș, România", "AJVPS TIMIȘ"),
        ("Arad (vărsare)", "Arad, România", "AJVPS ARAD"),
    ],
    "siret": [
        ("Siret (Suceava)", "Siret, Suceava, România", "AJVPS BOTOȘANI"),
        ("Tudora (Botoșani)", "Tudora, Botoșani, România", "AJVPS BOTOȘANI"),
        ("Lespezi (Iași)", "Lespezi, Iași, România", "AVPS IAȘI"),
        ("Roman (Neamț)", "Roman, Neamț, România", "AVPS ROMAN"),
        ("Bacău", "Bacău, România", "Centrul Regional de Ecologie Bacău"),
        ("Suraia (Vrancea)", "Suraia, Vrancea, România", "AJVPS VRANCEA"),
        ("Șendreni (Brăila, vărsare)", "Șendreni, România", "AJVPS Brăila"),
    ],
    "prut": [
        ("Bădărăi (Botoșani)", "Bădărăi, Botoșani, România", "AJVPS BOTOȘANI"),
        ("Gorban (Iași)", "Gorban, Iași, România", "AVPS IAȘI"),
        ("Drânceni (Vaslui)", "Drânceni, Vaslui, România", "AJVPS VASLUI"),
        ("Vădeni (Galați)", "Vădeni, Galați, România", "AJVPS GALAȚI"),
        ("Galați (vărsare)", "Galați, România", "AJVPS GALAȚI"),
    ],
    "somes": [
        ("Dej (Cluj)", "Dej, Cluj, România", "AJVPS CLUJ"),
        ("Seini (Maramureș)", "Seini, Maramureș, România", "AJVPS MARAMUREȘ"),
        ("Satu Mare", "Satu Mare, România", "AJVPS SATU MARE"),
    ],
    "crisul-repede": [
        ("Oradea", "Oradea, Bihor, România", "AJVPS BIHOR"),
        ("Vadu Crișului (inferior)", "Vadu Crișului, Bihor, România", "AJVPS BIHOR"),
        ("Bucea (mijlociu)", "Bucea, Cluj, România", "AJVPS BIHOR"),
        ("Huedin (Cluj mijlociu)", "Huedin, Cluj, România", "D.S. Cluj"),
        ("Valea Drăganului (superior)", "Valea Drăganului, Cluj, România", "D.S. Cluj"),
    ],
    "arges": [
        ("Pitești (Argeș)", "Pitești, Argeș, România", "AJVPS ARGEȘ"),
        ("Potlogi (Dâmbovița)", "Potlogi, Dâmbovița, România", "AJVPS DÂMBOVIȚA"),
        ("Hotarele (Giurgiu)", "Hotarele, Giurgiu, România", "AJVPS GIURGIU"),
        ("Oltenița (Călărași, vărsare)", "Oltenița, Călărași, România", "AJVPS CĂLĂRAȘI"),
    ],
    "ialomita": [
        ("Fieni (Dâmbovița)", "Fieni, Dâmbovița, România", "AJVPS DÂMBOVIȚA"),
        ("Dridu (Ialomița)", "Dridu, Ialomița, România", "AVPS IALOMIȚA"),
    ],
    "dambovita": [
        ("Dragoslavele (superioară)", "Dragoslavele, Argeș, România", "APS AQUA CRISIUS"),
        ("Stoenești (mijlocie)", "Stoenești, Argeș, România", "AJVPS ARGEȘ"),
        ("Brezoaele (Dâmbovița)", "Brezoaele, Dâmbovița, România", "AJVPS DÂMBOVIȚA"),
        ("Cernica (Ilfov)", "Cernica, Ilfov, România", "AVPS ACVILA"),
    ],
    "jiu": [
        ("Târgu Jiu", "Târgu Jiu, România", "AJVPS GORJ"),
        ("Țânțăreni (Gorj)", "Țânțăreni, Gorj, România", "AJVPS GORJ"),
        ("Bâlta (Dolj)", "Bâlta, Dolj, România", "AJVPS DOLJ"),
        ("Bechet (vărsare)", "Bechet, Dolj, România", "AJVPS DOLJ"),
    ],
}

def main() -> None:
    db = gc.get_db()
    out: dict[str, list[dict]] = {}
    for river, cases in TEST_POINTS.items():
        out[river] = []
        for label, query, expect in cases:
            pt = geocode_cached(db, query)
            if not pt:
                print(f"  !! {river}/{label}: NO geocode for {query!r}")
                continue
            out[river].append({"label": label, "lon": pt[0], "lat": pt[1], "expect": expect})
            print(f"  {river:14} {label:26} ({pt[0]:.4f},{pt[1]:.4f}) expect={expect}")
    (ROOT / "scripts" / "test_points.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(f"\n[done] wrote scripts/test_points.json")


if __name__ == "__main__":
    main()
