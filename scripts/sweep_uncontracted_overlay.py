#!/usr/bin/env python3
"""SWEEP validator (t_963f40e4): find every uncontracted overlay river/lake
that actually BELONGS to (overlaps / is the same body as) a contracted water —
the systematic version of the 'Siriu' duplicate fix (t_0ca43d1a).

For each uncontracted river (~4.2k) and lake (~5.7k) in
public/data/uncontracted_rivers.json / uncontracted_lakes.json, compare against
every contracted water in public/data/waters.json that has geometry, using a
STRtree spatial index + name matching, and classify each hit:

  DUPLICATE      — same body: the uncontracted feature should be merged into
                   the contracted entry and removed from the overlay.
  TRIBUTARY      — genuinely separate stream feeding the contracted river
                   (touches it at one end only). Keep uncontracted.
  NAME_COLLISION — same name, different water (geometries far apart). Keep.
  AMBIGUOUS      — partial overlap / unclear; report only, do not touch.

Outputs:
  data/sweep_overlay_report.json — full machine-readable hit list
  data/sweep_overlay_report.md   — human-readable summary w/ counts + lists

Usage:
  .venv/bin/python scripts/sweep_uncontracted_overlay.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE_WATERS = ROOT / "public" / "data" / "waters.json"
FE_RIVERS = ROOT / "public" / "data" / "uncontracted_rivers.json"
FE_LAKES = ROOT / "public" / "data" / "uncontracted_lakes.json"
OUT_JSON = ROOT / "data" / "sweep_overlay_report.json"
OUT_MD = ROOT / "data" / "sweep_overlay_report.md"

# proximity epsilon: ~90 m in degrees (same as build guard)
EPS_DEG = 0.0008
# expand candidate bbox by this much when querying the STRtree (~300 m)
SEARCH_DEG = 0.003

sys.path.insert(0, str(ROOT / "scripts"))
from audit_missing_rivers import norm  # noqa: E402
from build_uncontracted_lakes import lake_core_name  # noqa: E402


def river_core_name(n: str) -> str:
    """Strip common river-name prefixes for matching:
    'raul siriul'/'rau siriul'/'siriul' -> 'siriul'."""
    n = norm(n)
    for prefix in ("raul", "rau", "paraul", "parau", "valea", "val"):
        if n.startswith(prefix + " "):
            n = n[len(prefix):].strip()
            break
    return n


def name_match(a: str, b: str) -> bool:
    """True when normalized names agree (either full or core)."""
    na, nb = norm(a), norm(b)
    if na == nb:
        return True
    ca, cb = river_core_name(a), river_core_name(b)
    if ca and cb and ca == cb:
        return True
    la, lb = lake_core_name(na), lake_core_name(nb)
    if len(la) >= 3 and la == lb:
        return True
    return False


def load_geoms(entries):
    from shapely.geometry import shape
    out = []
    for e in entries:
        g = e.get("geometry")
        if not g:
            continue
        try:
            geom = shape(g)
        except Exception:
            continue
        if geom.is_empty:
            continue
        out.append((e, geom))
    return out


def line_points(geom):
    """Flatten a LineString/MultiLineString to a list of (lon, lat)."""
    if geom.geom_type == "LineString":
        return list(geom.coords)
    return [c for part in geom.geoms for c in part.coords]


def classify_river_hit(unc, unc_geom, w, w_geom, dist, frac_near, end_near, name_hit,
                       part_fracs=None):
    """Return (label, confidence, note).

    part_fracs (optional): per-part fraction of points near the contracted
    course for MultiLineString overlays. A single PART lying almost entirely
    on the contracted course is a PARTIAL_DUPLICATE even when the whole entry
    (with other genuinely-uncontracted parts) has a low overall frac_near —
    the Doftana class (t_f4ff3853): the upper part of the Prahova 'Doftana'
    overlay was the contracted Râul Doftana Gârcin course while its lower
    parts were a different, uncontracted river.
    """
    # Douglas-Peucker can collapse a winding stream to a straight 2-pt chord
    # that happens to lie on the contracted course (t_963f40e4: 'Valea
    # Brustuletului' — raw 169-pt stream meanders 900 m away mid-course, the
    # simplified chord lies on Râul Dambovicioara). A 2-pt geometry cannot be
    # judged by course-proximity alone — report, don't guess.
    if unc_geom.geom_type == "LineString" and len(list(unc_geom.coords)) <= 2:
        return ("AMBIGUOUS", "low",
                f"simplified 2-pt chord lies on {w['name']} (raw course meanders away?)")
    if part_fracs:
        # PARTIAL_DUPLICATE only when a real STRETCH of the overlay lies on
        # the contracted course (t_f4ff3853: Doftana seg8 was a 191-pt /
        # 7.6 km way). Tiny 2-pt connector fragments at a confluence also have
        # 100% of THEIR points near the course but are just the mouth touch —
        # require the part to look like a genuine course (> 1 km).
        best_part = None
        for pi, pf, plen in part_fracs:
            if pf >= 0.9 and plen >= 1.0:
                if best_part is None or plen > best_part[2]:
                    best_part = (pi, pf, plen)
        if best_part:
            return ("PARTIAL_DUPLICATE", "high",
                    f"part {best_part[0]} ({best_part[1]:.0%}, {best_part[2]:.1f} km on "
                    f"contracted course) is the course of {w['name']}")
    if name_hit and frac_near >= 0.5:
        return ("DUPLICATE", "high",
                f"name {unc['name']!r}=={w['name']!r} and {frac_near:.0%} of course on contracted water")
    if frac_near >= 0.9 and end_near:
        return ("DUPLICATE", "high",
                f"{frac_near:.0%} of course + both ends within {EPS_DEG} deg of {w['name']}")
    # mouth-only contact: one end within eps, course then moves away
    if (not end_near) and frac_near <= 0.35 and dist <= EPS_DEG:
        return ("TRIBUTARY", "medium",
                f"touches {w['name']} at mouth only ({frac_near:.0%} near)")
    if name_hit and dist > 0.02:  # ~2 km apart — same name, different river
        return ("NAME_COLLISION", "high",
                f"same name as {w['name']} but {dist * 111e3:.0f} m away")
    if frac_near >= 0.5:
        return ("AMBIGUOUS", "medium",
                f"{frac_near:.0%} of course within eps of {w['name']} (partial overlap)")
    return None


def classify_lake_hit(unc, unc_geom, w, w_geom, overlap_frac, centroid_in, dist, name_hit):
    """Return (label, confidence, note) for lake vs contracted lake."""
    if overlap_frac >= 0.5:
        return ("DUPLICATE", "high",
                f"{overlap_frac:.0%} of lake area overlaps contracted {w['name']}")
    if name_hit and overlap_frac >= 0.15:
        return ("DUPLICATE", "high",
                f"name {unc['name']!r}=={w['name']!r} and {overlap_frac:.0%} area overlap")
    if name_hit and (centroid_in or dist <= EPS_DEG):
        return ("DUPLICATE", "high",
                f"name matches {w['name']} and centroid inside / within {dist * 111e3:.0f} m")
    if overlap_frac >= 0.15:
        return ("AMBIGUOUS", "medium",
                f"{overlap_frac:.0%} of lake area overlaps {w['name']} (check)")
    if name_hit and dist > 0.02:
        return ("NAME_COLLISION", "high",
                f"same name as {w['name']} but {dist * 111e3:.0f} m away")
    if name_hit:
        return ("AMBIGUOUS", "low", f"same name as {w['name']} but no overlap found")
    return None


def main() -> None:
    from shapely.geometry import Point, box, shape
    from shapely.strtree import STRtree

    waters = json.loads(FE_WATERS.read_text(encoding="utf-8"))
    rivers = json.loads(FE_RIVERS.read_text(encoding="utf-8"))
    lakes = json.loads(FE_LAKES.read_text(encoding="utf-8"))
    print(f"[load] {len(waters)} contracted, {len(rivers)} unc rivers, {len(lakes)} unc lakes")

    # contracted geometries
    contracted = []          # (entry, geom) — only river courses & lake polys
    for w in waters:
        g = w.get("geometry")
        if not g:
            continue
        try:
            geom = shape(g)
        except Exception:
            continue
        if geom.is_empty:
            continue
        contracted.append((w, geom))
    print(f"[geom] {len(contracted)} contracted with usable geometry")

    # STRtree index
    tree = STRtree([cg for _, cg in contracted])

    # name index for NAME_COLLISION detection: same (core) name, far apart.
    # bbox-query candidates are always within SEARCH_DEG, so a same-name pair
    # 5 km away would never be compared without this pass.
    name_index: dict[str, list] = {}   # norm/core name -> [(entry, geom)]
    for w, g in contracted:
        for key in (norm(w["name"]), river_core_name(w["name"]), lake_core_name(norm(w["name"]))):
            if key and len(key) >= 3:
                name_index.setdefault(key, []).append((w, g))

    hits = []  # one dict per (uncontracted, contracted) pair
    n_river = n_lake = 0

    # ---------------- RIVERS ----------------
    for u, u_geom in load_geoms(rivers):
        n_river += 1
        pts = line_points(u_geom)
        if len(pts) < 2:
            continue
        sample = pts[:: max(1, len(pts) // 40)]
        bbox = u_geom.bounds
        x0, y0, x1, y1 = bbox
        # query STRtree with expanded bbox
        query_box = box(x0 - SEARCH_DEG, y0 - SEARCH_DEG, x1 + SEARCH_DEG, y1 + SEARCH_DEG)
        cands = tree.query(query_box)
        for ci in cands:
            w, w_geom = contracted[ci]
            if w_geom.geom_type in ("Polygon", "MultiPolygon"):
                continue  # river vs lake: only check name/proximity below
            dist = u_geom.distance(w_geom)
            if dist > SEARCH_DEG:
                continue
            near = sum(1 for p in sample if w_geom.distance(Point(p)) <= EPS_DEG)
            frac_near = near / len(sample)
            first, last = Point(pts[0]), Point(pts[-1])
            end_near = w_geom.distance(first) <= EPS_DEG and w_geom.distance(last) <= EPS_DEG
            name_hit = name_match(u["name"], w["name"])
            # per-part fractions for MultiLineString overlays — a single part
            # lying on the contracted course is a PARTIAL_DUPLICATE even when
            # the whole entry is mostly a different river (t_f4ff3853).
            part_fracs = None
            if u_geom.geom_type == "MultiLineString":
                part_fracs = []
                for pi, part in enumerate(u_geom.geoms):
                    pc = list(part.coords)
                    ps = pc[:: max(1, len(pc) // 40)]
                    pn = sum(1 for p in ps if w_geom.distance(Point(p)) <= EPS_DEG)
                    plen = sum(
                        __import__("math").hypot(pc[k][0] - pc[k - 1][0],
                                                 pc[k][1] - pc[k - 1][1]) * 111.0
                        for k in range(1, len(pc))
                    ) if len(pc) > 1 else 0.0
                    part_fracs.append((pi, pn / len(ps) if ps else 0.0, plen))
            cls = classify_river_hit(u, u_geom, w, w_geom, dist, frac_near, end_near,
                                     name_hit, part_fracs)
            if cls is None:
                continue
            label, conf, note = cls
            hits.append({
                "kind": "river", "unc_slug": u["slug"], "unc_name": u["name"],
                "unc_judet": u.get("judet"), "unc_lengthKm": u.get("lengthKm"),
                "water_slug": w["slug"], "water_name": w["name"],
                "water_judet": w.get("judet"), "label": label, "confidence": conf,
                "dist_m": round(dist * 111e3), "frac_near": round(frac_near, 3),
                "part_frac": (round(max(p[1] for p in part_fracs), 3)
                              if part_fracs else None),
                "end_near": bool(end_near), "note": note,
            })

    # ---------------- LAKES ----------------
    # contracted lake polygon index (for area overlap)
    lake_polys = [(w, g) for w, g in contracted if g.geom_type in ("Polygon", "MultiPolygon")]
    lake_tree = STRtree([g for _, g in lake_polys])

    for u, u_geom in load_geoms(lakes):
        n_lake += 1
        bbox = u_geom.bounds
        query_box = box(bbox[0] - SEARCH_DEG, bbox[1] - SEARCH_DEG,
                        bbox[2] + SEARCH_DEG, bbox[3] + SEARCH_DEG)
        u_area = u_geom.area
        if u_area <= 0:
            continue
        cpt = u_geom.representative_point()
        cands = lake_tree.query(query_box)
        for ci in cands:
            w, w_geom = lake_polys[ci]
            dist = u_geom.distance(w_geom)
            if dist > SEARCH_DEG:
                continue
            try:
                inter = u_geom.intersection(w_geom)
            except Exception:
                # invalid ring in a contracted geometry — repair and retry
                try:
                    inter = u_geom.buffer(0).intersection(w_geom.buffer(0))
                except Exception:
                    inter = None
            overlap_frac = (inter.area / u_area) if inter is not None and not inter.is_empty else 0.0
            centroid_in = w_geom.contains(Point(cpt.x, cpt.y))
            name_hit = name_match(u["name"], w["name"])
            cls = classify_lake_hit(u, u_geom, w, w_geom, overlap_frac, centroid_in,
                                    dist, name_hit)
            if cls is None:
                continue
            label, conf, note = cls
            hits.append({
                "kind": "lake", "unc_slug": u["slug"], "unc_name": u["name"],
                "unc_judet": u.get("judet"), "unc_areaHa": u.get("areaHa"),
                "water_slug": w["slug"], "water_name": w["name"],
                "water_judet": w.get("judet"), "label": label, "confidence": conf,
                "dist_m": round(dist * 111e3), "overlap_frac": round(overlap_frac, 3),
                "centroid_in": bool(centroid_in), "note": note,
            })

    # ---------------- NAME COLLISIONS (far-apart same-name pairs) --------
    # Spatial passes above only compare bbox-adjacent features; a same-name
    # pair 10 km apart (e.g. two 'Crasna' rivers in different counties) must be
    # flagged as a collision, not silently kept. Only report pairs whose name
    # matched but whose geometries are far apart (> 2 km).
    seen_pairs = {(h["kind"], h["unc_slug"], h["water_slug"]) for h in hits}
    for kind, entries in (
        ("river", load_geoms(rivers)),
        ("lake", load_geoms(lakes)),
    ):
        for u, u_geom in entries:
            keys = {norm(u["name"]), river_core_name(u["name"]),
                    lake_core_name(norm(u["name"]))}
            for key in keys:
                if not key or len(key) < 3:
                    continue
                for w, w_geom in name_index.get(key, []):
                    if (kind, u["slug"], w["slug"]) in seen_pairs:
                        continue
                    dist = u_geom.distance(w_geom)
                    if dist <= 0.02:  # within ~2 km — not a collision (already checked or near)
                        continue
                    if not name_match(u["name"], w["name"]):
                        continue
                    hits.append({
                        "kind": kind, "unc_slug": u["slug"], "unc_name": u["name"],
                        "unc_judet": u.get("judet"),
                        "water_slug": w["slug"], "water_name": w["name"],
                        "water_judet": w.get("judet"), "label": "NAME_COLLISION",
                        "confidence": "high",
                        "dist_m": round(dist * 111e3),
                        "note": f"same name as {w['name']} but {dist * 111e3:.0f} m away",
                    })
                    seen_pairs.add((kind, u["slug"], w["slug"]))

    # sort: duplicates first, then by label/confidence
    order = {"DUPLICATE": 0, "PARTIAL_DUPLICATE": 0, "AMBIGUOUS": 1,
             "TRIBUTARY": 2, "NAME_COLLISION": 3}
    conf_order = {"high": 0, "medium": 1, "low": 2}
    hits.sort(key=lambda h: (order.get(h["label"], 9), conf_order.get(h["confidence"], 9),
                             h["unc_name"].lower(), h["unc_slug"], h["water_slug"]))

    # write JSON
    OUT_JSON.write_text(json.dumps(hits, ensure_ascii=False, indent=1), encoding="utf-8")

    # write MD report
    from collections import Counter
    by_label = Counter(h["label"] for h in hits)
    by_kind = Counter(h["kind"] for h in hits)
    by_conf = Counter(h["confidence"] for h in hits)

    lines = []
    lines.append("# Overlay sweep report (t_963f40e4)\n")
    lines.append(f"Generated: sweep of {n_river} uncontracted rivers + {n_lake} "
                 f"uncontracted lakes vs {len(contracted)} contracted waters with geometry.\n")
    lines.append("## Counts\n")
    lines.append(f"- DUPLICATE: **{by_label.get('DUPLICATE', 0)}**")
    lines.append(f"- AMBIGUOUS: **{by_label.get('AMBIGUOUS', 0)}**")
    lines.append(f"- TRIBUTARY: **{by_label.get('TRIBUTARY', 0)}**")
    lines.append(f"- NAME_COLLISION: **{by_label.get('NAME_COLLISION', 0)}**")
    lines.append(f"- total hits: **{len(hits)}** (rivers {by_kind.get('river', 0)}, "
                 f"lakes {by_kind.get('lake', 0)})")
    lines.append("")
    lines.append(f"Confidence: {dict(by_conf)}\n")
    lines.append("## DUPLICATES\n")
    lines.append("| # | kind | uncontracted | judet | contracted water | dist_m | frac | note |")
    lines.append("|---|------|--------------|-------|------------------|--------|------|------|")
    for i, h in enumerate(hits, 1):
        if h["label"] not in ("DUPLICATE", "PARTIAL_DUPLICATE"):
            continue
        frac = h.get("frac_near") if h["kind"] == "river" else h.get("overlap_frac")
        if h["label"] == "PARTIAL_DUPLICATE":
            frac = h.get("part_frac")
        lines.append(f"| {i} | {h['kind']} | {h['unc_name']} | {h['unc_judet']} | "
                     f"{h['water_name']} ({h['water_slug']}) | {h['dist_m']} | {frac} | {h['note']} |")
    lines.append("")
    lines.append("## AMBIGUOUS\n")
    lines.append("| # | kind | uncontracted | judet | contracted water | dist_m | frac | note |")
    lines.append("|---|------|--------------|-------|------------------|--------|------|------|")
    for i, h in enumerate(hits, 1):
        if h["label"] != "AMBIGUOUS":
            continue
        frac = h.get("frac_near") if h["kind"] == "river" else h.get("overlap_frac")
        lines.append(f"| {i} | {h['kind']} | {h['unc_name']} | {h['unc_judet']} | "
                     f"{h['water_name']} ({h['water_slug']}) | {h['dist_m']} | {frac} | {h['note']} |")
    lines.append("")
    lines.append("## TRIBUTARIES\n")
    lines.append("| # | kind | uncontracted | judet | contracted water | note |")
    lines.append("|---|------|--------------|-------|------------------|------|")
    for i, h in enumerate(hits, 1):
        if h["label"] != "TRIBUTARY":
            continue
        lines.append(f"| {i} | {h['kind']} | {h['unc_name']} | {h['unc_judet']} | "
                     f"{h['water_name']} | {h['note']} |")
    lines.append("")
    lines.append("## NAME COLLISIONS\n")
    lines.append("| # | kind | uncontracted | judet | contracted water | note |")
    lines.append("|---|------|--------------|-------|------------------|------|")
    for i, h in enumerate(hits, 1):
        if h["label"] != "NAME_COLLISION":
            continue
        lines.append(f"| {i} | {h['kind']} | {h['unc_name']} | {h['unc_judet']} | "
                     f"{h['water_name']} | {h['note']} |")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[write] {len(hits)} hits -> {OUT_JSON}")
    print(f"[write] report -> {OUT_MD}")
    print(f"[counts] {dict(by_label)} | {dict(by_kind)} | conf {dict(by_conf)}")


def append_fixed_section() -> None:
    """Append '## FIXED' to OUT_MD: uncontracted lakes present at git HEAD but
    missing now (removed because they duplicate a contracted water). Run once
    after applying removals so the report documents the fix (t_963f40e4)."""
    import subprocess
    from shapely.geometry import shape

    try:
        old_raw = subprocess.run(
            ["git", "show", "HEAD:public/data/uncontracted_lakes.json"],
            capture_output=True, text=True, check=True).stdout
    except Exception:
        print("[fixed] cannot read git HEAD lakes — skip", flush=True)
        return
    old = json.loads(old_raw)
    new = json.loads(FE_LAKES.read_text(encoding="utf-8"))
    new_slugs = {y["slug"] for y in new}
    removed = [x for x in old if x["slug"] not in new_slugs]
    if not removed:
        print("[fixed] no removals vs HEAD — skip", flush=True)
        return
    waters = json.loads(FE_WATERS.read_text(encoding="utf-8"))
    rows = []
    for u in removed:
        ug = shape(u["geometry"])
        best, best_frac = None, 0.0
        for ww in waters:
            g = ww.get("geometry")
            if not g or g.get("type") not in ("Polygon", "MultiPolygon"):
                continue
            try:
                inter = ug.intersection(shape(g))
            except Exception:
                continue
            frac = inter.area / ug.area if not inter.is_empty and ug.area else 0.0
            if frac > best_frac:
                best_frac, best = frac, ww["name"]
        rows.append((u, best or "?", best_frac))
    lines = ["", "## FIXED (this sweep)", "",
             f"{len(rows)} uncontracted lakes removed from the overlay — each is "
             "the same water body as a contracted lake (>=50% area overlap), kept "
             "in waters.json as contracted.", "",
             "| # | removed (overlay) | judet | areaHa | contracted water | overlap |",
             "|---|-------------------|-------|--------|------------------|---------|"]
    for i, (u, name, frac) in enumerate(rows, 1):
        lines.append(f"| {i} | {u['name']} | {u['judet']} | {u.get('areaHa')} | "
                     f"{name} | {frac:.0%} |")
    with open(OUT_MD, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[fixed] appended {len(rows)} fixed rows to {OUT_MD}", flush=True)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-fixed", action="store_true",
                    help="append the FIXED section (removals vs git HEAD) to the report")
    ap.add_argument("--gate", action="store_true",
                    help="CI gate: exit 1 when any DUPLICATE / PARTIAL_DUPLICATE remains "
                         "(plan §5.1 pass criteria: 0 DUPLICATE + 0 PARTIAL_DUPLICATE)")
    args = ap.parse_args()
    main()
    if args.with_fixed:
        append_fixed_section()
    if args.gate:
        import json as _json
        hits = _json.loads(OUT_JSON.read_text(encoding="utf-8")) if OUT_JSON.exists() else []
        blockers = [h for h in hits if h["label"] in ("DUPLICATE", "PARTIAL_DUPLICATE")]
        if blockers:
            from collections import Counter as _C
            by_label = _C(h["label"] for h in blockers)
            print(f"[gate] FAIL: {len(blockers)} DUPLICATE/PARTIAL_DUPLICATE remaining "
                  f"({dict(by_label)}) — overlay is not clean")
            for h in blockers[:20]:
                print(f"  {h['label']:18} {h['kind']:6} {h['unc_name'][:40]:42} "
                      f"== {h['water_name'][:40]} ({h['water_judet']})")
            sys.exit(1)
        print("[gate] PASS: 0 DUPLICATE + 0 PARTIAL_DUPLICATE remaining")
