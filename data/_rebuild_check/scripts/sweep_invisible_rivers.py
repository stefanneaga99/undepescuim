#!/usr/bin/env python3
"""Second-pass sweep: attach OSM geometry to remaining invisible rivers.

The conservative matcher (audit_missing_rivers.best_osm_match) requires
token/prefix/char agreement on the CORE name. Rivers that remain invisible
after it (no geometry, no bbox, no group render) often fail because:

  - ANPA/Romsilva names carry qualifiers the OSM course lacks
    ('Valea Drăganului' vs OSM 'Drăgan', 'Râul Canciu- Bosorogu' vs 'Canciu')
  - the water is a genitive/compound the index stores differently
    ('Valea Gâlzii' vs 'Pârâul Gâlzii', 'Izvoarele Ampoiului' vs 'Ampoi')
  - suffix sectors ('Moneasa Superioară' vs OSM 'Moneasa')

This pass is deliberately AGGRESSIVE but still county-guarded: it tries
substring and first-token matches against every named OSM cluster and only
accepts a geometry whose centroid is within ~0.35 deg of the water's county
centroid (or bbox overlap when the water has coordinates). It reports every
candidate it would map; --write applies them.

Usage: python3 scripts/sweep_invisible_rivers.py [--write] [--json-report PATH]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE_WATERS = ROOT / "public" / "data" / "waters.json"

sys.path.insert(0, str(ROOT / "scripts"))
from audit_missing_rivers import (  # noqa: E402
    build_county_centroids,
    core,
    geom_centroid,
    load_osm_index,
    make_cluster_geoms,
    norm,
)

# words that are NOT part of the river name on the Romsilva/ANPA side
QUALIFIER_WORDS = {
    "izvoare", "izvorul", "izvoarele", "confluenta", "confluența", "confl",
    "superior", "superioara", "superioară", "mijlociu", "mijlocie",
    "inferior", "inferioara", "inferioară", "tronson", "aval", "amonte",
    "baraj", "lac", "lacul", "de", "la", "cu", "raul", "rau", "paraul",
    "parau", "valea", "vl", "pana", "până", "la",
}


def strip_qualifiers(name_core: str) -> list[str]:
    """Candidate reduced forms of a river core name.

    'canciu bosorogu' -> ['canciu bosorogu', 'canciu', 'bosorogu']
    'izvoarele ampoiului' -> ['izvoarele ampoiului', 'ampoiului', 'ampoi']
    'valea galzii' -> ['valea galzii', 'galzii', 'galzi']
    """
    tokens = name_core.split()
    out = {name_core}
    # drop leading qualifiers
    for i in range(len(tokens)):
        if tokens[i] in QUALIFIER_WORDS:
            out.add(" ".join(tokens[i + 1:]))
        else:
            break
    # drop trailing qualifiers
    for i in range(len(tokens) - 1, -1, -1):
        if tokens[i] in QUALIFIER_WORDS:
            out.add(" ".join(tokens[:i]))
        else:
            break
    # all tokens minus qualifiers
    kept = [t for t in tokens if t not in QUALIFIER_WORDS]
    if kept:
        out.add(" ".join(kept))
    # genitive-strip the last token: 'ampoiului' -> 'ampoi', 'galzii' -> 'galzi'
    base = set()
    for form in list(out):
        last = form.split()[-1]
        for suf in ("ului", "ului", "eii", "ii", "ei", "a"):
            if last.endswith(suf) and len(last) - len(suf) >= 4:
                base.add(" ".join(form.split()[:-1] + [last[: -len(suf)]]))
                break
    out |= base
    return sorted(out, key=len, reverse=True)


def water_in_bbox(water: dict, bbox: tuple) -> bool:
    """True when the water's coordinates/bbox overlap the cluster bbox."""
    c = water.get("coordinates")
    if c and len(c) >= 2:
        lon, lat = c[0], c[1]
        return bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]
    wb = water.get("bbox")
    if wb:
        return not (wb[2] < bbox[0] or wb[0] > bbox[2] or wb[3] < bbox[1] or wb[1] > bbox[3])
    return False


