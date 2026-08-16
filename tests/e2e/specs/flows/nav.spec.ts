/**
 * F11 — hamburger menu nav, F12 — back/home (docs/e2e-test-plan.md §3).
 * F11 runs mobile + desktop (plan §3; tablet skipped).
 */
import type { TestInfo } from '@playwright/test';
import { test, expect } from '../../fixtures/app';
import { MapPage } from '../../pages/MapPage';
import { Header } from '../../pages/Header';

function skipTablet(testInfo: TestInfo): void {
  test.skip(testInfo.project.name === 'tablet', 'F11 runs on mobile + desktop (plan §3)');
}

test.describe('F11 — hamburger menu (mobile) / inline nav (desktop)', () => {
  test('mobile: hamburger opens the sheet, links navigate, overlay tap closes', async ({
    mapReady,
    page,
  }, testInfo) => {
    skipTablet(testInfo);
    await mapReady();

    const header = new Header(page);
    const map = new MapPage(page);

    // hamburger visible, inline links hidden on mobile
    await expect(header.hamburger).toBeVisible();
    await expect(header.navSpecii).toBeHidden();
    await expect(header.navPermis).toBeHidden();

    // open the sheet → Specii + Permis links with descriptions
    await header.openMenu();
    await expect(page.getByRole('heading', { name: 'Meniu' })).toBeVisible();
    await expect(header.sheetSpeciiLink).toContainText('Specii');
    await expect(header.sheetPermisLink).toContainText('Permis 2026');

    // navigate via the sheet, then come back
    await header.sheetSpeciiLink.click();
    await expect(page).toHaveURL(/\/specii$/);

    // overlay tap closes the sheet without navigating
    await header.goHome();
    await expect(page).toHaveURL(/\/$/);
    await header.openMenu();
    await page.locator('[data-slot="sheet-overlay"]').click();
    await expect(header.sheetSpeciiLink).toHaveCount(0);
  });

  test('desktop: inline links visible, hamburger hidden; inline link navigates', async ({
    mapReady,
    page,
  }, testInfo) => {
    skipTablet(testInfo);
    await mapReady();

    const header = new Header(page);
    await expect(header.navSpecii).toBeVisible();
    await expect(header.navPermis).toBeVisible();
    await expect(header.hamburger).toBeHidden();

    await header.navPermis.click();
    await expect(page).toHaveURL(/\/permis$/);
  });
});

test.describe('F12 — logo returns home', () => {
  test('clicking the logo from /specii goes back to the map', async ({ page }) => {
    await page.goto('/specii');
    const header = new Header(page);

    await header.goHome();
    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByTestId('map-root')).toBeVisible();
  });
});