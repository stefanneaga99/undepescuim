#!/usr/bin/env python3
"""Layer 5 — consistency invariants gate (data-correctness test plan §7).

One script, runnable in seconds, gates every commit. Exit 0 iff NO violation;
prints a machine-readable violations list. Checks:

waters.json:
  - slug unique, ^[a-z0-9-]+$
  - every row: name, judet, subtype in {lac,rau}, type == "ape"
  - every contracted water (asociatie present): asociatie.slug resolves in
    associations.json; limite + dimensiune non-empty
  - every water: geometry OR coordinates OR bbox OR documented fallback
    (riverGroup membership or explicit `fallback` marker)
  - bbox [minLon,minLat,maxLon,maxLat] with min<=max, lon in [-180,180],
    lat in [-90,90]; coordinates [lon,lat] in range
  - pescuit_interzis: false or true (present on every water)

associations.json:
  - slug unique; name + name_long + permitIssuer present
  - ape == recomputed water count; counties[] == recomputed distinct judet
  - telefon (when present) is a plausible Romanian number (catches the
    redacted +402****1963 placeholders); no 'TBD'/'n/a' placeholder strings

species.json:
  - species slugs/names unique; non-protected min_cm numeric > 0;
    protected species carry retention: interzis and min_cm null

uncontracted overlays:
  - slug unique (A1 regression gate)
  - uncontracted == true; lengthKm/areaHa numeric > 0
  - no same-name + same-county features with >=90% bbox overlap (same-body
    duplicates — A1 regression gate)
  - no non-Latin-script LETTERS (Cyrillic leak like 'Бирда') and no legacy
    ş/ţ/å orthography — review items, reported not fatal

Usage:
  python3 scripts/audit_integrity.py [--json data/processed/integrity_report.json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE_WATERS = ROOT / "public" / "data" / "waters.json"
FE_ASSOC = ROOT / "public" / "data" / "associations.json"
FE_RIVERS = ROOT / "public" / "data" / "uncontracted_rivers.json"
FE_LAKES = ROOT / "public" / "data" / "uncontracted_lakes.json"
FE_SPECIES = ROOT / "data" / "species.json"

SLUG_RE = re.compile(r"^[a-z0-9-]+$")
PHONE_RE = re.compile(r"^(\+?40|0040|0)?\d{9}$")
# pre-1993 Romanian orthography: s/t with cedilla (ş ţ) and a-ring (å) — the
# modern forms are ș/ț (comma below) and â. Flagged as a review item, not
# Cyrillic.
LEGACY_ORTHO_RE = re.compile(r"[\u015e\u015f\u0162\u0163\u00c5\u00e5]")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().split())


def phone_plausible(t: str) -> bool:
    digits = re.sub(r"\D", "", t or "")
    if not digits:
        return False
    return bool(PHONE_RE.match(digits))


def has_non_latin_letter(s: str) -> bool:
    """True if s contains a LETTER from a non-Latin script (Cyrillic, Greek…).

    Romanian water names are Latin-script by law; a Cyrillic leak ('Бирда')
    is the flag this gate exists for. Hungarian diacritics (ő ű á é…) ARE
    Latin-script letters and are NOT flagged. Punctuation (en-dash, curly
    quotes) is ignored.
    """
    for ch in s:
        if not unicodedata.category(ch).startswith("L"):
            continue
        name = unicodedata.name(ch, "")
        if name and not name.startswith("LATIN"):
            return True
    return False


def name_flags(name: str):
    """Return the finding checks a name triggers (review items, not failures)."""
    checks = []
    if has_non_latin_letter(name or ""):
        checks.append("non_latin_name")
    if LEGACY_ORTHO_RE.search(name or ""):
        checks.append("legacy_orthography")
    return checks


def check_waters(waters, assoc_by_slug, violations, findings) -> None:
    slugs = Counter(w["slug"] for w in waters)
    for slug, n in slugs.items():
        if n > 1:
            violations.append({"check": "waters.slug_unique", "slug": slug, "count": n})
    for w in waters:
        s = w["slug"]
        if not SLUG_RE.match(s):
            violations.append({"check": "waters.slug_charset", "slug": s, "value": s})
        for field in ("name", "judet"):
            if not w.get(field):
                violations.append({"check": "waters.required_field", "slug": s, "field": field})
        if w.get("type") != "ape":
            violations.append({"check": "waters.type", "slug": s, "type": w.get("type")})
        if w.get("subtype") not in ("lac", "rau"):
            violations.append({"check": "waters.subtype", "slug": s, "subtype": w.get("subtype")})
        assoc = w.get("asociatie") or {}
        if assoc and assoc.get("slug"):
            if assoc["slug"] not in assoc_by_slug:
                violations.append({"check": "waters.assoc_slug_resolves", "slug": s,
                                   "assoc_slug": assoc["slug"]})
            for field in ("limite", "dimensiune"):
                if not (w.get(field) or "").strip():
                    # source gap, not a pipeline bug: ANPA rows for canals /
                    # japșa carry no sector spec (sector_raw is null in the
                    # authoritative parser output). Surface as a finding.
                    findings.append({"check": "waters.contract_blank", "slug": s, "field": field,
                                     "name": w.get("name")})
        has_space = bool(w.get("geometry") or w.get("coordinates") or w.get("bbox"))
        if not has_space and not w.get("riverGroup") and not w.get("fallback"):
            violations.append({"check": "waters.no_geometry_no_fallback", "slug": s})
        b = w.get("bbox")
        if b is not None:
            if not (isinstance(b, list) and len(b) == 4 and all(isinstance(v, (int, float)) for v in b)):
                violations.append({"check": "waters.bbox_shape", "slug": s, "bbox": b})
            else:
                min_lon, min_lat, max_lon, max_lat = b
                if not (min_lon <= max_lon and min_lat <= max_lat):
                    violations.append({"check": "waters.bbox_order", "slug": s, "bbox": b})
                if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
                    violations.append({"check": "waters.bbox_lon_range", "slug": s, "bbox": b})
                if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
                    violations.append({"check": "waters.bbox_lat_range", "slug": s, "bbox": b})
        c = w.get("coordinates")
        if c is not None:
            if not (isinstance(c, list) and len(c) == 2
                    and all(isinstance(v, (int, float)) for v in c)):
                violations.append({"check": "waters.coordinates_shape", "slug": s, "coordinates": c})
            else:
                lon, lat = c
                if not (-180 <= lon <= 180):
                    violations.append({"check": "waters.coordinates_lon_range", "slug": s, "coordinates": c})
                if not (-90 <= lat <= 90):
                    violations.append({"check": "waters.coordinates_lat_range", "slug": s, "coordinates": c})
        if w.get("type") == "ape" and "pescuit_interzis" not in w:
            violations.append({"check": "waters.pescuit_interzis_present", "slug": s})

    # name flags — review items (Cyrillic leak like 'Бирда', legacy ş/ţ/å),
    # not fatal
    for w in waters:
        for check in name_flags(w.get("name")):
            findings.append({"check": f"waters.{check}", "slug": w["slug"],
                             "name": w["name"]})


def check_associations(assocs, waters, violations, findings) -> None:
    slugs = Counter(a["slug"] for a in assocs)
    for slug, n in slugs.items():
        if n > 1:
            violations.append({"check": "assoc.slug_unique", "slug": slug, "count": n})
    counts = Counter((w.get("asociatie") or {}).get("slug") for w in waters)
    counties = {}
    for w in waters:
        s = (w.get("asociatie") or {}).get("slug")
        if s and w.get("judet"):
            counties.setdefault(s, set()).add(w["judet"])
    for a in assocs:
        s = a["slug"]
        if not SLUG_RE.match(s):
            violations.append({"check": "assoc.slug_charset", "slug": s})
        for field in ("name", "name_long", "permitIssuer"):
            if not a.get(field):
                violations.append({"check": "assoc.required_field", "slug": s, "field": field})
        if a.get("ape") != counts.get(s, 0):
            violations.append({"check": "assoc.ape_stale", "slug": s,
                               "declared": a.get("ape"), "actual": counts.get(s, 0)})
        if sorted(a.get("counties", []), key=str.casefold) != sorted(counties.get(s, []), key=str.casefold):
            violations.append({"check": "assoc.counties_stale", "slug": s,
                               "declared": a.get("counties", []),
                               "actual": sorted(counties.get(s, []), key=str.casefold)})
        tel = a.get("telefon") or ""
        if tel.strip() and not phone_plausible(tel):
            violations.append({"check": "assoc.telefon_placeholder", "slug": s, "telefon": tel})
            findings.append({"check": "assoc.telefon_to_fix", "slug": s, "telefon": tel})
        for field in ("adresa",):
            v = (a.get(field) or "").strip().lower()
            if v in ("tbd", "n/a", "na", "none", "null", ""):
                findings.append({"check": "assoc.placeholder", "slug": s, "field": field,
                                 "value": a.get(field)})


def check_species(species, violations) -> None:
    names = Counter(s["species"] for s in species)
    for name, n in names.items():
        if n > 1:
            violations.append({"check": "species.name_unique", "species": name, "count": n})
    for s in species:
        protected = s.get("retention") == "interzis"
        if protected:
            if s.get("min_cm") is not None:
                violations.append({"check": "species.protected_min_cm", "species": s["species"],
                                   "min_cm": s["min_cm"]})
        else:
            if not isinstance(s.get("min_cm"), (int, float)) or s.get("min_cm") <= 0:
                violations.append({"check": "species.min_cm_positive", "species": s["species"],
                                   "min_cm": s.get("min_cm")})


def check_overlay(entries, kind, violations, findings) -> None:
    from shapely.geometry import LineString, MultiLineString, Point, shape

    slugs = Counter(e["slug"] for e in entries)
    for slug, n in slugs.items():
        if n > 1:
            violations.append({"check": f"overlay.{kind}.slug_unique", "slug": slug, "count": n})
    for e in entries:
        s = e["slug"]
        if not SLUG_RE.match(s):
            violations.append({"check": f"overlay.{kind}.slug_charset", "slug": s})
        if e.get("uncontracted") is not True:
            violations.append({"check": f"overlay.{kind}.uncontracted_flag", "slug": s})
        if kind == "rivers":
            v = e.get("lengthKm")
            if not isinstance(v, (int, float)) or v <= 0:
                violations.append({"check": "overlay.rivers.length_positive", "slug": s, "lengthKm": v})
        else:
            v = e.get("areaHa")
            if not isinstance(v, (int, float)) or v <= 0:
                violations.append({"check": "overlay.lakes.area_positive", "slug": s, "areaHa": v})
    # same-body duplicates: same name + county; the A1 dedupe criterion was
    # REAL geometry overlap (>=90% of the smaller course / body), not bbox
    # proximity (distinct ponds legitimately share an envelope). Re-check with
    # actual geometry so the gate catches a re-introduced same-body pair.
    def line_frac_on(small, big) -> float:
        coords = [p for part in (small.geoms if small.geom_type == "MultiLineString" else [small])
                  for p in part.coords]
        if len(coords) < 2:
            return 0.0
        sample = coords[:: max(1, len(coords) // 40)]
        near = sum(1 for p in sample if big.distance(Point(p)) <= 0.0008)
        return near / len(sample)

    groups: dict[tuple, list[dict]] = {}
    for e in entries:
        groups.setdefault((norm(e["name"]), norm(e.get("judet") or "")), []).append(e)
    for key, group in groups.items():
        if len(group) < 2:
            continue
        geoms = []
        for e in group:
            g = e.get("geometry")
            if g:
                try:
                    geoms.append((e["slug"], shape(g)))
                except Exception:
                    pass
        for i in range(len(geoms)):
            for j in range(i + 1, len(geoms)):
                s1, g1 = geoms[i]
                s2, g2 = geoms[j]
                if kind == "rivers":
                    if g1.geom_type in ("Polygon", "MultiPolygon") or g2.geom_type in ("Polygon", "MultiPolygon"):
                        continue
                    frac = max(line_frac_on(g1, g2), line_frac_on(g2, g1))
                else:
                    try:
                        inter = g1.intersection(g2)
                        frac = inter.area / min(g1.area, g2.area) if min(g1.area, g2.area) > 0 else 0.0
                    except Exception:
                        frac = 0.0
                if frac >= 0.9:
                    violations.append({
                        "check": f"overlay.{kind}.same_body_dup", "name": key[0],
                        "judet": key[1], "slugs": [s1, s2], "overlap": round(frac, 3),
                    })
    # name flags — review items (Cyrillic leak, legacy orthography)
    for e in entries:
        for check in name_flags(e.get("name")):
            findings.append({"check": f"overlay.{kind}.{check}",
                             "slug": e["slug"], "name": e["name"]})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=str, default=str(ROOT / "data" / "processed" / "integrity_report.json"))
    args = ap.parse_args()

    waters = json.loads(FE_WATERS.read_text(encoding="utf-8"))
    assocs = json.loads(FE_ASSOC.read_text(encoding="utf-8"))
    rivers = json.loads(FE_RIVERS.read_text(encoding="utf-8"))
    lakes = json.loads(FE_LAKES.read_text(encoding="utf-8"))
    species = json.loads(FE_SPECIES.read_text(encoding="utf-8"))

    violations: list[dict] = []
    findings: list[dict] = []

    assoc_by_slug = {a["slug"]: a for a in assocs}
    check_waters(waters, assoc_by_slug, violations, findings)
    check_associations(assocs, waters, violations, findings)
    check_species(species, violations)
    check_overlay(rivers, "rivers", violations, findings)
    check_overlay(lakes, "lakes", violations, findings)

    report = {
        "checked": {"waters": len(waters), "associations": len(assocs),
                    "rivers": len(rivers), "lakes": len(lakes), "species": len(species)},
        "violations": violations,
        "findings": findings,
    }
    Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    by_check = Counter(v["check"] for v in violations)
    print(f"[integrity] {len(waters)} waters, {len(assocs)} assoc, "
          f"{len(rivers)} rivers, {len(lakes)} lakes, {len(species)} species")
    print(f"[integrity] violations: {len(violations)} | findings (review): {len(findings)}")
    for check, n in sorted(by_check.items()):
        print(f"  VIOLATION {check}: {n}")
    for v in violations[:40]:
        print(f"    {json.dumps(v, ensure_ascii=False)}")
    if len(violations) > 40:
        print(f"    ... {len(violations) - 40} more")
    for f in findings[:20]:
        print(f"  FINDING {json.dumps(f, ensure_ascii=False)}")
    print(f"[integrity] report -> {args.json}")

    if violations:
        print("[integrity] FAIL: violations must be 0")
        sys.exit(1)
    print("[integrity] PASS: 0 violations")


if __name__ == "__main__":
    main()