def find_aggressive(water: dict, osm_geo_by_norm: dict,
                    county_centroids: dict) -> tuple[str | None, dict | None, str]:
    """Return (osm_name, geometry, how) for an aggressive county-guarded match."""
    from audit_missing_rivers import first_token_ok
    wname = water.get("name", "")
    wc = core(wname)
    if not wc:
        return None, None, "no-core"
    forms = strip_qualifiers(wc)
    judet = water.get("judet") or ""
    ccent = county_centroids.get(judet) if judet else None

    # index candidates: any OSM norm whose tokens intersect ours strongly
    candidates = []
    for idx_name, geoms_list in osm_geo_by_norm.items():
        ic = core(idx_name)
        if not ic:
            continue
        ic_tokens = ic.split()
        if not ic_tokens:
            continue
        # generic OSM cores (single-word 'canal', 'tei', 'vale', ...) are NOT
        # specific enough to claim a long ANPA name
        if len(ic_tokens) == 1 and len(ic_tokens[0]) < 5:
            continue
        for form in forms:
            if not form:
                continue
            ft = form.split()
            if not ft:
                continue
            # substring: 'dragan' in 'draganului' (genitive of the same river).
            # Reject when the OSM name EXTENDS the water name by a suffix that
            # changes the river (chechis vs chechisel): first-token guard.
            if form in ic:
                if first_token_ok(ft[0], ic_tokens[0]) or len(ft) >= 2:
                    candidates.append((idx_name, geoms_list, "substr"))
                    break
            elif ic in form and len(ic_tokens[0]) >= 5:
                if first_token_ok(ft[0], ic_tokens[0]):
                    candidates.append((idx_name, geoms_list, "substr-rev"))
                    break
            else:
                # token-level: >= 1 shared significant token (len>=5)
                it = set(ic_tokens)
                shared = set(ft) & it
                if any(len(t) >= 5 for t in shared):
                    candidates.append((idx_name, geoms_list, "token"))
                    break

    best, best_score, best_how = None, 0.0, None
    for idx_name, geoms_list, how in candidates:
        for geom in geoms_list:
            gcent = geom_centroid(geom)
            if not gcent:
                continue
            # county guard: geometry must be near the water's county (or
            # overlap the water's own coordinates/bbox)
            d = 0.0
            if ccent:
                d = ((gcent[0] - ccent[0]) ** 2 + (gcent[1] - ccent[1]) ** 2) ** 0.5
                if d > 0.45:
                    continue
            base = 1.0 if how == "substr" else (0.9 if how == "substr-rev" else 0.85)
            # tiebreak: closer to the county centroid wins (kills the Prahova
            # 'slanic' when Buzău's own Slănic cluster exists)
            score = base - 0.02 * d
            if water_in_bbox(water, (gcent[0] - 0.1, gcent[1] - 0.1, gcent[0] + 0.1, gcent[1] + 0.1)):
                score += 0.1
            if score > best_score:
                best_score, best, best_how = score, (idx_name, geom), how
    if best and best_score >= 0.9:
        return best[0], best[1], f"aggressive:{best_how}"
    return None, None, "none"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--json-report", type=str)
    args = ap.parse_args()

    waters = json.loads(FE_WATERS.read_text(encoding="utf-8"))
    from collections import defaultdict
    groups = defaultdict(list)
    for x in waters:
        if x.get("riverGroup"):
            groups[x["riverGroup"]].append(x)
    group_has_geom = {g: any(m.get("geometry") for m in members) for g, members in groups.items()}
    todo = [x for x in waters
            if not x.get("geometry") and not x.get("bbox")
            and not (x.get("riverGroup") and group_has_geom.get(x.get("riverGroup")))
            and x.get("subtype") == "rau"]
    print(f"[sweep] {len(todo)} invisible rivers to try")

    print("[osm] loading index...")
    name_index, geoms = load_osm_index()
    osm_geo_by_norm = {}
    for n, ids in name_index.items():
        gs = make_cluster_geoms(ids, geoms)
        if gs:
            osm_geo_by_norm[n] = gs
    county_centroids = build_county_centroids(waters)
    print(f"[osm] {len(osm_geo_by_norm)} named clusters")

    matched, unmatched = [], []
    for w in todo:
        best, geom, how = find_aggressive(w, osm_geo_by_norm, county_centroids)
        if best and geom:
            matched.append((w["slug"], w["name"], w.get("judet", ""), best, how))
            if args.write:
                w["geometry"] = geom
                w["source_detail"] = f"sweep:{how}"
                w["source"] = w.get("source") or "osm_bulk"
        else:
            unmatched.append((w["slug"], w["name"], w.get("judet", "")))

    print(f"[sweep] matched {len(matched)}/{len(todo)}")
    for slug, name, judet, osm, how in matched:
        print(f"   {name} ({judet}) -> {osm} ({how})")
    print(f"[sweep] still unmatched: {len(unmatched)}")

    if args.json_report:
        report = {
            "tried": len(todo),
            "matched": [{"slug": s, "name": n, "judet": j, "osm": o, "how": h} for s, n, j, o, h in matched],
            "unmatched": [{"slug": s, "name": n, "judet": j} for s, n, j in unmatched],
        }
        Path(args.json_report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[report] wrote {args.json_report}")

    if args.write:
        FE_WATERS.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
        with_geom = sum(1 for x in waters if x.get("geometry"))
        print(f"[write] waters.json: {len(waters)} waters, {with_geom} with geometry")


if __name__ == "__main__":
    main()
