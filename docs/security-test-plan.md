# UndePescuim.ro — Security Test Plan & Checklist

**Task:** t_1817e34a (QA SPIKE — SECURITY)
**Author:** plan-maker
**Date:** 2026-08-16
**Status:** DRAFT — for review (see §9)
**Repo:** `/home/stefan/undepescuim` (GitHub `neagastefan99/undepescuim`, public)

---

## 0. How to read this document

- **`[CONFIRMED]`** = verified statically this session (read the code, ran the command).
- **`[RUNTIME]`** = must be verified against a live deployment / in the GitHub & Vercel
  consoles — cannot be done from a sandbox without deploy access.
- Every test case has an ID (`SEC-NN`), a command/procedure, and a pass criterion, so
  the executioner can run it mechanically and tick a box.

---

## 1. Executive summary

UndePescuim.ro is a **static-first Next.js app with exactly one serverless endpoint**
(`POST /api/report`) whose only job is to create a GitHub issue from an in-app form.
The app has **no database, no auth/session, no user accounts, and no URL-accepting
input**, which eliminates whole classes of vulnerability (SQLi, auth bypass, SSRF,
CSRF-with-cookies) by construction.

The residual, real risks — ranked in §3 — are:

1. **Report-endpoint abuse / spam** (no rate limiting, honeypot only) — HIGH likelihood.
2. **GitHub token mishandling** (scope too broad, or leakage via future change / supply
   chain) — LOW likelihood, HIGH impact.
3. **Issue-content injection** (markdown/`@mention`/tracking-pixel via the free-text
   `details` and `waterName` fields) — LOW severity, but real.
4. **PII in public issues** (`contactEmail` is written verbatim into a *public* GitHub
   issue body) — privacy risk, not a classic vuln.
5. **Missing hardening headers** (no CSP, no HSTS, no explicit frame/ref protections
   beyond Next.js defaults) — LOW severity for this threat model, cheap to fix.

The codebase is in genuinely good shape: **no `dangerouslySetInnerHTML`/`innerHTML`/
`eval`**, **no `http://` mixed-content subresources**, **`.env.local` and `.vercel/`
correctly gitignored**, **lockfile committed**, **`npm audit` = 0 vulnerabilities**,
and **all external links carry `rel="noopener noreferrer"`**. The work below is mostly
hardening + adding automated guards, not fixing an active exploit.

---

## 2. Attack surface inventory

### 2.1 POST /api/report — `src/app/api/report/route.ts` (the only backend endpoint)

| # | Item | Finding | Risk |
|---|------|---------|------|
| 1a | GH token handling | `REPORT_GITHUB_TOKEN` read from `process.env` (server-side only, never `NEXT_PUBLIC_`), used as `Authorization: Bearer ${token}`. `[CONFIRMED]` correct. Token scope per ARCHITECTURE.md is fine-grained **Issues: Read & Write on `neagastefan99/undepescuim` only** — `[RUNTIME]` verify in GitHub → Settings → Developer settings → Fine-grained tokens. | Token theft = repo write (issues) |
| 1b | Token leakage in responses/logs | Responses return only generic codes (`invalid_json`, `invalid_reason`, `missing_water`, `not_configured`, `github_error`) — never the token. `[CONFIRMED]` **BUT** line 71 logs `res.text()` of the GitHub error body: `console.error('[report] create issue failed', res.status, await res.text())`. GitHub error bodies do not include the token, and Vercel function logs are private, but a paranoid future edit could log the request/response headers. Flag as a review item. | Low (log hygiene) |
| 1c | Input validation | `reason` whitelisted against a `Set` (5 values). `[CONFIRMED]` ✓. Length caps: `waterSlug` 128, `waterName` 256, `details` 2000, `contactEmail` 254. `[CONFIRMED]` ✓. **No format validation** on slug/name/email; `contactEmail` is not validated as an email. | Low |
| 1d | Rate limiting | **NONE.** No per-IP/per-key throttle, no captcha, no Vercel WAF rule. The only bot defense is a honeypot `website` field (hidden, `tabIndex=-1`, `aria-hidden`; filled → silent `200 {ok:true, issueUrl:null}`). Honeypot stops naive bots, not a scripted loop. `[CONFIRMED]` | **HIGH** (spam/abuse) |
| 1e | Abuse / spam issue creation | Confirmed risk — an attacker can `curl` the endpoint in a loop to flood the repo with `report`-labelled issues and burn the token's GitHub API quota (fine-grained tokens: 5,000 req/hr). | **HIGH** |
| 1f | SSRF | **No URL inputs anywhere** in the request schema. The only outbound fetch is a hardcoded `https://api.github.com/repos/neagastefan99/undepescuim/issues`. `[CONFIRMED]` no SSRF. | None |
| 1g | Error messages / stack traces | All error paths return generic JSON; no stack traces. `[CONFIRMED]` ✓ | None |
| 1h | Content injection (issue title/body) | `waterName` is interpolated **unescaped** into the issue **title**; `details` and `contactEmail` into the **body**. User input can inject GitHub markdown: `@mentions` (pings maintainers/other users), `#refs`, embedded images (tracking pixels / IP logging), `[x]` task lists, links. No code execution on GitHub, but a spam/phish/notification-abuse vector. `[CONFIRMED]` | Low–Med |
| 1i | PII in public issue | `contactEmail` is written verbatim into a **public** GitHub issue body. The form labels it "optional, for clarifications" with no warning that it becomes public. `[CONFIRMED]` | Privacy (Med) |
| 1j | Method handling | Only `POST` and `GET` are exported; `GET` returns 405, other verbs fall to Next's 405. `[CONFIRMED]` ✓ | None |

