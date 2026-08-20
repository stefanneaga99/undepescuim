# Live production QA

This suite is intentionally opt-in: it targets the deployed site, never the
seeded Playwright fixture, and stubs `POST /api/report` before any interaction.

## Browserless CDP (WSL)

Start browserless on port 3000, then run:

```bash
PLAYWRIGHT_CDP=http://localhost:3000 \
LIVE_PROD=1 LIVE_URL=https://undepescuim.vercel.app \
npx playwright test --project=live-prod-desktop --project=live-prod-mobile \
  tests/e2e/specs/live-prod.spec.ts
```

The Playwright config defaults `LIVE_URL` to `https://undepescuim.vercel.app`.
Set it to a preview URL for another deployment. `LIVE_PROD=1` disables the
local `next build`/`next start` web server and selects only the two live
projects. The job is not part of default CI; schedule or invoke it manually
because it exercises a production deployment.

The suite checks map loading and sampled path clicks, county/locality/
association controls, report-dialog stacking and a stubbed report request,
dark mode, language switching, `/specii`, `/permis`, and the PWA manifest.
