import { test, expect } from '@playwright/test';

type BrowserLayer = { feature?: { properties?: Record<string, unknown> }; fire: (event: string, data: unknown) => void };
type BrowserMap = { _layers?: Record<string, BrowserLayer>; getCenter: () => unknown };

test.describe('Class2 physical preview rendering', () => {
  test('deduplicates physical lines and focuses canonical Buzău selection', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('.leaflet-container')).toBeVisible();

    const preview = await page.waitForFunction(() => {
      const map = (window as unknown as { __UNDEPESCUIM_MAP__?: BrowserMap }).__UNDEPESCUIM_MAP__;
      if (!map) return null;
      const features: Array<Record<string, unknown>> = [];
      for (const layer of Object.values(map._layers ?? {})) {
        const properties = layer.feature?.properties;
        if (Array.isArray(properties?.physicalAliases)) features.push(properties);
      }
      return features.length ? features : null;
    }, undefined, { timeout: 45_000 });
    const features = await preview.jsonValue() as Array<Record<string, unknown>>;
    const buzau = features.filter((f) => (f.physicalAliases as string[]).includes('anpa-anpa-0207'));
    expect(buzau).toHaveLength(1);
    expect(buzau[0].physicalAliases).toEqual(expect.arrayContaining(['anpa-anpa-0214', 'anpa-anpa-0261']));
    expect(buzau[0].riverGroup).toBe('buzau');
    expect(buzau[0].asociatieSlug).toBeNull();

    await page.evaluate(() => {
      const map = (window as unknown as { __UNDEPESCUIM_MAP__?: BrowserMap }).__UNDEPESCUIM_MAP__;
      const layer = Object.values(map?._layers ?? {}).find((candidate) =>
        (candidate.feature?.properties?.physicalAliases as string[] | undefined)?.includes('anpa-anpa-0207'),
      );
      layer?.fire('click', { latlng: map?.getCenter() });
    });
    await expect(page.getByTestId('water-card')).toBeVisible();
    await expect(page.getByTestId('water-card')).toContainText('Râul Buzăul superior');
    await expect.poll(async () => page.evaluate(() => {
      const map = (window as unknown as { __UNDEPESCUIM_MAP__?: BrowserMap }).__UNDEPESCUIM_MAP__;
      return Object.values(map?._layers ?? {}).some((layer) =>
        (layer.feature?.properties?.physicalAliases as string[] | undefined)?.includes('anpa-anpa-0207') &&
        (layer as BrowserLayer & { options?: { color?: string } }).options?.color === '#f97316',
      );
    })).toBeTruthy();

  });
});
