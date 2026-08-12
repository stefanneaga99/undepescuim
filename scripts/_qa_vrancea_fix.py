#!/usr/bin/env python3
"""Verify the t_9a7cf783 fix: geometry stats + FE click-resolution simulation.

Ports the FE logic from src/components/map/WaterFeatureLayer.tsx
(orderParts / fractionAtPoint / contractAtFraction / groupKeyOf /
isMainCourse / courseRank) so we can check what association a tap on the
Siret / Râmnicu Sărat / Zăbala resolves to, without running the browser.
"""
import json
import math
import sys
import unicodedata

FE_WATERS = "public/data/waters.json"
waters = json.loads(open(FE_WATERS, encoding="utf-8").read())
by_slug = {w["slug"]: w for w in waters}


def norm(s):
    s = s.lower().strip()
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def water_key(name):
    lower = norm(name)
    for pref in ("raul ", "paraul ", "parau ", "valea ", "lacul ", "balta ", "acumularea ", "acumulare "):
        if lower.startswith(pref):
            lower = lower[len(pref):]
            break
    lower = lower.replace("(", "").replace(")", "").strip()
    return lower.split()[0] if lower.split() else ""


def group_key_of(w):
    if w.get("riverGroup"):
        return w["riverGroup"]
    return water_key(w.get("name") or "")


def same_river(a, b):
    return a[:5] == b[:5]


