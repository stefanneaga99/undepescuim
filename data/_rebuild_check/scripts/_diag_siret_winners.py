#!/usr/bin/env python3
"""Preview the FE click resolution winners across the course, using the
sector table + smallest-interval rule from contractAtFraction."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
d = json.loads((ROOT / "data/processed/siret_full_course.json").read_text(encoding="utf-8"))
sectors = d["sectors"]

# association per county
ASSOC = {
    "Suceava": "AJVPS BOTOȘANI", "Botoșani": "AJVPS BOTOȘANI", "Iași": "AVPS IAȘI",
    "Neamț": "AVPS ROMAN", "Bacău": "Centrul Regional de Ecologie BACĂU",
    "Vrancea": "AJVPS VRANCEA", "Galați": "AJVPS GALAȚI", "Brăila": "AJVPS Brăila",
}

# sort all sector boundaries
bounds = sorted({b for s in sectors.values() for b in s})
print("boundaries:", [round(b, 4) for b in bounds])

def winner(frac):
    best, best_len = None, float("inf")
    for c, (s, e) in sectors.items():
        if s <= frac < e and (e - s) < best_len:
            best, best_len = c, e - s
    return best

print("\ninterval -> winner:")
for i in range(len(bounds) - 1):
    mid = (bounds[i] + bounds[i + 1]) / 2
    w = winner(mid)
    print(f"  {bounds[i]:.4f} .. {bounds[i+1]:.4f}  -> {w:10s} {ASSOC.get(w, '?')}")

# point checks: lat -> frac -> winner
coords = d["geometry"]["coordinates"]
def frac_at_lat(lat):
    # nearest course point by lat
    idx = min(range(len(coords)), key=lambda i: abs(coords[i][1] - lat))
    return idx / (len(coords) - 1), coords[idx]

print("\nlat checks:")
for lat, expect in [(48.0, "Suceava"), (47.7, "Botoșani"), (47.2, "Iași"), (46.9, "Neamț"),
                    (46.5, "Bacău"), (45.91, "Vrancea"), (45.76, "Vrancea"), (45.70, "Vrancea"),
                    (45.55, "Vrancea"), (45.45, "Galați"), (45.42, "Brăila")]:
    f, pt = frac_at_lat(lat)
    w = winner(f)
    mark = "OK" if (w == expect or (expect == "Botoșani" and w == "Suceava")) else "!!"
    print(f"  lat {lat:.2f} -> frac {f:.4f} -> {w:10s} {ASSOC.get(w,'?')}  (expect {expect}) {mark}")
