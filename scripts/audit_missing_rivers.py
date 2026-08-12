#!/usr/bin/env python3
"""Full river audit: find missing rivers + attach OSM geometry to all fixable ones.

Audit (task 1):
  - ANPA list (data/processed/anpa_waters.jsonl) vs public/data/waters.json
  - arebaltapeste list (data/raw/arebaltapeste_probe/snapshot_waters.json) vs waters.json

Matching (tasks 2+3):
  - Improved fuzzy matcher vs the bulk OSM download (data/rivers_osm.geojson):
    * strips generic prefixes (raul/paraul/valea/lacul/balta) from BOTH sides
    * token overlap + prefix + char-level similarity (Rozilei~Rosiliei)
    * prefers relation geometry (full course), else merges all same-name ways
    * COUNTY-AWARE: candidates whose geometry centroid is far from the water's
      judet centroid are penalized (kills the Vrancea 'Bâsca' vs Buzău
      'Bâsca Chiojdului' collision).
    * Conservative: char-level matches require first-token agreement and a
      higher bar, so Cibinul Mare -> belinul mare / Ierul -> fierul are
      rejected.
  - GROUP-AWARE: multi-contract rivers carry one geometry OWNER per riverGroup
    (t_ac697770). Only a group's owner (or the best main-course member when the
    group has none) gets geometry; sector copies stay geometry-free.

Usage: python3 scripts/audit_missing_rivers.py [--write] [--json-report PATH]
"""

import argparse
import difflib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE_WATERS = ROOT / "public" / "data" / "waters.json"
ANPA_FILE = ROOT / "data" / "processed" / "anpa_waters.jsonl"
AREBALTAPESTE_SNAP = ROOT / "data" / "raw" / "arebaltapeste_probe" / "snapshot_waters.json"
OSM_FILE = ROOT / "data" / "rivers_osm.geojson"

PREFIX_RE = re.compile(
    r"^(raul|rau|paraul|parau|valea|vale|lacul|lac|balta|baltile|canalul|canal|izvorul|acumularea|acumulare|garla|japsa)\s+"
)

# Words that denote a SECTOR of a longer river rather than a distinct course.
SECTOR_WORDS = {"superior", "superioara", "mijlociu", "mijlocie", "inferior",
                "inferioara", "montan", "montana", "mare", "mica", "mic", "nou",
                "noua", "vechi", "veche", "i", "ii", "iii", "iv", "v", "vi",
                "vii", "viii", "a", "b", "c", "de", "cu", "si", "sau", "ale",
                "afluentii", "afluenti", "superioare", "inferioare", "mijlocii",
                "marele", "micul", "mica", "curs", "principal", "obarsia",
                "izvoare", "izvoarele", "cuanfluentii"}

# Noise tokens allowed on the OSM side of a prefix match (English/Romanian
# descriptive words that don't identify the river itself).
NOISE_WORDS = {"river", "stream", "rau", "raul", "paraul", "parau", "valea", "val"}


def norm(s: str) -> str:
    """Lowercase, strip diacritics, collapse punctuation/whitespace.

    Parenthetical annotations ('Râul Nădrag (Valea Nădragului)') are
    stripped entirely — they explain the same river, not a distinct one.
    """
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"[()\[\]\"'.,;:!?\-–—]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def core(name: str) -> str:
    """Normalized name with generic water-type prefix stripped."""
    n = norm(name)
    return PREFIX_RE.sub("", n, count=1).strip()


PREFIX_LEAD = ("raul ", "rau ", "paraul ", "parau ", "valea ", "vale ", "lacul ",
               "lac ", "balta ", "baltile ", "canalul ", "canal ", "izvorul ",
               "acumularea ", "acumulare ", "garla ", "japsa ")

# Water-type prefixes that all denote RIVER/STREAM courses and are therefore
# interchangeable when matching (ANPA writes 'Râul X', OSM often 'Pârâul X'
# or bare 'X'). Cross-type rejection still applies vs valea/lac/balta/canal.
RIVER_PREFIXES = {"raul", "rau", "paraul", "parau"}


