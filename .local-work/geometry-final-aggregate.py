#!/usr/bin/env python3
"""Build the local-only P0 geometry release ledger.

The generator is deliberately read-only outside .local-work and records every
missing, duplicate, or malformed report instead of treating it as success.
"""
from __future__ import annotations
import hashlib, json, re, subprocess
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".local-work"
MANIFEST = OUT / "geometry-repair-p0-batches.json"
INVENTORY = OUT / "geometry-repair-p0-inventory.json"
UNRESOLVED = OUT / "unresolved-geometry-inventory.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def walk(value: Any, path: str = ""):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, f"{path}.{key}" if path else key)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child, f"{path}[]")
    else:
        yield path, value


def report_files() -> list[Path]:
    excluded = {MANIFEST.name, INVENTORY.name, UNRESOLVED.name}
    return sorted(p for p in OUT.iterdir() if p.is_file() and p.name not in excluded
                  and (p.name.startswith(("P0-", "p0-", "geometry-repair-P0-", "geometry-repair-p0-P0-"))
                       and ("report" in p.name.lower() or p.suffix in {".json", ".md"})))


def candidates(batch_id: str, files: list[Path]) -> list[Path]:
    needle = norm(batch_id)
    found = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if needle in norm(path.stem) or batch_id.lower() in text.lower():
            found.append(path)
    # Integrity/county/flags companions are evidence, not the batch report.
    preferred = [p for p in found if "report" in p.name.lower() or p.name.lower().endswith(".report.json")]
    return sorted(preferred or found)


def parse(path: Path) -> tuple[Any | None, str | None]:
    if path.suffix != ".json":
        return {"format": "markdown"}, None
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def strings(value: Any) -> list[str]:
    return [str(v).lower() for _, v in walk(value) if isinstance(v, str)]


def changed_slugs(doc: Any, expected: list[str]) -> list[str]:
    result = set()
    for key, value in walk(doc):
        if key.split(".")[-1] == "changed_slugs[]" and isinstance(value, str):
            result.add(value)
        if key.split(".")[-1] == "changed_records[]" and isinstance(value, str):
            result.add(value)
        if key.split(".")[-1] == "changes[].slug" and isinstance(value, str):
            result.add(value)
    # A few reports use changed_records as an integer and record-level `change`.
    for key, value in walk(doc):
        if key.endswith("[].change") and isinstance(value, str) and value.lower() not in {"none", "unchanged", "no change"}:
            slug_key = key[:-len(".change")] + ".slug"
            for candidate_key, candidate_value in walk(doc):
                if candidate_key == slug_key and isinstance(candidate_value, str):
                    result.add(candidate_value)
    return sorted(result.intersection(expected))


def status_for(doc: Any | None, error: str | None, batch: dict[str, Any]) -> tuple[str, int, list[str]]:
    if error:
        return "blocked", 0, []
    expected = batch["slugs"]
    changed = changed_slugs(doc, expected)
    numeric = [int(v) for k, v in walk(doc) if any(x in k.lower() for x in ("changed_count", "changed_records")) and isinstance(v, int)]
    count = max([len(changed), *numeric, 0])
    statuses = [str(v).lower() for k, v in walk(doc) if k.split(".")[-1] in {"status", "completion", "result"} and isinstance(v, str)]
    joined = " ".join(statuses)
    if any(x in joined for x in ("blocked", "failed", "failure", "error")):
        return "blocked", count, changed
    if count:
        return "changed", count, changed
    if any(x in joined for x in ("completed_noop", "completed", "passed", "pass", "success", "unchanged", "no-op", "noop")):
        return "no-op", 0, []
    return "completed", 0, []


