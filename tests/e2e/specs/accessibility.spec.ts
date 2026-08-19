import { test, expect } from '@playwright/test';

test.describe('PWA shell accessibility smoke checks', () => {
  test('mobile shell exposes landmarks, named controls, and keyboard focus', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('header')).toBeVisible();
    await expect(page.locator('main')).toBeVisible();
    await expect(page.locator('header nav[aria-label]')).toHaveCount(1);

    const unnamed = await page.locator('button').evaluateAll((buttons) =>
      buttons.filter((button) => {
        const label = button.getAttribute('aria-label') || button.textContent?.trim();
        return !label && !button.hasAttribute('aria-hidden');
      }).length,
    );
    expect(unnamed, 'every interactive button must have an accessible name').toBe(0);

    await page.keyboard.press('Tab');
    await expect(page.locator(':focus-visible')).toHaveCount(1);
  });

  test('touch controls meet the 44px mobile target', async ({ page }) => {
    await page.goto('/');
    const coarse = await page.evaluate(() => matchMedia('(pointer: coarse)').matches);
    test.skip(!coarse, 'target-size assertion is for touch pointers');
    const undersized = await page.locator('[data-slot="button"]:visible').evaluateAll((buttons) =>
      buttons.filter((button) => {
        const rect = button.getBoundingClientRect();
        return rect.width < 44 || rect.height < 44;
      }).length,
    );
    expect(undersized).toBe(0);
  });
});
