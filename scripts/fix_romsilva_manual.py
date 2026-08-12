#!/usr/bin/env python3
"""Final manual corrections for Romsilva groupings (t_1f8b1b06).

Runs AFTER fix_romsilva_groups.py and fixes the cases that generic
base-name grouping gets wrong — different rivers that share a base name
across counties, and sector owners that must not double-draw:

  * casin:  Harghita Râul Cașin (Olt basin) != Bacău Cașinul (Trotuș basin)
  * bistra: Mureș Bistra (ANPA) != Sibiu Bistra (Romsilva)
  * cerna:  Vâlcea Cerna (Lotru trib) != Caraș-Severin/Mehedinți Cerna
            (Danube basin, Băile Herculane)
  * putna:  Suceava Putna (Moldova trib) != Vrancea Putna (Siret basin)
  * bistricioara: Vâlcea (Lotru trib) != Gorj (Jiu trib) != Harghita (Bistrița)
  * basca-mica: Covasna headwater sector must not draw its own line
  * oltet: Gorj Romsilva is a headwater sector of the same Olteț — one owner
  * barzauta: Covasna upstream sector [0, 15/33), Bacău downstream [15/33, 1]

Usage: python3 scripts/fix_romsilva_manual.py [--write]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE_WATERS = ROOT / "public" / "data" / "waters.json"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    w = json.loads(FE_WATERS.read_text(encoding="utf-8"))

    def by_slug(slug):
        return next(x for x in w if x["slug"] == slug)

    # ---- casin: two DIFFERENT rivers ----
    by_slug("anpa-anpa-0342").update({"riverGroup": "casin",
                                      "sectorStart": None, "sectorEnd": None,
                                      "course_frac": 0.2545})
    by_slug("phmbrdj5").update({"riverGroup": "casinul",
                                "sectorStart": 0.73, "sectorEnd": 1.0,
                                "course_frac": 0.865})
    by_slug("romsilva-bacau-casinul-superior").update({
        "riverGroup": "casinul", "geometry": None,
        "source_detail": "romsilva_map:group-shares-course",
        "sectorStart": 0.0, "sectorEnd": 0.73, "course_frac": 0.365})

    # ---- bistra: two DIFFERENT rivers (Mureș vs Sibiu) ----
    by_slug("anpa-anpa-0446").update({"riverGroup": "bistra-mures",
                                      "course_frac": 0.5})
    by_slug("romsilva-sibiu-bistra").update({"riverGroup": "bistra-sibiu",
                                             "course_frac": 0.5})

    # ---- cerna: Vâlcea (Lotru trib) separate from Herculane Cerna ----
    by_slug("5bbhtdfc").update({"riverGroup": "cerna-valcea"})
    cerna_rs = [x for x in w if x.get("slug", "").startswith("romsilva-")
                and x.get("riverGroup") == "cerna"]
    # keep only Cerna mijlocie as the Herculane-group geometry owner
    for x in cerna_rs:
        x["riverGroup"] = "cerna-herculane"
        if x["slug"] != "romsilva-caras-severin-cerna-mijlocie":
            x["geometry"] = None
            x["source_detail"] = "romsilva_map:group-shares-course"
    ranks = {"romsilva-mehedinti-cerna-superioara": 0,
             "romsilva-caras-severin-cerna-mijlocie": 1,
             "romsilva-caras-severin-cerna-inferioara": 2,
             "romsilva-mehedinti-cerna": 3}
    cerna_rs.sort(key=lambda x: ranks.get(x["slug"], 9))
    n = len(cerna_rs)
    for i, x in enumerate(cerna_rs):
        x["course_frac"] = round((i + 1) / (n + 1), 4)

    # ---- putna: Suceava (Moldova trib) != Vrancea (Siret basin) ----
    by_slug("romsilva-suceava-putna").update({"riverGroup": "putna-suceava",
                                              "course_frac": 0.5})
    anpa_putna = by_slug("anpa-anpa-0681")
    anpa_putna["riverGroup"] = "putna"
    anpa_putna["course_frac"] = 0.7412
    by_slug("romsilva-vrancea-putna-superioara").update({
        "riverGroup": "putna", "geometry": None,
        "source_detail": "romsilva_map:group-shares-course", "course_frac": 0.25})
    by_slug("romsilva-vrancea-putna-mijlocie").update({
        "riverGroup": "putna", "geometry": None,
        "source_detail": "romsilva_map:group-shares-course", "course_frac": 0.5})

    # ---- bistricioara: three DIFFERENT rivers ----
    by_slug("6ofvb2jf").update({"riverGroup": "bistricioara-valcea"})
    by_slug("romsilva-gorj-bistricioara").update({"riverGroup": "bistricioara-gorj",
                                                  "course_frac": 0.5})
    by_slug("romsilva-harghita-bistricioara-tronson-i").update({
        "riverGroup": "bistricioara-harghita", "course_frac": 0.3333})
    by_slug("romsilva-harghita-bistricioara-tronson-ii").update({
        "riverGroup": "bistricioara-harghita", "course_frac": 0.6667})

    # ---- basca-mica: Covasna headwater sector resolves by click only ----
    BORDER = round(15 / 83, 4)  # 0.1807
    by_slug("romsilva-covasna-basca-mica").update({
        "geometry": None, "source_detail": "romsilva_map:group-shares-course",
        "sectorStart": 0.0, "sectorEnd": BORDER, "course_frac": round(BORDER / 2, 4)})
    by_slug("basca-mica").update({"sectorStart": BORDER, "sectorEnd": 1.0,
                                  "course_frac": round((BORDER + 1) / 2, 4)})

    # ---- oltet: Gorj Romsilva is a headwater sector of the same river ----
    by_slug("romsilva-gorj-oltet").update({
        "geometry": None, "source_detail": "romsilva_map:group-shares-course",
        "course_frac": 0.1667})
    by_slug("dvhkx2a2").update({"course_frac": 0.5})
    by_slug("e8r6r01g").update({"course_frac": 0.8333})

    # ---- barzauta: Covasna upstream [0, 15/33), Bacău downstream ----
    BARZ = round(15 / 33, 4)  # 0.4545
    by_slug("romsilva-covasna-barzauta").update({
        "geometry": None, "source_detail": "romsilva_map:group-shares-course",
        "sectorStart": 0.0, "sectorEnd": BARZ, "course_frac": round(BARZ / 2, 4)})
    by_slug("romsilva-bacau-barzauta").update({
        "sectorStart": BARZ, "sectorEnd": 1.0,
        "course_frac": round((BARZ + 1) / 2, 4)})

    if args.write:
        FE_WATERS.write_text(json.dumps(w, ensure_ascii=False, indent=1), encoding="utf-8")
        with_geom = sum(1 for x in w if x.get("geometry"))
        print(f"[write] waters.json: {len(w)} waters, {with_geom} with geometry")


if __name__ == "__main__":
    main()
