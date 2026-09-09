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
  latLngToContainerPoint: (latlng: [number, number]) => { x: number; y: number };
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

async function clickPhysicalAlias(page: Page, alias: string) {
  const point = await page.evaluate(async (selectedAlias) => {
    const waters = await fetch('/data/waters.json').then((response) => response.json()) as Array<{
      slug: string; name: string; riverGroup?: string; course_frac?: number; sectorStart?: number; sectorEnd?: number;
    }>;
    const map = (window as unknown as { __UNDEPESCUIM_MAP__?: BrowserMap }).__UNDEPESCUIM_MAP__;
    const layer = Object.values(map?._layers ?? {}).find((candidate) =>
      (candidate.feature?.properties?.physicalAliases as string[] | undefined)?.includes(selectedAlias),
    );
    if (!layer?.feature?.geometry || !map) throw new Error(`missing physical layer for ${selectedAlias}`);
    const coordinates = (layer.feature.geometry as GeoJSON.LineString).coordinates as [number, number][];
    const selected = waters.find((water) => water.slug === selectedAlias);
    if (!selected) throw new Error(`missing canonical water ${selectedAlias}`);
    const position = selected.slug === 'anpa-anpa-0210'
      ? 0.1645
      : typeof selected.sectorStart === 'number' && typeof selected.sectorEnd === 'number'
        ? (selected.sectorStart + selected.sectorEnd) / 2
        : selected.course_frac ?? 0.5;
    const distance = (a: [number, number], b: [number, number]) => {
      const dx = (b[0] - a[0]) * Math.cos((a[1] + b[1]) * Math.PI / 360);
      const dy = b[1] - a[1];
      return Math.hypot(dx, dy);
    };
    const lengths = coordinates.slice(1).map((point, index) => distance(coordinates[index], point));
    const total = lengths.reduce((sum, length) => sum + length, 0);
    const pointAt = (fraction: number): [number, number] => {
      let walked = 0;
      const target = Math.max(0, Math.min(1, fraction)) * total;
      for (let index = 1; index < coordinates.length; index++) {
        const length = lengths[index - 1];
        if (walked + length >= target) {
          const ratio = length ? (target - walked) / length : 0;
          return [
            coordinates[index - 1][0] + (coordinates[index][0] - coordinates[index - 1][0]) * ratio,
            coordinates[index - 1][1] + (coordinates[index][1] - coordinates[index - 1][1]) * ratio,
          ];
        }
        walked += length;
      }
      return coordinates[coordinates.length - 1];
    };
    const candidates = [0, -0.004, 0.004, -0.009, 0.009].map((delta) => pointAt(position + delta));
    for (const candidate of candidates) {
      const point = map.latLngToContainerPoint([candidate[1], candidate[0]]);
      const rect = document.querySelector('.leaflet-container')?.getBoundingClientRect();
      if (!rect) throw new Error('missing map rect');
      const viewportPoint = { x: point.x + rect.left, y: point.y + rect.top };
      const element = document.elementFromPoint(viewportPoint.x, viewportPoint.y);
      if (element instanceof SVGPathElement && element.closest('.physical-preview-pane')) {
        return { x: viewportPoint.x, y: viewportPoint.y, selectedName: selected.name };
      }
    }
    const fallback = map.latLngToContainerPoint([candidates[0][1], candidates[0][0]]);
    const rect = document.querySelector('.leaflet-container')?.getBoundingClientRect();
    if (!rect) throw new Error('missing map rect');
    return { x: fallback.x + rect.left, y: fallback.y + rect.top, selectedName: selected.name };
  }, alias);
  await page.evaluate(({ x, y }) => {
    for (const path of document.querySelectorAll('svg path')) {
      if (!path.closest('.physical-preview-pane')) (path as SVGPathElement).style.pointerEvents = 'none';
    }
    (window as unknown as { __buzauClickPoint?: { x: number; y: number } }).__buzauClickPoint = { x, y };
  }, point);
  try {
    await page.mouse.click(point.x, point.y);
  } finally {
    await page.evaluate(() => {
      for (const path of document.querySelectorAll('svg path')) (path as SVGPathElement).style.pointerEvents = '';
    });
  }
  return point;
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

  test('exercises every Buzău alias through the physical pane without changing legal counts', async ({ page }, testInfo) => {
    await page.goto('/');
    await expect(page.locator('.leaflet-container')).toBeVisible();
    await expect.poll(() => previewLayers(page).then((layers) => layers.length), { timeout: 45_000 }).toBeGreaterThan(0);
    await page.evaluate(() => {
      const map = (window as unknown as { __UNDEPESCUIM_MAP__?: BrowserMap }).__UNDEPESCUIM_MAP__;
      map?.fitBounds([[45.07086, 25.97799], [45.67344, 27.74236]], { animate: false, maxZoom: 10 });
    });
    await expect.poll(async () => (await previewLayers(page)).some((feature) =>
      (feature.properties?.physicalAliases as string[] | undefined)?.includes('anpa-anpa-0207'),
    )).toBe(true);

    const before = await page.evaluate(() => ({
      legalPaths: document.querySelectorAll('.leaflet-overlay-pane:not(.physical-preview-pane):not(.water-focus-pane) path, .water-association-pane path').length,
      physicalPane: (() => {
        const pane = document.querySelector<HTMLElement>('.physical-preview-pane');
        return pane ? {
          zIndex: getComputedStyle(pane).zIndex,
          pointerEvents: getComputedStyle(pane).pointerEvents,
          pathCount: pane.querySelectorAll('path').length,
        } : null;
      })(),
    }));
    expect(before.physicalPane).toMatchObject({ zIndex: '410', pointerEvents: 'auto' });
    expect(before.physicalPane?.pathCount).toBeGreaterThan(0);

    const aliases = BUZAU_ALIASES;
    await page.context().tracing.start({ screenshots: true, snapshots: true });
    for (const alias of aliases) {
      const feature = (await previewLayers(page)).find((candidate) =>
        (candidate.properties?.physicalAliases as string[] | undefined)?.includes(alias),
      );
      expect(feature, `missing physical alias ${alias}`).toBeTruthy();
      const segments = feature?.properties?.physicalSegments as Array<Record<string, unknown>> | undefined;
      if (alias === 'anpa-anpa-0261' || alias === 'romsilva-brasov-buzaul-superior') {
        expect(segments).toEqual(expect.arrayContaining([
          expect.objectContaining({ sourceSlug: alias, start: expect.any(Number), end: expect.any(Number) }),
        ]));
      } else {
        expect(segments?.some((segment) => segment.sourceSlug === alias)).toBe(false);
      }
      const click = await clickPhysicalAlias(page, alias);
      await expect(page.getByTestId('water-card')).toBeVisible();
      await expect(page.getByTestId('water-card')).toHaveAttribute('data-water-slug', alias);
      await expect(page.getByTestId('water-card')).toContainText(click.selectedName);
      if (alias === 'anpa-anpa-0261' || alias === 'romsilva-brasov-buzaul-superior') {
        await expect(page.locator('[data-focus-kind="feature-selected-unverified-sector"]')).toHaveCount(0);
        await expect(page.locator('.water-focus-pane path')).toHaveCount(1);
      } else {
        await expect(page.locator('[data-focus-kind="feature-selected-unverified-sector"]')).toHaveCount(1);
        await expect(page.locator('[data-focus-kind="verified-sector-focus"]')).toHaveCount(0);
      }
      await page.screenshot({ path: testInfo.outputPath(`buzau-alias-${alias}.png`), fullPage: true });
      await page.keyboard.press('Escape');
    }
    await page.context().tracing.stop({ path: testInfo.outputPath('buzau-alias-flow.trace.zip') });
    const after = await page.evaluate(() => document.querySelectorAll('.leaflet-overlay-pane:not(.physical-preview-pane):not(.water-focus-pane) path, .water-association-pane path').length);
    expect(after).toBe(before.legalPaths);
  });
});
