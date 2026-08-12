#!/usr/bin/env python3
"""Fix Buzău contract positions (task t_84b29064).

Assigns each Buzău contract its REAL position along the Râul Buzău course
(0=source near Întorsura Buzăului, 1=mouth into the Siret), anchored on
geocoded limit places (Nominatim, cached in data/cache/geocode.db):

  place           frac   contract anchor
  ---------------- ------ ---------------------------------------------
  Întorsura Buzăului 0.093 (Covasna sector town)
  Crasna (Siriu)     0.154  'Valea Buzăului superior' start (vărsare Crasna)
  (Grămăticu est.)   0.176  'Râul Buzăul superior' start (vărsare Grămăticu)
  Barajul Siriu      0.2004 'Valea Buzăului inferior' start (barajul Siriu)
  Sibiciu de Sus     0.277  'Râul Buzăul inferior' start (conf. Sibiciu)
  (county exit)     ~0.61   'Râul Buzău' (Brăila) start — contract kept at 1.0

Resulting Voronoi intervals (click resolution):
  Pârâu Buzăul Mijlociu (Covasna) [0, 0.124)
  Valea Buzăului superior  [0.124, 0.165)
  Râul Buzăul superior     [0.165, 0.188)
  Valea Buzăului inferior  [0.188, 0.239)   ← Siriu dam (0.2004) + user click (0.2155)
  Râul Buzăul inferior     [0.239, 0.639)
  Râul Buzău (Brăila)      [0.639, 1]

The three prefix-named sectors ('Pârâu Buzăul Mijlociu', 'Valea Buzăului
superior', 'Valea Buzăului inferior') are flagged mainCourse=true so the
click-resolution filter includes them (their names start with Pârâu/Valea,
which the generic filter treats as tributaries).
"""
import json

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WATERS = ROOT / "public" / "data" / "waters.json"


def main() -> None:
    waters = json.loads(WATERS.read_text(encoding="utf-8"))
    by_slug = {w["slug"]: w for w in waters}

    updates = {
        # slug                          course_frac mainCourse
        "anpa-anpa-0261": (0.094, True),    # Pârâu Buzăul Mijlociu (Covasna)
        "anpa-anpa-0210": (0.154, True),    # Valea Buzăului superior
        "anpa-anpa-0207": (0.176, False),   # Râul Buzăul superior cu afluenții săi
        "anpa-anpa-0211": (0.2004, True),   # Valea Buzăului inferior (barajul Siriu)
        "anpa-anpa-0214": (0.277, False),   # Râul Buzăul inferior
        "ufdigh4c":       (1.0, False),     # Râul Buzău (Brăila) — mouth sector
    }
    for slug, (frac, flag) in updates.items():
        w = by_slug.get(slug)
        if w is None:
            raise SystemExit(f"missing water {slug}")
        w["course_frac"] = frac
        if flag:
            w["mainCourse"] = True
        else:
            w.pop("mainCourse", None)
        print(f"  {w['name'][:44]:46} frac={frac} mainCourse={flag}")

    WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n[done] updated {len(updates)} Buzău contracts")


if __name__ == "__main__":
    main()
