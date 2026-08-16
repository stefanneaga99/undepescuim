#!/usr/bin/env python3
"""t_45a0beae / A1 — dedupe same-body entries in the uncontracted overlays.

Baseline found 4 river + 9 lake duplicate SLUGS in
public/data/uncontracted_rivers.json / uncontracted_lakes.json. Investigation
shows each "duplicate" is actually the SAME water body/course emitted twice by
the OSM extract (the same river mapped under two way segments with the same
name; the same pond mapped as both a way and a relation polygon):

  rivers: Galbena (Hunedoara), Ghimbășel (Brașov), Râșca Mare (Cluj),
          Бирда (Timiș) — the smaller course lies 100% on the larger one.
  lakes:  "Iaz neidentificat" ×7 (Iași), Lacul Dobroești (Ilfov),
          Lacul Neptun I (Constanța) — polygon overlap >= 0.999 of the
          smaller body.

Fix: drop the smaller copy (deterministic: sorted by lengthKm/areaHa, keep
largest; ties by slug order). Also transliterate the Cyrillic name "Бирда"
to its Romanian form "Birda" (Romanian water names are Latin-script by law;
the OSM way on the Serbian side of the border carries the Cyrillic name).

The BUILD SCRIPTS are patched separately (build_uncontracted_rivers.py /
build_uncontracted_lakes.py) so a future rebuild cannot re-emit same-body
duplicates: slugs now include the full bbox + county, and an intra-output
same-body dedupe runs before emit.
"""

from __future__ import annotations

import json
from pathlib import Path

from shapely.geometry import LineString, MultiLineString, Point, shape

ROOT = Path(__file__).resolve().parent.parent
FE_RIVERS = ROOT / "public" / "data" / "uncontracted_rivers.json"
FE_LAKES = ROOT / "public" / "data" / "uncontracted_lakes.json"

# ~90 m in degrees — same epsilon the build scripts use for duplicate tests.
EPS_DEG = 0.0008

# Non-Latin -> Romanian transliteration map. Romanian water names are
# Latin-script by law (plan §5.3); OSM leaks Cyrillic names for border
# rivers mapped from the Serbian/Hungarian/Ukrainian side. Only the
# well-known Romanian-named rivers are mapped here; obscure foreign
# streams stay as-is and are FLAGGED by audit_integrity as a review item.
TRANSLITERATE = {
    "Бирда": "Birda",
    # Danube (RO name on the Serbian/Ukrainian bank variants)
    "Dunărea - Дунав": "Dunărea",
    "Dunărea - Дунай": "Dunărea",
    "Дунав": "Dunărea",
    "Дунав/Dunărea": "Dunărea",
    # Prut (RO name)
    "Prut / Прут": "Prut",
    # Aranca / Zlatica (Rom. Aranca)
    "Aranca / Златица": "Aranca",
    "Златица": "Aranca",
    # Caraș (Rom. Caraș)
    "Караш": "Caraș",
    # Vilia (Rom. Vilia)
    "Râul Vilia - Вілія": "Râul Vilia",
}


