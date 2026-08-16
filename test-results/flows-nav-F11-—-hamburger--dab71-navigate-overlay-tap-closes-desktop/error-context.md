# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: flows/nav.spec.ts >> F11 — hamburger menu (mobile) / inline nav (desktop) >> mobile: hamburger opens the sheet, links navigate, overlay tap closes
- Location: tests/e2e/specs/flows/nav.spec.ts:15:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator:  getByTestId('hamburger')
Expected: visible
Received: hidden
Timeout:  10000ms

Call log:
  - Expect "toBeVisible" with timeout 10000ms
  - waiting for getByTestId('hamburger')
    24 × locator resolved to <button type="button" aria-label="Meniu" data-size="icon-sm" data-state="closed" data-variant="ghost" aria-expanded="false" aria-haspopup="dialog" data-testid="hamburger" data-slot="sheet-trigger" class="group/button inline-flex shrink-0 items-center justify-center border border-transparent bg-clip-padding text-sm font-medium whitespace-nowrap transition-all outline-none select-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 active:not-aria-[haspopup]:translate-y-px disa…>…</button>
       - unexpected value "hidden"

```

```yaml
- main:
  - link "UndePescuim.ro — acasă":
    - /url: /
    - text: UndePescuim.ro
  - button "Caută asociația…"
  - navigation:
    - link "Permis 2026":
      - /url: /permis
    - link "Specii":
      - /url: /specii
  - text: RO Județ Toate județele
  - button "Brașov"
  - button "Cluj"
  - button "Iași"
  - button "Ilfov"
  - text: Tip
  - group "Tipul apei":
    - button "Toate" [pressed]
    - button "Lacuri"
    - button "Râuri"
  - text: Contract
  - group "Statusul contractului":
    - button "Toate" [pressed]
    - button "Contractate"
    - button "Necontractate"
  - img
  - button "Zoom in"
  - button "Zoom out"
  - link "Leaflet":
    - /url: https://leafletjs.com
  - text: ©
  - link "OpenStreetMap":
    - /url: https://www.openstreetmap.org/copyright
  - text: Vedere neutră Râuri necontractate Bălți / iazuri necontractate
  - button "Localizează-mă"
- alert
```

# Test source

```ts
  1  | /**
  2  |  * F11 — hamburger menu nav, F12 — back/home (docs/e2e-test-plan.md §3).
  3  |  * F11 runs mobile + desktop (plan §3; tablet skipped).
  4  |  */
  5  | import type { TestInfo } from '@playwright/test';
  6  | import { test, expect } from '../../fixtures/app';
  7  | import { MapPage } from '../../pages/MapPage';
  8  | import { Header } from '../../pages/Header';
  9  | 
  10 | function skipTablet(testInfo: TestInfo): void {
  11 |   test.skip(testInfo.project.name === 'tablet', 'F11 runs on mobile + desktop (plan §3)');
  12 | }
  13 | 
  14 | test.describe('F11 — hamburger menu (mobile) / inline nav (desktop)', () => {
  15 |   test('mobile: hamburger opens the sheet, links navigate, overlay tap closes', async ({
  16 |     mapReady,
  17 |     page,
  18 |   }, testInfo) => {
  19 |     skipTablet(testInfo);
  20 |     await mapReady();
  21 | 
  22 |     const header = new Header(page);
  23 |     const map = new MapPage(page);
  24 | 
  25 |     // hamburger visible, inline links hidden on mobile
> 26 |     await expect(header.hamburger).toBeVisible();
     |                                    ^ Error: expect(locator).toBeVisible() failed
  27 |     await expect(header.navSpecii).toBeHidden();
  28 |     await expect(header.navPermis).toBeHidden();
  29 | 
  30 |     // open the sheet → Specii + Permis links with descriptions
  31 |     await header.openMenu();
  32 |     await expect(page.getByRole('heading', { name: 'Meniu' })).toBeVisible();
  33 |     await expect(header.sheetSpeciiLink).toContainText('Specii');
  34 |     await expect(header.sheetPermisLink).toContainText('Permis 2026');
  35 | 
  36 |     // navigate via the sheet, then come back
  37 |     await header.sheetSpeciiLink.click();
  38 |     await expect(page).toHaveURL(/\/specii$/);
  39 | 
  40 |     // overlay tap closes the sheet without navigating
  41 |     await header.goHome();
  42 |     await expect(page).toHaveURL(/\/$/);
  43 |     await header.openMenu();
  44 |     await page.locator('[data-slot="sheet-overlay"]').click();
  45 |     await expect(header.sheetSpeciiLink).toHaveCount(0);
  46 |   });
  47 | 
  48 |   test('desktop: inline links visible, hamburger hidden; inline link navigates', async ({
  49 |     mapReady,
  50 |     page,
  51 |   }, testInfo) => {
  52 |     skipTablet(testInfo);
  53 |     await mapReady();
  54 | 
  55 |     const header = new Header(page);
  56 |     await expect(header.navSpecii).toBeVisible();
  57 |     await expect(header.navPermis).toBeVisible();
  58 |     await expect(header.hamburger).toBeHidden();
  59 | 
  60 |     await header.navPermis.click();
  61 |     await expect(page).toHaveURL(/\/permis$/);
  62 |   });
  63 | });
  64 | 
  65 | test.describe('F12 — logo returns home', () => {
  66 |   test('clicking the logo from /specii goes back to the map', async ({ page }) => {
  67 |     await page.goto('/specii');
  68 |     const header = new Header(page);
  69 | 
  70 |     await header.goHome();
  71 |     await expect(page).toHaveURL(/\/$/);
  72 |     await expect(page.getByTestId('map-root')).toBeVisible();
  73 |   });
  74 | });
```