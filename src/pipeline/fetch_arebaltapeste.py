#!/usr/bin/env python3
"""
arebaltapeste.ro API ingest (secondary source) — Phase 3 of the
UndePescuim.ro data pipeline.

Fetches the complete contracted-waters dataset from the site's own REST
backend and normalizes it to JSONL records that mirror the ANPA parser's
output schema (sector_km/sector_ha/sector_unit, name_normalized, county_id),
ready for the Phase 5 merge.

API (verified 2026-08-11 against the probe report):
  * GET https://api.arebaltapeste.ro/api/search?type=ape&limit=100&skip=N
      -> {metadata:{count}, items:[{type:"ape", item:{...}}]}
      THE listing endpoint; paginated. /api/ape is broken (ignores skip).
  * GET https://api.arebaltapeste.ro/api/asociatii?limit=200
      -> {docs:[...], totalDocs, ...}  (82 docs; skip ignored, one call)
  The item shape matches data/raw/arebaltapeste_probe/snapshot_waters.json.

Outputs:
  data/raw/arebaltapeste_probe/snapshot_full.json      — raw 426 waters (API)
  data/raw/arebaltapeste_probe/snapshot_asociatii.json — raw 82 associations
  data/processed/arebaltapeste_waters.jsonl            — one record per water
  data/processed/arebaltapeste_associations.jsonl      — one record per assoc
  data/processed/sources.jsonl                         — idempotent append

Run:  .venv/bin/python src/pipeline/fetch_arebaltapeste.py
      [--offline] [--out DIR] [--schema-version 1.0.0]

Requires: curl_cffi (in the project venv) unless --offline is used.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    from curl_cffi import requests as cffi_requests
except ImportError:  # pragma: no cover
    cffi_requests = None

API_BASE = "https://api.arebaltapeste.ro"
WATERS_PATH = "/api/search"
ASSOC_PATH = "/api/asociatii"
POLITE_DELAY_S = 0.8
PAGE_LIMIT = 100

# --------------------------------------------------------------------------
# Name normalization (shared with parse_anpa.py conventions)
# --------------------------------------------------------------------------
def ascii_fold(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def name_normalized(text: str) -> str:
    return re.sub(r"\s+", " ", ascii_fold(text).lower()).strip()


# --------------------------------------------------------------------------
# dimensiune parsing ("240 Ha", "35 km", "0,24 Ha", "12,4", "-")
# --------------------------------------------------------------------------
DIM_RE = re.compile(r"^([0-9]+(?:[.,][0-9]+)?)\s*(km|ha)?$", re.I)


def parse_dimensiune(raw: str):
    """Return (numeric, unit, sector_raw, flags).

    * "240 Ha" / "35 km" -> (240.0, "ha", "240 Ha", [])
    * "0,24 Ha"          -> (0.24, "ha", "0,24 Ha", [])
    * "0.3"/"12,4"       -> (0.3, None, "0.3", ["dimensiune_no_unit"])
    * "-"                -> (None, None, "-", ["dimensiune_unparsed"])
    """
    value = (raw or "").strip()
    if not value:
        return None, None, None, ["dimensiune_missing"]
    m = DIM_RE.match(value)
    if not m:
        return None, None, value, ["dimensiune_unparsed"]
    try:
        num = float(m.group(1).replace(",", "."))
    except ValueError:
        return None, None, value, ["dimensiune_unparsed"]
    unit = m.group(2).lower() if m.group(2) else None
    flags = [] if unit else ["dimensiune_no_unit"]
    return num, unit, value, flags


# --------------------------------------------------------------------------
# subtype -> pipeline water_type
# --------------------------------------------------------------------------
SUBTYPE_TO_TYPE = {
    "lac": "lake",
    "rau": "river",
    "balti": "pond",  # private ponds are a separate category (type=balti)
}

# --------------------------------------------------------------------------
# association type from name pattern (probe report breakdown:
# AJVPS/AJPS 30, APS 21, AVPS 16, Direcția Silvică/Romsilva 14, ANPA 1)
# --------------------------------------------------------------------------
def association_type(name: str) -> str:
    n = name_normalized(name)
    if n.startswith("anpa"):
        return "anpa"
    if "silvica" in n or "romsilva" in n or n.startswith("d.s.") or n.startswith("ds "):
        return "ds"
    if n.startswith("ajvps") or n.startswith("ajps"):
        return "ajvps"
    if n.startswith("avps"):
        return "avps"
    if n.startswith("aps"):
        return "aps"
    return "other"


# --------------------------------------------------------------------------
# county lookup (counties.json by ASCII name)
# --------------------------------------------------------------------------
def county_lookup() -> dict:
    path = Path(__file__).resolve().parents[2] / "data" / "raw" / "counties.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {c["name_ascii"].lower(): c["id"] for c in data}
    except (OSError, json.JSONDecodeError, KeyError):
        return {}


def is_contracted_referinta(referinta: str) -> bool:
    """ANPA's 'necontractate' list (13 records) is the only non-contracted
    provenance tag in this dataset; Romsilva / ProPescar waters are
    administered (contracted) but come from separate lists."""
    return "necontractate" not in (referinta or "").lower()


# --------------------------------------------------------------------------
# Fetchers
# --------------------------------------------------------------------------
def http_get(url: str, params: dict, impersonate: str = "chrome"):
    if cffi_requests is None:
        raise RuntimeError("curl_cffi is not installed; run .venv/bin/pip install curl_cffi")
    r = cffi_requests.get(url, params=params, impersonate=impersonate, timeout=30)
    r.raise_for_status()
    return r.json()


def fetch_waters(raw_dir: Path) -> list:
    """Paginate /api/search?type=ape until we have all records."""
    seen = {}
    skip = 0
    total = None
    while True:
        j = http_get(API_BASE + WATERS_PATH, {"type": "ape", "limit": PAGE_LIMIT, "skip": skip})
        meta = j.get("metadata") or {}
        if total is None:
            total = meta.get("count")
            print(f"waters total from API: {total}", file=sys.stderr)
        items = j.get("items") or []
        for it in items:
            item = it.get("item") or {}
            seen[item.get("id")] = item
        print(f"  fetched skip={skip} -> {len(items)} items ({len(seen)} unique)", file=sys.stderr)
        if not items:
            break
        # The API hard-caps page size at 20 regardless of `limit`, so advance
        # by the actual page size, not by PAGE_LIMIT.
        skip += len(items)
        if total is not None and len(seen) >= total:
            break
        if total is None and skip > PAGE_LIMIT * 20:
            break  # runaway protection
        time.sleep(POLITE_DELAY_S)
    return list(seen.values())


def fetch_associations(raw_dir: Path) -> list:
    j = http_get(API_BASE + ASSOC_PATH, {"limit": 200})
    docs = j.get("docs") or []
    print(f"associations total from API: {j.get('totalDocs')} (got {len(docs)})", file=sys.stderr)
    return docs


# --------------------------------------------------------------------------
# Normalizers
# --------------------------------------------------------------------------
def normalize_waters(waters: list, county_ids: dict, fname: str) -> list:
    out = []
    for i, w in enumerate(waters):
        name = (w.get("name") or "").strip()
        subtype = (w.get("subtype") or "").strip().lower()
        num, unit, raw, dim_flags = parse_dimensiune(w.get("dimensiune"))
        coords = w.get("coordinates") or []
        assoc = w.get("asociatie") or {}
        rec = {
            "id": f"abp-{i + 1:04d}",
            "source": "arebaltapeste",
            "file": fname,
            "source_row": i,  # 0-based index in the raw JSON array
            "slug": w.get("slug"),
            "county": w.get("judet"),
            "county_id": county_ids.get(name_normalized(w.get("judet") or "")),
            "association": assoc.get("name"),
            "association_slug": assoc.get("slug"),
            "association_id": assoc.get("id"),
            "water_name": name,
            "name_normalized": name_normalized(name),
            "water_type": SUBTYPE_TO_TYPE.get(subtype, "other"),
            "subtype": subtype,
            "limits_text": w.get("limite") or None,
            "referinta": w.get("referinta") or None,
            "pescuit_interzis": bool(w.get("pescuit_interzis")),
            "sector_km": num if unit == "km" else None,
            "sector_ha": num if unit == "ha" else None,
            "sector_unit": unit,
            "sector_raw": raw,
            "coordinates_lon": coords[0] if len(coords) > 0 else None,
            "coordinates_lat": coords[1] if len(coords) > 1 else None,
            "bbox": w.get("bbox") or None,
            "is_contracted": is_contracted_referinta(w.get("referinta")),
            "flags": sorted(set(dim_flags)),
        }
        if not rec["sector_unit"]:
            rec["flags"].append("missing_value")
        out.append(rec)
    return out


def normalize_associations(assocs: list, water_slugs, fname: str) -> list:
    out = []
    for i, a in enumerate(assocs):
        adrese = a.get("adrese") or []
        first = (adrese[0].get("adresa") or {}) if adrese else {}
        rec = {
            "id": f"abp-a{i + 1:04d}",
            "source": "arebaltapeste",
            "file": fname,
            "source_row": i,  # 0-based index in the raw JSON array
            "name": a.get("name"),
            "name_long": a.get("name_long") or None,
            "name_normalized": name_normalized(a.get("name") or ""),
            "type": association_type(a.get("name") or ""),
            "slug": a.get("slug"),
            "address": first.get("adresa") or None,
            "phone": first.get("telefon") or None,
            "website": a.get("siteUrl") or None,
            "permit_url": a.get("link_permis") or None,
            "bbox": a.get("bbox") or None,
            "adrese": adrese,
            "water_count": water_slugs.get(a.get("slug"), 0),
            "flags": ["no_waters"] if not water_slugs.get(a.get("slug")) else [],
        }
        out.append(rec)
    return out


# --------------------------------------------------------------------------
# sources.jsonl (idempotent append — replace row with same raw_file_path)
# --------------------------------------------------------------------------
def append_sources(sources_out: Path, recs: list):
    rows = []
    if sources_out.exists():
        for line in sources_out.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r0 = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r0.get("raw_file_path") in {r["raw_file_path"] for r in recs}:
                continue  # replaced below
            rows.append(r0)
    rows.extend(recs)
    with sources_out.open("w", encoding="utf-8") as f:
        for r0 in rows:
            f.write(json.dumps(r0, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description="Fetch + normalize arebaltapeste.ro data.")
    ap.add_argument(
        "--offline",
        action="store_true",
        help="skip the network; reuse existing snapshots (snapshot_full.json "
        "falls back to snapshot_waters.json)",
    )
    ap.add_argument("--out", default=None, help="output directory (default data/processed)")
    ap.add_argument("--schema-version", default="1.0.0")
    args = ap.parse_args(argv)

    repo = Path(__file__).resolve().parents[2]
    raw_dir = repo / "data" / "raw" / "arebaltapeste_probe"
    out_dir = Path(args.out) if args.out else repo / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)

    county_ids = county_lookup()
    ingested_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    schema_version = args.schema_version

    # ---------------- fetch / load raw ----------------
    full_path = raw_dir / "snapshot_full.json"
    assoc_path = raw_dir / "snapshot_asociatii.json"
    if args.offline:
        print("offline mode: reusing local snapshots", file=sys.stderr)
        if full_path.exists():
            waters = json.loads(full_path.read_text(encoding="utf-8"))
        else:
            waters = json.loads((raw_dir / "snapshot_waters.json").read_text(encoding="utf-8"))
        assocs = json.loads(assoc_path.read_text(encoding="utf-8"))
    else:
        waters = fetch_waters(raw_dir)
        assocs = fetch_associations(raw_dir)
        full_path.write_text(json.dumps(waters, ensure_ascii=False, indent=1), encoding="utf-8")
        assoc_path.write_text(json.dumps(assocs, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"wrote {full_path} ({len(waters)} records)", file=sys.stderr)
        print(f"wrote {assoc_path} ({len(assocs)} records)", file=sys.stderr)

    # ---------------- normalize ----------------
    water_recs = normalize_waters(waters, county_ids, full_path.name)
    assoc_slugs = {}
    for w in waters:
        slug = (w.get("asociatie") or {}).get("slug")
        if slug:
            assoc_slugs[slug] = assoc_slugs.get(slug, 0) + 1
    assoc_recs = normalize_associations(assocs, assoc_slugs, assoc_path.name)

    with (out_dir / "arebaltapeste_waters.jsonl").open("w", encoding="utf-8") as f:
        for r in water_recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (out_dir / "arebaltapeste_associations.jsonl").open("w", encoding="utf-8") as f:
        for r in assoc_recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ---------------- sources.jsonl ----------------
    src_recs = [
        {
            "id": str(uuid.uuid4()),
            "source_name": "arebaltapeste",
            "raw_file_path": f"data/raw/arebaltapeste_probe/{full_path.name}",
            "raw_file_url": f"{API_BASE}{WATERS_PATH}?type=ape&limit={PAGE_LIMIT}&skip=N",
            "source_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "ingested_at": ingested_at,
            "record_count": len(water_recs),
            "schema_version": schema_version,
        },
        {
            "id": str(uuid.uuid4()),
            "source_name": "arebaltapeste",
            "raw_file_path": f"data/raw/arebaltapeste_probe/{assoc_path.name}",
            "raw_file_url": f"{API_BASE}{ASSOC_PATH}?limit=200",
            "source_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "ingested_at": ingested_at,
            "record_count": len(assoc_recs),
            "schema_version": schema_version,
        },
    ]
    append_sources(out_dir / "sources.jsonl", src_recs)

    # ---------------- validation report ----------------
    report = validate(water_recs, assoc_recs)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def validate(waters, assocs):
    n_km = sum(r["sector_km"] or 0 for r in waters)
    n_ha = sum(r["sector_ha"] or 0 for r in waters)
    return {
        "waters": len(waters),
        "associations": len(assocs),
        "associations_with_waters": sum(1 for a in assocs if a["water_count"] > 0),
        "counties_with_waters": len({r["county_id"] for r in waters}),
        "lakes": sum(1 for r in waters if r["subtype"] == "lac"),
        "rivers": sum(1 for r in waters if r["subtype"] == "rau"),
        "km_rows": sum(1 for r in waters if r["sector_unit"] == "km"),
        "ha_rows": sum(1 for r in waters if r["sector_unit"] == "ha"),
        "total_km": round(n_km, 2),
        "total_ha": round(n_ha, 2),
        "unparsed_dimensiune": sum(1 for r in waters if "dimensiune_unparsed" in r["flags"]),
        "no_unit_dimensiune": sum(1 for r in waters if "dimensiune_no_unit" in r["flags"]),
        "uncontracted": sum(1 for r in waters if not r["is_contracted"]),
        "with_coordinates": sum(1 for r in waters if r["coordinates_lat"] is not None),
        "with_limits": sum(1 for r in waters if r["limits_text"]),
        "prohibition_flag": sum(1 for r in waters if r["pescuit_interzis"]),
    }


if __name__ == "__main__":
    main()