def frac_small_on_big(gs, gb):
    """Fraction of the smaller line's sampled points within EPS_DEG of the
    larger course — 1.0 means the small feature IS a sub-segment of the big."""
    coords = [p for part in (gs.geoms if gs.geom_type == "MultiLineString" else [gs])
              for p in part.coords]
    if len(coords) < 2:
        return 0.0
    sample = coords[:: max(1, len(coords) // 40)]
    near = sum(1 for p in sample if gb.distance(Point(p)) <= EPS_DEG)
    return near / len(sample)


def dedupe_overlay(entries: list[dict], kind: str) -> tuple[list[dict], list[dict]]:
    """Return (kept, dropped) where same-body duplicates collapse to the
    largest entry. Slugs may still collide afterwards only when two features
    are genuinely distinct — the caller reports those as hard errors."""
    # group by slug first (the known collision set)
    from collections import defaultdict
    by_slug: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        by_slug[e["slug"]].append(e)

    kept: list[dict] = []
    dropped: list[dict] = []
    for slug, group in by_slug.items():
        if len(group) == 1:
            kept.append(group[0])
            continue
        if kind == "rau":
            group.sort(key=lambda e: -(e.get("lengthKm") or 0))
            big = group[0]
            for small in group[1:]:
                gs = shape(small["geometry"])
                gb = shape(big["geometry"])
                frac = frac_small_on_big(gs, gb)
                if frac >= 0.9:
                    dropped.append({**small, "_dup_of": big["slug"], "_overlap_frac": frac})
                else:
                    # distinct courses sharing a slug hash — must not happen
                    # after the bbox-in-hash fix; keep with a discriminator.
                    small["slug"] = f"{small['slug']}-{small.get('judet', 'x')[:3]}"
                    kept.append(small)
            kept.append(big)
        else:  # lac
            group.sort(key=lambda e: -(e.get("areaHa") or 0))
            big = group[0]
            gb = shape(big["geometry"])
            for small in group[1:]:
                gs = shape(small["geometry"])
                try:
                    inter = gb.intersection(gs)
                    frac = inter.area / min(gb.area, gs.area) if min(gb.area, gs.area) > 0 else 0.0
                except Exception:
                    frac = 0.0
                if frac >= 0.9:
                    dropped.append({**small, "_dup_of": big["slug"], "_overlap_frac": round(frac, 3)})
                else:
                    small["slug"] = f"{small['slug']}-{small.get('judet', 'x')[:3]}"
                    kept.append(small)
            kept.append(big)
    return kept, dropped


def dedupe_same_name_county(entries: list[dict], kind: str) -> tuple[list[dict], list[dict]]:
    """Second pass (t_45a0beae): same-body duplicates that carry DIFFERENT
    slugs (same name + county, geometry overlap >= 0.9 of the smaller) — the
    same OSM double-mapping as the slug collisions, just without the hash
    collision (Bahlui Iași 409 km vs 61.9 km, Balta Arcerului Dolj 9 ha vs
    165 ha, nested 'Iaz neidentificat' polygons). The plan §5.3 classifies
    same-name + same-county + near-identical geometry as DUPLICATE: drop the
    smaller copy, keep the largest per group."""
    from collections import defaultdict
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for e in entries:
        groups[(e["name"], e.get("judet"))].append(e)

    kept: list[dict] = []
    dropped: list[dict] = []
    for key, group in groups.items():
        if len(group) == 1:
            kept.append(group[0])
            continue
        if kind == "rau":
            group.sort(key=lambda e: -(e.get("lengthKm") or 0))
        else:
            group.sort(key=lambda e: -(e.get("areaHa") or 0))
        group_kept: list[dict] = []
        for cand in group:
            gs = shape(cand["geometry"])
            is_dup = False
            for ke in group_kept:
                gb = shape(ke["geometry"])
                if kind == "rau":
                    frac = frac_small_on_big(gs, gb)
                else:
                    try:
                        inter = gb.intersection(gs)
                        frac = inter.area / min(gb.area, gs.area) if min(gb.area, gs.area) > 0 else 0.0
                    except Exception:
                        frac = 0.0
                if frac >= 0.9:
                    dropped.append({**cand, "_dup_of": ke["slug"], "_overlap_frac": round(frac, 3)})
                    is_dup = True
                    break
            if not is_dup:
                group_kept.append(cand)
        kept.extend(group_kept)
    return kept, dropped


def transliterate(entries: list[dict]) -> list[str]:
    """Rename any non-Latin water names; return the list of renames."""
    renames = []
    for e in entries:
        if e.get("name") in TRANSLITERATE:
            old = e["name"]
            e["name"] = TRANSLITERATE[old]
            renames.append(f"{old} -> {e['name']} ({e['slug']})")
    return renames


def main() -> None:
    rivers = json.loads(FE_RIVERS.read_text(encoding="utf-8"))
    lakes = json.loads(FE_LAKES.read_text(encoding="utf-8"))
    print(f"[a1] rivers {len(rivers)}, lakes {len(lakes)}")

    # transliterate FIRST so dedupe sees the final names (Aranca/Златица
    # became the same 'Aranca' name only after renaming — deduping before
    # would miss the pair)
    r_renames = transliterate(rivers)
    l_renames = transliterate(lakes)
    print(f"[a1] transliterations: {r_renames + l_renames or 'none'}")

    r_kept, r_dropped = dedupe_overlay(rivers, "rau")
    l_kept, l_dropped = dedupe_overlay(lakes, "lac")
    # same-body pairs that escaped the slug collision (different slugs)
    r_kept, r_dropped2 = dedupe_same_name_county(r_kept, "rau")
    l_kept, l_dropped2 = dedupe_same_name_county(l_kept, "lac")
    r_dropped += r_dropped2
    l_dropped += l_dropped2
    print(f"[a1] rivers: kept {len(r_kept)}, dropped {len(r_dropped)}")
    for d in r_dropped:
        print(f"     DROP {d['name']} ({d['judet']}) len={d.get('lengthKm')} "
              f"dup_of={d['_dup_of']} frac={d['_overlap_frac']:.2f}")
    print(f"[a1] lakes: kept {len(l_kept)}, dropped {len(l_dropped)}")
    for d in l_dropped:
        print(f"     DROP {d['name']} ({d['judet']}) area={d.get('areaHa')} "
              f"dup_of={d['_dup_of']} frac={d['_overlap_frac']}")

    # determinism: keep the existing sort order (by name)
    r_kept.sort(key=lambda w: w["name"].lower())
    l_kept.sort(key=lambda w: w["name"].lower())

    # hard gate: slug uniqueness must now hold
    from collections import Counter
    r_dups = {s: n for s, n in Counter(x["slug"] for x in r_kept).items() if n > 1}
    l_dups = {s: n for s, n in Counter(x["slug"] for x in l_kept).items() if n > 1}
    if r_dups or l_dups:
        raise SystemExit(f"ABORT: slug collisions remain — rivers {r_dups}, lakes {l_dups}")

    FE_RIVERS.write_text(json.dumps(r_kept, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    FE_LAKES.write_text(json.dumps(l_kept, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"[a1] wrote {FE_RIVERS} ({len(r_kept)}), {FE_LAKES} ({len(l_kept)})")


if __name__ == "__main__":
    main()
