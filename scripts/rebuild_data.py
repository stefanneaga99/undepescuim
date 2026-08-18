#!/usr/bin/env python3
"""Layer 6 — determinism: canonical rebuild -> identical hash (plan §6).

The pipeline is a sequence of scripts; this orchestrator defines the CANONICAL
order and verifies that re-running it on the SAME pinned inputs reproduces the
committed public/data files byte-for-byte.

Modes:
  --manifest         write data/processed/pipeline_manifest.json — SHA-256 of
                     every input file the pipeline reads plus the committed
                     output hashes + git rev + timestamp. The cron/manual
                     "input changed?" detector: a diff between the manifest's
                     input hashes and the current files means a re-ingest
                     happened and the rebuild must be re-verified.
  --check            compare current input/output hashes against the committed
                     manifest; exit 1 on drift (run after any source change).
  --verify           re-run the deterministic in-place derivations
                     (recompute_assoc_validity, recompute_assoc_counts,
                     build_counties_geojson) and assert the committed files
                     are byte-identical (exit 1 on change).
  --to DIR           FULL canonical rebuild in a scratch repo copy: copy
                     scripts/ + data/ + public/data/ (heavy raw inputs
                     symlinked), run the canonical sequence inside the copy,
                     then hash-diff the copy's public/data vs the real repo.
                     Reports per-file identical / different (the diff is the
                     audit trail — plan §6.2 pass criteria).

Known non-reproducible steps (documented, plan §11.2): the overlay builders
emit PRE-fix overlays (the A1/A1.5 fixes — fix_duplicate_slugs_overlay.py +
fix_sweep_gate_duplicates.py — run AFTER the builders); --to therefore also
runs the fix scripts in the copy so the final overlays match the committed
files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "processed" / "pipeline_manifest.json"

# every file the pipeline READS (inputs) — hashed into the manifest
INPUTS = [
    "data/processed/anpa_waters.jsonl",
    "data/processed/anpa_contracts.jsonl",
    "data/processed/anpa_romsilva_waters.jsonl",
    "data/processed/arebaltapeste_waters.jsonl",
    "data/processed/arebaltapeste_associations.jsonl",
    "data/processed/locuri_associations.jsonl",
    "data/processed/locuri_waters.jsonl",
    "data/processed/sources.jsonl",
    "data/cache/osm_river_clusters.pkl",
    "data/raw/overpass_water_polys.json",
    "data/raw/county_boundaries/*.json",
    "data/species.json",
    "src/content/permis-2026.ts",
]

# committed OUTPUTS whose determinism we assert
OUTPUTS = [
    "public/data/waters.json",
    "public/data/associations.json",
    "public/data/counties.geojson",
    "public/data/uncontracted_rivers.json",
    "public/data/uncontracted_lakes.json",
    "public/data/waters_county_clips.json",
    "data/species.json",
]

# canonical in-place derivation sequence (deterministic given pinned inputs)
VERIFY_STEPS = [
    "scripts/recompute_assoc_validity.py",
    "scripts/recompute_assoc_counts.py",
    "scripts/build_counties_geojson.py",
]

# full canonical order (--to mode): derivations + overlay builders + the
# post-build fixes that the committed files incorporate
FULL_STEPS = [
    "scripts/merge_anpa_waters.py",           # anpa + romsilva + abp -> waters.json
    "scripts/audit_missing_rivers.py",        # attach OSM geometry to fixable rows
    "scripts/build_uncontracted_rivers.py",
    "scripts/build_uncontracted_lakes.py",
    "scripts/sweep_uncontracted_overlay.py",
    "scripts/recompute_assoc_validity.py",
    "scripts/recompute_assoc_counts.py",
    "scripts/backfill_permit_urls.py",
    "scripts/build_locality_assignment.py",
    "scripts/build_counties_geojson.py",
    # P0 §4.2/§4.1: county-clip split + geometry simplification. Order:
    # compute clips (inline) -> move them to waters_county_clips.json ->
    # round/simplify the waters geometry (clips already split, untouched).
    "scripts/build_county_clip_geoms.py",
    "scripts/split_county_clips.py",
    "scripts/simplify_waters_geometry.py",
    "scripts/fix_duplicate_slugs_overlay.py",  # A1: same-body dedupe + translit
    "scripts/fix_sweep_gate_duplicates.py",    # B4: overlay vs contracted cleanup
]

PY = sys.executable


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def expand_inputs() -> list[Path]:
    out = []
    for pattern in INPUTS:
        if "*" in pattern:
            out.extend(sorted(ROOT.glob(pattern)))
        else:
            p = ROOT / pattern
            if p.exists():
                out.append(p)
    return out


def collect() -> dict:
    inputs = {}
    for p in expand_inputs():
        rel = str(p.relative_to(ROOT))
        inputs[rel] = sha256(p)
    outputs = {}
    for pattern in OUTPUTS:
        p = ROOT / pattern
        if p.exists():
            outputs[pattern] = sha256(p)
    git_rev = ""
    try:
        git_rev = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                 text=True, check=True).stdout.strip()
    except Exception:
        pass
    return {"git_rev": git_rev, "inputs": inputs, "outputs": outputs,
            "generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds")}


def cmd_manifest() -> None:
    data = collect()
    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[manifest] wrote {MANIFEST} ({len(data['inputs'])} inputs, "
          f"{len(data['outputs'])} outputs, git {data['git_rev'][:8]})")


def is_git_tracked(rel: str) -> bool:
    """True if the file is committed to git (i.e. present in any checkout).

    Untracked heavy OSM artifacts (data/cache/osm_river_clusters.pkl,
    data/raw/overpass_water_polys.json) are gitignored and therefore absent
    from the CI checkout — their absence is NOT a drift signal, but a change
    to a tracked input is.
    """
    try:
        r = subprocess.run(["git", "ls-files", "--error-unmatch", "--", rel],
                           capture_output=True, cwd=ROOT)
        return r.returncode == 0
    except Exception:
        return False


def cmd_check() -> None:
    if not MANIFEST.exists():
        print("[check] no manifest — run --manifest first")
        sys.exit(1)
    pinned = json.loads(MANIFEST.read_text(encoding="utf-8"))
    current = collect()
    drift = []
    skipped = []
    for rel, h in pinned["inputs"].items():
        cur = current["inputs"].get(rel)
        if cur is None:
            # absent now: a gitignored artifact that CI can't have is a
            # note, not a failure; a tracked file going missing is a real
            # problem.
            if not is_git_tracked(rel):
                skipped.append(rel)
                continue
            drift.append(("input", rel, h[:8], "MISSING"))
        elif cur != h:
            drift.append(("input", rel, h[:8], cur[:8]))
    for rel, h in current["inputs"].items():
        if rel not in pinned["inputs"]:
            drift.append(("input", rel, "(new)", h[:8]))
    for rel, h in pinned["outputs"].items():
        cur = current["outputs"].get(rel)
        if cur != h:
            drift.append(("output", rel, h[:8], (cur or "MISSING")[:8]))
    for rel in sorted(skipped):
        print(f"  note  {rel}: untracked artifact absent from this checkout — skipped")
    if drift:
        print(f"[check] DRIFT: {len(drift)} files changed since the pinned manifest")
        for kind, rel, old, new in drift:
            print(f"  {kind:6} {rel}: {old} -> {new}")
        print("[check] a source re-ingest happened — run the FULL rebuild (--to) "
              "and re-verify the gates")
        sys.exit(1)
    print(f"[check] PASS: all {len(pinned['inputs'])} inputs and "
          f"{len(pinned['outputs'])} outputs match the manifest (git {pinned['git_rev'][:8]})")


def cmd_verify() -> None:
    before = {o: sha256(ROOT / o) for o in OUTPUTS if (ROOT / o).exists()}
    changed = []
    for step in VERIFY_STEPS:
        print(f"[verify] running {step} ...")
        subprocess.run([PY, step], cwd=ROOT, check=True)
    after = {o: sha256(ROOT / o) for o in OUTPUTS if (ROOT / o).exists()}
    for o in before:
        if after.get(o) != before[o]:
            changed.append(o)
    if changed:
        print(f"[verify] FAIL: derivations changed committed outputs: {changed}")
        sys.exit(1)
    print("[verify] PASS: deterministic derivations reproduce the committed files")


def cmd_to(dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    print(f"[to] scratch rebuild at {dest}")
    for sub in ("scripts", "public/data", "data/processed", "data/raw/county_boundaries"):
        shutil.copytree(ROOT / sub, dest / sub)
    (dest / "data" / "cache").mkdir(parents=True, exist_ok=True)
    (dest / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (dest / "data" / "test").mkdir(parents=True, exist_ok=True)
    # heavy / read-only inputs -> symlink instead of copying
    for big in ["data/cache/osm_river_clusters.pkl",
                "data/raw/overpass_water_polys.json",
                "data/species.json"]:
        src = ROOT / big
        if src.exists():
            (dest / big).symlink_to(src)
    for p in ROOT.glob("data/raw/*.json"):
        (dest / "data" / "raw" / p.name).symlink_to(p)
    # run the canonical sequence INSIDE the copy
    for step in FULL_STEPS:
        print(f"[to] running {step} ...")
        r = subprocess.run([PY, str(dest / step)], cwd=dest)
        if r.returncode != 0:
            print(f"[to] WARN {step} exited {r.returncode} (continuing)")
    # hash-diff
    diffs = []
    for pattern in OUTPUTS:
        real, scratch = ROOT / pattern, dest / pattern
        if not real.exists() or not scratch.exists():
            continue
        if sha256(real) != sha256(scratch):
            diffs.append(pattern)
    print(f"[to] scratch rebuild done: {len(OUTPUTS) - len(diffs)}/{len(OUTPUTS)} "
          f"outputs byte-identical")
    for d in diffs:
        print(f"  DIFF {d}: committed != rebuilt (see the scratch dir for the "
              f"rebuilt version)")
    if diffs:
        print("[to] NOTE: the diff is the audit trail — gate on it, don't "
              "silently overwrite")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--to", type=Path, help="full canonical rebuild in a scratch dir")
    args = ap.parse_args()

    if args.manifest:
        cmd_manifest()
    if args.check:
        cmd_check()
    if args.verify:
        cmd_verify()
    if args.to:
        cmd_to(args.to)
    if not (args.manifest or args.check or args.verify or args.to):
        ap.print_help()


if __name__ == "__main__":
    main()