def type_prefix(name: str) -> str | None:
    """Leading water-type prefix of the RAW name, or None.

    'Râul Mare' -> 'raul'; 'Valea Mare' -> 'valea'. Used to reject cross-type
    matches (Râul Mare must NOT match Valea Mare — the prefix strip alone
    collapses both to 'mare', and 'Valea Mare' is an extremely common generic
    stream name). 'Râul X' vs 'Pârâul X' are BOTH river-type and match.
    """
    n = norm(name)
    for p in PREFIX_LEAD:
        if n.startswith(p):
            return p.strip()
    return None


def same_water_type(a: str | None, b: str | None) -> bool:
    """True when two type prefixes denote the same water kind.

    rau/raul/parau/paraul are all river-type and interchangeable; anything
    else must match exactly; None (no prefix) matches anything.
    """
    if a is None or b is None:
        return True
    if a in RIVER_PREFIXES and b in RIVER_PREFIXES:
        return True
    return a == b


def strip_article_variants(tokens: list[str]) -> list[list[str]]:
    """All definite-article-stripped variants of the token list.

    Romanian river names carry the masculine definite article on the first
    (river-name) token in several shapes while OSM uses the bare form:
      'Cibinul Mare'  -> 'Cibin'      (strip 'ul')
      'Săcuieul'      -> 'Săcuieu'    (strip 'l')
      'Pian' / OSM 'Pianu'            (OSM kept a trailing 'u')
      'Ierul'         -> 'Ier'
    Returns [raw, stripped-ul, stripped-l, stripped-u] with duplicates
    removed. Guards keep short names ('Tur', 'Mal') and non-article endings
    ('Chechișel'->'Chechișe' never equals 'Chechiș') safe.
    """
    if not tokens:
        return [tokens]
    t = tokens[0]
    variants = {tuple(tokens)}
    if len(t) >= 5 and t.endswith("ul"):
        # 'Gurghiul' -> 'gurghi' (strip 'ul') AND 'gurghiu' (strip 'l'):
        # vowel-ending nouns take only '-l' as the definite article, so the
        # bare form retains the final 'u'.
        s = t[:-2]
        if len(s) >= 3:
            variants.add(tuple([s, *tokens[1:]]))
        s2 = t[:-1]
        if len(s2) >= 3 and s2 != s:
            variants.add(tuple([s2, *tokens[1:]]))
    if len(t) >= 5 and t.endswith("l") and t[-2] in "aeiou" and not t.endswith("ul"):
        s = t[:-1]
        if len(s) >= 3:
            variants.add(tuple([s, *tokens[1:]]))
    if len(t) >= 5 and t.endswith("u") and t[-2] not in "aeiou":
        s = t[:-1]
        if len(s) >= 3:
            variants.add(tuple([s, *tokens[1:]]))
    return [list(v) for v in variants]


def is_sector_name(name: str) -> bool:
    """True when the name is a sector of a river (has superior/mijlociu/...)."""
    c = core(name)
    tokens = set(c.split())
    return bool(tokens & SECTOR_WORDS)


def token_sim(a: str, b: str) -> float:
    ta, tb = a.split(), b.split()
    if not ta or not tb:
        return 0.0
    return len(set(ta) & set(tb)) / max(len(ta), len(tb))


