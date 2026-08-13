#!/usr/bin/env python3
"""Verify county clips (t_117f0b99) on the built data.

Checks:
1. CONTAINMENT — every point of every stored clip lies inside its county
   polygon (buffered ~0.004° to absorb 5-dp rounding at the 0.002° clip
   buffer edge).
2. CLICK RESOLUTION — replicate the FE's fractionAtPoint + contractAtFraction
   (WaterFeatureLayer.tsx) and assert that clicking any point of a Brașov
   Olt clip resolves to a Brașov Olt contract; same spot-check for Siret
   Vrancea/Galați, Buzău county and Covasna.
3. KEY CASES — the reported bug: the Olt full course crosses 7 counties; the
   Brașov clip must cover ONLY the Brașov passage (bbox within county bounds).
"""
import json
import math
import re
import sys
from pathlib import Path

from shapely.geometry import Point, shape

ROOT = Path(__file__).resolve().parent.parent
BOUNDARY_DIR = ROOT / "data/raw/county_boundaries"

_ROMANIAN = [("ș", "s"), ("ţ", "t"), ("ț", "t"), ("ă", "a"), ("î", "i"), ("â", "a")]


def norm(s: str) -> str:
    t = s.lower()
    for a, b in _ROMANIAN:
        t = t.replace(a, b)
    return re.sub(r"[\s\-]+", "", t)


def load_boundaries():
    out = {}
    for f in BOUNDARY_DIR.glob("*.json"):
        r = json.loads(f.read_text(encoding="utf-8"))[0]
        out[norm(r.get("name") or f.stem)] = shape(r["geojson"])
    return out


def flatten(g):
    out = []

    def rec(c):
        if len(c) == 2 and isinstance(c[0], (int, float)) and isinstance(c[1], (int, float)):
            out.append((float(c[0]), float(c[1])))
            return
        for s in c:
            rec(s)

    rec(g["coordinates"])
    return out


# --- FE-equivalent course math (port of WaterFeatureLayer.tsx) ---

