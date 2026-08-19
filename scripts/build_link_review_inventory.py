#!/usr/bin/env python3
"""Build a conservative, source-backed review inventory from live link evidence.

This command never proposes a replacement URL.  Redirect destinations remain
observations in the attempt history and require explicit first-party review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

CATEGORY = {
    "ok": "ok",
    "client_error": "client_error",
    "server_error": "server_error",
    "transient_error": "transient_error",
    "blocked": "blocked/policy",
    "redirected": "redirect",
}


def key_for(record: dict) -> str:
    value = "|".join(str(record.get(k) or "") for k in ("originalUrl", "field", "sourcePath"))
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def build(report: dict, repairs: list[dict]) -> tuple[list[dict], dict]:
    repair_by_key = {item["repairKey"]: item for item in repairs}
    url_counts = Counter(item.get("originalUrl") for item in repairs)
    url_seen: Counter[str] = Counter()
    rows = []
    for record in report["records"]:
        status = record["status"]
        repair = repair_by_key.get(
            hashlib.sha256(
                "|".join(str(record.get(k) or "") for k in ("sourceKind", "associationSlug", "field", "sourcePath", "originalUrl")).encode()
            ).hexdigest()
        )
        original = record.get("originalUrl")
        url_seen[original] += 1
        duplicate_total = url_counts.get(original, 0)
        failed = status != "ok"
        rows.append(
            {
                "schemaVersion": 1,
                "recordKey": key_for(record),
                "associationSlug": record.get("associationSlug"),
                "field": record["field"],
                "sourcePath": record["sourcePath"],
                "sourceKind": record["sourceKind"],
                "originalUrl": original,
                "errorCategory": CATEGORY.get(status, status),
                "observedStatus": status,
                "attemptHistory": {
                    "checkedAt": record.get("checkedAt"),
                    "httpStatus": record.get("httpStatus"),
                    "failureReason": record.get("failureReason"),
                    "finalUrl": record.get("finalUrl"),
                    "redirect": record.get("redirect"),
                    "retry": record.get("retry"),
                },
                "firstPartyEvidence": {
                    "status": "missing" if failed else "not_required",
                    "urls": [],
                    "note": (
                        "No first-party evidence is attached; do not invent or accept a destination."
                        if failed
                        else "Original URL passed the live check."
                    ),
                },
                "candidateUrl": None,
                "reviewStatus": "needs_first_party_review" if failed else "not_in_repair_scope",
                "repairProposal": bool(repair),
                "duplicate": {
                    "key": hashlib.sha256(str(original or "").encode()).hexdigest()[:16],
                    "occurrence": url_seen[original],
                    "total": duplicate_total,
                    "isDuplicate": duplicate_total > 1,
                },
            }
        )
    if len(rows) != report["summary"]["total"]:
        raise ValueError("report total does not match records")
    if sum(row["repairProposal"] for row in rows) != len(repairs):
        raise ValueError("repair proposals do not map one-to-one to report records")
    summary = {
        "schemaVersion": 1,
        "reportTotal": len(rows),
        "failedTotal": sum(row["reviewStatus"] == "needs_first_party_review" for row in rows),
        "repairProposalTotal": len(repairs),
        "byCategory": dict(sorted(Counter(row["errorCategory"] for row in rows).items())),
        "duplicateOriginalUrlRows": sum(row["duplicate"]["isDuplicate"] for row in rows),
        "duplicateOriginalUrlGroups": sum(1 for count in url_counts.values() if count > 1),
        "candidateUrlCount": sum(row["candidateUrl"] is not None for row in rows),
        "policy": "Candidates and redirects are never accepted automatically; first-party evidence is mandatory.",
    }
    return rows, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default="data/processed/link_validation_report.json")
    parser.add_argument("--repairs", default="data/processed/link_validation_repairs.jsonl")
    parser.add_argument("--output", default="data/processed/link_review_inventory.jsonl")
    parser.add_argument("--summary", default="data/processed/link_review_inventory_summary.json")
    args = parser.parse_args()
    report = json.loads(Path(args.report).read_text())
    repairs = [json.loads(line) for line in Path(args.repairs).read_text().splitlines() if line.strip()]
    rows, summary = build(report, repairs)
    Path(args.output).write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows))
    Path(args.summary).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
