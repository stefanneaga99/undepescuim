#!/usr/bin/env python3
"""t_5f5f2cce — fix per-segment association resolution for the Jiu system.

Root cause: the "Râul Jiu" water (qrjybswm, AJVPS GORJ) carried the WHOLE
Jiu course (confluence → Danube) and the Jiul Inferior (fanvixkg, Pro Pescar)
carried the same course with duplicated parts, so any association holding
either entry highlighted (or double-drew) the entire Jiu including other
counties' sectors. The Sohodol I/II contracts (A.CERBUL CARPATIN vs
AJVPS GORJ) shared one fuzzy group 'sohodol' AND identical full-course
geometry, so clicks on Cerbul's highlight resolved to Gorj's contract.

Fix (Siret pattern, t_ebd873fe): ONE geometry owner + geometry-less sector
members with full-course sectorStart/sectorEnd.

  Jiu group ('jiu'), fractions on the full ordered course (confluence → Danube):
    fanvixkg   Jiul Inferior (Pro Pescar)        [0.0000, 0.0160]  (conf. Jiul est+vest → Valea Polatiște / HD border)
    anpa-romsilva-0239  Râul Jiu (D.S. Gorj, NEW) [0.0160, 0.1267]  (HD border → Bumbești-Jiu, 30 km)
    qrjybswm   Râul Jiu (AJVPS GORJ, owner)       [0.1267, 0.4887]  (Bumbești-Jiu → Gorj/Dolj border ≈ Țânțăreni)
    anpa-anpa-0280  Râul Jiu și afluenții (AJVPS DOLJ) [0.4887, 1.0]

  Sohodol group ('sohodol'), fractions on the deduped/ordered course:
    2yxhr1b0   Râul Sohodol I (A.CERBUL CARPATIN, owner) [0.0, 0.4952] (izvoare → DN67D Runcu)
    8rd9jm0l   Râul Sohodol II (AJVPS GORJ)              [0.4952, 0.7422] (Runcu → Stolojani)

  Jiul de vest ('jiul-de-vest'): dcomrepi (mijlociu) loses its duplicate
  fragment geometry → sector member; course_frac Voronoi split 0.35/0.85.

Also: recompute association bboxes for the affected associations from their
FE waters (Cerbul's bbox still contained the Jiu — the map flew to the Jiu
valley on select), clear stale geometryByCounty, fix dmswvndo bbox.
"""
import json
import math
import sys

WATERS = 'public/data/waters.json'
ASSOCS = 'public/data/associations.json'


def haversine(a, b):
    R = 6371
    dlat = math.radians(b[1] - a[1])
    dlon = math.radians(b[0] - a[0])
    h = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(a[1])) * math.cos(math.radians(b[1]))
         * math.sin(dlon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(h))


def bbox_of_geom(geom):
    coords = geom['coordinates']
    if geom['type'] == 'LineString':
        coords = [coords]
    lons = [c[0] for p in coords for c in p]
    lats = [c[1] for p in coords for c in p]
    return [min(lons), min(lats), max(lons), max(lats)]


def chain_line(parts):
    """Chain parts into ONE ordered LineString (source→mouth)."""
    out = []
    for p in parts:
        if out and out[-1] != p[0]:
            out.append(p[0])  # straight bridge segment (documented gap)
        out.extend(p)
    return out


