# Dependency Upgrade Plan — UndePescuim.ro

Date: 2026-08-17
Author: plan-maker (task t_6c9a5175)
Scope: full audit of all direct deps + the two major-blocked upgrades (eslint 10, typescript 7), plus a concrete unblock path.

## TL;DR

Only **two** packages are stale (`npm outdated`), and **both major bumps are blocked upstream**:

| Package | Current | Latest | Verdict |
|---|---|---|---|
| `eslint` | 9.39.5 | 10.8.1 | **BLOCKED** — `eslint-plugin-react` hard-crashes on eslint 10 |
| `typescript` | 5.9.3 | 7.0.2 | **BLOCKED** — TS 7 is the Go rewrite with no programmatic API |

Everything else is already at latest (next 16.3.1, react 19.2.8, tailwind 4.3.3, zustand 5.0.15, shadcn 4.18.0, etc.). See the full table in §4.

Recommended immediate action: pin both with `ignore` rules in `dependabot.yml` (§6). No code changes.

---

## 1. ESLint 10 — can it work with eslint-config-next? **No (today).**

### 1.1 The crash is real, not a peer warning

Reproduced locally against this exact project (eslint 10.8.1 + eslint-config-next 16.3.1, `--legacy-peer-deps`, linting `src/app/permis/page.tsx`):

```
Oops! Something went wrong! :(

ESLint: 10.8.1

TypeError: Error while loading rule 'react/display-name':
  contextOrFilename.getFilename is not a function
  at resolveBasedir (eslint-plugin-react/lib/util/version.js:31:100)
```

This is the *same* failure that forced the revert in t_c3965b7c.

### 1.2 Root cause

ESLint 10 (released Feb 2026) removed the deprecated `RuleContext` methods
`context.getFilename()`, `context.getCwd()`, `context.getSourceCode()`, replacing
them with properties (`context.filename`, etc.).

`eslint-plugin-react@7.37.5` (latest on npm) still calls the removed methods, in
**three unguarded sites** (verified by grep of the installed package):

- `lib/util/version.js:31` — `contextOrFilename.getFilename()`  ← the crash site
- `lib/rules/jsx-filename-extension.js:64` — `context.getFilename()`
- `lib/rules/forward-ref-uses-ref.js:60` — `context.getSourceCode()`

(`lib/util/eslint.js:4` uses a guarded fallback `context.getSourceCode ? … : context.sourceCode` and is safe.)

There is **no released version** of eslint-plugin-react that supports eslint 10.
The fix exists only as an **unmerged draft PR** — jsx-eslint/eslint-plugin-react#3979
("Fix ESLint v10 RuleContext API removal", drafted 2026-02-10, still not merged as of
2026-08). Tracking issue #3977 is open.

### 1.3 The other two plugins: peer-capped, but not crashing

| Plugin (transitive dep of eslint-config-next) | Latest | peer `eslint` | Deprecated API calls | Real crash risk |
|---|---|---|---|---|
| `eslint-plugin-react` | 7.37.5 | `^3 … ^9.7` | **3 unguarded** | **YES — crashes** |
| `eslint-plugin-import` | 2.32.0 | `^2 … ^9` | none found | none detected |
| `eslint-plugin-jsx-a11y` | 6.10.2 | `^3 … ^9` | none found | none detected |

import and jsx-a11y are only held back by their conservative `peerDependencies`
range (they do not use the removed APIs), but they are pinned by eslint-config-next,
so the *whole* config resolves to eslint 9 today.

### 1.4 What already supports eslint 10 (verified via npm registry peerDeps)

- `typescript-eslint@8.67.0` → peer `eslint: ^8.57.0 || ^9.0.0 || ^10.0.0` ✅
- `eslint-plugin-react-hooks@7.1.1` → peer `eslint: … || ^9.0.0 || ^10.0.0` ✅
- `eslint-config-next@16.3.1` **itself** declares `eslint: >=9.0.0` (so 10 is *not* rejected by the config's own peer range) — but it depends on react/import/jsx-a11y, which are the real blockers.

### 1.5 Flat config — already done

The project is already on ESLint **flat config** (`eslint.config.mjs` using
`defineConfig` + `globalIgnores`). ESLint 10 dropping legacy `.eslintrc` support is
therefore **not** a migration concern for us. The only blocker is the react plugin.

### 1.6 Can we force it with `overrides` / `peerDependenciesMeta`? Not safely.

`npm overrides` can force a *version*, but there is no compatible version of
eslint-plugin-react to force — overriding to 7.37.5 still crashes. `overrides`
alone does not solve this.

The only working stopgap would be a **local source patch** (pnpm `patch` /
`patch-package`) applying PR #3979's diff (replace `context.getFilename()` →
`context.filename`, etc.). This is possible but **not recommended**:

- it vendors an unmerged, draft patch against a third-party package;
- react has three call sites, so a partial patch (version.js only) would merely move
  the crash to jsx-filename-extension.js / forward-ref-uses-ref.js;
- it must be re-checked against every upstream release.

**Decision: keep eslint pinned to `^9`. Wait for upstream.**

### 1.7 Unblock conditions (what must release, in order)

1. eslint-plugin-react ships a release with eslint 10 support (merge + publish PR #3979, close #3977).
2. eslint-config-next bumps its `eslint-plugin-react` / `eslint-plugin-import` / `eslint-plugin-jsx-a11y` deps to those releases (tracking: vercel/next.js#91702).
3. *Then* bump `eslint` to `^10` and run `npm lint` + `npm test` + `npm run build`.

---

## 2. TypeScript — 5.9.3 → 7.0.2 is a trap. **Stay on 5.x.**

### 2.1 What typescript "latest" actually is

`npm outdated` reports `typescript 5.9.3 → 7.0.2`. The npm `latest` tag now points
at the **Go rewrite** ("tsgo"). Version line-up:

- `5.9.3` — current, JavaScript-based, fully supported by everything in the tree.
- `6.0.3` — the **last JavaScript-based** release (a bridge major).
- `7.0.2` — the Go compiler. **No Node programmatic API** (that is slated for TS 7.1).

### 2.2 Why 7.0.2 breaks this project

- `typescript-eslint@8.67.0` peer: `typescript: ">=4.8.4 <6.1.0"` → **rejects TS 7**.
  Even forced, it crashes: `TypeError: Cannot read properties of undefined (reading 'Cjs')`
  in `@typescript-eslint/typescript-estree`. Tracking: typescript-eslint/typescript-eslint#12518
  (status "not planned" — waiting for TS 7.1).
- `next@16.3.1` also fails to detect TS 7: `It looks like you're trying to use TypeScript
  but do not have the required package(s) installed.` (Next's code only gates with
  `semver.gte(tsVersion, '5.0.0'/'5.4.0')`; it has no upper cap, but TS 7's module shape
  is different enough that detection/typing fails.)

### 2.3 Optional: TypeScript 6.0.3

`typescript-eslint` supports `<6.1.0`, so **6.0.3 is allowed by the linter** and it is
a normal JS-based compiler. It is a *possible* stopgap upgrade, but it is **not
required** (5.9.3 is fully supported) and must be verified before merge:

1. `npm i -D typescript@6.0.3`
2. `npm run build` (typecheck + Next build)
3. `npm lint` (typescript-eslint against TS 6)
4. `npm test`

Only adopt if all green. Otherwise stay on 5.9.3.

---

## 3. What's already done / not blocked

Per task handoff, already merged and current: `@types/node@26`, `shadcn@4.18`,
`zustand@5.0.15`. The full `npm outdated` output confirms nothing else is stale.

---

## 4. Full dependency table

`current` = installed, `latest` = npm registry `dist-tags.latest` at 2026-08-17.

| Package | Current | Latest | Compat | Blocker | Action |
|---|---|---|---|---|---|
| eslint | 9.39.5 | 10.8.1 | BLOCKED | eslint-plugin-react crashes on eslint 10 | **PIN ^9**, wait (see §1.7) |
| typescript | 5.9.3 | 7.0.2 | BLOCKED | tsgo no API; typescript-eslint `<6.1.0` | **PIN ^5** (optionally verify 6.0.3, §2.3) |
| eslint-plugin-react *(transitive)* | 7.37.5 | 7.37.5 | BLOCKED | `getFilename()` removed in eslint 10 | wait for upstream release (PR #3979) |
| eslint-plugin-import *(transitive)* | 2.32.0 | 2.32.0 | peer `^9` | peer cap only (no crash) | wait |
| eslint-plugin-jsx-a11y *(transitive)* | 6.10.2 | 6.10.2 | peer `^9` | peer cap only (no crash) | wait |
| eslint-plugin-react-hooks *(transitive)* | 7.1.1 | 7.1.1 | ✅ eslint ^10 | none | already ready |
| typescript-eslint *(transitive)* | 8.67.0 | 8.67.0 | ✅ eslint ^10 / ts <6.1 | none | already ready |
| eslint-config-next | 16.3.1 | 16.3.1 | BLOCKED for eslint 10 | transitive plugin caps | wait (next.js#91702) |
| next | 16.3.1 | 16.3.1 | current | none | no change |
| react / react-dom | 19.2.8 | 19.2.8 | current | none | no change |
| tailwindcss / @tailwindcss/postcss | ^4 → 4.3.3 | 4.3.3 | current | none | no change |
| zustand | 5.0.15 | 5.0.15 | current | none | no change |
| shadcn | 4.18.0 | 4.18.0 | current | none | no change |
| lucide-react | 1.31.0 | 1.31.0 | current | none | no change |
| leaflet / react-leaflet | 1.9.4 / 5.0.0 | same | current | none | no change |
| @types/node | ^26 → 26.2.0 | 26.2.0 | current | none | no change (already merged) |
| @playwright/test / playwright | 1.62.1 | 1.62.1 | current | none | no change |
| vitest / @vitest/coverage-v8 | 4.1.10 | 4.1.10 | current | none | no change |
| serwist / @serwist/next | 9.5.12 | 9.5.12 | current | none | no change |
| remaining deps | — | — | current | none | no change |

---

## 5. Verification already performed (this task)

1. `npm outdated` → only `eslint` (→10.8.1) and `typescript` (→7.0.2) stale.
2. Reproduced the eslint-10 crash against a real project file (exact `getFilename` TypeError).
3. Grepped installed plugin source for deprecated `context.*()` calls:
   react = 3 unguarded sites (crash); import = 0; jsx-a11y = 0; react-hooks = compatible.
4. Queried npm registry peerDeps for all 9 eslint-related packages (react, jsx-a11y,
   import, react-hooks, typescript-eslint ×3, eslint-config-next stable + canary, globals).
5. Confirmed `eslint-config-next@16.3.1-canary.21` still pins the same blocked plugin
   versions (no upstream fix yet).
6. Confirmed baseline is green: `eslint` (9.39.5) on `src/app/permis/page.tsx` → exit 0.
7. Confirmed upstream tracking: jsx-eslint/eslint-plugin-react#3977 (open) / #3979
   (draft, unmerged); vercel/next.js#91702 (open); typescript-eslint#12518 ("not planned").

---

## 6. Recommended change: `dependabot.yml` ignore rules

Add to the existing `npm` update block in `.github/dependabot.yml` (file already exists,
see REM-6). This stops Dependabot from re-opening the two poisoned major bumps while
leaving minor/patch updates flowing:

```yaml
    ignore:
      # eslint 10 removes RuleContext.getFilename() and hard-crashes
      # eslint-plugin-react@7.37.5. Unblock once eslint-config-next supports
      # eslint 10 (it must first bump eslint-plugin-react/import/jsx-a11y).
      # Tracking: vercel/next.js#91702 ; jsx-eslint/eslint-plugin-react#3977 (fix PR #3979)
      - dependency-name: "eslint"
        update-types: ["version-update:semver-major"]
      # typescript 7 (tsgo) has no programmatic API; typescript-eslint (<6.1.0)
      # and Next.js don't support it. Unblock once typescript-eslint ships TS 7
      # support (expected after TS 7.1).
      # Tracking: typescript-eslint/typescript-eslint#12518
      - dependency-name: "typescript"
        update-types: ["version-update:semver-major"]
```

`update-types: ["version-update:semver-major"]` blocks only *major* bumps; weekly
minor/patch PRs for eslint 9.x and typescript 5.x continue normally.

---

## 7. Risks / tradeoffs

- **Local patch escape hatch (NOT recommended):** patching eslint-plugin-react via
  pnpm `patch`/`patch-package` would unblock eslint 10 today, but it vendors an
  unmerged draft against a package with three affected call sites, must be re-verified
  on every release, and would need to be torn out once upstream ships. Rejected for
  this repo's stability posture.
- **Doing nothing on typescript:** 5.9.3 remains fully supported by next + typescript-eslint,
  so there is no urgency; the risk is low. The 6.0.3 option exists if a TS 6-only
  feature is ever needed, but is not required now.
- **Pin drift:** the `ignore` rules are silent by design — the tracking-issue comments
  in the YAML are the trigger for a human to revisit. This is the documented, standard
  mitigation for "ecosystem lag" major bumps (flat-config migration took >1yr; this is
  the same pattern).

---

## 8. Acceptance / unblock checklist (for when upstream catches up)

- [ ] eslint-plugin-react releases an eslint-10-compatible version (PR #3979 merged+pubbed).
- [ ] eslint-config-next bumps react/import/jsx-a11y to compatible versions (next.js#91702).
- [ ] Bump `eslint` to `^10`; run `npm lint`, `npm test`, `npm run build` — all green.
- [ ] typescript-eslint releases TS 7 support (post TS 7.1) AND next supports TS 7.
- [ ] Bump `typescript` accordingly; re-run the same gates.
