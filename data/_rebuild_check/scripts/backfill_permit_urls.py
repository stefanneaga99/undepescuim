#!/usr/bin/env python3
"""F1a — backfill/merge permit info into the frontend dataset.

Reads the authoritative pipeline records, emits the enrichment manifest that
documents what is KNOWN vs a manual-curation queue, and applies the result to
the CURRENT public/data files in place (preserving all geometry/grouping work
that a full re-extraction chain would clobber).

Inputs:
  data/processed/arebaltapeste_associations.jsonl  (94 records; `type` + `permit_url`)
  data/processed/locuri_associations.jsonl          (64 records; website candidates)
  public/data/associations.json                     (FE directory, 94)
  public/data/waters.json                           (FE waters, ~1013)

Outputs:
  data/processed/permit_enrichment.json:
      known            — [{slug, permit_url, permit_issuer}] (7 today)
      website_no_permit— [{slug, website}] associations with a site but no
                          permit store (manual-curation queue, human confirms
                          each is actually a permit page before promoting)
      no_website       — [slug] dead-ends (nothing to link)
  data/processed/permit_overrides.json  — empty {slug, permit_url, permit_issuer}
                          template; entries here WIN over `known` at apply time.
  public/data/associations.json         — permitIssuer on every record (derived
                          from pipeline `type`: anpa→anadspa, ds→romsilva,
                          else asociatie), permitUrl on the known/override ones.
  public/data/waters.json               — water.asociatie gains permitUrl +
                          permitIssuer for every water whose association has one.

Usage: python3 scripts/backfill_permit_urls.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROC_DIR = ROOT / "data" / "processed"
FE_ASSOC = ROOT / "public" / "data" / "associations.json"
FE_WATERS = ROOT / "public" / "data" / "waters.json"
ENRICH = PROC_DIR / "permit_enrichment.json"
OVERRIDES = PROC_DIR / "permit_overrides.json"

ISSUER_FROM_TYPE = {"anpa": "anadspa", "ds": "romsilva"}


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def issuer_for(assoc_type: str) -> str:
    return ISSUER_FROM_TYPE.get(assoc_type, "asociatie")


def main() -> None:
    abp = load_jsonl(PROC_DIR / "arebaltapeste_associations.jsonl")
    locuri = load_jsonl(PROC_DIR / "locuri_associations.jsonl")

    fe = json.loads(FE_ASSOC.read_text(encoding="utf-8"))
    waters = json.loads(FE_WATERS.read_text(encoding="utf-8"))

    # ---- type map: pipeline slug -> pipeline type ---------------------------
    # The FE is the apply target, so also keep an alias map for slugs that the
    # FE normalization strips (avps-tarnava-mare- -> avps-tarnava-mare).
    type_map: dict[str, str] = {}
    fe_by_slug = {a["slug"]: a for a in fe}
    fe_by_name: dict[str, str] = {}
    for a in fe:
        fe_by_name.setdefault((a.get("name") or "").strip().lower(), a["slug"])
        fe_by_name.setdefault((a.get("name_long") or a.get("name") or "").strip().lower(), a["slug"])
    for r in [*abp, *locuri]:
        if not (r.get("slug") and r.get("type")):
            continue
        type_map.setdefault(r["slug"], r["type"])
        # alias: trailing-dash pipeline slug -> FE slug
        stripped = r["slug"].rstrip("-")
        if stripped in fe_by_slug:
            type_map.setdefault(stripped, r["type"])
        else:
            name_key = (r.get("name") or "").strip().lower()
            if name_key in fe_by_name:
                type_map.setdefault(fe_by_name[name_key], r["type"])

    def fe_slug_for(rec: dict) -> str | None:
        """Map a pipeline record to its FE slug (exact, name, or dash-strip)."""
        if rec["slug"] in fe_by_slug:
            return rec["slug"]
        name_key = (rec.get("name") or "").strip().lower()
        if name_key in fe_by_name:
            return fe_by_name[name_key]
        stripped = rec["slug"].rstrip("-")
        if stripped in fe_by_slug:
            return stripped
        return None

    # ---- known permit URLs (authoritative, from the pipeline) ---------------
    known: list[dict] = []
    seen: set[str] = set()
    for r in abp:
        if not (r.get("permit_url") and r.get("slug") and r["slug"] not in seen):
            continue
        seen.add(r["slug"])
        fe_slug = fe_slug_for(r)
        if fe_slug is None:
            print(f"[enrich] WARN: known permit slug {r['slug']} not found in FE directory — skipping")
            continue
        known.append(
            {
                "slug": fe_slug,
                "permit_url": r["permit_url"],
                "permit_issuer": issuer_for(r.get("type", "other")),
            }
        )

    # ---- emit enrichment manifest ------------------------------------------
    known_by_slug = {k["slug"]: k for k in known}
    website_no_permit = []
    no_website = []
    for a in sorted(fe, key=lambda x: x["slug"]):
        if a["slug"] in known_by_slug:
            continue
        if a.get("siteUrl"):
            website_no_permit.append({"slug": a["slug"], "website": a["siteUrl"]})
        else:
            no_website.append(a["slug"])

    overrides: list[dict] = []
    if OVERRIDES.exists():
        overrides = json.loads(OVERRIDES.read_text(encoding="utf-8"))

    ENRICH.write_text(
        json.dumps(
            {"known": known, "website_no_permit": website_no_permit, "no_website": no_website},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    # Empty template on first run (never overwrite curated overrides).
    if not overrides:
        overrides = [{"slug": "", "permit_url": "", "permit_issuer": ""}]
        OVERRIDES.write_text(json.dumps(overrides, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[enrich] known={len(known)} website_no_permit={len(website_no_permit)} no_website={len(no_website)}")
    print(f"[enrich] wrote {ENRICH.name} + {OVERRIDES.name}")

    # ---- apply to FE associations -------------------------------------------
    over_by_slug = {o["slug"]: o for o in overrides if o.get("slug")}
    applied_assoc = 0
    for a in fe:
        a_type = type_map.get(a["slug"], "other")
        a["permitIssuer"] = issuer_for(a_type)
        rec = over_by_slug.get(a["slug"]) or known_by_slug.get(a["slug"])
        if rec and rec.get("permit_url"):
            a["permitUrl"] = rec["permit_url"]
            applied_assoc += 1
    FE_ASSOC.write_text(json.dumps(fe, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[apply] associations.json: {len(fe)} records, {applied_assoc} with permitUrl")

    # ---- apply to waters (asociatie block) -----------------------------------
    applied_water = 0
    issuer_fix = 0
    for w in waters:
        asoc = w.get("asociatie")
        if not asoc:
            continue
        slug = asoc.get("slug")
        if not slug:
            continue
        a_type = type_map.get(slug)
        if a_type:
            asoc["permitIssuer"] = issuer_for(a_type)
            issuer_fix += 1
        rec = over_by_slug.get(slug) or known_by_slug.get(slug)
        if rec and rec.get("permit_url"):
            asoc["permitUrl"] = rec["permit_url"]
            applied_water += 1
    FE_WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[apply] waters.json: {len(waters)} waters, {applied_water} with permitUrl, {issuer_fix} with permitIssuer")


if __name__ == "__main__":
    main()
