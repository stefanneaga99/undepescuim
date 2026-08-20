import { test, expect } from '../../fixtures/app';
import { MapPage } from '../../pages/MapPage';

type MapLayer = {
  feature?: { properties?: { slug?: string } };
  options?: { color?: string };
};

type TestMap = {
  eachLayer: (callback: (layer: MapLayer) => void) => void;
};

/** P1 map/control regression coverage; all data and tiles are deterministic. */
test.describe('P1 map controls and visual states', () => {
  test('county chips support additive multi-select without dropping the first county', async ({ mapReady, page }) => {
    await mapReady();
    const map = new MapPage(page);

    await map.filterBar.toggleCounty('Cluj');
    await map.filterBar.toggleCounty('Brașov');
    await expect(map.filterBar.countyChip('Cluj')).toHaveAttribute('aria-pressed', 'true');
    await expect(map.filterBar.countyChip('Brașov')).toHaveAttribute('aria-pressed', 'true');
    await expect(page.getByText('Toate județele').filter({ visible: true })).toHaveCount(0);
    await expect(map.filterBar.localityTrigger).toBeVisible();
  });

  test('selected contracted water paints orange focus and bbox fallback paints violet', async ({ mapReady, page }) => {
    await mapReady();
    const map = new MapPage(page);

    await map.clickWater('raul-somesul-test');
    await expect.poll(async () => (await map.focusSnapshot()).orangePaths).toBeGreaterThan(0);
    expect((await map.focusSnapshot()).slug).toBe('raul-somesul-test');

    await page.keyboard.press('Escape');
    await map.zoomTo(9);
    const fallbackColors = await page.evaluate((slug) => {
      const mapInstance = (window as unknown as { __UNDEPESCUIM_MAP__?: TestMap }).__UNDEPESCUIM_MAP__;
      const colors: string[] = [];
      mapInstance?.eachLayer((layer) => {
        if (layer.feature?.properties?.slug === slug && layer.options?.color) colors.push(layer.options.color);
      });
      return colors;
    }, 'lacul-beta-fara-permis');
    expect(fallbackColors.map((color) => color.toLowerCase())).toContain('#8b5cf6');
    await map.clickWater('lacul-beta-fara-permis');
    const selectedFallbackColors = await page.evaluate((slug) => {
      const mapInstance = (window as unknown as { __UNDEPESCUIM_MAP__?: TestMap }).__UNDEPESCUIM_MAP__;
      const colors: string[] = [];
      mapInstance?.eachLayer((layer) => {
        if (layer.feature?.properties?.slug === slug && layer.options?.color) colors.push(layer.options.color);
      });
      return colors;
    }, 'lacul-beta-fara-permis');
    expect(selectedFallbackColors.map((color) => color.toLowerCase())).toContain('#f97316');
  });

  test('mobile legend expands into labeled rows and returns to compact dots', async ({ mapReady, page }) => {
    await mapReady();
    test.skip((await page.evaluate(() => window.innerWidth)) > 600, 'mobile-only legend interaction');
    const toggle = page.getByRole('button', { name: 'Legendă culori' });
    await expect(toggle).toHaveAttribute('aria-expanded', 'false');
    await toggle.click();
    await expect(toggle).toHaveAttribute('aria-expanded', 'true');
    await expect(toggle).toContainText('Vedere neutră');
    await expect(toggle).toContainText('Râuri necontractate');
    await page.waitForTimeout(5100);
    await expect(toggle).toHaveAttribute('aria-expanded', 'false');
  });

  test('mounted map replaces the loading skeleton with settled map data', async ({ page, mapReady }) => {
    await mapReady();
    await expect(page.getByTestId('map-root').getByRole('status')).toHaveCount(0);
    await expect(page.getByTestId('waters-drawn')).toBeAttached();
    await expect(page.locator('.leaflet-container')).toBeVisible();
  });
});
