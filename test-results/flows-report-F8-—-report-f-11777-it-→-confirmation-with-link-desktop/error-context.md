# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: flows/report.spec.ts >> F8 — report flow >> quick positive tap pre-selects data_correct → submit → confirmation with link
- Location: tests/e2e/specs/flows/report.spec.ts:32:7

# Error details

```
Error: expect(locator).toBeChecked() failed

Locator: getByTestId('report-dialog').getByTestId('report-reason').filter({ has: locator('[data-value="data_correct"]') }).locator('input')
Expected: checked
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeChecked" with timeout 10000ms
  - waiting for getByTestId('report-dialog').getByTestId('report-reason').filter({ has: locator('[data-value="data_correct"]') }).locator('input')

```

```yaml
- dialog "Raportează o problemă":
  - heading "Raportează o problemă" [level=2]
  - paragraph:
    - text: Raportezi date pentru
    - strong: Râul Someșul Test
    - text: .
  - group "Motivul raportului":
    - text: Motivul raportului
    - radio "Datele sunt corecte (am pescuit aici)" [checked]
    - text: Datele sunt corecte (am pescuit aici)
    - radio "Această apă nu mai există / nu se poate pescui"
    - text: Această apă nu mai există / nu se poate pescui
    - radio "Asociația s-a schimbat"
    - text: Asociația s-a schimbat
    - radio "Coordonatele sunt greșite"
    - text: Coordonatele sunt greșite
    - radio "Altă problemă"
    - text: Altă problemă
  - text: Detalii (opțional)
  - textbox "Detalii (opțional)":
    - /placeholder: Descrie ce e greșit, ce ai observat la fața locului…
  - text: Email (opțional, pentru clarificări)
  - textbox "Email (opțional, pentru clarificări)":
    - /placeholder: tu@exemplu.ro
  - paragraph: Dacă îl completezi, adresa va fi vizibilă în raportul public de pe GitHub.
  - button "Anulează"
  - button "Trimite raportul"
  - button "Close"
```

# Test source

```ts
  1   | /**
  2   |  * F8 — report flow (docs/e2e-test-plan.md §3): both entry points, radios,
  3   |  * submit disabled until reason, stubbed /api/report → confirmation with a
  4   |  * GitHub link. Runs desktop + mobile (plan §3; tablet skipped).
  5   |  */
  6   | import type { TestInfo } from '@playwright/test';
  7   | import { test, expect } from '../../fixtures/app';
  8   | import { MapPage } from '../../pages/MapPage';
  9   | import { ReportDialog } from '../../pages/ReportDialog';
  10  | 
  11  | function skipTablet(testInfo: TestInfo): void {
  12  |   test.skip(testInfo.project.name === 'tablet', 'F8 runs on desktop + mobile (plan §3)');
  13  | }
  14  | 
  15  | test.describe('F8 — report flow', () => {
  16  | 
  17  |   test.beforeEach(async ({ page }) => {
  18  |     // Never create real GitHub issues — stub the endpoint (as _e2e_report.mjs).
  19  |     await page.route('**/api/report', async (route) => {
  20  |       if (route.request().method() !== 'POST') return route.continue();
  21  |       const body = route.request().postDataJSON() as Record<string, unknown>;
  22  |       await route.fulfill({
  23  |         contentType: 'application/json',
  24  |         json: {
  25  |           ok: !!(body.reason && body.waterSlug && body.waterName),
  26  |           issueUrl: 'https://github.com/neagastefan99/undepescuim/issues/1',
  27  |         },
  28  |       });
  29  |     });
  30  |   });
  31  | 
  32  |   test('quick positive tap pre-selects data_correct → submit → confirmation with link', async ({
  33  |     mapReady,
  34  |     page,
  35  |   }, testInfo) => {
  36  |     skipTablet(testInfo);
  37  |     await mapReady();
  38  |     const map = new MapPage(page);
  39  |     const dialog = new ReportDialog(page);
  40  | 
  41  |     await map.clickWater('raul-somesul-test');
  42  |     await map.waterCard.clickButton(map.waterCard.reportPositive);
  43  | 
  44  |     await expect(dialog.dialog).toBeVisible();
> 45  |     await expect(dialog.reason('data_correct').locator('input')).toBeChecked();
      |                                                                  ^ Error: expect(locator).toBeChecked() failed
  46  |     await expect(dialog.submitButton).toBeEnabled();
  47  | 
  48  |     await dialog.submit();
  49  |     await expect(dialog.successText).toBeVisible();
  50  |     await expect(dialog.githubLink).toHaveAttribute(
  51  |       'href',
  52  |       'https://github.com/neagastefan99/undepescuim/issues/1',
  53  |     );
  54  |   });
  55  | 
  56  |   test('flag entry: submit disabled until a reason is picked', async ({ mapReady, page }, testInfo) => {
  57  |     skipTablet(testInfo);
  58  |     await mapReady();
  59  |     const map = new MapPage(page);
  60  |     const dialog = new ReportDialog(page);
  61  | 
  62  |     await map.clickWater('raul-somesul-test');
  63  |     await map.waterCard.clickButton(map.waterCard.reportFlag);
  64  | 
  65  |     await expect(dialog.dialog).toBeVisible();
  66  |     await expect(dialog.submitButton).toBeDisabled();
  67  | 
  68  |     await dialog.pickReason('wrong_coordinates');
  69  |     await expect(dialog.submitButton).toBeEnabled();
  70  | 
  71  |     await dialog.submit();
  72  |     await expect(dialog.successText).toBeVisible();
  73  |     await expect(dialog.githubLink).toBeVisible();
  74  |   });
  75  | 
  76  |   test('details + email are optional and carried on the payload', async ({ mapReady, page }, testInfo) => {
  77  |     skipTablet(testInfo);
  78  |     await mapReady();
  79  |     const map = new MapPage(page);
  80  |     const dialog = new ReportDialog(page);
  81  | 
  82  |     const payloadPromise = page.waitForRequest((r) => r.url().endsWith('/api/report'));
  83  |     await map.clickWater('raul-somesul-test');
  84  |     await map.waterCard.clickButton(map.waterCard.reportFlag);
  85  | 
  86  |     await dialog.pickReason('other');
  87  |     await dialog.details.fill('Bariera lipsește pe sectorul test');
  88  |     await dialog.email.fill('pescar@exemplu.ro');
  89  |     await dialog.submit();
  90  | 
  91  |     const payload = payloadPromise.then((r) => r.postDataJSON());
  92  |     await expect(dialog.successText).toBeVisible();
  93  |     const body = await payload;
  94  |     expect(body.reason).toBe('other');
  95  |     expect(body.waterSlug).toBe('raul-somesul-test');
  96  |     expect(body.waterName).toBe('Râul Someșul Test');
  97  |     expect(body.details).toContain('Bariera lipsește');
  98  |     expect(body.contactEmail).toBe('pescar@exemplu.ro');
  99  |   });
  100 | });
```