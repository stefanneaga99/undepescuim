/**
 * F10 — /permis page (2026 permit & rules guide).
 * Runs in all three viewports. SSR static content — no map involved.
 */
import { test, expect } from '../../fixtures/app';
import { PermisPage } from '../../pages/PermisPage';

test.describe('F10 — /permis page', () => {
  test('renders heading, sections, portal link, and /specii cross-link', async ({ page }) => {
    const permis = new PermisPage(page);
    await page.goto('/permis');

    await expect(permis.h1).toBeVisible();
    await expect(page.getByRole('heading', { name: /Ce s-a schimbat: ANPA → ANADSPA/ })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Cum obții permisul în 2026/ })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Cum reînnoiești permisul/ })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Capcane cunoscute/ })).toBeVisible();
    await expect(page.getByRole('heading', { name: /FAQ/ })).toBeVisible();

    // the official permit portal link opens externally (target _blank)
    await expect(permis.portalLink).toHaveAttribute('target', '_blank');
    await expect(permis.portalLink).toHaveAttribute('href', /^https:\/\//);

    // cross-link to the species page
    await expect(permis.speciiCrossLink).toBeVisible();
    await permis.speciiCrossLink.click();
    await expect(page).toHaveURL(/\/specii$/);
    await expect(page.getByRole('heading', { name: /Dimensiuni minime de reținere/ })).toBeVisible();
  });

  test('back link returns to the map', async ({ page }) => {
    const permis = new PermisPage(page);
    await page.goto('/permis');

    await expect(permis.backLink).toBeVisible();
    await permis.backLink.click();
    await expect(page).toHaveURL(/\/$/);
  });
});