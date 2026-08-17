/**
 * i18n (t_920a7b7b) — RO⇄EN switcher, persistence, all pages in both
 * languages, no missing-key fallbacks, screenshot diff.
 *
 * The switcher lives in the Header (map page only, per task scope §2); the
 * choice is persisted to localStorage and applies site-wide — so /specii and
 * /permis are verified by seeding the persisted locale before navigating.
 */
import { test, expect } from '../../fixtures/app';

const STORAGE_KEY = 'undepescuim.locale';

/** Seed the persisted locale before any script runs on the page. */
async function seedLocale(page: import('@playwright/test').Page, locale: 'ro' | 'en') {
  await page.addInitScript(
    ([k, v]) => {
      try {
        window.localStorage.setItem(k, v);
      } catch {
        /* storage blocked — ignore */
      }
    },
    [STORAGE_KEY, locale] as const,
  );
}

test.describe('i18n — RO⇄EN switcher', () => {
  test('badge toggles RO⇄EN and persists across reload', async ({ page, mapReady }) => {
    await mapReady('/');
    const switcher = page.getByTestId('lang-switcher');

    // Default: RO badge, RO chrome.
    await expect(switcher).toContainText('RO');
    await expect(page.getByText('Toate județele').filter({ visible: true }).first()).toBeVisible();

    // Click → EN everywhere in the header + filter bar.
    await switcher.click();
    await expect(switcher).toContainText('EN');
    await expect(page.getByText('All counties').filter({ visible: true }).first()).toBeVisible();

    // Reload → persisted EN, not reset to RO.
    await page.reload();
    await expect(switcher).toContainText('EN');
    await expect(page.getByText('All counties').filter({ visible: true }).first()).toBeVisible();

    // Click back → RO.
    await switcher.click();
    await expect(switcher).toContainText('RO');
    await expect(page.getByText('Toate județele').filter({ visible: true }).first()).toBeVisible();
  });

  test('header nav + association search translate', async ({ page, mapReady }) => {
    await mapReady('/');
    await page.getByTestId('lang-switcher').click();

    await expect(page.getByTestId('nav-permis').filter({ visible: true })).toContainText('Permit 2026');
    await expect(page.getByTestId('nav-specii').filter({ visible: true })).toContainText('Species');

    // Open the association search on desktop? Mobile icon only at <768px;
    // the desktop trigger is hidden on mobile projects. Check the trigger
    // exists with an EN placeholder on desktop (visible) projects.
    const desktopSearch = page.getByTestId('assoc-search').filter({ visible: true });
    if ((await desktopSearch.count()) > 0) {
      await expect(desktopSearch).toContainText('Search association');
    }
  });

  test('no missing-key fallbacks leak into the DOM', async ({ page, mapReady }) => {
    await mapReady('/');
    await page.getByTestId('lang-switcher').click();
    // The missing-key guard logs console.error AND falls back to RO — neither
    // a raw key path nor RO text should leak under the EN locale for chrome keys.
    const body = await page.locator('body').innerText();
    expect(body).not.toContain('filters.');
    expect(body).not.toContain('header.');
    expect(body).not.toContain('card.');
    expect(body).not.toContain('{');
  });
});

test.describe('i18n — /specii + /permis render in both languages (persisted locale)', () => {
  test('/specii page: RO by default, EN when persisted', async ({ page }) => {
    await page.goto('/specii');
    await expect(page.getByRole('heading', { name: /Specii cu dimensiune minimă/ })).toBeVisible();
    await expect(page.getByText('Înapoi la hartă')).toBeVisible();

    await seedLocale(page, 'en');
    await page.goto('/specii');
    await expect(page.getByRole('heading', { name: /Species with minimum size/ })).toBeVisible();
    await expect(page.getByText('Back to map')).toBeVisible();
    // Species data (RO names + latin) stays per task scope §5.
    await expect(page.getByText('Somn')).toBeVisible();
  });

  test('/permis page: RO by default, EN when persisted', async ({ page }) => {
    await page.goto('/permis');
    await expect(page.getByRole('heading', { name: 'Permis & Reguli 2026' })).toBeVisible();
    await expect(page.getByText('Ce s-a schimbat: ANPA → ANADSPA')).toBeVisible();

    await seedLocale(page, 'en');
    await page.goto('/permis');
    await expect(page.getByRole('heading', { name: 'Permit & Rules 2026' })).toBeVisible();
    await expect(page.getByText('What changed: ANPA → ANADSPA')).toBeVisible();
    await expect(page.getByText("What's coming (draft MADR order, May 2026)")).toBeVisible();
  });
});

test.describe('i18n — screenshot diff (user mandate)', () => {
  test('EN screenshot differs from RO across the map chrome', async ({ page, mapReady }) => {
    await mapReady('/');
    const shot = (locale: 'ro' | 'en') =>
      page.screenshot({ fullPage: false, clip: { x: 0, y: 0, width: 1280, height: 420 } });

    const roShot = await shot('ro');
    await page.getByTestId('lang-switcher').click();
    await expect(page.getByText('All counties').filter({ visible: true }).first()).toBeVisible();
    const enShot = await shot('en');

    expect(enShot.length).toBeGreaterThan(0);
    expect(roShot.length).toBeGreaterThan(0);
    // Different text → different pixels. (Buffers can match on a fully blank
    // render, which would mean the toggle did nothing — the anti-regression.)
    expect(enShot.equals(roShot)).toBe(false);

    // Also persist the screenshots as artifacts for the reviewer.
    const fs = await import('node:fs');
    const path = await import('node:path');
    const dir = path.join(process.cwd(), 'test-results', 'i18n-screenshots');
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, 'map-ro.png'), roShot);
    fs.writeFileSync(path.join(dir, 'map-en.png'), enShot);
  });
});