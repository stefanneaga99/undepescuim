# Local P0 geometry final aggregate

## Scope
- Batches: **190**; Class-1 target coverage: **701**; unresolved Classes 2–6: **312**.
- Reports: completed=40, no-op=149, changed=1, blocked=0, missing=0.
- Changed records: **1**; slugs: 3idcxbvx.

## Canonical safety
- waters before/after/observed: `56380740bbc6a9f91a49b1f4f57ee8465821e9d144eaa39822e9d19d8caab7c0` / `56380740bbc6a9f91a49b1f4f57ee8465821e9d144eaa39822e9d19d8caab7c0` / `56380740bbc6a9f91a49b1f4f57ee8465821e9d144eaa39822e9d19d8caab7c0`
- county clips before/after/observed: `4bf26bb9d352bc112782f5dc2bc9950e5c341ee369493d39b7b84ebe2eda5e92` / `4bf26bb9d352bc112782f5dc2bc9950e5c341ee369493d39b7b84ebe2eda5e92` / `4bf26bb9d352bc112782f5dc2bc9950e5c341ee369493d39b7b84ebe2eda5e92`
- Canonical data mutation: **False**.

## Preview and gates
- Preview: https://undepescuim-geofabrik-preview-gpin6wu2h-stefan-a190.vercel.app — READY (Vercel CLI observed locally); Preview deployment READY; no Production promotion performed.
- Local tsc: blocked separately because the local check/build OOMed.
- Vercel build: passed (Preview READY).
- Aggregate regeneration, unique coverage, and duplicate detection: passed.

## Unresolved artifacts
- Class 2: 163 — `/home/stefan/undepescuim-local-work/.local-work/unresolved-geometry-inventory.json`
- Class 3: 13 — `/home/stefan/undepescuim-local-work/.local-work/unresolved-geometry-inventory.json`
- Class 4: 6 — `/home/stefan/undepescuim-local-work/.local-work/unresolved-geometry-inventory.json`
- Class 5: 12 — `/home/stefan/undepescuim-local-work/.local-work/unresolved-geometry-inventory.json`
- Class 6: 118 — `/home/stefan/undepescuim-local-work/.local-work/unresolved-geometry-inventory.json`

## Local git
- Branch: `local/geometry-batches`; HEAD: `ba20b188634b5f44afe0f5fbd11a4bf77e73e7ab`
- Worktree status captured in JSON; local commit list is captured there.

## External actions
- **No GitHub push and no Production promotion occurred.**

## Report integrity
- Duplicate report groups detected: 5; these are listed in JSON and were not silently counted twice.
- Malformed reports: 0; missing reports: 0.
