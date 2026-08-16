/**
 * F8 — report flow (docs/e2e-test-plan.md §3): both entry points, radios,
 * submit disabled until reason, stubbed /api/report → confirmation with a
 * GitHub link. Runs desktop + mobile (plan §3; tablet skipped).
 */
import type { TestInfo } from '@playwright/test';
import { test, expect } from '../../fixtures/app';
import { MapPage } from '../../pages/MapPage';
import { ReportDialog } from '../../pages/ReportDialog';

function skipTablet(testInfo: TestInfo): void {
  test.skip(testInfo.project.name === 'tablet', 'F8 runs on desktop + mobile (plan §3)');
}

test.describe('F8 — report flow', () => {

  test.beforeEach(async ({ page }) => {
    // Never create real GitHub issues — stub the endpoint (as _e2e_report.mjs).
    await page.route('**/api/report', async (route) => {
      if (route.request().method() !== 'POST') return route.continue();
      const body = route.request().postDataJSON() as Record<string, unknown>;
      await route.fulfill({
        contentType: 'application/json',
        json: {
          ok: !!(body.reason && body.waterSlug && body.waterName),
          issueUrl: 'https://github.com/neagastefan99/undepescuim/issues/1',
        },
      });
    });
  });

  test('quick positive tap pre-selects data_correct → submit → confirmation with link', async ({
    mapReady,
    page,
  }, testInfo) => {
    skipTablet(testInfo);
    await mapReady();
    const map = new MapPage(page);
    const dialog = new ReportDialog(page);

    await map.clickWater('raul-somesul-test');
    await map.waterCard.clickButton(map.waterCard.reportPositive);

    await expect(dialog.dialog).toBeVisible();
    await expect(dialog.reason('data_correct').locator('input')).toBeChecked();
    await expect(dialog.submitButton).toBeEnabled();

    await dialog.submit();
    await expect(dialog.successText).toBeVisible();
    await expect(dialog.githubLink).toHaveAttribute(
      'href',
      'https://github.com/neagastefan99/undepescuim/issues/1',
    );
  });

  test('flag entry: submit disabled until a reason is picked', async ({ mapReady, page }, testInfo) => {
    skipTablet(testInfo);
    await mapReady();
    const map = new MapPage(page);
    const dialog = new ReportDialog(page);

    await map.clickWater('raul-somesul-test');
    await map.waterCard.clickButton(map.waterCard.reportFlag);

    await expect(dialog.dialog).toBeVisible();
    await expect(dialog.submitButton).toBeDisabled();

    await dialog.pickReason('wrong_coordinates');
    await expect(dialog.submitButton).toBeEnabled();

    await dialog.submit();
    await expect(dialog.successText).toBeVisible();
    await expect(dialog.githubLink).toBeVisible();
  });

  test('details + email are optional and carried on the payload', async ({ mapReady, page }, testInfo) => {
    skipTablet(testInfo);
    await mapReady();
    const map = new MapPage(page);
    const dialog = new ReportDialog(page);

    const payloadPromise = page.waitForRequest((r) => r.url().endsWith('/api/report'));
    await map.clickWater('raul-somesul-test');
    await map.waterCard.clickButton(map.waterCard.reportFlag);

    await dialog.pickReason('other');
    await dialog.details.fill('Bariera lipsește pe sectorul test');
    await dialog.email.fill('pescar@exemplu.ro');
    await dialog.submit();

    const payload = payloadPromise.then((r) => r.postDataJSON());
    await expect(dialog.successText).toBeVisible();
    const body = await payload;
    expect(body.reason).toBe('other');
    expect(body.waterSlug).toBe('raul-somesul-test');
    expect(body.waterName).toBe('Râul Someșul Test');
    expect(body.details).toContain('Bariera lipsește');
    expect(body.contactEmail).toBe('pescar@exemplu.ro');
  });
});