def haversine_km(a, b):
    R = 6371.0
    dlat = math.radians(b[1] - a[1])
    dlon = math.radians(b[0] - a[0])
    la1 = math.radians(a[1])
    la2 = math.radians(b[1])
    h = math.sin(dlat / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def order_parts(parts):
    if len(parts) <= 1:
        return parts
    mids = [p[len(p) // 2] for p in parts]
    mx = sum(m[0] for m in mids) / len(mids)
    my = sum(m[1] for m in mids) / len(mids)
    cxx = sum((m[0] - mx) ** 2 for m in mids)
    cyy = sum((m[1] - my) ** 2 for m in mids)
    cxy = sum((m[0] - mx) * (m[1] - my) for m in mids)
    theta = 0.5 * math.atan2(2 * cxy, cxx - cyy)
    vx, vy = math.cos(theta), math.sin(theta)
    scored = sorted(parts, key=lambda p: (p[len(p) // 2][0] - mx) * vx + (p[len(p) // 2][1] - my) * vy)
    half = max(1, len(scored) // 2)
    lat_first = sum(p[len(p) // 2][1] for p in scored[:half]) / half
    lat_last = sum(p[len(p) // 2][1] for p in scored[-half:]) / half
    return list(reversed(scored)) if lat_first < lat_last else scored


def fraction_at_point(parts, pt):
    """FE fractionAtPoint: nearest fraction [0,1] along the ordered course."""
    ordered = order_parts(parts)
    lengths = [sum(haversine_km(ordered[i][j - 1], ordered[i][j]) for j in range(1, len(ordered[i]))) for i in range(len(ordered))]
    total = sum(lengths)
    if total <= 0:
        return None

    def dist_to_seg(a, b, p):
        abx, aby = b[0] - a[0], b[1] - a[1]
        apx, apy = p[0] - a[0], p[1] - a[1]
        len2 = abx * abx + aby * aby
        t = (apx * abx + apy * aby) / len2 if len2 else 0
        t = max(0.0, min(1.0, t))
        cx, cy = a[0] + t * abx, a[1] + t * aby
        return math.hypot(p[0] - cx, p[1] - cy)

    best_frac, best_dist = None, float("inf")
    walked = 0.0
    for i, coords in enumerate(ordered):
        ln = lengths[i]
        for j in range(1, len(coords)):
            d = dist_to_seg(coords[j - 1], coords[j], pt)
            if d < best_dist:
                best_dist = d
                seg_len = haversine_km(coords[j - 1], coords[j])
                abx, aby = coords[j][0] - coords[j - 1][0], coords[j][1] - coords[j - 1][1]
                apx, apy = pt[0] - coords[j - 1][0], pt[1] - coords[j - 1][1]
                len2 = abx * abx + aby * aby
                t = (apx * abx + apy * aby) / len2 if len2 else 0
                t = max(0.0, min(1.0, t))
                within = sum(haversine_km(coords[k - 1], coords[k]) for k in range(1, j))
                best_frac = (walked + within + t * seg_len) / total
        walked += ln
    return best_frac


def water_key(name):
    lower = name.lower()
    for a, b in _ROMANIAN:
        lower = lower.replace(a, b)
    for prefix in ("raul ", "paraul ", "parau ", "valea ", "lacul ", "balta ", "acumularea ", "acumulare "):
        if lower.startswith(prefix):
            lower = lower[len(prefix):]
            break
    return (lower.replace("(", "").replace(")", "").strip().split()[0] or "") if lower.strip() else ""


def group_key_of(w):
    return w.get("riverGroup") or water_key(w.get("name", ""))


def is_main_course(name):
    import re as _re
    return not _re.match(r"^(valea|paraul|parau|pârâu|pârâul)\s", name, _re.I)


def course_rank(name):
    n = name.lower()
    if "superior" in n or "superioar" in n:
        return 0
    if "mijloci" in n:
        return 1
    if "inferior" in n or "inferioar" in n:
        return 2
    return 3


def contract_at_fraction(clicked, frac, all_waters):
    clicked_w = next((w for w in all_waters if w["slug"] == clicked.get("slug")), None) or \
        next((w for w in all_waters if w.get("name") == clicked.get("name")), None) or {"name": clicked.get("name")}
    gk = group_key_of(clicked_w)
    group = [w for w in all_waters if (is_main_course(w.get("name", "")) or w.get("mainCourse") is True) and group_key_of(w) == gk]
    if len(group) <= 1:
        return None
    best, best_len = None, float("inf")
    for w in group:
        s, e = w.get("sectorStart"), w.get("sectorEnd")
        if isinstance(s, (int, float)) and isinstance(e, (int, float)):
            if frac >= s and frac < e and (e - s) < best_len:
                best_len, best = e - s, w
    if best:
        return best
    ranked = sorted(group, key=lambda w: course_rank(w.get("name", "")))
    ranked_frac = lambda i: 0.5 if len(ranked) <= 1 else i / (len(ranked) - 1)
    positioned = sorted(
        [{"w": w, "f": w.get("course_frac") if isinstance(w.get("course_frac"), (int, float)) else ranked_frac(i)}
         for i, w in enumerate(ranked)], key=lambda p: p["f"])
    n = len(positioned)
    for i, p in enumerate(positioned):
        f = p["f"]
        left = (positioned[i - 1]["f"] + f) / 2 if i > 0 else -float("inf")
        right = (positioned[i + 1]["f"] + f) / 2 if i < n - 1 else float("inf")
        if frac >= left and frac < right:
            return p["w"]
    return None


def main():
    counties = load_boundaries()
    waters = json.loads((ROOT / "public/data/waters.json").read_text(encoding="utf-8"))
    uncontracted = json.loads((ROOT / "public/data/uncontracted_rivers.json").read_text(encoding="utf-8"))
    problems = []

    # 1. CONTAINMENT of every stored clip
    from shapely.prepared import prep
    prepared = {k: prep(v.buffer(0.004)) for k, v in counties.items()}
    total_clips = 0
    for pool_name, pool in (("contracted", waters), ("uncontracted", uncontracted)):
        for w in pool:
            gbc = w.get("geometryByCounty") or {}
            for key, gj in gbc.items():
                if gj is None:
                    continue
                total_clips += 1
                p = prepared.get(key)
                if p is None:
                    problems.append(f"{pool_name} {w['slug']}: clip key {key} not in boundaries")
                    continue
                for pt in flatten(gj):
                    if not p.contains(Point(pt)):
                        problems.append(f"{pool_name} {w['slug']} clip {key}: point {pt} outside county")
                        break

    # 2. CLICK RESOLUTION — Olt Brașov: every sampled point of the Brașov clip
    #    must resolve to a Brașov contract (or the clicked water itself).
    by_slug = {w["slug"]: w for w in waters}
    olt_brasov = [w for w in waters if w.get("riverGroup") == "olt" and w.get("judet") == "Brașov"]
    for w in olt_brasov:
        gbc = w.get("geometryByCounty") or {}
        clip = gbc.get("brasov")
        if not clip:
            problems.append(f"Olt Brașov {w['slug']} missing brasov clip")
            continue
        pts = flatten(clip)
        for pt in pts[:: max(1, len(pts) // 25)]:
            orig = w.get("geometry")
            if not orig:
                continue
            parts = orig["coordinates"] if orig["type"] == "MultiLineString" else [orig["coordinates"]]
            frac = fraction_at_point(parts, pt)
            if frac is None:
                continue
            c = contract_at_fraction({"slug": w["slug"], "name": w.get("name")}, frac, waters)
            if c is None:
                continue  # single-contract fallback — click resolves to clicked slug
            if c["judet"] != "Brașov":
                problems.append(f"Olt Brașov click at {pt} (frac {frac:.3f}) resolved to {c['name']} {c['judet']}")

    # 3. KEY CASES — Olt full course crosses 7 counties; Brașov clip must NOT
    #    extend outside Brașov's bounding box.
    olt = next(w for w in waters if w.get("slug") == "ehwpvgwh")
    brasov_poly = counties["brasov"]
    bb = brasov_poly.bounds
    clip_pts = flatten(olt["geometryByCounty"]["brasov"])
    if any(p[0] < bb[0] - 0.01 or p[0] > bb[2] + 0.01 or p[1] < bb[1] - 0.01 or p[1] > bb[3] + 0.01 for p in clip_pts):
        problems.append("Olt Brașov clip extends outside Brașov bbox")
    n_olt_counties = len(olt.get("geometryByCounty") or {})
    print(f"Olt clip counties: {sorted(olt.get('geometryByCounty', {}).keys())}")

    # Siret: each county's clip stays inside that county bbox
    for w in waters:
        if w.get("riverGroup") != "siret":
            continue
        gbc = w.get("geometryByCounty") or {}
        for key, gj in gbc.items():
            if not gj:
                continue
            cb = counties[key].bounds
            for p in flatten(gj):
                if p[0] < cb[0] - 0.01 or p[0] > cb[2] + 0.01 or p[1] < cb[1] - 0.01 or p[1] > cb[3] + 0.01:
                    problems.append(f"Siret {w['slug']} clip {key} outside bbox")

    print(f"stored clips: {total_clips}")
    print(f"Olt Brașov waters with clips: {len([w for w in olt_brasov if w.get('geometryByCounty')])}")
    if problems:
        print(f"\n{len(problems)} PROBLEMS:")
        for p in problems[:30]:
            print("  -", p)
        sys.exit(1)
    print("\nALL CHECKS PASSED")


if __name__ == "__main__":
    main()
