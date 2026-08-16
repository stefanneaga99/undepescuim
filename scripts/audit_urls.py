#!/usr/bin/env python3
"""Layer 4.2 — association URL reachability audit (plan §4.2, scheduled cron,
NOT a CI gate: reachability is world-state, not code-state).

For every siteUrl + permitUrl in public/data/associations.json, do a
HEAD/GET with a browser UA (timeout 10 s), follow redirects, and record
{slug, url, kind, status, final_url, checked_at} to
data/processed/url_audit.jsonl.

Classification:
  ok        2xx/3xx (or a final URL after a 301 follow)
  soft_fail 4xx
  dead      5xx / DNS failure / timeout / connection error

Severity (plan §4.2):
  P1  a dead/4xx permitUrl — users cannot buy the permit the card advertises
  P2  a dead siteUrl — stale contact info

Exit code 1 when any URL is dead (the cron alerts on the exit code / the
JSONL is the durable record; the plan §9.2 wants a GitHub issue per dead/
redirected URL — wired by the scheduler).

Usage:
  .venv/bin/python scripts/audit_urls.py [--limit N] [--jsonl data/processed/url_audit.jsonl]
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
FE_ASSOC = ROOT / "public" / "data" / "associations.json"
OUT_JSONL = ROOT / "data" / "processed" / "url_audit.jsonl"

TIMEOUT = 10
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def check_url(slug: str, kind: str, url: str) -> dict:
    rec: dict = {"slug": slug, "kind": kind, "url": url,
                 "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    try:
        r = requests.get(url, timeout=TIMEOUT, allow_redirects=True,
                         headers={"User-Agent": UA}, verify=False)
        rec["status"] = r.status_code
        rec["final_url"] = r.url
        if r.status_code < 400:
            rec["classification"] = "ok"
        elif r.status_code < 500:
            rec["classification"] = "soft_fail"
        else:
            rec["classification"] = "dead"
    except requests.exceptions.SSLError as e:
        rec["status"] = None
        rec["classification"] = "dead"
        rec["error"] = f"ssl: {type(e).__name__}"
    except requests.exceptions.RequestException as e:
        rec["status"] = None
        rec["classification"] = "dead"
        rec["error"] = type(e).__name__
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="check only the first N urls (dry probe)")
    ap.add_argument("--jsonl", type=str, default=str(OUT_JSONL))
    args = ap.parse_args()

    assocs = json.loads(FE_ASSOC.read_text(encoding="utf-8"))
    targets = []
    for a in assocs:
        slug = a["slug"]
        if a.get("siteUrl"):
            targets.append((slug, "siteUrl", a["siteUrl"]))
        if a.get("permitUrl"):
            targets.append((slug, "permitUrl", a["permitUrl"]))
    # the ANPA state-permit portal is a hardcoded fact (permis-2026.ts) — audit it too
    targets.append(("anpa-portal", "permitUrl", "https://permise.anpa.ro:12443/portal-public/permis"))
    if args.limit:
        targets = targets[: args.limit]
    print(f"[urls] {len(targets)} URLs from {len(assocs)} associations")

    results = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(check_url, s, k, u) for s, k, u in targets]
        for f in as_completed(futs):
            results.append(f.result())

    results.sort(key=lambda r: (r["classification"], r["slug"], r["kind"]))
    out = Path(args.jsonl)
    out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in results) + "\n",
                   encoding="utf-8")

    from collections import Counter
    by_cls = Counter(r["classification"] for r in results)
    print(f"[urls] {dict(by_cls)} -> {out}")
    p1 = [r for r in results if r["kind"] == "permitUrl" and r["classification"] in ("dead", "soft_fail")]
    p2 = [r for r in results if r["kind"] == "siteUrl" and r["classification"] in ("dead", "soft_fail")]
    for r in p1:
        print(f"  P1 {r['slug']:32} {r['classification']:9} {r['url'][:70]}")
    for r in p2:
        print(f"  P2 {r['slug']:32} {r['classification']:9} {r['url'][:70]}")
    # redirects worth a one-line fix (plan §4.2)
    redirects = [r for r in results if r.get("final_url") and r["final_url"] != r["url"]]
    for r in redirects:
        print(f"  REDIRECT {r['slug']:32} {r['url'][:50]} -> {r['final_url'][:50]}")

    dead = [r for r in results if r["classification"] == "dead"]
    if dead:
        print(f"[urls] FAIL: {len(dead)} dead URL(s)")
        sys.exit(1)
    print("[urls] PASS: no dead URLs")


if __name__ == "__main__":
    main()