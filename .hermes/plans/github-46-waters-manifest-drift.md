# GitHub #46 — remediate `waters.json` manifest drift safely

## Goal
Restore the Layer 6 pipeline-manifest pin so `data-integrity` is green, without treating a changed generated data file as an unexplained hash update. The only intended repository data change should be the refreshed `data/processed/pipeline_manifest.json`, unless the isolated canonical rebuild proves that a source/pipeline output also needs correction.

## Evidence and root cause

- Failing run: `data-integrity` #56 / `32138496392`, commit `cfe25e2` on `main`.
  - Integrity, source traceability, county audit, overlap sweep, species gate, and deterministic derivations all passed.
  - The run failed at `python3 scripts/rebuild_data.py --check`; Node setup and the payload-budget gate were skipped after that failure.
- Current pin: `data/processed/pipeline_manifest.json` records `public/data/waters.json` as `7a307e429f...` and has `git_rev` `09d50fa`.
- Current committed `waters.json` SHA-256 is `fe87d14b224c99998a5f8c49e09609285559bc3ba2c8d9b8fc20420202f2351a`.
- The stale pin was created by `972f7bc` after the P0 rebuild, but `9df733a` later changed `public/data/waters.json` and did not run `--manifest` afterward. `9df733a` is a descendant of `972f7bc`; no source input drift is reported.
- The one-line minified JSON change in `9df733a` is intentional P1 LOD enrichment: its update to `scripts/simplify_waters_geometry.py` adds derived `lengthKm` for line geometries and `areaHa` for polygon geometries. A semantic comparison shows the same 1,013 slugs and 714 changed records, with the added derived size field; no slug-set, association, or geometry replacement was observed. `9df733a` also added `public/data/uncontracted_majors.json` to `OUTPUTS` and to `FULL_STEPS`.

Therefore this is an output-pin omission after an intentional, derivable `waters.json` change—not evidence of an upstream re-ingest. The canonical rebuild remains the required proof before re-pinning.

## Safety constraints

1. Do not use `git reset --hard`, `git clean`, or overwrite the existing `/home/stefan/undepescuim` tree. It currently contains unrelated/unowned work (`scripts/rebuild_data.py` modified and `data/_rebuild_check/` untracked).
2. Build and verify in a separate clean worktree based on the latest `origin/main`. Keep audit output outside the tracked tree (for example `/tmp/undepescuim-issue46-audit`).
3. Do not run `--manifest` until the canonical scratch rebuild and every local gate below have passed. If the scratch rebuild differs, preserve the scratch directory and report the file-level/semantic diff rather than overwriting any generated output.
4. Per `AGENTS.md`, any necessary pipeline-code fix must include a deterministic offline pytest regression test. A manifest-only pin update does not change pipeline logic.

## Implementation plan

### 1. Create an isolated, current baseline (2–3 min)

```bash
cd /home/stefan/undepescuim
git fetch origin
git worktree add -b fix/issue-46-waters-manifest /tmp/undepescuim-issue46 origin/main
cd /tmp/undepescuim-issue46
git status --short --branch
git rev-parse --verify HEAD
git log --oneline -5
```

Expected: a clean tree, with a `HEAD` at the fetched `origin/main`. If `origin/main` changed since `cfe25e2`, repeat the evidence comparison against the actual checkout; do not blindly apply the hash values above.

### 2. Establish the failing condition and preserve audit evidence (1 min)

```bash
python3 scripts/rebuild_data.py --check || true
sha256sum public/data/waters.json data/processed/pipeline_manifest.json
mkdir -p /tmp/undepescuim-issue46-audit
cp data/processed/pipeline_manifest.json /tmp/undepescuim-issue46-audit/pipeline_manifest.before.json
```

The expected pre-fix failure is one changed output, `public/data/waters.json`. Record command output in the execution card/issue comment.

### 3. Perform a full canonical rebuild only in scratch and compare it (5–15 min)

```bash
rm -rf /tmp/undepescuim-issue46-rebuild
python3 scripts/rebuild_data.py --to /tmp/undepescuim-issue46-rebuild
```

The command itself hashes every `OUTPUTS` item against the checkout. Supplement its output with a bounded semantic comparison for `waters.json`:

