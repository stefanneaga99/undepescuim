#!/usr/bin/env python3
"""Deterministic offline link validator; live mode is deliberately not CI-enabled."""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
from link_validation_lib import LinkTarget, build_report, enumerate_targets, repair_record, result_for

ROOT = Path(__file__).resolve().parent.parent

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("fixtures", "live"), default="fixtures")
    ap.add_argument("--report", default="data/processed/link_validation_report.json")
    ap.add_argument("--repairs", default="data/processed/link_validation_repairs.jsonl")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only-source")
    ap.add_argument("--fail-on", choices=("critical", "none"), default="critical")
    args = ap.parse_args()
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if args.mode == "live":
        print("live reachability is scheduled/manual only; use a reviewed transport runner", file=sys.stderr)
        return 2
    fixture_path = ROOT / "tests/fixtures/link_validation/targets.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    targets = []
    for item in fixture:
        targets.append((LinkTarget(item.get("associationSlug"), item["field"], item["sourcePath"], item["sourceKind"], item["url"]), item.get("outcome")))
    if not fixture:
        targets = [(t, None) for t in enumerate_targets(ROOT)]
    if args.only_source: targets = [(t, o) for t, o in targets if t.source_kind == args.only_source]
    if args.limit: targets = targets[:args.limit]
    records = [result_for(t, now=now, outcome=o) for t, o in targets]
    records.sort(key=lambda r: (r["sourceKind"], r["associationSlug"] is None, r["associationSlug"] or "", r["field"], r["sourcePath"]))
    report = build_report(records, mode=args.mode, generated_at=now)
    report_path = Path(args.report); report_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = report_path.with_suffix(report_path.suffix + ".tmp")
    tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"); tmp.replace(report_path)
    repairs = [repair_record(r) for r in records]; repairs = [r for r in repairs if r]
    repair_path = Path(args.repairs); repair_path.parent.mkdir(parents=True, exist_ok=True)
    repair_path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in repairs), encoding="utf-8")
    print(json.dumps(report["summary"], sort_keys=True))
    if args.fail_on == "critical" and any(r["status"] == "blocked" for r in records): return 1
    return 0

if __name__ == "__main__": sys.exit(main())
