#!/usr/bin/env python3
"""Layer 3.1 — source traceability audit (data-correctness test plan §3.1).

For EVERY water in public/data/waters.json, find >= 1 source row in the
canonical source files (S1 anpa_waters.jsonl, S3 anpa_romsilva_waters.jsonl,
S4 arebaltapeste_waters.jsonl). The join is EXACT where the slug encodes the
source key, fuzzy (name_normalized + county + association) elsewhere:

  waters.json slug                        -> source lookup
  -----------------                       -------------------------
  <7-char random>                      -> arebaltapeste_waters.jsonl.slug
  anpa-<id> (anpa-anpa-0008)           -> anpa_waters.jsonl.id == <id>
  romsilva-<judet>-<norm-name> / basca -> anpa_romsilva_waters.jsonl by
                                          (name_normalized, county)
  anything else                        -> fuzzy re-join on
                                          (name_normalized, county,
                                           association) across all 3 sources

Classification:
  traced    -> {source, file, source_row, contract_number, contract_date}
  untraced  -> water has NO source row (FABRICATION / merge artifact)
  ambiguous -> >1 source rows with DIFFERENT contracts for the same key
               (merge conflict — human review item, not a hard fail)

Exit code 1 iff untraced > 0 (CI gate). ambiguous counts as a finding.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE_WATERS = ROOT / "public" / "data" / "waters.json"
SOURCES = {
    "anpa": ROOT / "data" / "processed" / "anpa_waters.jsonl",
    "romsilva": ROOT / "data" / "processed" / "anpa_romsilva_waters.jsonl",
    "arebaltapeste": ROOT / "data" / "processed" / "arebaltapeste_waters.jsonl",
}

COUNTY_ALIASES = {
    "arges": "arges", "argeș": "arges", "bistrita": "bistrita-nasaud",
    "bistrita-nasaud": "bistrita-nasaud", "bistrița-năsăud": "bistrita-nasaud",
    "brasov": "brasov", "brașov": "brasov", "calarasi": "calarasi",
    "călărași": "calarasi", "caras-severin": "caras-severin",
    "caraș-severin": "caras-severin", "constanta": "constanta",
    "constanța": "constanta", "dambovita": "dambovita", "dâmbovița": "dambovita",
    "galati": "galati", "galați": "galati", "ialomita": "ialomita",
    "ialomița": "ialomita", "iasi": "iasi", "iași": "iasi", "ilfov": "ilfov",
    "maramures": "maramures", "maramureș": "maramures", "mehedinti": "mehedinti",
    "mehedinți": "mehedinti", "mures": "mures", "mureș": "mures",
    "neamt": "neamt", "neamț": "neamt", "salaj": "salaj", "sălaj": "salaj",
    "satu mare": "satu-mare", "sibiu": "sibiu", "suceava": "suceava",
    "teleorman": "teleorman", "timis": "timis", "timiș": "timis",
    "tulcea": "tulcea", "valcea": "valcea", "vâlcea": "valcea",
    "vrancea": "vrancea", "bucuresti": "bucuresti", "bucurești": "bucuresti",
    "covasna": "covasna", "harghita": "harghita", "hunedoara": "hunedoara",
    "gorj": "gorj", "dolj": "dolj", "ol gi": "olgi",
}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().split())


def county_key(s: str) -> str:
    n = norm(s).replace("_", "-")
    if n.endswith("-nasaud"):
        return "bistrita-nasaud"
    return COUNTY_ALIASES.get(n, n)


def load_rows(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def contract_of(row: dict) -> tuple:
    for k in ("contract_number", "contract_no", "contract"):
        if row.get(k):
            return (str(row[k]), str(row.get("contract_date") or ""))
    return ("", "")


def main() -> None:
    waters = json.loads(FE_WATERS.read_text(encoding="utf-8"))
    anpa = load_rows(SOURCES["anpa"])
    romsilva = load_rows(SOURCES["romsilva"])
    abp = load_rows(SOURCES["arebaltapeste"])
    print(f"[trace] waters {len(waters)}; sources: anpa {len(anpa)}, "
          f"romsilva {len(romsilva)}, arebaltapeste {len(abp)}")

    # ---- exact indexes ----
    abp_by_slug: dict[str, dict] = {r["slug"]: r for r in abp if r.get("slug")}
    anpa_by_id: dict[str, dict] = {r["id"]: r for r in anpa}
    # romsilva: (norm name, county key) -> rows (a name can repeat across counties)
    rom_by_key: dict[tuple, list[dict]] = defaultdict(list)
    for r in romsilva:
        rom_by_key[(r.get("name_normalized") or "", county_key(r.get("county") or ""))].append(r)
    # arebaltapeste fuzzy: (norm name, county) -> rows (name-based fallback
    # for waters whose slug was rewritten by a fix script)
    abp_by_key: dict[tuple, list[dict]] = defaultdict(list)
    for r in abp:
        abp_by_key[(r.get("name_normalized") or "", county_key(r.get("county") or ""))].append(r)

    # ---- prefix-stripped core name (Romsilva source rows drop the
    # 'Râul'/'Valea' prefix; compare on the core like the rest of the repo)
    RIVER_PREFIXES = ("raul", "rau", "paraul", "parau", "paraul", "pârâul",
                      "valea", "val", "lacul", "lac", "acumulare", "acumularea",
                      "balta", "balta ", "iazul", "iaz", "garla")

    def core_name(s: str) -> str:
        n = norm(s)
        for p in RIVER_PREFIXES:
            if n.startswith(p + " ") or n == p:
                n = n[len(p):].strip()
                break
        return n

    # county name like 'Bistrița-Năsăud' -> the slug segment used in the
    # romsilva-* water slugs
    def county_slug(s: str) -> str:
        c = county_key(s)
        # romsilva slugs are built from the county name slugified; keep only
        # the leading county segment for reconstruction (bistrita-nasaud
        # stays intact)
        return c

    # 'ROMSILVA – ALBA', 'ROMSILVA – BUZĂU' and 'Direcția Silvică Alba' are
    # the SAME org family (RNP-Romsilva county directorate). Reduce both
    # sides to the distinguishing remainder before comparing.
    def org_key(s: str) -> str:
        n = norm(str(s or ""))
        for tok in ("romsilva", "rnp", "directia", "silvica", "d.s", "ds",
                    "administrata", "administrat", "de", "o.s", "ocol"):
            n = n.replace(tok, " ")
        return " ".join(n.split())

    traced: list[dict] = []
    untraced: list[dict] = []
    ambiguous: list[dict] = []
    suspect: list[dict] = []

    for w in waters:
        slug = w["slug"]
        rec = {"slug": slug, "name": w["name"], "judet": w.get("judet"),
               "asociatie": (w.get("asociatie") or {}).get("name")}
        hits: list[dict] = []
        seen_ids: set[tuple] = set()

        def add(source: str, row: dict) -> None:
            key = (source, row.get("id"))
            if key not in seen_ids:
                seen_ids.add(key)
                hits.append({"source": source, "row": row})

        # 1. exact slug -> arebaltapeste (the 7-char random slugs)
        if slug in abp_by_slug:
            add("arebaltapeste", abp_by_slug[slug])
        # 2. anpa-<id> — only when the id resolves; sector slugs created by
        #    later mapping scripts (anpa-neamt-bistrita-32 …) fall through to
        #    the fuzzy join instead of being dropped
        if slug.startswith("anpa-"):
            row = anpa_by_id.get(slug[len("anpa-"):])
            if row:
                add("anpa", row)
        # 3. romsilva / basca slugs — the romsilva slug encodes the source
        #    row's name_normalized directly (romsilva-<county>-<name>);
        #    basca slugs are custom contract names
        if slug.startswith("romsilva-"):
            county_s = county_slug(w.get("judet") or "")
            if slug.startswith(f"romsilva-{county_s}-"):
                expected = slug[len(f"romsilva-{county_s}-"):].replace("-", " ")
                for r in rom_by_key.get((expected, county_key(w.get("judet") or "")), []):
                    add("anpa_romsilva", r)
        elif slug.startswith("basca-"):
            for r in rom_by_key.get((core_name(w["name"]), county_key(w.get("judet") or "")), []):
                add("anpa_romsilva", r)
        # 4. fuzzy: core name + county across all three sources (catches
        #    sector waters whose slug encodes a different id scheme)
        nk = (core_name(w["name"]), county_key(w.get("judet") or ""))
        if nk[0]:
            for r in anpa:
                if core_name(r.get("water_name") or r.get("name_normalized") or "") == nk[0] \
                        and county_key(r.get("county") or "") == nk[1]:
                    add("anpa", r)
            for r in rom_by_key.get(nk, []):
                add("anpa_romsilva", r)
            for r in abp_by_key.get(nk, []):
                add("arebaltapeste", r)

        if not hits:
            untraced.append(rec)
            continue

        # associations that the hits actually carry
        def row_assoc(row: dict) -> str:
            return row.get("association") or row.get("gestionar_assoc") or row.get("admin") or ""

        assoc_name = norm(rec["asociatie"])
        matching = [h for h in hits if assoc_name and (
            assoc_name in norm(row_assoc(h["row"]))
            or org_key(assoc_name) in org_key(row_assoc(h["row"]))
            or org_key(row_assoc(h["row"])) in org_key(assoc_name)
        )]
        if not matching and assoc_name:
            # hit exists but EVERY source row carries a different association
            # (e.g. Râul Jiu is listed under A.Cerbul Carpatin by
            # arebaltapeste while ANPA attributes it to AJVPS GORJ) — keep
            # traced, surface as a suspect finding for human review.
            suspect.append({**rec, "source_associations": sorted({norm(row_assoc(h["row"])) for h in hits})})
        choose_from = matching if matching else hits

        # exact contract disambiguation: multiple rows with the SAME contract
        # are fine (same water in two source editions); DIFFERENT contracts
        # for the same water = merge conflict
        contracts = {(str(contract_of(h["row"])[0]), str(contract_of(h["row"])[1])) for h in choose_from}
        if len({c[0] for c in contracts if c[0]}) > 1:
            ambiguous.append({
                **rec,
                "contracts": sorted({c[0] for c in contracts if c[0]}),
                "sources": sorted({h["source"] for h in choose_from}),
            })
        best = choose_from[0]
        row = best["row"]
        traced.append({
            **rec,
            "source": best["source"],
            "file": row.get("file"),
            "source_row": row.get("source_row"),
            "source_id": row.get("id"),
            "contract_number": row.get("contract_number"),
            "contract_date": row.get("contract_date"),
            "contracts_seen": len({h["row"].get("contract_number") for h in choose_from}),
        })

    print(f"[trace] traced {len(traced)}, untraced {len(untraced)}, "
          f"ambiguous {len(ambiguous)}, suspect {len(suspect)}")
    for u in untraced:
        print(f"  UNTRACED {u['slug']} | {u['name'][:45]} | {u['judet']} | {u['asociatie']}")
    for s in suspect[:20]:
        print(f"  SUSPECT {s['slug']} | {s['name'][:40]} | water assoc={s['asociatie']} | "
              f"source assocs={s['source_associations']}")
    for a in ambiguous[:20]:
        print(f"  AMBIGUOUS {a['slug']} | {a['name'][:40]} | contracts {a['contracts'][:4]}")

    out = ROOT / "data" / "processed" / "traceability_report.json"
    out.write_text(json.dumps({
        "checked": len(waters), "traced": len(traced),
        "untraced": untraced, "ambiguous": ambiguous, "suspect": suspect,
        "traced_rows": traced,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[trace] report -> {out}")

    if untraced:
        print("[trace] FAIL: untraced waters must be 0 (fabrications / merge artifacts)")
        sys.exit(1)
    print("[trace] PASS: every water traces to a source row")


if __name__ == "__main__":
    main()