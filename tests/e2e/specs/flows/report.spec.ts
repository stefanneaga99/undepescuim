/**
 * F8 — report flow (docs/e2e-test-plan.md §3): both entry points, radios,
 * submit disabled until reason, stubbed /api/report → confirmation with a
 * GitHub link. Runs desktop + mobile (plan §3; tablet skipped).
 */
import type { TestInfo } from '@playwright/test';
import { test, expect } from '../../fixtures/app';
import { MapPage } from '../../pages/MapPage';
import { ReportDialog } from '../../pages/ReportDialog';
import { clickWaterBySlugAtFraction } from '../../helpers/map';
import {
  MULTI_CONTRACT_SELECTED_SLUG,
  REPORT_MULTI_CONTRACT_WATERS,
  seed,
} from '../../fixtures/seed-data';

function skipTablet(testInfo: TestInfo): void {
  test.skip(testInfo.project.name === 'tablet', 'F8 runs on desktop + mobile (plan §3)');
}

test.describe('F8 — report flow', () => {

  test.beforeEach(async ({ page }) => {
    // Keep the multi-contract fixture local to report tests: the rest of the
    // seeded suite has exact path-count assertions over its baseline dataset.
    await page.route('**/data/waters.json', (route) =>
      route.fulfill({ json: [...seed.waters, ...REPORT_MULTI_CONTRACT_WATERS] }),
    );
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

  test('mobile report success preserves multi-contract sector focus pane', async ({ mapReady, page, collectedErrors }, testInfo) => {
    test.skip(testInfo.project.name !== 'mobile', 'focus persistence regression is mobile-only');
    await mapReady();
    const map = new MapPage(page);
    const dialog = new ReportDialog(page);

    await clickWaterBySlugAtFraction(page, 'raul-multi-contract-test', 0.9);
    await expect(map.waterCard.card).toBeVisible();
    const before = await map.focusSnapshot();
    expect(before.slug).toBe(MULTI_CONTRACT_SELECTED_SLUG);
    expect(before.orangePaths).toBeGreaterThan(0);
    expect(Number(before.zIndex)).toBeGreaterThan(400);

    await map.waterCard.clickButton(map.waterCard.reportPositive);
    await dialog.submit();
    await expect(dialog.successText).toBeVisible();
    expect(await map.focusSnapshot()).toEqual(before);
    await dialog.dialog.getByRole('button', { name: 'Închide' }).click();
    await expect(dialog.dialog).toBeHidden();
    expect(await map.focusSnapshot()).toEqual(before);
    expect(collectedErrors).toEqual([]);
  });

  test('mobile report success preserves whole-feature single-contract focus', async ({ mapReady, page, collectedErrors }, testInfo) => {
    test.skip(testInfo.project.name !== 'mobile', 'focus persistence regression is mobile-only');
    await mapReady();
    const map = new MapPage(page);
    const dialog = new ReportDialog(page);

    await map.clickWater('raul-somesul-test');
    const before = await map.focusSnapshot();
    expect(before.slug).toBe('raul-somesul-test');
    expect(before.orangePaths).toBeGreaterThan(0);
    await map.waterCard.clickButton(map.waterCard.reportPositive);
    await dialog.submit();
    await expect(dialog.successText).toBeVisible();
    expect(await map.focusSnapshot()).toEqual(before);
    await dialog.dialog.getByRole('button', { name: 'Închide' }).click();
    expect(await map.focusSnapshot()).toEqual(before);
    expect(collectedErrors).toEqual([]);
  });
});