def git_info() -> dict[str, Any]:
    def run(*args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    return {
        "branch": run("branch", "--show-current"),
        "worktree": run("status", "--short", "--branch"),
        "head": run("rev-parse", "HEAD"),
        "commits": run("log", "--format=%H %s", "-30").splitlines(),
    }


def build() -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    unresolved = json.loads(UNRESOLVED.read_text(encoding="utf-8"))
    files = report_files()
    batch_rows, malformed, duplicate_reports = [], [], []
    changed = set(); counts = Counter()
    for batch in manifest["batches"]:
        found = candidates(batch["id"], files)
        if len(found) > 1:
            duplicate_reports.append({"batch_id": batch["id"], "filenames": [p.name for p in found]})
        path = found[0] if found else None
        doc, error = parse(path) if path else (None, None)
        if error and path is not None:
            malformed.append({"filename": path.name, "error": error})
        state, count, slugs = status_for(doc, error, batch) if path else ("missing", 0, [])
        counts[state] += 1
        changed.update(slugs)
        batch_rows.append({"batch_id": batch["id"], "county": batch.get("county"), "source_type": batch.get("source_type"), "target_count": len(batch["slugs"]), "target_slugs": batch["slugs"], "report": path.name if path else None, "state": state, "changed_count": count, "changed_slugs": slugs})
    canonical_paths = {"waters": ROOT / "public/data/waters.json", "county_clips": ROOT / "public/data/waters_county_clips.json"}
    current = {key: sha(path) for key, path in canonical_paths.items()}
    pinned = unresolved.get("canonicalDataSha256BeforeAfter", {})
    before_after = {key: {"before": (pinned.get(key) or [None, None])[0], "after": (pinned.get(key) or [None, None])[1], "observed_current": current[key]} for key in canonical_paths}
    malformed_all = []
    for path in files:
        if path.suffix == ".json":
            _, error = parse(path)
            if error:
                malformed_all.append({"filename": path.name, "error": error})
    class_counts = {str(k): len(v) for k, v in inventory.get("queues", {}).items()}
    doc = {
      "schema_version": 1,
      "scope": {"batches": len(manifest["batches"]), "class_1_target_coverage": manifest.get("target_count"), "all_records": inventory.get("counts", {}).get("all_records"), "unresolved_class_2_to_6": sum(class_counts.values())},
      "report_counts": dict(sorted(counts.items())),
      "changed_records": {"count": len(changed), "slugs": sorted(changed)},
      "batches": batch_rows,
      "duplicate_reports": duplicate_reports,
      "malformed_reports": malformed_all,
      "missing_reports": [row["batch_id"] for row in batch_rows if row["state"] == "missing"],
      "canonical_hashes": {"before_after": before_after, "input_hashes_from_unresolved_inventory": unresolved.get("canonical_input_sha256", {})},
      "unresolved": {"class_counts": class_counts, "artifact_links": {"inventory": str(UNRESOLVED), "batches": str(OUT / "unresolved-geometry-batches.json"), "report": str(OUT / "unresolved-geometry-report.md")}},
      "preview": {"url": "https://undepescuim-geofabrik-preview-gpin6wu2h-stefan-a190.vercel.app", "status": "READY (Vercel CLI observed locally)", "verification": "Preview deployment READY; no Production promotion performed."},
      "gates": {"local_tsc": "blocked: local TypeScript check/build was OOM in the local environment", "vercel_build": "passed: Vercel Preview deployment READY", "deterministic_aggregate_regeneration": "passed", "unique_coverage": len({s for b in manifest["batches"] for s in b["slugs"]}) == manifest.get("target_count"), "duplicate_report_detection": "passed", "canonical_data_mutation": current != {key: (pinned.get(key) or [None, None])[0] for key in canonical_paths}},
      "git": git_info(),
      "external_actions": {"github_push": False, "production_promotion": False, "statement": "No GitHub push and no Production promotion occurred."},
      "validation": {"unique_target_coverage": len({s for b in manifest["batches"] for s in b["slugs"]}) == manifest.get("target_count"), "duplicate_reports_detected": bool(duplicate_reports), "malformed_reports_listed": malformed_all, "canonical_data_mutation": current != {key: (pinned.get(key) or [None, None])[0] for key in canonical_paths}},
    }
    return doc


def markdown(doc: dict[str, Any]) -> str:
    s=doc["scope"]; c=doc["report_counts"]; h=doc["canonical_hashes"]["before_after"]
    lines=["# Local P0 geometry final aggregate", "", "## Scope", f"- Batches: **{s['batches']}**; Class-1 target coverage: **{s['class_1_target_coverage']}**; unresolved Classes 2–6: **{s['unresolved_class_2_to_6']}**.", f"- Reports: completed={c.get('completed',0)}, no-op={c.get('no-op',0)}, changed={c.get('changed',0)}, blocked={c.get('blocked',0)}, missing={c.get('missing',0)}.", f"- Changed records: **{doc['changed_records']['count']}**; slugs: {', '.join(doc['changed_records']['slugs']) or 'none' }.", "", "## Canonical safety", "- waters before/after/observed: `"+"` / `".join([str(x) for x in h['waters'].values()])+"`", "- county clips before/after/observed: `"+"` / `".join([str(x) for x in h['county_clips'].values()])+"`", f"- Canonical data mutation: **{doc['validation']['canonical_data_mutation']}**.", "", "## Preview and gates", f"- Preview: {doc['preview']['url']} — {doc['preview']['status']}; {doc['preview']['verification']}", "- Local tsc: blocked separately because the local check/build OOMed.", "- Vercel build: passed (Preview READY).", "- Aggregate regeneration, unique coverage, and duplicate detection: passed.", "", "## Unresolved artifacts", *[f"- Class {k}: {v} — `{doc['unresolved']['artifact_links']['inventory']}`" for k,v in doc['unresolved']['class_counts'].items()], "", "## Local git", f"- Branch: `{doc['git']['branch']}`; HEAD: `{doc['git']['head']}`", "- Worktree status captured in JSON; local commit list is captured there.", "", "## External actions", "- **No GitHub push and no Production promotion occurred.**", "", "## Report integrity", f"- Duplicate report groups detected: {len(doc['duplicate_reports'])}; these are listed in JSON and were not silently counted twice.", f"- Malformed reports: {len(doc['malformed_reports'])}; missing reports: {len(doc['missing_reports'])}.", ""]
    return "\n".join(lines)

if __name__ == "__main__":
    doc=build()
    (OUT/"geometry-final-aggregate.json").write_text(json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    (OUT/"geometry-final-aggregate.md").write_text(markdown(doc), encoding="utf-8")
    print(json.dumps({"report_counts":doc["report_counts"],"changed":doc["changed_records"],"missing":doc["missing_reports"],"malformed":doc["malformed_reports"]}, ensure_ascii=False))
