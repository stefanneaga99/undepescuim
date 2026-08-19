# Association link safety E2E

Run the seeded presentation checks on the desktop project with:

```bash
env -u PLAYWRIGHT_CDP npx playwright test tests/e2e/specs/flows/association.spec.ts tests/e2e/specs/flows/water-detail.spec.ts --project=desktop
```

The association-detail test covers the association website, location phone/email/site contact, and location provenance/source links. It asserts that external links use `target="_blank"`, `rel` contains both `noopener` and `noreferrer`, and `href` begins with `https://`; phone and email links are checked as `tel:` and `mailto:` destinations. An unsafe `javascript:` fixture URL is asserted to have no clickable anchor.

The water-card test covers the association website, national permit, association permit, telephone, and internal guide links. It asserts that external `href`s are HTTPS with both rel protections, while every rendered card link is limited to `https://`, `tel:`, `mailto:`, or an internal `/` path. Labels are checked for the national permit and guide purpose, and the permit row destination is checked exactly.

Fixtures intercept all app data, including `association_locations.json`; no real network calls are made by these tests.
