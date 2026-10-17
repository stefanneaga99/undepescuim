"""``rivernet build``: extract -> graph -> courses -> QA (T2.4).

Writes into ``--out-dir`` (default ``data/rivernet``):

* ``qa.json``                — QA report (always committed)
* ``courses_all.jsonl.gz``   — every course (gitignored; debugging / review page)
* ``courses.jsonl.gz``       — only courses that are a match candidate for some
  river water (committed), unless it exceeds ``--max-commit-mb`` (then it is
  not written and ``build_summary.json`` says ``commit_courses: false`` so the
  file can be published as a release asset instead)
* ``build_summary.json``     — counts and sizes
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
from pathlib import Path
from typing import Any, Iterable, Sequence

from .courses import build_courses
from .extract_schema import load_extract
from .graph import build_graph
from .qa import qa_report, write_qa
from .textnorm import article_variants, river_keys, river_match_keys

DEFAULT_MAX_COMMIT_MB = 25.0


def river_candidate_keys(waters: Iterable[dict[str, Any]]) -> set[str]:
    keys: set[str] = set()
    for w in waters:
        if w.get("subtype") == "rau":
            keys.update(river_match_keys(w.get("name")))
    return keys


def is_candidate(rec: dict[str, Any], keys: set[str]) -> bool:
    """A course is a candidate when its name key or any alias key is wanted."""
    if rec["name_key"] in keys or any(v in keys for v in article_variants(rec["name_key"])):
        return True
    return any(k in keys for a in rec.get("aliases") or [] for k in river_match_keys(a))


def write_jsonl_gz(path: Path, records: Iterable[dict[str, Any]]) -> int:
    """Deterministic gzip JSONL; returns the file size in bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as gz:
            with io.BufferedWriter(gz) as out:  # type: ignore[arg-type]
                for rec in records:
                    line = json.dumps(rec, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                    out.write(line.encode("utf-8") + b"\n")
    return path.stat().st_size


def build(
    extract_path: str | Path,
    out_dir: str | Path,
    waters_path: str | Path | None = None,
    max_commit_mb: float = DEFAULT_MAX_COMMIT_MB,
) -> dict[str, Any]:
    out = Path(out_dir)
    extract = load_extract(extract_path)
    wg = build_graph(extract)
    courses = build_courses(wg, extract)
    records = [c.to_record() for c in courses]

    write_qa(out / "qa.json", qa_report(wg, courses, extract))
    all_size = write_jsonl_gz(out / "courses_all.jsonl.gz", records)

    subset = records
    candidate_keys: set[str] | None = None
    if waters_path is not None:
        waters = json.loads(Path(waters_path).read_text(encoding="utf-8"))
        candidate_keys = river_candidate_keys(waters)
        subset = [r for r in records if is_candidate(r, candidate_keys)]

    subset_path = out / "courses.jsonl.gz"
    subset_size = write_jsonl_gz(subset_path, subset)
    commit = subset_size <= max_commit_mb * 1024 * 1024
    if not commit:
        subset_path.unlink()

    summary = {
        "extract_pbf_sha256": extract.meta.pbf_sha256,
        "osm_timestamp": extract.meta.osm_timestamp,
        "courses_total": len(records),
        "courses_candidates": len(subset),
        "candidate_filter": "river_keys(water.name) of subtype rau" if candidate_keys is not None else "none",
        "courses_all_bytes": all_size,
        "courses_bytes": subset_size,
        "commit_courses": commit,
        "max_commit_mb": max_commit_mb,
    }
    (out / "build_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=1) + "\n", encoding="utf-8"
    )
    return summary


def cli(argv: Sequence[str]) -> int:
    p = argparse.ArgumentParser(prog="rivernet build", description=__doc__.split("\n")[0])
    p.add_argument("--extract", required=True, help="water-extract.jsonl.gz (schema v1)")
    p.add_argument("--out-dir", default="data/rivernet")
    p.add_argument("--waters", default="public/data/waters.json", help="'' to skip candidate filtering")
    p.add_argument("--max-commit-mb", type=float, default=DEFAULT_MAX_COMMIT_MB)
    ns = p.parse_args(list(argv))
    summary = build(ns.extract, ns.out_dir, ns.waters or None, ns.max_commit_mb)
    print(json.dumps(summary, sort_keys=True), flush=True)
    return 0
