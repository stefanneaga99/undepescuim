/**
 * Dark mode (docs/dark-mode-feasibility-plan.md §10 — TESTS).
 * The basic toggle/persist behaviors live in edge-cases.spec.ts; this spec
 * covers the rest of the acceptance matrix:
 *   - system preference respected on first visit (no stored choice)
 *   - no FOUC: the theme class is applied before first paint (next-themes'
 *     injected <head> script — no flash of the wrong theme)
 *   - every public page renders dark with distinct (dark) body background,
 *     evidenced by light vs dark screenshots attached to the run
 * Runs in all three viewports (mobile 390 / tablet 768 / desktop 1280).
 */
import { test, expect } from '../../fixtures/app';
import { Selectors } from '../../helpers/selectors';

const PAGES = ['/', '/specii', '/permis'] as const;

test.describe('dark mode', () => {
  test('dark system preference is respected on first visit (no stored choice)', async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.goto('/');
    await expect(page.locator('html')).toHaveClass(/dark/);
  });

  test('light system preference renders light (no stored choice)', async ({ page }) => {
    await page.emulateMedia({ colorScheme: 'light' });
    await page.goto('/');
    await expect(page.locator('html')).not.toHaveClass(/dark/);
  });

  test('no FOUC: .dark applied before first paint on dark preference', async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: 'dark' });
    // domcontentloaded = immediately after HTML parse, BEFORE React hydration.
    // next-themes' head script runs synchronously during parse, so the class
    // must already be there — that is the no-flash mechanism.
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    const state = await page.evaluate(() => ({
      htmlHasDark: document.documentElement.classList.contains('dark'),
      themeScriptPresent: Array.from(document.querySelectorAll('script')).some(
        (s) =>
          s.textContent?.includes('localStorage') &&
          s.textContent.includes('documentElement'),
      ),
    }));
    expect(state.themeScriptPresent).toBe(true);
    expect(state.htmlHasDark).toBe(true);
  });

  for (const path of PAGES) {
    test(`${path} renders dark (screenshot light vs dark)`, async ({ page, mapReady }, testInfo) => {
      // Light capture: explicit light preference, no stored choice.
      await page.emulateMedia({ colorScheme: 'light' });
      if (path === '/') await mapReady();
      else await page.goto(path);
      const lightBg = await page.evaluate(
        () => getComputedStyle(document.body).backgroundColor,
      );
      const lightShot = testInfo.outputPath('light.png');
      await page.screenshot({ path: lightShot, fullPage: false });

      // Dark capture: flip via the header toggle (same control a user uses).
      const toggle = page.getByTestId(Selectors.themeToggle);
      await expect(toggle).toBeVisible();
      await toggle.click();
      await expect(page.locator('html')).toHaveClass(/dark/);
      const darkBg = await page.evaluate(
        () => getComputedStyle(document.body).backgroundColor,
      );
      const darkShot = testInfo.outputPath('dark.png');
      await page.screenshot({ path: darkShot, fullPage: false });

      // The dark palette must actually be applied (CSS variables swapped).
      expect(darkBg).not.toBe(lightBg);
      await testInfo.attach('light', { path: lightShot, contentType: 'image/png' });
      await testInfo.attach('dark', { path: darkShot, contentType: 'image/png' });
    });
  }
});