def char_sim(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def first_token_ok(wfirst: str, ifirst: str) -> bool:
    """First (discriminating) token must agree.

    Allowed: exact equality, or one being the other plus only the Romanian
    definite-article suffix 'ul'/'l' (Timișu ~ Timișul). This rejects distinct
    rivers (Chechiș ~ Chechișel, Ierul ~ Fierul, Bucureasa ~ Cucureasa,
    Cibinul ~ Belinul, Avrigul ~ Arieșul).
    """
    if wfirst == ifirst:
        return True
    if len(wfirst) >= 5 and len(ifirst) >= 5:
        if ifirst.startswith(wfirst) and ifirst[len(wfirst):] in ("ul", "l"):
            return True
        if wfirst.startswith(ifirst) and wfirst[len(ifirst):] in ("ul", "l"):
            return True
    return False


def geom_centroid(g: dict) -> tuple[float, float] | None:
    """Approx centroid (lon, lat) of a geometry (LineString/MultiLineString)."""
    try:
        coords = g["coordinates"]
        if g["type"] == "MultiLineString":
            pts = [p for part in coords for p in part]
        else:
            pts = coords
        if not pts:
            return None
        n = len(pts)
        return (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n)
    except Exception:
        return None


def build_county_centroids(waters: list[dict]) -> dict[str, tuple[float, float]]:
    """judet -> approx centroid from waters that HAVE geometry/bbox/coordinates."""
    sums: dict[str, list[tuple[float, float]]] = {}
    for w in waters:
        j = w.get("judet")
        if not j:
            continue
        pt = None
        g = w.get("geometry")
        if g:
            pt = geom_centroid(g)
        if pt is None and w.get("bbox"):
            b = w["bbox"]
            pt = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
        if pt is None and w.get("coordinates"):
            c = w["coordinates"]
            if len(c) >= 2:
                pt = (c[0], c[1])
        if pt:
            sums.setdefault(j, []).append(pt)
    out = {}
    for j, pts in sums.items():
        out[j] = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
    return out


# Curated overrides: water name (normalized, prefix-stripped) -> OSM index
# name, for well-known same-river pairs where a geographic qualifier on the
# ANPA side ('Moldovenesc', 'Gârcin', 'Aușel Voievodul', ...) is NOT a sector
# word and the generic ladder rejects them. Each is still validated against
# the county centroid before geometry is attached (so a wrong-county OSM
# twin is never used). Keys are norm(name) with the leading 'raul ' etc.
# stripped, exactly like core().
MANUAL_OVERRIDES = {
    # Slănic Moldova (Bacău) == OSM Slănic cluster in Bacău
    "slanic moldova": "slanic",
    # Oituzul Moldovenesc (Bacău) == OSM Oituz
    "oituzul moldovenesc": "oituz",
    # Doftana Gârcin (Brașov) == OSM Doftana Ardeleană / Doftana (Brașov)
    "doftana garcin": "doftana",
    # Taia Aușel Voievodul (Hunedoara) == OSM Taia
    "taia ausel voievodul": "taia",
    # Bistra Ardealului, mijlociu (Caraș-Severin) == OSM Bistra (the CS one)
    "bistra ardealului mijlociu": "bistra",
    # Strâmbu Băiuț (Maramureș) == OSM Strâmbu (the Maramureș cluster)
    "strambu baiut": "strambu",
    # Plescioara (Vâlcea) == OSM Valea Plescioarei (genitive of same name)
    "plescioara": "valea plescioarei",
    # Rudărie (Caraș-Severin) == OSM Valea Rudăriei (genitive of same name)
    "rudarie": "valea rudariei",
}


def county_penalty_for(geom: dict, ccent) -> float:
    """Reuse the county-penalty scoring without the water context."""
    if not ccent:
        return 0.0
    c = geom_centroid(geom)
    if not c:
        return 0.0
    d = ((c[0] - ccent[0]) ** 2 + (c[1] - ccent[1]) ** 2) ** 0.5
    if d <= 1.0:
        return -(0.001 * (1.0 - d))
    if d <= 2.0:
        return 0.15
    return 0.3


def try_manual_override(water: dict, osm_geo_by_norm: dict,
                        county_centroids: dict) -> tuple[str | None, dict | None, float, str]:
    """Curated fallback for known same-river pairs the generic ladder rejects."""
    key = core(water.get("name", ""))
    target = MANUAL_OVERRIDES.get(key)
    if not target:
        return None, None, 0.0, "no-override"
    geoms_list = osm_geo_by_norm.get(target)
    if not geoms_list:
        return None, None, 0.0, "override-no-osm"
    ccent = county_centroids.get(water.get("judet") or "") if water.get("judet") else None
    best, best_score = None, -1.0
    for geom in geoms_list:
        score = 1.0 - county_penalty_for(geom, ccent)
        if score > best_score:
            best_score, best = score, geom
    if best and best_score >= 0.72:
        return target, best, best_score, "override"
    return None, None, 0.0, "override-county-reject"


def best_osm_match(water: dict, osm_geo_by_norm: dict,
                   county_centroids: dict[str, tuple[float, float]]) -> tuple[str | None, dict | None, float, str]:
    """Return (matched_norm_name, geometry, score, how) for the best OSM candidate.

    Conservative ladder (comparing CORES):
      1. exact                          -> 1.0
      2. token-prefix where the extra tokens are all SECTOR words
         ('Râul Moldova II' -> 'moldova'; 'Bâsca Chiojdului' vs bare 'Bâsca'
         is REJECTED because 'chiojdului' is not a sector word)
      3. token overlap >= 0.6 with >=2 shared tokens (or exact single token)
      4. char-level: first token EQUAL AND full-core sim >= 0.87
         (Rozilei~Rosiliei 0.89 passes; Ierul~Fierul rejected: first tokens
         differ; Cibinul~Belinul 0.83 rejected; Chechiș~Chechișel 0.875 and
         Bucureasa~Cucureasa 0.889 rejected: first tokens differ)
    County: candidates > COUNTY_MAX_DEG from the water's judet centroid are
    heavily penalized (still listed when nothing else matches, so we can see
    them in the report).
    A curated MANUAL_OVERRIDES fallback runs after the ladder for
    well-known pairs the qualifier-word rule rejects.
    """
    wc = core(water.get("name", ""))
    if not wc:
        return None, None, 0.0, "no-core"
    wt = wc.split()
    wfirst = wt[0]

    judet = water.get("judet") or ""
    ccent = county_centroids.get(judet) if judet else None

    def county_penalty(geom: dict) -> float:
        """Continuous penalty + tiebreak.

        Clusters within 1.0 deg of the county centroid get no penalty (plus a
        tiny distance bonus so the CLOSEST cluster wins ties, e.g. Mehedinți
        Cerna vs Hunedoara Cerna). Farther clusters are penalized.
        """
        if not ccent:
            return 0.0
        c = geom_centroid(geom)
        if not c:
            return 0.0
        d = ((c[0] - ccent[0]) ** 2 + (c[1] - ccent[1]) ** 2) ** 0.5
        if d <= 1.0:
            # tiebreaker: closest cluster wins by a hair
            return -(0.001 * (1.0 - d))
        if d <= 2.0:
            return 0.15
        return 0.3

    best, best_score, best_how = None, 0.0, "no-match"
    wprefix = type_prefix(water.get("name", ""))
    # article-stripped water token variants: 'Cibinul Mare' -> [cibin, mare]
    wt_variants = strip_article_variants(wt)
    for idx_name, geoms_list in osm_geo_by_norm.items():
        ic = core(idx_name)
        if not ic:
            continue
        # Cross-type rejection: 'Râul Mare' must not match OSM 'Valea Mare'
        # (both strip to 'mare'); 'Râul X' vs 'Pârâul X' are both river-type.
        iprefix = type_prefix(idx_name)
        if not same_water_type(wprefix, iprefix):
            continue
        it = ic.split()
        ifirst = it[0]
        it_variants = strip_article_variants(it)

        # For each candidate geometry cluster, compute its own county penalty
        # and pick the best one for this name.
        name_best, name_score = None, -1.0
        for geom in geoms_list:
            pen = county_penalty(geom)
            # try every (water-variant x osm-variant) token pairing and keep
            # the highest ladder score
            pair_score = -1.0
            for wv in wt_variants:
                for iv in it_variants:
                    score = 0.0
                    wv_len, iv_len = len(wv), len(iv)
                    # 1. exact
                    if iv == wv:
                        score = 1.0 - pen
                    # 2. token-prefix with sector-only extras:
                    #    'Cibinul Mare' vs 'Cibin' -> [cibin, mare] vs [cibin]
                    #    'Ierul' vs 'Ier' -> [ier] vs [ier] (handled by rule 3)
                    elif wv_len != iv_len:
                        shorter, longer = (wv, iv) if wv_len < iv_len else (iv, wv)
                        if shorter and all(x == y for x, y in zip(shorter, longer)):
                            extra = set(longer[len(shorter):])
                            if extra and extra <= (SECTOR_WORDS | NOISE_WORDS):
                                ratio = len(shorter) / len(longer)
                                score = 0.85 + 0.10 * ratio - pen
                    # 3. token overlap (article-aware on both sides)
                    else:
                        ts = token_sim(" ".join(wv), " ".join(iv))
                        shared = set(wv) & set(iv)
                        if (len(shared) >= 2 or (len(shared) == 1 and wv_len == 1 and iv_len == 1)) and ts >= 0.6:
                            score = ts - pen
                    if score > pair_score:
                        pair_score = score
            # 4. char-level (only when first token agrees)
            if pair_score <= 0 and first_token_ok(wfirst, ifirst):
                cs = char_sim(wc, ic)
                if cs >= 0.85:
                    pair_score = cs - pen

            if pair_score > name_score:
                name_score = pair_score
                name_best = geom

        if name_best is not None and name_score > best_score:
            best, best_score = (idx_name, name_best), name_score
    # recompute "how" for the winner
    if best:
        winnername = best[0]
        ic = core(winnername)
        if ic == wc:
            best_how = "exact"
        elif first_token_ok(wt[0], ic.split()[0]) and char_sim(wc, ic) >= 0.85:
            best_how = f"char{char_sim(wc, ic):.2f}"
        elif len(wt) != len(ic.split()):
            best_how = "prefix"
        else:
            best_how = f"token{token_sim(wc, ic):.2f}"

    if best and best_score >= 0.72:
        return best[0], best[1], best_score, best_how
    return None, None, 0.0, "below-threshold"


def load_osm_index() -> tuple[dict, dict]:
    """Return (name_index: norm_name -> [geometry-ids], geoms: id -> geometry).

    NOTE: the bulk OSM file contains DUPLICATE way ids (the same way appears
    both with and without tags in different overpass result chunks). The dict
    must keep the TAGGED copy: an id seen first without tags must not be
    overwritten by a later tag-less occurrence, and a tagged occurrence must
    win over an earlier tag-less one. Otherwise real names (e.g. 'Vasluieț',
    way 27568976) silently vanish from the index.
    """
    data = json.loads(OSM_FILE.read_text(encoding="utf-8"))
    nodes = {
        el["id"]: (el.get("lat"), el.get("lon"))
        for el in data.get("elements", [])
        if el["type"] == "node" and "lat" in el
    }
    ways = {}
    for el in data.get("elements", []):
        if el["type"] != "way":
            continue
        coords = [[nodes[n][1], nodes[n][0]] for n in el.get("nodes", []) if n in nodes]
        if len(coords) < 2:
            continue
        w = {
            "kind": "way",
            "geometry": {"type": "LineString", "coordinates": coords},
            "name": el.get("tags", {}).get("name", ""),
        }
        # duplicate id: prefer the copy that carries a name (or the first one)
        prev = ways.get(el["id"])
        if prev is None or (not prev.get("name") and w.get("name")):
            ways[el["id"]] = w
    rel_geoms = {}
    for el in data.get("elements", []):
        if el["type"] != "relation":
            continue
        coords = [ways[m["ref"]]["geometry"]["coordinates"] for m in el.get("members", [])
                  if m["type"] == "way" and m["ref"] in ways]
        if coords:
            rel_geoms[el["id"]] = {
                "kind": "relation",
                "geometry": {"type": "MultiLineString", "coordinates": coords},
                "name": el.get("tags", {}).get("name", ""),
            }
    all_geoms = {**ways, **rel_geoms}
    name_index: dict[str, list[int]] = {}
    for gid, g in all_geoms.items():
        n = norm(g["name"])
        if n:
            name_index.setdefault(n, []).append(gid)
    return name_index, all_geoms


def combine_geoms(ids: list[int], geoms: dict) -> dict | None:
    """Merge geometries: prefer a relation, else merge all LineStrings."""
    for gid in ids:
        g = geoms.get(gid)
        if g and g.get("kind") == "relation":
            return g["geometry"]
    parts = []
    for gid in ids:
        g = geoms.get(gid)
        if g and g["geometry"]["type"] == "LineString":
            parts.append(g["geometry"]["coordinates"])
    if len(parts) == 1:
        return {"type": "LineString", "coordinates": parts[0]}
    if len(parts) > 1:
        return {"type": "MultiLineString", "coordinates": parts}
    return None


def _part_endpoints(part: list) -> tuple[tuple[float, float], tuple[float, float]]:
    return (tuple(part[0]), tuple(part[-1]))


def cluster_parts(parts: list, max_gap_deg: float = 0.06) -> list[list]:
    """Group LineString parts into spatially-connected clusters.

    Same-name waterways in DIFFERENT basins (e.g. Gorj Bistrița vs Moldavian
    Bistrița, Vrancea Bâsca vs Buzău Bâsca) must NOT be merged into one
    MultiLineString — the frontend would render a river that jumps across
    the country. Two parts belong to the same cluster when an endpoint of one
    is within max_gap_deg of an endpoint of another (OSM splits rivers at
    way boundaries with shared junction nodes).
    """
    if len(parts) <= 1:
        return [parts]
    clusters: list[list] = []
    for part in parts:
        eps = _part_endpoints(part)
        placed = False
        for cl in clusters:
            for existing in cl:
                eeps = _part_endpoints(existing)
                for a in eps:
                    for b in eeps:
                        if abs(a[0] - b[0]) <= max_gap_deg and abs(a[1] - b[1]) <= max_gap_deg:
                            cl.append(part)
                            placed = True
                            break
                    if placed:
                        break
                if placed:
                    break
            if placed:
                break
        if not placed:
            clusters.append([part])
    return clusters


def make_cluster_geoms(ids: list[int], geoms: dict) -> list[dict]:
    """All spatially-distinct geometries for a name.

    Collects parts from relations (MultiLineString) AND ways, then clusters
    them spatially. Same-name rivers in different basins (Vâlcea Cerna vs
    Hunedoara Cerna, Gorj Bistrița vs Moldavian Bistrița) end up as separate
    clusters. Returns list of {"type": LineString|MultiLineString,
    "coordinates": ...}.
    """
    parts = []
    for gid in ids:
        g = geoms.get(gid)
        if not g:
            continue
        gt = g["geometry"]["type"]
        if gt == "LineString":
            parts.append(g["geometry"]["coordinates"])
        elif gt == "MultiLineString":
            parts.extend(g["geometry"]["coordinates"])
    if not parts:
        return []
    clusters = cluster_parts(parts)
    out = []
    for cl in clusters:
        if len(cl) == 1:
            out.append({"type": "LineString", "coordinates": cl[0]})
        else:
            out.append({"type": "MultiLineString", "coordinates": cl})
    return out


def group_geometry_targets(waters: list[dict]) -> tuple[list[dict], set[str]]:
    """Decide which waters may receive geometry.

    Returns (candidates, skipped_slugs):
    - Any water whose riverGroup ALREADY has a member with geometry is NOT a
      candidate (its group owner renders the course; sector copies resolve by
      click).
    - Groups with NO geometry: the best main-course member (plain name,
      no superior/mijlociu/inferior qualifier) is the candidate.
    - Waters without riverGroup are candidates (single-course rivers).
    """
    from collections import defaultdict
    groups = defaultdict(list)
    for w in waters:
        if w.get("riverGroup"):
            groups[w["riverGroup"]].append(w)

    candidates, skipped = [], set()
    for w in waters:
        gk = w.get("riverGroup")
        if not gk:
            candidates.append(w)
            continue
        members = groups[gk]
        if any(m.get("geometry") for m in members):
            skipped.add(w["slug"])
            continue
        # No owner yet: only the "main" member becomes the candidate
        plain = [m for m in members if not is_sector_name(m.get("name", ""))]
        chosen = plain[0] if plain else members[0]
        if w["slug"] == chosen["slug"]:
            candidates.append(w)
        else:
            skipped.add(w["slug"])
    return candidates, skipped


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="write changes back to waters.json")
    ap.add_argument("--json-report", type=str, help="write audit report JSON to this path")
    args = ap.parse_args()

    fe = json.loads(FE_WATERS.read_text(encoding="utf-8"))
    fe_by_norm = {norm(x["name"]): x for x in fe}

    # ---- AUDIT: source lists vs waters.json ------------------------------
    anpa = [json.loads(l) for l in ANPA_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    snap = json.loads(AREBALTAPESTE_SNAP.read_text(encoding="utf-8"))
    snap = snap if isinstance(snap, list) else snap.get("waters", [])

    anpa_missing = [w for w in anpa if norm(w["water_name"]) not in fe_by_norm]
    snap_missing = [s for s in snap if norm(s["name"]) not in fe_by_norm]
    print(f"[audit] ANPA waters missing from waters.json: {len(anpa_missing)}")
    for w in anpa_missing:
        print(f"   {w['id']} {w['water_name']} ({w['county']})")
    print(f"[audit] arebaltapeste waters missing from waters.json: {len(snap_missing)}")
    for s in snap_missing:
        print(f"   {s['slug']} {s['name']} ({s['judet']})")

    # ---- MATCH -------------------------------------------------------------
    print("[match] loading OSM index...")
    name_index, geoms = load_osm_index()
    print(f"[match] OSM index: {len(name_index)} named waterways, {len(geoms)} geometries")

    osm_geo_by_norm: dict[str, list[dict]] = {}
    for n, ids in name_index.items():
        gs = make_cluster_geoms(ids, geoms)
        if gs:
            osm_geo_by_norm[n] = gs

    county_centroids = build_county_centroids(fe)
    print(f"[match] county centroids: {len(county_centroids)} counties")

    candidates, skipped = group_geometry_targets(fe)
    candidates = [x for x in candidates if x.get("subtype") == "rau" and not x.get("geometry")]
    print(f"[match] {len(candidates)} river candidates to try ({len(skipped)} skipped as grouped copies)")

    matched, unmatched = [], []
    for w in candidates:
        best, geom, score, how = best_osm_match(w, osm_geo_by_norm, county_centroids)
        if not best:
            best, geom, score, how = try_manual_override(w, osm_geo_by_norm, county_centroids)
        if best and geom:
            w["geometry"] = geom
            w["source_detail"] = f"audit_match:{how}"
            w["source"] = w.get("source") or "osm_bulk"
            matched.append((w["name"], best, score, how))
        else:
            unmatched.append(w["name"])
    print(f"[match] matched geometry for {len(matched)}/{len(candidates)} rivers")
    for name, osm, score, how in sorted(matched):
        print(f"   {name}  ->  {osm}  ({how})")
    print(f"[match] still no OSM match ({len(unmatched)}):")
    for name in sorted(unmatched):
        print(f"   {name}")

    # ---- REPORT ------------------------------------------------------------
    report = {
        "anpa_total": len(anpa),
        "anpa_missing": [{"id": w["id"], "name": w["water_name"], "county": w["county"]} for w in anpa_missing],
        "arebaltapeste_total": len(snap),
        "arebaltapeste_missing": [{"slug": s["slug"], "name": s["name"], "judet": s["judet"]} for s in snap_missing],
        "candidates_tried": len(candidates),
        "grouped_copies_skipped": len(skipped),
        "matched": [{"name": n, "osm": o, "score": round(s, 3), "how": h} for n, o, s, h in matched],
        "unmatched": sorted(unmatched),
    }
    if args.json_report:
        Path(args.json_report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[report] wrote {args.json_report}")

    if args.write:
        FE_WATERS.write_text(json.dumps(fe, ensure_ascii=False, indent=1), encoding="utf-8")
        with_geom = sum(1 for x in fe if x.get("geometry"))
        print(f"[write] waters.json: {len(fe)} waters, {with_geom} with geometry")


if __name__ == "__main__":
    main()
