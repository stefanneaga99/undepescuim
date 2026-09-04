import { test, expect, type Page } from '@playwright/test';

type BrowserLayer = {
  feature?: { geometry?: GeoJSON.Geometry; properties?: Record<string, unknown> };
  options?: { color?: string; dashArray?: string | number[] };
  fire: (event: string, data: unknown) => void;
};
type BrowserMap = {
  _layers?: Record<string, BrowserLayer>;
  fitBounds: (bounds: [[number, number], [number, number]], options: Record<string, unknown>) => void;
  getCenter: () => unknown;
  setView: (center: [number, number], zoom: number, options: Record<string, unknown>) => void;
};

const BUZAU_ALIASES = [
  'anpa-anpa-0207',
  'anpa-anpa-0210',
  'anpa-anpa-0211',
  'anpa-anpa-0214',
  'anpa-anpa-0261',
  'romsilva-brasov-buzaul-superior',
];

async function previewLayers(page: Page) {
  return page.evaluate(() => {
    const map = (window as unknown as { __UNDEPESCUIM_MAP__?: BrowserMap }).__UNDEPESCUIM_MAP__;
    return Object.values(map?._layers ?? {}).filter((layer) =>
      Array.isArray(layer.feature?.properties?.physicalAliases),
    ).map((layer) => ({
      geometry: layer.feature?.geometry,
      properties: layer.feature?.properties,
      color: layer.options?.color,
      dashArray: layer.options?.dashArray,
    }));
  });
}

test.describe('ledger-backed Class2 physical preview rendering', () => {
  test('keeps one neutral continuous Buzău course with exact aliases and explicit projections', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('.leaflet-container')).toBeVisible();

    await expect.poll(() => previewLayers(page).then((layers) => layers.length), { timeout: 45_000 }).toBeGreaterThan(0);
    const features = await previewLayers(page);
    const buzau = features.filter((feature) =>
      (feature.properties?.physicalAliases as string[]).includes('anpa-anpa-0207'),
    );
    expect(buzau).toHaveLength(1);
    expect(buzau[0].properties).toMatchObject({
      physicalAliases: BUZAU_ALIASES,
      physicalGeometryHash: '54cd5d70f881461215170da4d68b60397e2b651c67b1f542edbbcd9cc2855e1d',
      riverGroup: 'buzau',
      asociatieSlug: null,
    });
    expect(buzau[0].color).toBe('#14b8a6');
    expect(buzau[0].dashArray).toBeTruthy();
    expect(buzau[0].geometry?.type).toBe('LineString');
    expect((buzau[0].geometry as GeoJSON.LineString).coordinates).toHaveLength(3115);
    const segments = buzau[0].properties?.physicalSegments as Array<Record<string, unknown>>;
    expect(segments).toEqual(expect.arrayContaining([
      expect.objectContaining({ sourceSlug: 'anpa-anpa-0261', start: 0.0774, end: 0.1641 }),
      expect.objectContaining({ sourceSlug: 'romsilva-brasov-buzaul-superior', start: 0, end: 0.0797 }),
    ]));
    expect(segments).toHaveLength(2);

    await page.evaluate(() => {
      const map = (window as unknown as { __UNDEPESCUIM_MAP__?: BrowserMap }).__UNDEPESCUIM_MAP__;
      map?.setView([47.5, 22], 10, { animate: false });
    });
    await expect.poll(async () => (await previewLayers(page)).some((feature) =>
      (feature.properties?.physicalAliases as string[]).includes('anpa-anpa-0207'),
    )).toBe(false);
    await page.evaluate(() => {
      const map = (window as unknown as { __UNDEPESCUIM_MAP__?: BrowserMap }).__UNDEPESCUIM_MAP__;
      map?.fitBounds([[45.07086, 25.97799], [45.67344, 27.74236]], { animate: false, maxZoom: 10 });
    });
    await expect.poll(async () => (await previewLayers(page)).filter((feature) =>
      (feature.properties?.physicalAliases as string[]).includes('anpa-anpa-0207'),
    ).length).toBe(1);

    await page.evaluate(() => {
      const map = (window as unknown as { __UNDEPESCUIM_MAP__?: BrowserMap }).__UNDEPESCUIM_MAP__;
      const layer = Object.values(map?._layers ?? {}).find((candidate) =>
        (candidate.feature?.properties?.physicalAliases as string[] | undefined)?.includes('anpa-anpa-0207') &&
        candidate.options?.color === '#14b8a6',
      );
      layer?.fire('click', { latlng: map?.getCenter() });
    });
    await expect(page.getByTestId('water-card')).toBeVisible();
    await expect(page.getByTestId('water-card')).toContainText('Râul Buzăul superior');
    await expect(page.getByTestId('physical-preview-disclosure')).toContainText('sector legal neverificat');
    await expect(page.locator('[data-focus-kind="feature-selected-unverified-sector"]')).toHaveCount(1);
    expect(await page.evaluate(() => window.innerWidth < 1024
      ? Boolean(document.querySelector('[data-testid="water-detail-sheet"]'))
      : Boolean(document.querySelector('aside:has([data-testid="water-card"])')),
    )).toBe(true);
    expect((await previewLayers(page)).filter((feature) => feature.color === '#f97316')).toHaveLength(0);
  });

  test('ships structurally renderable representatives for every ledger classification and subtype', async ({ page }) => {
    await page.goto('/');
    const result = await page.evaluate(async () => {
      const [ledger, waters] = await Promise.all([
        fetch('/data/geometry-ledger.json').then((response) => response.json()),
        fetch('/data/waters.json').then((response) => response.json()),
      ]);
      const canonical = new Map(waters.map((water: { slug: string }) => [water.slug, water]));
      const groups = new Map<string, number>();
      const repairedWithoutCanonical = [];
      for (const record of ledger.records) {
        groups.set(`${record.classification}:${record.subtype}`, (groups.get(`${record.classification}:${record.subtype}`) ?? 0) + 1);
        if (record.classification === 'repaired') {
          const water = canonical.get(record.sourceSlug) as { geometry?: unknown } | undefined;
          if (!water?.geometry || !record.geometryVariants.some((variant: { state: string }) => variant.state === 'canonical-legal-sector')) {
            repairedWithoutCanonical.push(record.sourceSlug);
          }
        }
      }
      return { groups: Object.fromEntries(groups), repairedWithoutCanonical };
    });
    expect(result.repairedWithoutCanonical).toEqual([]);
    for (const classification of ['repaired', 'preview-only', 'unresolved']) {
      for (const subtype of ['rau', 'lac']) {
        expect(result.groups[`${classification}:${subtype}`]).toBeGreaterThan(0);
      }
    }
  });
});