def haversine_km(a, b):
    R = 6371
    dlat = math.radians(b[1] - a[1])
    dlon = math.radians(b[0] - a[0])
    la1 = math.radians(a[1])
    la2 = math.radians(b[1])
    h = math.sin(dlat / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def part_length(coords):
    return sum(haversine_km(coords[i - 1], coords[i]) for i in range(1, len(coords)))


def order_parts(parts):
    if len(parts) <= 1:
        return parts
    mids = [p[len(p) // 2] for p in parts]
    mx = sum(m[0] for m in mids) / len(mids)
    my = sum(m[1] for m in mids) / len(mids)
    cxx = cyy = cxy = 0.0
    for m in mids:
        cxx += (m[0] - mx) ** 2
        cyy += (m[1] - my) ** 2
        cxy += (m[0] - mx) * (m[1] - my)
    theta = 0.5 * math.atan2(2 * cxy, cxx - cyy)
    vx, vy = math.cos(theta), math.sin(theta)
    scored = sorted(
        ((p, (p[len(p) // 2][0] - mx) * vx + (p[len(p) // 2][1] - my) * vy) for p in parts),
        key=lambda x: x[1],
    )
    ordered = [s[0] for s in scored]
    half = max(1, len(ordered) // 2)
    lat_first = sum(p[len(p) // 2][1] for p in ordered[:half]) / half
    lat_last = sum(p[len(p) // 2][1] for p in ordered[-half:]) / half
    return list(reversed(ordered)) if lat_first < lat_last else ordered


def fraction_at_point(parts, pt):
    ordered = order_parts(parts)
    lengths = [part_length(p) for p in ordered]
    total = sum(lengths)
    if total <= 0:
        return None
    best_frac, best_dist, walked = None, float("inf"), 0.0
    for i, coords in enumerate(ordered):
        ln = lengths[i]
        for j in range(1, len(coords)):
            a, b = coords[j - 1], coords[j]
            abx, aby = b[0] - a[0], b[1] - a[1]
            apx, apy = pt[0] - a[0], pt[1] - a[1]
            len2 = abx * abx + aby * aby
            t = (apx * abx + apy * aby) / len2 if len2 else 0
            t = max(0, min(1, t))
            cx, cy = a[0] + t * abx, a[1] + t * aby
            d = math.hypot(pt[0] - cx, pt[1] - cy)
            if d < best_dist:
                best_dist = d
                seg_len = haversine_km(a, b)
                within = sum(haversine_km(coords[k - 1], coords[k]) for k in range(1, j))
                best_frac = (walked + within + t * seg_len) / total
        walked += ln
    return best_frac


def is_main_course(name):
    return not __import__("re").match(r"^(valea|paraul|parau|pârâu|pârâul)\s", name, __import__("re").I)


def course_rank(name):
    n = name.lower()
    if "superior" in n or "superioar" in n:
        return 0
    if "mijloci" in n:
        return 1
    if "inferior" in n or "inferioar" in n:
        return 2
    return 3


def contract_at_fraction(clicked_ref, frac):
    clicked = None
    if clicked_ref.get("slug"):
        clicked = by_slug.get(clicked_ref["slug"])
    if clicked is None and clicked_ref.get("name"):
        clicked = next((w for w in waters if w["name"] == clicked_ref["name"]), None)
    if clicked is None:
        clicked = {"name": clicked_ref.get("name")}
    gk = group_key_of(clicked)
    group = [w for w in waters
             if (is_main_course(w.get("name") or "") or w.get("mainCourse") is True)
             and group_key_of(w) == gk]
    if len(group) <= 1:
        return None
    best, best_len = None, float("inf")
    for w in group:
        s, e = w.get("sectorStart"), w.get("sectorEnd")
        if isinstance(s, (int, float)) and isinstance(e, (int, float)) and s <= frac < e and (e - s) < best_len:
            best_len, best = e - s, w
    if best:
        return best
    ranked = sorted(group, key=lambda w: course_rank(w.get("name") or ""))
    ranked_frac = lambda i: 0.5 if len(ranked) <= 1 else i / (len(ranked) - 1)
    positioned = sorted(
        [{"w": w, "f": w.get("course_frac") if isinstance(w.get("course_frac"), (int, float)) else ranked_frac(i)}
         for i, w in enumerate(ranked)],
        key=lambda x: x["f"],
    )
    n = len(positioned)
    for i, item in enumerate(positioned):
        f = item["f"]
        left = -float("inf") if i == 0 else (positioned[i - 1]["f"] + f) / 2
        right = float("inf") if i == n - 1 else (f + positioned[i + 1]["f"]) / 2
        if left <= frac < right:
            return item["w"]
    return None


def geom_parts(w):
    g = w.get("geometry")
    if not g:
        return None
    if g["type"] == "MultiLineString":
        return g["coordinates"]
    return [g["coordinates"]]


def click_test(slug, label, pt):
    w = by_slug[slug]
    parts = geom_parts(w)
    frac = fraction_at_point(parts, pt)
    contract = contract_at_fraction({"slug": slug, "name": w["name"]}, frac)
    res = contract["name"] + " / " + ((contract.get("asociatie") or {}).get("name") or "?") if contract else "(own slug)"
    print(f"  {label:38s} frac={frac:.3f} -> {res}")
    return res


print("=== 1. changed waters geometry ===")
for slug in ["anpa-anpa-0674", "anpa-vrancea-ramnicu-sarat", "anpa-anpa-0215", "anpa-anpa-0676"]:
    w = by_slug[slug]
    g = w.get("geometry")
    gt = g.get("type") if g else None
    n = len(g["coordinates"]) if gt == "LineString" else (len(g["coordinates"]) if gt == "MultiLineString" else 0)
    print(f"  {slug:28s} {w['name']:24s} {w['judet']:8s} {gt} pts={n} bbox={w.get('bbox')} "
          f"sStart={w.get('sectorStart')} sEnd={w.get('sectorEnd')} group={w.get('riverGroup')}")

print("\n=== 2. Siret (Vrancea sector) click resolution — reported area ===")
# sample points ON the Siret sector: interpolate along the geometry
ws = by_slug["anpa-anpa-0674"]
sc = ws["geometry"]["coordinates"]
# pick river points near Focșani (45.70), Odobești (45.76), Panciu (45.91), south end (45.55)
targets = [("Focșani lat 45.70", 45.70), ("Odobești lat 45.76", 45.76), ("Panciu lat 45.91", 45.91),
           ("south end 45.55", 45.55), ("north end 46.15", 46.15)]
for label, lat in targets:
    pt = min(sc, key=lambda p: abs(p[1] - lat))
    print(f"  river point at {label}: ({pt[0]:.4f},{pt[1]:.4f})")
    click_test("anpa-anpa-0674", f"click Siret {label}", pt)

print("\n=== 3. Râmnicu Sărat (Vrancea) click resolution ===")
wr = by_slug["anpa-vrancea-ramnicu-sarat"]
rc = wr["geometry"]["coordinates"]
for label, lat in [("source end 45.58", 45.583), ("mid 45.45", 45.45), ("mouth end 45.53", 45.527)]:
    pt = min(rc, key=lambda p: abs(p[1] - lat))
    print(f"  river point at {label}: ({pt[0]:.4f},{pt[1]:.4f})")
    click_test("anpa-vrancea-ramnicu-sarat", f"click Râmnicu Sărat {label}", pt)

print("\n=== 4. Zăbala (full course) click resolution ===")
wz = by_slug["anpa-anpa-0676"]
zc = wz["geometry"]["coordinates"]
for label, lat in [("source 45.83", 45.834), ("upper-mid 45.72", 45.72), ("mid 45.75", 45.755),
                   ("lower 45.82", 45.815), ("mouth 45.857", 45.8575)]:
    pt = min(zc, key=lambda p: abs(p[1] - lat))
    print(f"  river point at {label}: ({pt[0]:.4f},{pt[1]:.4f})")
    click_test("anpa-anpa-0676", f"click Zăbala {label}", pt)

print("\n=== 5. Sanity: Siret group members (unchanged) ===")
siret = [w for w in waters if norm(w.get("name", "")) == "raul siret"]
print("  siret entries:", len(siret))
for w in sorted(siret, key=lambda x: x.get("course_frac") or 0):
    g = w.get("geometry")
    print(f"  {w['judet']:10s} cfrac={w.get('course_frac')} geom={bool(g)} bbox={bool(w.get('bbox'))}")
