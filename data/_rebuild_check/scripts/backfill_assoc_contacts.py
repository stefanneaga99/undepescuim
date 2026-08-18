#!/usr/bin/env python3
"""t_45a0beae / A4 — best-effort association contact backfill.

Baseline contact coverage: telefon 66/94, siteUrl 69/94, permitUrl 7/94.
Sources used (in order of reliability):
  1. locuri_associations.jsonl   — scraped from locuridepescuit.ro pages
     (phone/email/address where the earlier merge missed them)
  2. Public association listings — MMEDIU 2011-2017 list of fishing
     associations (authorized orgs: official tel/fax), forum threads with
     official contact persons, association Facebook pages.

Every number here is a REAL phone found in a public source for the exact
association (matched by name), never a placeholder. Associations where no
public number/site could be found keep NO contact fields (the plan §4.1
allows a "no public contact" note rather than a fake value).
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE_ASSOC = ROOT / "public" / "data" / "associations.json"

# slug -> {field: value} verified backfills
BACKFILL = {
    # locuridepescuit.ro scrape (data/processed/locuri_associations.jsonl)
    "ajvps-giurgiu": {
        "telefon": "0722545527",
        "email": "ajvpsgiurgiu@yahoo.com",
    },
    "aps-cheile-lapusului": {
        "telefon": "0747872721",
    },
    # APS Deva — official phone published on the association's public
    # Facebook group (facebook.com/groups/3888070591293700, post "APS DEVA
    # 0734207460 … Susții pescuitul sportiv").
    "aps-deva": {
        "telefon": "0734207460",
    },
    # A.Lucioperca Club Pescar Modern — contact person published in the
    # association's membership threads (rapitori.ro t14118, pescuitul.ro
    # 99160): dl. Vasile Stiopei, Bistrița, str. Vasile Lucaciu nr. 5 —
    # matches the registry address.
    "a-lucioperca-club-pescar-modern": {
        "telefon": "0744 699 088",
    },
    # AVPS Diana Turnu Arad — MMEDIU "Lista asociațiilor de pescari
    # sportivi 2011-2017" (mmediu.ro upload): tel/fax 0257 28 93 08.
    "avps-diana-turnu-arad": {
        "telefon": "0257 28 93 08",
    },
    # Asociația Cerbul Carpatin Târgu Jiu — same MMEDIU list:
    # tel/fax 0253/215935.
    "a-cerbul-carpatin": {
        "telefon": "0253 215 935",
    },
    # locuridepescuit.ro scrape (data/processed/locuri_associations.jsonl) —
    # second pass: associations whose phone/website the first merge missed.
    "ajvps-bacau": {
        "telefon": "0234543800",
    },
    "ajvps-satu-mare": {
        "telefon": "0261717620",
    },
    "avps-campina": {
        "telefon": "0244336931",
    },
    "ajvps-covasna": {
        "siteUrl": "http://www.ajvpscovasna.ro/",
    },
    "ajvps-hunedoara": {
        "siteUrl": "https://ajvpshunedoara.wgz.ro/",
    },
    "ajvps-valcea": {
        "siteUrl": "https://ajvpsrmvl.wixsite.com/asociatia",
    },
    # Asociația Fly Fishing Rarău — official site (flyfishingrarau.ro, verified
    # HTTP 200 on 2026-08-17; referenced by flyfishingoutlet.ro's partner page).
    "asociatia-fly-fishing-rarau": {
        "siteUrl": "https://flyfishingrarau.ro/",
    },
}


def main() -> None:
    assocs = json.loads(FE_ASSOC.read_text(encoding="utf-8"))
    by_slug = {a["slug"]: a for a in assocs}
    filled = 0
    for slug, fields in BACKFILL.items():
        a = by_slug.get(slug)
        if not a:
            print(f"[a4] WARN {slug} not in directory — skipping")
            continue
        for k, v in fields.items():
            if not a.get(k):
                a[k] = v
                filled += 1

    FE_ASSOC.write_text(json.dumps(assocs, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    n = len(assocs)
    n_tel = sum(1 for a in assocs if (a.get("telefon") or "").strip())
    n_site = sum(1 for a in assocs if (a.get("siteUrl") or "").strip())
    n_permit = sum(1 for a in assocs if (a.get("permitUrl") or "").strip())
    n_any = sum(1 for a in assocs if (a.get("telefon") or "").strip() or (a.get("siteUrl") or "").strip())
    print(f"[a4] filled {filled} fields; coverage: telefon {n_tel}/{n}, "
          f"siteUrl {n_site}/{n}, permitUrl {n_permit}/{n}, either {n_any}/{n}")
    print("[a4] no-contact (documented, no fake value):")
    for a in assocs:
        if not (a.get("telefon") or "").strip() and not (a.get("siteUrl") or "").strip():
            print(f"     {a['slug']} | {a.get('name')} | adresa: {a.get('adresa') or '—'}")


if __name__ == "__main__":
    main()