```bash
python3 - <<'PY'
import json
from pathlib import Path
current = json.loads(Path('public/data/waters.json').read_text())
rebuilt = json.loads(Path('/tmp/undepescuim-issue46-rebuild/public/data/waters.json').read_text())
a = {row['slug']: row for row in current}
b = {row['slug']: row for row in rebuilt}
changed = [slug for slug in a.keys() & b.keys() if a[slug] != b[slug]]
print({'current': len(a), 'rebuilt': len(b),
       'only_current': len(a.keys() - b.keys()),
       'only_rebuilt': len(b.keys() - a.keys()),
       'changed_records': len(changed)})
assert a.keys() == b.keys(), 'slug-set mismatch: do not re-pin'
assert not changed, 'canonical rebuild mismatch: inspect scratch; do not re-pin'
PY
```

Decision point:
- If all eight declared outputs are byte-identical and the assertions pass, the current `waters.json` is canonical and may be pinned.
- If any output differs, stop the re-pin. Use the scratch copy as the audit trail, identify the first non-deterministic/missing FULL_STEPS behavior, fix the pipeline plus an offline pytest regression test, then repeat this step from a clean worktree.

### 4. Run the deterministic derivations and all data-integrity gates (5–15 min)

Install the exact CI Python dependencies if the worktree has no usable environment. Run the verification suite in the same clean worktree:

```bash
python3 -m pip install --quiet shapely==2.1.2 pytest requests
python3 scripts/rebuild_data.py --verify
python3 scripts/audit_integrity.py
python3 scripts/audit_source_trace.py
python3 scripts/validate_geometry_county.py --json data/processed/county_audit_report.json
python3 scripts/sweep_uncontracted_overlay.py --gate
pytest tests/test_data_gates.py -q
npm ci
node scripts/check-data-budget.mjs
```

`--verify` runs in-place derivations; immediately confirm it left no data changes:

```bash
git diff --exit-code -- public/data/associations.json public/data/counties.geojson public/data/uncontracted_rivers.json public/data/uncontracted_lakes.json public/data/uncontracted_majors.json public/data/waters.json public/data/waters_county_clips.json data/species.json
```

If it changes an output or any gate fails, do not re-pin. Diagnose/fix in a separate follow-up changeset with its required tests, then rerun the full sequence.

### 5. Re-pin only the verified state and make the postcondition explicit (1–2 min)

```bash
python3 scripts/rebuild_data.py --manifest
python3 scripts/rebuild_data.py --check
git diff -- data/processed/pipeline_manifest.json
git status --short
```

Expected postcondition: `--check` reports PASS; the manifest captures the current `waters.json` hash (`fe87d14b...` for the investigated revision), includes `uncontracted_majors.json` if it is part of the current `OUTPUTS`, and has only its own generated timestamp/revision/hashes changed.

### 6. Commit, push, and verify GitHub Actions (3–10 min)

Before committing, ensure only the verified manifest (and any explicitly justified/tested pipeline fix if Step 3 required one) is staged:

```bash
git add data/processed/pipeline_manifest.json
git diff --cached --check
git diff --cached --name-only
git commit -m "chore(data): re-pin manifest after LOD rebuild"
git push origin HEAD:main
```

Use authenticated GitHub CLI or GitHub REST credentials to follow the newly triggered `data-integrity` run until completion. Confirm all expected steps run, especially both `Pipeline manifest input pinning (Layer 6)` and `Enforce data payload budgets (M7/M8/M9) — BLOCK`, and that the conclusion is `success`.

Finally comment on and close GitHub issue #46 with: commit SHA, scratch-rebuild byte-identity result, local command results, final `--check` PASS, and Actions run URL/conclusion. Do not close the issue until the post-push workflow is green.

## Risks and tradeoffs

- A manifest is a snapshot, not a repair. Re-pinning without the isolated `--to` proof would hide a non-deterministic pipeline or unintended generated-data change.
- The full rebuild uses linked heavy local artifacts. The clean worktree plus explicit scratch directory prevents altering the shared production checkout while still exercising the documented canonical sequence.
- `--verify` writes derivable outputs in place before comparing hashes; this is safe only in the disposable clean worktree. Its diff check is mandatory before re-pin.
- The exact hashes can legitimately differ if `origin/main` advances. The invariant is canonical byte identity plus zero post-pin drift, not preservation of an old hash.

## Acceptance checklist

- [ ] Clean-worktree `--to` reports every declared output byte-identical; semantic `waters.json` comparison has equal slug sets and zero changed records.
- [ ] All eight local data-integrity gates pass, including `--verify` and the Node payload budget.
- [ ] `--manifest` is run only after those checks; final `--check` reports zero drift.
- [ ] Commit is scoped, pushed, and new `data-integrity` run is green.
- [ ] Issue #46 contains evidence and is closed only after the green run.
