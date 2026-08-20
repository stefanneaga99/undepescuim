import { test, expect } from '@playwright/test';

test.describe('incident routing guide', () => {
  test('keeps emergency and non-urgent routes distinct', async ({ page }) => {
    await page.goto('/sesizeaza');
    await expect(page.getByRole('heading', { name: 'Ai văzut braconaj, poluare sau unelte ilegale?' })).toBeVisible();
    await expect(page.getByTestId('incident-emergency-112')).toHaveCount(0);
    await expect(page.getByTestId('incident-route-poaching')).toContainText('0374 466 139');
    await expect(page.getByTestId('incident-route-pollution')).toContainText('021 326 89 70');
    await expect(page.getByTestId('incident-gnm-directory')).toHaveAttribute('href', 'https://www.gnm.ro/contact/');
    await page.getByRole('button', { name: /arată opțiunea 112/i }).click();
    await expect(page.getByTestId('incident-emergency-112')).toHaveAttribute('href', 'tel:112');
  });
});