def main():
    with open(WATERS) as f:
        waters = json.load(f)
    by_slug = {w['slug']: w for w in waters}

    # ── 1. Jiu: build the full ordered course (confluence → Danube) ──────────
    jiu = by_slug['qrjybswm']
    parts = jiu['geometry']['coordinates']
    # parts 8..12 = confluence (45.3685) → Bumbești-Jiu; parts 0..7 = Bumbești → Danube.
    # part 13 is a disconnected oxbow fragment near Filiași — drop it.
    chain = chain_line([parts[i] for i in (8, 9, 10, 11, 12, 0, 1, 2, 3, 4, 5, 6, 7)])
    jiu_course = {'type': 'LineString', 'coordinates': chain}
    print(f'jiu course: {len(chain)} pts, bbox {bbox_of_geom(jiu_course)}')

    # boundary fractions (computed from localities + county polygons)
    P = 0.0160   # Valea Polatiște confluence / Hunedoara-Gorj border
    B = 0.1267   # Bumbești-Jiu (Gorj contract start)
    T = 0.4887   # Gorj/Dolj border (Țânțăreni)

    # qrjybswm — AJVPS GORJ — geometry owner
    jiu['geometry'] = jiu_course
    jiu['bbox'] = bbox_of_geom(jiu_course)
    jiu['riverGroup'] = 'jiu'
    jiu['sectorStart'] = B
    jiu['sectorEnd'] = T
    jiu['course_frac'] = round((B + T) / 2, 4)
    jiu.pop('geometryByCounty', None)

    # fanvixkg — Râul Jiul Inferior (Pro Pescar) — geometry-less sector member
    fan = by_slug['fanvixkg']
    fan['geometry'] = None
    fan['bbox'] = None
    fan['riverGroup'] = 'jiu'
    fan['sectorStart'] = 0.0
    fan['sectorEnd'] = P
    fan['course_frac'] = round(P / 2, 4)
    fan.pop('geometryByCounty', None)

    # anpa-anpa-0280 — Râul Jiu și afluenții săi (AJVPS DOLJ) — geometry-less
    dolj = by_slug['anpa-anpa-0280']
    dolj['riverGroup'] = 'jiu'
    dolj['sectorStart'] = T
    dolj['sectorEnd'] = 1.0
    dolj['course_frac'] = round((T + 1) / 2, 4)
    dolj.pop('geometryByCounty', None)

    # NEW: Romsilva Jiu (Direcția Silvică Gorj) — 30 km HD border → Bumbești-Jiu
    if 'anpa-romsilva-0239' not in by_slug:
        waters.append({
            'slug': 'anpa-romsilva-0239',
            'name': 'Râul Jiu',
            'judet': 'Gorj',
            'type': 'ape',
            'subtype': 'rau',
            'limite': 'Limita jud. HD - localitatea Bumbești Jiu',
            'dimensiune': '30 Km',
            'pescuit_interzis': False,
            'referinta': ('Administrat de RNP-Romsilva – ape de munte în administrare directă '
                          '(Protocol 12935/LAV/17.09.2013, ANEXA 1 – Lista habitatelor piscicole '
                          'naturale din apele de munte); O.S. D.S. Gorj'),
            'coordinates': None,
            'driving': None,
            'bbox': None,
            'asociatie': {
                'name': 'Direcția Silvică Gorj',
                'name_long': 'Direcția Silvică Gorj – Regia Națională a Pădurilor Romsilva',
                'slug': 'directia-silvica-gorj',
            },
            'source': 'anpa_romsilva',
            'source_detail': 'romsilva_map:t_5f5f2cce',
            'geometry': None,
            'riverGroup': 'jiu',
            'course_frac': round((P + B) / 2, 4),
            'sectorStart': P,
            'sectorEnd': B,
            'mainCourse': True,
        })
        print('added Romsilva Jiu water (anpa-romsilva-0239)')

    # ── 2. Sohodol: dedupe + order Sohodol I course, sector-split with II ────
    soh = by_slug['2yxhr1b0']
    sparts = soh['geometry']['coordinates']
    # unique parts: 2(C),4(E),1(B),3(D),0(A) chain source(45.28)→mouth(44.96); 5..9 duplicates
    unique = [sparts[2], sparts[4], sparts[1], sparts[3], sparts[0]]
    soh_course = {'type': 'LineString', 'coordinates': chain_line(unique)}
    print(f'sohodol course: {len(soh_course["coordinates"])} pts, bbox {bbox_of_geom(soh_course)}')
    R = 0.4952   # Runcu / DN67D bridge (Sohodol I ↔ II boundary)
    S = 0.7422   # Stolojani (Sohodol II end)

    soh['geometry'] = soh_course
    soh['bbox'] = bbox_of_geom(soh_course)
    soh['riverGroup'] = 'sohodol'
    soh['sectorStart'] = 0.0
    soh['sectorEnd'] = R
    soh['course_frac'] = round(R / 2, 4)
    soh.pop('geometryByCounty', None)

    soh2 = by_slug['8rd9jm0l']
    soh2['geometry'] = None
    soh2['bbox'] = None
    soh2['riverGroup'] = 'sohodol'
    soh2['sectorStart'] = R
    soh2['sectorEnd'] = S
    soh2['course_frac'] = round((R + S) / 2, 4)
    soh2.pop('geometryByCounty', None)

    # ── 3. Jiul de vest: dcomrepi (mijlociu) loses duplicate geometry ────────
    vest = by_slug['dcomrepi']
    vest['geometry'] = None
    vest['bbox'] = None
    vest['course_frac'] = 0.85   # lower sector (Valea Braia → confluence) — Voronoi approx
    by_slug['6vsle29k']['course_frac'] = 0.35  # upper sector (izvoare → Valea Braia)
    # dmswvndo (Jiul de est) — fix bbox to match its geometry
    est = by_slug['dmswvndo']
    if est.get('geometry'):
        est['bbox'] = bbox_of_geom(est['geometry'])

    # ── 4. Association bboxes for the affected associations ──────────────────
    with open(ASSOCS) as f:
        assocs = json.load(f)
    assoc_by_slug = {a['slug']: a for a in assocs}

    def waters_bbox_union(slug):
        bb = None
        for w in waters:
            if (w.get('asociatie') or {}).get('slug') != slug:
                continue
            b = w.get('bbox')
            if not b:
                continue
            bb = b if bb is None else [min(bb[0], b[0]), min(bb[1], b[1]),
                                       max(bb[2], b[2]), max(bb[3], b[3])]
        return bb

    for slug in ('a-cerbul-carpatin', 'ajvps-gorj', 'pro-pescar'):
        nb = waters_bbox_union(slug)
        if nb and slug in assoc_by_slug:
            print(f'assoc {slug}: bbox {assoc_by_slug[slug].get("bbox")} -> {nb}')
            assoc_by_slug[slug]['bbox'] = nb

    # ── 5. Write (round-trip format: indent=1, ensure_ascii=False, no newline) ──
    with open(WATERS, 'w') as f:
        f.write(json.dumps(waters, indent=1, ensure_ascii=False))
    with open(ASSOCS, 'w') as f:
        f.write(json.dumps(assocs, indent=1, ensure_ascii=False))
    print('written', WATERS, ASSOCS)


if __name__ == '__main__':
    main()
