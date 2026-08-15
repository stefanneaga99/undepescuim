#!/usr/bin/env python3
"""
locuridepescuit.ro scraper (enrichment source) — Phase 4 of the
UndePescuim.ro data pipeline.

Crawls all 64 association detail pages enumerated by the probe
(data/raw/locuri_probe/association_urls.json), parses each page into an
association record + its contracted-waters list, extracts km/Ha from
parenthetical notes where parseable, and writes user-contributed records:

  data/processed/locuri_associations.jsonl   — one record per association
  data/processed/locuri_waters.jsonl         — one record per water
  data/processed/sources.jsonl               — idempotent append, one row/page

USER-CONTRIBUTED enrichment: locuri waters are is_contracted=false by
default and never override ANPA canonical data (see data_model_proposal.md
§2 "User-contributed data (locuri) ... Treat as enrichment; never as primary
authority").

Known blockers (probe-verified, do NOT re-diagnose):
  * The site serves a Let's Encrypt wildcard cert (*.locuridepescuit.ro)
    that does NOT cover the apex hostname, and every hostname 301-redirects
    to the apex. requests fails with curl error 60 -> verify=False.
  * Listing grids on index pages are JS-loaded; the association detail
    pages themselves are static server-rendered HTML — they are the data
    carrier (probe report §Data fields observed).

Run:  .venv/bin/python src/pipeline/scrape_locuri.py
      [--refresh] [--workers 4] [--delay 0.6] [--out DIR] [--schema-version 1.0.0]

Idempotency: raw HTML is cached under data/raw/locuri_probe/pages/;
re-runs skip cached files unless --refresh is passed. sources.jsonl rows
are replaced per raw_file_path. JSONL outputs are regenerated deterministically
(sorted by the input URL order).

Requires: curl_cffi, beautifulsoup4 (in the project venv).
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import threading
import time
import unicodedata
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

try:
    from curl_cffi import requests as cffi_requests
except ImportError:  # pragma: no cover
    cffi_requests = None

from bs4 import BeautifulSoup

BASE = "https://locuridepescuit.ro"
URLS_PATH = "data/raw/locuri_probe/association_urls.json"
PAGES_DIR = "data/raw/locuri_probe/pages"

# per-worker min delay between requests (politeness); workers multiply throughput
DEFAULT_WORKERS = 4
DEFAULT_DELAY = 0.6

RETRY_ATTEMPTS = 3
RETRY_BACKOFF_S = (1, 3, 9)

NOISE = ("Obtineti Instructiuni deplasare", "Obțineți Instrucțiuni deplasare")


# --------------------------------------------------------------------------
# Name normalization (shared with fetch_arebaltapeste.py conventions)
# --------------------------------------------------------------------------
def ascii_fold(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def name_normalized(text: str) -> str:
    return re.sub(r"\s+", " ", ascii_fold(text).lower()).strip()


# --------------------------------------------------------------------------
# association type from name pattern (same logic as fetch_arebaltapeste.py)
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
# water_type inference from the water name prefix
# --------------------------------------------------------------------------
def water_type(name: str) -> str:
    n = name_normalized(name)
    if n.startswith("raul"):
        return "river"
    if n.startswith("acumulare"):
        return "accumulation"
    if n.startswith("lac"):
        return "lake"
    if n.startswith("paraul") or n.startswith("pârâul"):
        return "stream"
    if n.startswith("valea") or n.startswith("vale "):
        return "stream"
    if n.startswith("balta") or n.startswith("baltile"):
        return "pond"
    if n.startswith("canal"):
        return "canal"
    return "other"


# --------------------------------------------------------------------------
# km/Ha extraction from water-name parentheticals
#   "Râul Cugir (Cugir 15 Km, de la loc. Cugir - conf. râul Mureș)"
#     -> sector_km=15.0, sector_unit="km", sector_raw="15 Km"
#   "Balta X (10 Ha)" -> sector_ha=10.0, sector_unit="ha"
# --------------------------------------------------------------------------
KM_HA_RE = re.compile(r"(?<![A-Za-z0-9])(\d+(?:[.,]\d+)?)\s*(km|ha)\b", re.I)


def parse_km_ha(text: str):
    """Return (sector_km, sector_ha, sector_unit, sector_raw, flags).

    Only the first km/ha token is honored; values are kept in whichever unit
    appears. No unit found -> (None, None, None, None, ["km_ha_missing"]).
    """
    m = KM_HA_RE.search(text or "")
    if not m:
        return None, None, None, None, ["km_ha_missing"]
    try:
        num = float(m.group(1).replace(",", "."))
    except ValueError:
        return None, None, None, m.group(0), ["km_ha_unparsed"]
    unit = m.group(2).lower()
    flags = ["km_ha_parsed"]
    if unit == "km":
        return num, None, "km", m.group(0), flags
    return None, num, "ha", m.group(0), flags


# --------------------------------------------------------------------------
# water name split: "Râul Olt (Limită jud. Brașov – ...)" -> name + note
# --------------------------------------------------------------------------
PAREN_RE = re.compile(r"^(.*?)\s*\((.*)\)\s*$", re.S)


def split_water(raw: str):
    m = PAREN_RE.match(raw)
    if not m:
        return raw.strip(), None
    name = m.group(1).strip()
    note = m.group(2).strip()
    return (name, note) if name else (raw.strip(), None)


# --------------------------------------------------------------------------
# county lookup (counties.json by id, fallback by ASCII name)
# --------------------------------------------------------------------------
def county_lookup() -> dict:
    path = Path(__file__).resolve().parents[2] / "data" / "raw" / "counties.json"
    out = {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        for c in data:
            out[c["id"]] = c
            out[c["name_ascii"].lower()] = c
    except (OSError, json.JSONDecodeError, KeyError):
        pass
    return out


# --------------------------------------------------------------------------
# HTML parsing (evolved from data/raw/locuri_probe/parse_association.py)
# --------------------------------------------------------------------------
def _clean(val: str, label: str) -> str:
    for n in NOISE:
        val = val.replace(n, "")
    val = val.replace(label, "", 1)
    return " ".join(val.split()).strip()


CONTACT_LABELS = {
    "Adresa": "address",
    "Telefon": "phone",
    "Email": "email",
    "Website": "website",
    "Județe în care Asociația are ape contractate": "counties_contract",
}


def parse_association(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    path = urlparse(url).path.rstrip("/").split("/")
    county = path[-2] if len(path) >= 2 else None
    slug = path[-1]

    out = {
        "url": url,
        "slug": slug,
        "county_from_url": county,
        "name": soup.h1.get_text(" ", strip=True) if soup.h1 else None,
    }

    # contact fields keyed by H5 label
    for h5 in soup.find_all("h5"):
        label = h5.get_text(" ", strip=True)
        key = CONTACT_LABELS.get(label)
        if not key:
            continue
        block = h5.find_parent("div", class_="element")
        if not block:
            continue
        val = _clean(block.get_text(" ", strip=True), label)
        if val:
            out[key] = val

    # description
    for h5 in soup.find_all("h5"):
        if h5.get_text(" ", strip=True) == "Descriere":
            block = h5.find_parent("div", class_="element")
            if block:
                out["description"] = _clean(block.get_text(" ", strip=True), "Descriere")
            break

    # contracted waters: within the main profile tab, the LAST div.listing-details
    # is the waters list (the FIRST holds counties; similar-listings section holds
    # related cards — excluded).
    main_tab = soup.find("section", class_=re.compile(r"tab-type-main"))
    waters = []
    if main_tab:
        details_divs = main_tab.find_all("div", class_="listing-details")
        if details_divs:
            for li in details_divs[-1].find_all("li"):
                span = li.find("span", class_="category-name")
                t = (span or li).get_text(" ", strip=True)
                if t:
                    waters.append(t)
    seen, uniq = set(), []
    for w in waters:
        if w not in seen:
            seen.add(w)
            uniq.append(w)
    out["contracted_waters"] = uniq
    out["contracted_waters_count"] = len(uniq)
    return out


# --------------------------------------------------------------------------
# fetch with retry/backoff + cache
# --------------------------------------------------------------------------
_tls = threading.local()


def _session():
    if getattr(_tls, "sess", None) is None:
        _tls.sess = cffi_requests.Session(impersonate="chrome", verify=False, timeout=40)
    return _tls.sess


def fetch_page(url: str, cache_path: Path, delay: float, refresh: bool):
    """Fetch one association page into cache_path; returns bytes."""
    if cache_path.exists() and not refresh:
        return cache_path.read_bytes()
    html_bytes = None
    last_err = None
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            r = _session().get(url, allow_redirects=True)
            r.raise_for_status()
            html_bytes = r.content
            break
        except Exception as e:  # noqa: BLE001 — network errors vary
            last_err = e
            if attempt < RETRY_ATTEMPTS:
                backoff = RETRY_BACKOFF_S[attempt - 1] + random.uniform(0, 0.5)
                print(f"  retry {attempt} {url}: {e} (sleep {backoff:.1f}s)", file=sys.stderr)
                time.sleep(backoff)
    if html_bytes is None:
        raise RuntimeError(f"failed after {RETRY_ATTEMPTS} attempts: {url}: {last_err}")
    cache_path.write_bytes(html_bytes)
    time.sleep(delay)
    return html_bytes


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
# main
# --------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description="Crawl + parse locuridepescuit.ro association pages.")
    ap.add_argument("--refresh", action="store_true", help="re-fetch pages even if cached")
    ap.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    ap.add_argument("--delay", type=float, default=DEFAULT_DELAY, help="polite delay per request")
    ap.add_argument("--out", default=None, help="output directory (default data/processed)")
    ap.add_argument("--schema-version", default="1.0.0")
    args = ap.parse_args(argv)

    if cffi_requests is None:
        raise RuntimeError("curl_cffi is not installed; run .venv/bin/pip install curl_cffi")

    repo = Path(__file__).resolve().parents[2]
    urls = json.loads((repo / URLS_PATH).read_text(encoding="utf-8"))
    if not isinstance(urls, list) or not urls:
        raise SystemExit(f"no URLs in {URLS_PATH}")
    pages_dir = repo / PAGES_DIR
    pages_dir.mkdir(parents=True, exist_ok=True)
    out_dir = Path(args.out) if args.out else repo / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    county_ids = county_lookup()
    ingested_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    crawl_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # ---------------- crawl ----------------
    cache_map = []  # (url, cache_path)
    for u in urls:
        path = urlparse(u).path.rstrip("/").split("/")
        county = path[-2] if len(path) >= 2 else "?"
        slug = path[-1]
        cache_map.append((u, pages_dir / f"{county}-{slug}.html"))

    todo = [(u, cp) for u, cp in cache_map if args.refresh or not cp.exists()]
    print(f"{len(urls)} association URLs; {len(todo)} to fetch "
          f"({len(urls) - len(todo)} cached)", file=sys.stderr)
    failures = []
    if todo:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {
                ex.submit(fetch_page, u, cp, args.delay, args.refresh): u
                for u, cp in todo
            }
            for fut in as_completed(futs):
                u = futs[fut]
                try:
                    fut.result()
                    print(f"  ok {u}", file=sys.stderr)
                except Exception as e:  # noqa: BLE001
                    failures.append((u, str(e)))
                    print(f"  FAIL {u}: {e}", file=sys.stderr)
    if failures:
        print(f"WARNING: {len(failures)} pages failed to fetch", file=sys.stderr)
        for u, e in failures:
            print(f"  {u}: {e}", file=sys.stderr)

    # ---------------- parse (deterministic, in URL order) ----------------
    assoc_recs = []
    water_recs = []
    src_recs = []
    for idx, (u, cp) in enumerate(cache_map):
        if not cp.exists():
            continue
        html = cp.read_text(encoding="utf-8", errors="replace")
        p = parse_association(html, u)
        slug = p["slug"]
        county = p["county_from_url"]
        county_rec = county_ids.get(county) or {}
        a_id = f"loci-a{idx + 1:04d}"
        assoc_recs.append(
            {
                "id": a_id,
                "source": "locuri",
                "file": f"{PAGES_DIR}/{cp.name}",
                "source_row": idx,
                "name": p.get("name"),
                "name_long": None,
                "name_normalized": name_normalized(p.get("name") or ""),
                "type": association_type(p.get("name") or ""),
                "slug": slug,
                "county_id": county_rec.get("id") or county,
                "address": p.get("address"),
                "phone": p.get("phone"),
                "email": p.get("email"),
                "website": p.get("website"),
                "counties_contract": p.get("counties_contract"),
                "description": p.get("description"),
                "water_count": p["contracted_waters_count"],
                "flags": [] if p["contracted_waters_count"] else ["no_waters"],
            }
        )
        for wi, wraw in enumerate(p["contracted_waters"]):
            wname, note = split_water(wraw)
            km, ha, unit, raw, flags = parse_km_ha(wraw)
            water_recs.append(
                {
                    "id": f"loci-{idx + 1:04d}-{wi + 1:03d}",
                    "source": "locuri",
                    "file": f"{PAGES_DIR}/{cp.name}",
                    "source_row": wi,
                    "slug": slug,
                    "county": county,
                    "county_id": county_rec.get("id") or county,
                    "association": p.get("name"),
                    "association_slug": slug,
                    "association_id": a_id,
                    "water_name": wname,
                    "name_normalized": name_normalized(wname),
                    "raw_name": wraw,
                    "water_type": water_type(wname),
                    "limits_text": note,
                    "sector_km": km,
                    "sector_ha": ha,
                    "sector_unit": unit,
                    "sector_raw": raw,
                    "is_contracted": False,  # user-contributed enrichment
                    "canonical_source": "locuri",
                    "flags": flags,
                }
            )
        src_recs.append(
            {
                # stable UUID5 per page URL -> re-runs rewrite identical rows,
                # keeping sources.jsonl byte-identical (true idempotency)
                "id": str(uuid.uuid5(uuid.NAMESPACE_URL, u)),
                "source_name": "locuri",
                "raw_file_path": f"{PAGES_DIR}/{cp.name}",
                "raw_file_url": u,
                "source_date": crawl_date,
                "ingested_at": ingested_at,
                "record_count": p["contracted_waters_count"],
                "schema_version": args.schema_version,
            }
        )

    # ---------------- write outputs ----------------
    with (out_dir / "locuri_associations.jsonl").open("w", encoding="utf-8") as f:
        for r in assoc_recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (out_dir / "locuri_waters.jsonl").open("w", encoding="utf-8") as f:
        for r in water_recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    append_sources(out_dir / "sources.jsonl", src_recs)

    report = validate(assoc_recs, water_recs, failures)
    report["pages_fetched"] = len(cache_map) - len(failures)
    report["pages_total"] = len(cache_map)
    report["fetch_failures"] = len(failures)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def validate(assocs, waters, failures):
    by_type = {}
    for w in waters:
        by_type[w["water_type"]] = by_type.get(w["water_type"], 0) + 1
    return {
        "associations": len(assocs),
        "waters": len(waters),
        "associations_with_waters": sum(1 for a in assocs if a["water_count"] > 0),
        "counties_with_waters": len({w["county_id"] for w in waters}),
        "waters_by_type": dict(sorted(by_type.items())),
        "km_rows": sum(1 for w in waters if w["sector_unit"] == "km"),
        "ha_rows": sum(1 for w in waters if w["sector_unit"] == "ha"),
        "total_km": round(sum(w["sector_km"] or 0 for w in waters), 2),
        "total_ha": round(sum(w["sector_ha"] or 0 for w in waters), 2),
        "km_ha_parsed": sum(1 for w in waters if "km_ha_parsed" in w["flags"]),
        "km_ha_missing": sum(1 for w in waters if "km_ha_missing" in w["flags"]),
        "with_limits_note": sum(1 for w in waters if w["limits_text"]),
        "with_contact_email": sum(1 for a in assocs if a["email"]),
        "with_contact_phone": sum(1 for a in assocs if a["phone"]),
    }


if __name__ == "__main__":
    main()
