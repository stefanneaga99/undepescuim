#!/usr/bin/env python3
"""t_5f5f2cce — recompute association bboxes from waters' SECTOR extents.

A multi-contract member (e.g. the 'jiu' group's owner) holds the FULL shared
course; its whole-geometry bbox would drag the association's fly-to bbox over
every other county's sector. Compute each water's contribution as the bbox of
its contract interval SLICE of the shared course (same math as the FE's
contractInterval + sliceMultiLine), fall back to the water's own bbox for
single-contract waters.
"""
import json
import math

WATERS = 'public/data/waters.json'
ASSOCS = 'public/data/associations.json'
TARGETS = {'a-cerbul-carpatin', 'ajvps-gorj', 'pro-pescar', 'directia-silvica-gorj'}


def haversine(a, b):
    R = 6371
    dlat = math.radians(b[1] - a[1])
    dlon = math.radians(b[0] - a[0])
    h = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(a[1])) * math.cos(math.radians(b[1]))
         * math.sin(dlon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(h))


def is_main_course(name):
    import re
    return not re.match(r'^(valea|paraul|parau|pârâu|pârâul)\s', name, re.I)


def water_key(name):
    import unicodedata, re
    lower = unicodedata.normalize('NFD', name.lower())
    lower = ''.join(c for c in lower if unicodedata.category(c) != 'Mn')
    lower = re.sub(r'^(raul|paraul|parau|valea|lacul|balta|acumularea|acumulare)\s+', '', lower)
    return (lower.split() or [''])[0]


def group_key(w):
    return w.get('riverGroup') or water_key(w.get('name') or '')


def contract_group(w, waters):
    gk = group_key(w)
    return [x for x in waters if (is_main_course(x.get('name') or '') or x.get('mainCourse'))
            and group_key(x) == gk]


def course_rank(name):
    n = (name or '').lower()
    if 'superior' in n or 'superioar' in n:
        return 0
    if 'mijloci' in n:
        return 1
    if 'inferior' in n or 'inferioar' in n:
        return 2
    return 3


def contract_interval(w, waters):
    s = w.get('sectorStart')
    e = w.get('sectorEnd')
    if isinstance(s, (int, float)) and isinstance(e, (int, float)):
        return [s, e]
    group = contract_group(w, waters)
    if len(group) <= 1:
        return [0.0, 1.0]
    ranked = sorted(group, key=lambda x: course_rank(x.get('name') or ''))
    n = len(ranked)
    ranked_frac = lambda i: 0.5 if n <= 1 else i / (n - 1)
    positioned = sorted(
        [{'w': x, 'f': x.get('course_frac') if isinstance(x.get('course_frac'), (int, float)) else ranked_frac(i)}
         for i, x in enumerate(ranked)],
        key=lambda p: p['f'],
    )
    idx = next((i for i, p in enumerate(positioned) if p['w']['slug'] == w['slug']), -1)
    if idx < 0:
        return [0.0, 1.0]
    f = positioned[idx]['f']
    left = 0.0 if idx == 0 else (positioned[idx - 1]['f'] + f) / 2
    right = 1.0 if idx == len(positioned) - 1 else (f + positioned[idx + 1]['f']) / 2
    return [left, right]


def slice_bbox(geom, f0, f1):
    """BBox of the [f0,f1] haversine slice of a LineString/MultiLineString."""
    coords = geom['coordinates']
    if geom['type'] == 'LineString':
        coords = [coords]
    # lengths per part
    lens = []
    for p in coords:
        lens.append(sum(haversine(p[i - 1], p[i]) for i in range(1, len(p))))
    total = sum(lens)
    if total <= 0:
        return None
    d0, d1 = f0 * total, f1 * total
    out = []
    walked = 0
    for p, ln in zip(coords, lens):
        seg_start, seg_end = walked, walked + ln
        walked = seg_end
        if seg_end <= d0 or seg_start >= d1:
            continue
        trimmed = []
        acc = seg_start
        for j, pt in enumerate(p):
            if j > 0:
                acc += haversine(p[j - 1], pt)
            if acc < d0:
                if trimmed:
                    trimmed[-1] = pt
                continue
            if acc > d1:
                if not trimmed or trimmed[-1] != p[j - 1]:
                    trimmed.append(p[j - 1])
                trimmed.append(pt)
                break
            trimmed.append(pt)
        if len(trimmed) >= 2:
            out.extend(trimmed)
    if not out:
        return None
    lons = [c[0] for c in out]
    lats = [c[1] for c in out]
    return [min(lons), min(lats), max(lons), max(lats)]


def water_contribution(w, waters):
    """BBox contribution of one water to its association's bbox."""
    geom = w.get('geometry')
    group = contract_group(w, waters)
    if len(group) > 1:
        # sector slice of the shared course
        owner = None
        for x in group:
            if x['slug'] != w['slug'] and x.get('geometry'):
                owner = x
                break
        if owner is None and geom:
            owner = w
        if owner and owner.get('geometry'):
            f0, f1 = contract_interval(w, waters)
            bb = slice_bbox(owner['geometry'], f0, f1)
            if bb:
                return bb
    if geom:
        return slice_bbox(geom, 0.0, 1.0)
    return w.get('bbox')


def main():
    with open(WATERS) as f:
        waters = json.load(f)
    with open(ASSOCS) as f:
        assocs = json.load(f)
    by_slug = {a['slug']: a for a in assocs}

    for a in assocs:
        slug = a['slug']
        if slug not in TARGETS:
            continue
        union = None
        for w in waters:
            if (w.get('asociatie') or {}).get('slug') != slug:
                continue
            bb = water_contribution(w, waters)
            if not bb:
                continue
            union = bb if union is None else [min(union[0], bb[0]), min(union[1], bb[1]),
                                              max(union[2], bb[2]), max(union[3], bb[3])]
        if union:
            print(f'{slug}: {a.get("bbox")} -> {[round(x, 6) for x in union]}')
            a['bbox'] = [round(x, 6) for x in union]

    with open(ASSOCS, 'w') as f:
        f.write(json.dumps(assocs, indent=1, ensure_ascii=False))
    print('written', ASSOCS)


if __name__ == '__main__':
    main()