### 2.2 Client-side XSS

| # | Item | Finding | Risk |
|---|------|---------|------|
| 2a | `dangerouslySetInnerHTML` / raw HTML | `grep` over `src/**/*.{ts,tsx}` for `dangerouslySetInnerHTML`, `innerHTML`, `insertAdjacentHTML`, `document.write`, `__html`, `new Function`, `eval(` → **0 hits**. `[CONFIRMED]` ✓ | None |
| 2b | User input rendered back? | Report-form fields (`details`, `contactEmail`) are sent to the server and never rendered into the DOM. `waterName`/`waterSlug` are auto-attached from trusted static JSON. The only report-derived value rendered is `issueUrl` (from GitHub's own `html_url`) as an `<a href>` — attribute-escaped by React, and sourced from GitHub's API, not user input. `[CONFIRMED]` ✓ | None |
| 2c | `href` scheme injection via data files | `siteUrl` / `permitUrl` are rendered as `<a href={siteUrl}>`. React does **not** sanitize `href` against `javascript:` URIs. These values come from repo-controlled `public/data/*.json` (trusted), so risk is near-zero — but a data-editing mistake (or a compromised data-refresh scrape) could inject `javascript:`. Add the data-integrity check in SEC-08. `[CONFIRMED]` low | Low |
| 2d | External links / reverse tabnabbing | All `target="_blank"` links (`siteUrl`, `permitUrl`, `NATIONAL_PERMIT_URL`) carry `rel="noopener noreferrer"`. `[CONFIRMED]` ✓ | None |

### 2.3 Dependency audit

| # | Item | Finding | Risk |
|---|------|---------|------|
| 3a | `npm audit` | **`found 0 vulnerabilities`** (run this session, lockfile `package-lock.json` present). `[CONFIRMED]` point-in-time. | None today |
| 3b | CVE watch on next/leaflet | `next 16.3.0`, `react 19.2.8`, `leaflet ^1.9.4`, `react-leaflet ^5.0.0`. No known CVEs at audit time. Next.js is the largest surface — needs ongoing monitoring. `[CONFIRMED]` clean today. | Med (future) |
| 3c | `fuse.js` | **Not a dependency.** The task brief assumed fuse (from the ARCHITECTURE.md draft), but search is implemented differently and `package.json` has no fuse. Remove fuse from any CVE watchlist; nothing to audit there. `[CONFIRMED]` | N/A |
| 3d | Audit in CI | The only workflow (`.github/workflows/data-refresh.yml`) runs `npm ci` but **no `npm audit`**, no Dependabot, no dependency-review action. `[CONFIRMED]` gap. | Med (gap) |

### 2.4 Headers / CSP

| # | Item | Finding | Risk |
|---|------|---------|------|
| 4a | Security headers | `vercel.json` sets **only** `Cache-Control` for `/data/*` and `/_next/static/*`. **No CSP, no HSTS, no `X-Frame-Options`, no `Referrer-Policy`, no `Permissions-Policy`, no `X-Content-Type-Options`.** Next.js ships `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, and `Referrer-Policy: strict-origin-when-cross-origin` by default, but **CSP and HSTS are not** set by default. `[CONFIRMED]` gap. | Low–Med |
| 4b | Mixed content | OSM tiles use `https://{s}.tile.openstreetmap.org/...`. No `http://` subresources found. `[CONFIRMED]` ✓. (External `siteUrl` values in data *may* be `http://` — that's an outbound link, not mixed content.) | None |
| 4c | Live headers | `undepescuim.ro` **does not resolve** (no DNS yet — `[CONFIRMED]` this session). Live header verification is a `[RUNTIME]` step post-deploy. | Deferred |

### 2.5 Secrets hygiene

| # | Item | Finding | Risk |
|---|------|---------|------|
| 5a | `.env` committed? | `.gitignore` contains `.env*`; `git check-ignore .env.local` → ignored; `git ls-files | grep -iE '\.env|secret|token|\.pem|\.key'` → **no hits**; `git status --porcelain` → clean. `[CONFIRMED]` ✓ | None |
| 5b | Env var names | `.env.local` declares `REPORT_GITHUB_TOKEN` and `VERCEL_OIDC_TOKEN` (keys only inspected; values not read). Neither is `NEXT_PUBLIC_*`. `[CONFIRMED]` ✓ | None |
| 5c | `.vercel/` committed? | `.gitignore` has `.vercel`; `.vercel/project.json` (projectId/orgId) is untracked. `[CONFIRMED]` ✓ | None |
| 5d | Vercel env scoping | Token must be scoped to **Production + Preview** (per ARCHITECTURE.md) and never exposed to the browser. `[RUNTIME]` verify in Vercel → Project → Settings → Environment Variables (and confirm no `NEXT_PUBLIC_REPORT_GITHUB_TOKEN` exists). | Med |
| 5e | Repo secret scanning | Public repo → enable GitHub **secret scanning** (free) and push protection. `[RUNTIME]` verify in GitHub → Settings → Code security. | Med |

### 2.6 Supply chain

| # | Item | Finding | Risk |
|---|------|---------|------|
| 6a | Lockfile integrity | `package-lock.json` (407 KB) committed; CI uses `npm ci` (reproducible). `[CONFIRMED]` ✓ | None |
| 6b | Pinning | Deps are caret-ranged (`^`). Lockfile pins exact transitive versions at install, so builds are reproducible; ranges only matter on `npm install`. Acceptable for this app. `[CONFIRMED]` OK | Low |
| 6c | Node pinning | Workflow pins `node-version: 20` but `package.json` has no `engines` field. Minor. | Low |
| 6d | Dependabot / SBOM | **None configured.** `[CONFIRMED]` gap. | Med (gap) |

---

## 3. Threat model (ranked)

**Attacker personas:** (A) internet rando / spammer, (B) scripted bot operator,
(C) an attacker who has stolen or tricked a token, (D) a poisoned upstream data source.

| Rank | Threat | Likelihood | Impact | Vector | Mitigation / test |
|------|--------|-----------|--------|--------|-------------------|
| 1 | Report-endpoint spam → issue flood + token quota burn | High | Medium | `curl` loop on `/api/report` | Rate limit + captcha (SEC-01, REM-1) |
| 2 | Token theft (leak via code change / supply-chain / misconfig) | Low | High | leaked `REPORT_GITHUB_TOKEN` | Fine-grained scope, secret scanning, pinning (SEC-04/05/07, REM-2) |
| 3 | Issue-content injection (markdown / `@mention` / tracking pixel) | Medium | Low | `details`/`waterName` → issue title/body | Sanitize issue body, strip markdown (SEC-02, REM-3) |
| 4 | PII exposure — user email in public issue | Medium | Medium (privacy) | `contactEmail` → public issue | Warn user / drop email from body (REM-4) |
| 5 | Defacement via data injection | Low | Low–Med | convincing a maintainer to merge a poisoned report into static JSON | Data-integrity checks in CI (SEC-08, REM-5) |
| 6 | XSS (stored/reflected) | Very low | Low | no render path today | keep the no-`innerHTML` invariant (SEC-06) |
| 7 | Dependency CVE (next.js et al.) | Low | Medium (future) | unpinned transitive dep | `npm audit` + Dependabot in CI (SEC-07, REM-6) |
| 8 | Clickjacking / missing hardening headers | Low | Low | missing CSP/HSTS/frame opts | add headers (SEC-03, REM-7) |
| 9 | `javascript:` href via data files | Very low | Low | poisoned `siteUrl` in JSON | data-integrity check (SEC-08) |

---

## 4. Test cases

Legend: each case states **Setup / Steps / Expected / Auto?**.

### SEC-01 — Report endpoint: validation & abuse (payload fuzz, no token)

Safe to run against a live or local deployment **without** a real token: all the
400-path assertions return *before* the token is read (line 30–44), so no GitHub
issues are created.

```bash
BASE=https://undepescuim.ro          # or http://localhost:3000 for `next dev`

# 1. valid JSON, invalid reason
curl -s -X POST "$BASE/api/report" -H 'Content-Type: application/json' \
  -d '{"reason":"__evil__","waterSlug":"x","waterName":"y"}' -w '\n%{http_code}\n'
# expect: {"ok":false,"error":"invalid_reason"} / 400

# 2. invalid JSON body
curl -s -X POST "$BASE/api/report" -H 'Content-Type: application/json' \
  -d '{not json' -w '\n%{http_code}\n'
# expect: {"ok":false,"error":"invalid_json"} / 400

# 3. missing water fields
curl -s -X POST "$BASE/api/report" -H 'Content-Type: application/json' \
  -d '{"reason":"other"}' -w '\n%{http_code}\n'
# expect: {"ok":false,"error":"missing_water"} / 400

# 4. GET (and PUT/HEAD) must be rejected
curl -s -X GET "$BASE/api/report" -w '\n%{http_code}\n'
# expect: {"ok":false,"error":"method_not_allowed"} / 405

# 5. honeypot filled → silent 200, no issue
curl -s -X POST "$BASE/api/report" -H 'Content-Type: application/json' \
  -d '{"reason":"other","waterSlug":"x","waterName":"y","website":"http://spam.example"}' -w '\n%{http_code}\n'
# expect: {"ok":true,"issueUrl":null} / 200

# 6. missing token (locally: unset REPORT_GITHUB_TOKEN) → 503, no crash
curl -s -X POST "$BASE/api/report" -H 'Content-Type: application/json' \
  -d '{"reason":"other","waterSlug":"x","waterName":"y"}' -w '\n%{http_code}\n'
# expect (local w/o token): {"ok":false,"error":"not_configured"} / 503

# 7. length-cap truncation: 10,000-char details must not 500
python3 - <<'PY'
import json,urllib.request
body=json.dumps({"reason":"other","waterSlug":"s","waterName":"n","details":"A"*10000}).encode()
req=urllib.request.Request("$BASE/api/report",data=body,headers={"Content-Type":"application/json"})
try:
    r=urllib.request.urlopen(req); print(r.status, r.read()[:200])
except urllib.error.HTTPError as e:
    print(e.code, e.read()[:200])
PY
# expect: 200 (with token) or 503 (no token) — never a 500 / stack trace
```

**Abuse check (manual, on a test repo first — do NOT flood production):**
time 50 sequential valid POSTs with a real token and confirm they all create issues
(expected today, since there is no rate limit) — then treat this as the failing test
that motivates REM-1.

### SEC-02 — Issue content injection (markdown)

1. POST with `reason:"other"`, `waterName:"<img src=x onerror=alert(1)>"` and
   `details` containing `@someuser`, `#123`, `![x](https://attacker.example/px.png)`,
   and `[ ] task`.
2. Inspect the created GitHub issue.
3. Expected **today**: the raw markdown lands in the title/body verbatim (this is the
   finding, not a pass). After REM-3: title/body should contain the *escaped* text
   (no active markdown, no `@mention`, no image).
4. Confirm no JavaScript executes in the GitHub issue view (it won't — GitHub
   sanitizes issue HTML; the residual risk is @mention abuse + tracking pixels).

### SEC-03 — Security headers (runtime, post-deploy)

```bash
curl -sI https://undepescuim.ro
curl -sI https://undepescuim.ro/api/report
# Assert (after REM-7): content-security-policy, strict-transport-security,
# x-frame-options (or frame-ancestors), referrer-policy, x-content-type-options, permissions-policy
```
Also verify `https://undepescuim.ro` auto-upgrades `http://` → 301 to https (HSTS).

### SEC-04 — Token scope (runtime, GitHub console)

1. GitHub → Settings → Developer settings → Fine-grained PATs → find the token backing
   `REPORT_GITHUB_TOKEN`.
2. Assert: **repository access = `neagastefan99/undepescuim` only** (not "all repos"),
   permissions = **Issues: Read & Write only**, no `Contents`, no org/admin scopes.

### SEC-05 — Secret hygiene (static, scripted)

```bash
cd ~/undepescuim
git ls-files | grep -iE '\.env|secret|token|credential|\.pem|\.key$' && echo "FAIL: secret-named file tracked" || echo "PASS"
git grep -nE 'REPORT_GITHUB_TOKEN|NEXT_PUBLIC_' -- ':!docs' ':!package-lock.json' || true   # only allowed in route.ts + .env.local
grep -rn "NEXT_PUBLIC_" src/ && echo "FAIL: client-exposed env" || echo "PASS: no NEXT_PUBLIC_ in src"
```
Also assert no `ghp_` / `github_pat_` / `Bearer ` literal token in `git log -p` history.

### SEC-06 — XSS static audit (scripted)

```bash
cd ~/undepescuim
grep -rnE 'dangerouslySetInnerHTML|__html|innerHTML|insertAdjacentHTML|document\.write|new Function|eval\(' src/ && echo "FAIL" || echo "PASS: no raw-HTML sinks"
```
Add this as a CI lint gate so a future `dangerouslySetInnerHTML` can't sneak in.

### SEC-07 — Dependency audit (automated, CI)

```bash
cd ~/undepescuim
npm ci
npm audit --audit-level=high        # fail build on high/critical
npm audit --omit=dev --audit-level=moderate   # prod deps stricter
```
Expected today: exit 0. Add the CI job in §5.

### SEC-08 — Data-integrity / scheme check (scripted, CI)

Assert every URL-ish field in `public/data/*.json` is `http(s)` (never `javascript:`/
`data:`/`vbscript:`), and every phone is numeric-ish:

```bash
cd ~/undepescuim
node -e '
const fs=require("fs");
const bad=[];
for(const f of fs.readdirSync("public/data").filter(x=>x.endsWith(".json"))){
  const j=JSON.parse(fs.readFileSync("public/data/"+f,"utf8"));
  const walk=(o,p)=>{ if(o==null)return; if(typeof o==="string"){
    if(/^(javascript|data|vbscript):/i.test(o.trim())) bad.push(f+" :: "+p+" = "+o);
    if((p.endsWith("Url")||p.endsWith("siteUrl"))&&o&&!/^https?:\/\//i.test(o)) bad.push(f+" :: "+p+" = "+o);
  } else if(Array.isArray(o)) o.forEach((v,i)=>walk(v,p+"["+i+"]"));
  else if(typeof o==="object") Object.entries(o).forEach(([k,v])=>walk(v,p+"."+k)); };
  walk(j,"$");
}
console.log(bad.length? "FAIL:\n"+bad.join("\n") : "PASS: no dangerous URL schemes in data");
process.exit(bad.length?1:0);
'
```

### SEC-09 — End-to-end report flow (automated, existing)

`scripts/_e2e_report.mjs` already stubs `/api/report` and asserts the form
(5 radios, disabled-until-reason, success state, positive-tap preselect). Re-run it
as the functional baseline, then layer the security cases on top:

```bash
cd ~/undepescuim && node scripts/_e2e_report.mjs http://localhost:3000
```

---

## 5. Automated checks to add (CI)

Add a second workflow (e.g. `.github/workflows/security.yml`) triggered on PR + push,
alongside the existing `data-refresh.yml`:

```yaml
name: Security
on: [pull_request, push]
permissions: { contents: read }
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - run: npm audit --audit-level=high
      - name: XSS sink scan
        run: |
          if grep -rnE 'dangerouslySetInnerHTML|__html|innerHTML|document\.write|new Function|eval\(' src/; then
            echo "::error:: raw-HTML sink found"; exit 1
          fi
      - name: Data scheme scan
        run: node scripts/security_data_check.mjs   # = SEC-08 script, extracted to a file
  deps:
    runs-on: ubuntu-latest
    permissions: { contents: read, pull-requests: write }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/dependency-review-action@v4     # flags new risky deps on PR
```

Also enable **Dependabot** (GitHub → Settings → Code security → Dependabot) for
`package-lock.json`, and **secret scanning + push protection** for the public repo.

---

## 6. Pre-launch security checklist (tick before shipping)

- [ ] **SEC-04** Token is fine-grained, single-repo, Issues-only — verified in GitHub.
- [ ] **SEC-05** No secret in git history or tracked files; `NEXT_PUBLIC_*` absent.
- [ ] **SEC-08** Data URL-scheme scan passes.
- [ ] **SEC-07** `npm audit` clean; Dependabot + dependency-review enabled.
- [ ] **SEC-03** `vercel.json` gains CSP + HSTS + frame/ref headers (REM-7); live `curl -sI` confirms.
- [ ] **SEC-01** Validation fuzz passes (400/405/503 branches, no 500s, no stack traces).
- [ ] **REM-1** Rate limiting (or captcha) in place on `/api/report` — otherwise accept
      the documented spam risk and set the repo up so `report`-labelled issues can be
      bulk-closed.
- [ ] **REM-3** Issue title/body sanitized (strip markdown / escape user text).
- [ ] **REM-4** `contactEmail` removed from the public issue body, or the form adds an
      explicit "your email will be visible in a public GitHub issue" notice.
- [ ] **SEC-09** `_e2e_report.mjs` green.
- [ ] **SEC-06** XSS-sink lint gate in CI.
- [ ] Vercel env `REPORT_GITHUB_TOKEN` scoped Production + Preview; `report` label
      exists on the repo (else issue creation 422s).

---

## 7. Remediation priorities

| # | Fix | Effort | File(s) | Why |
|---|-----|--------|---------|-----|
| REM-1 | Rate limiting: Vercel WAF rate-limit rule, or in-route IP throttle via `@upstash/ratelimit` + `@vercel/kv`, or a Cloudflare Turnstile captcha on the form. | Med | `src/app/api/report/route.ts` (+ Vercel dashboard) | Closes threat #1 |
| REM-2 | Confirm fine-grained token scope; enable secret scanning + push protection. | Low | GitHub settings | Closes threat #2 |
| REM-3 | Escape/neutralize user text before building the issue title/body: strip leading `#`, `@`, `![]`, blockquotes; or wrap `details` in a fenced block and truncate `waterName` to `[A-Za-z0-9 .\-]`. | Low | `src/app/api/report/route.ts` | Closes threat #3 |
| REM-4 | Drop `contactEmail` from the public body (route it to a private channel) or add a consent notice in the form. | Low | `route.ts` / `ReportForm.tsx` | Privacy (#4) |
| REM-5 | Data-integrity CI (SEC-08) so a bad scrape/merge can't inject `javascript:` or junk URLs. | Low | new CI step | #5, #9 |
| REM-6 | `npm audit` + Dependabot + dependency-review action. | Low | `.github/workflows/security.yml` | #7 |
| REM-7 | Add headers via `next.config.ts` `headers()` or `vercel.json`: CSP (start permissive, then tighten), `Strict-Transport-Security`, `X-Frame-Options: DENY`/`frame-ancestors 'none'`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy`. | Low | `next.config.ts` / `vercel.json` | #8 |

---

## 8. Risks & tradeoffs

- **Rate limiting vs. friction.** A captcha on a public fishing map adds friction to
  the exact crowdsourcing feature the app wants. A Vercel WAF per-IP rule is invisible
  to real users — prefer that first, captcha only if spam materializes.
- **CSP on a Leaflet app.** A strict CSP can break OSM tile loading, inline Leaflet
  styles, and `react-leaflet`'s injected SVG. Deploy CSP in report-only mode and
  iterate; start with `default-src 'self'; img-src 'self' data: blob: https://*.tile.openstreetmap.org; connect-src 'self'`.
- **Sanitizing issue text reduces fidelity.** Escaping markdown is safe; do not
  silently drop the `details` field — users rely on it. Neutralize, don't discard.
- **`npm audit --audit-level=high` can false-positive on dev-only deps.** Keep dev and
  prod audit separate (SEC-07) to avoid blocking builds on irrelevant dev tools.
- **Token in a static-ish repo.** There is no server besides the one serverless
  function, so the token can only live in Vercel env — that's the correct home. The
  residual risk is a future `NEXT_PUBLIC_` mistake, which SEC-05/CI guards against.

---

## 9. Sign-off

This plan covers the four mandated deliverables: attack-surface inventory (§2),
threat model (§3), per-surface checks incl. automatable ones (§4–5), and a security
test plan + checklist (§4, §6). `[RUNTIME]` items are queued for the first post-deploy
QA pass, when `undepescuim.ro` resolves. Flagging for **review-required** — the
remediation list (REM-1 rate limiting, REM-3 sanitization, REM-4 PII) needs a product
decision on friction vs. spam tolerance before implementation tasks are cut.
