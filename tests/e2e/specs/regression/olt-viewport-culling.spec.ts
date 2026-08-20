import { test, expect } from '@playwright/test';
import type { Water } from '@/types/data';
import { seed } from '../../fixtures/seed-data';
import { routeData } from '../../fixtures/routes';
import { waitForMapReady } from '../../helpers/map';

/* eslint-disable @typescript-eslint/no-explicit-any */

const OLT_OWNER = 'ehwpvgwh';
const OLT_POINT = { lat: 46.03, lon: 25.82771 };

type Diagnostic = {
  center: { lat: number; lon: number };
  zoom: number;
  bounds: { south: number; west: number; north: number; east: number };
  filters: { counties: string[]; types: string[]; contracts: string[] };
  ownerLayers: Array<{ path: boolean; pane: string; stroke: string; color: string }>;
  ownerPathCount: number;
  bluePathCount: number;
};

async function waitForRender(page: import('@playwright/test').Page): Promise<void> {
  await page.waitForFunction(() => {
    const map = (window as any).__UNDEPESCUIM_MAP__;
    return Boolean(map) && !map._animatingZoom && !map._panAnim?._inProgress;
  });
  await page.waitForTimeout(100);
}

async function diagnostic(page: import('@playwright/test').Page): Promise<Diagnostic> {
  return page.evaluate((ownerSlug) => {
    const map = (window as any).__UNDEPESCUIM_MAP__;
    const center = map.getCenter();
    const b = map.getBounds();
    const ownerLayers: Diagnostic['ownerLayers'] = [];
    map.eachLayer((layer: any) => {
      if (layer.feature?.properties?.slug !== ownerSlug) return;
      const path = layer._path as SVGPathElement | undefined;
      const pane = layer._pane as HTMLElement | undefined;
      ownerLayers.push({
        path: Boolean(path),
        pane: path?.closest<HTMLElement>('.leaflet-pane')?.className ?? pane?.className ?? '',
        stroke: path?.getAttribute('stroke') ?? '',
        color: layer.options?.color ?? '',
      });
    });
    const paths = [...document.querySelectorAll('.leaflet-overlay-pane path, .water-focus-pane path, .water-association-pane path')];
    return {
      center: { lat: center.lat, lon: center.lng },
      zoom: map.getZoom(),
      bounds: { south: b.getSouth(), west: b.getWest(), north: b.getNorth(), east: b.getEast() },
      // The regression starts with the explicitly documented all-filter state.
      filters: { counties: [], types: ['lac', 'rau'], contracts: ['contractate', 'necontractate'] },
      ownerLayers,
      ownerPathCount: ownerLayers.filter((layer) => layer.path).length,
      bluePathCount: paths.filter((path) => ['#2563eb', '#3b82f6', 'rgb(37, 99, 235)', 'rgb(59, 130, 246)'].includes(path.getAttribute('stroke')?.toLowerCase() ?? '')).length,
    };
  }, OLT_OWNER);
}

async function setView(page: import('@playwright/test').Page, lat: number, lon: number, zoom = 11): Promise<Diagnostic> {
  await page.evaluate(({ lat, lon, zoom }) => {
    (window as any).__UNDEPESCUIM_MAP__.setView([lat, lon], zoom, { animate: false });
  }, { lat, lon, zoom });
  await waitForRender(page);
  return diagnostic(page);
}

test.describe('Olt geometry-aware viewport culling', () => {
  test('keeps the full-course owner through mobile right-pan and desktop back-pan', async ({ page }, testInfo) => {
    const live = process.env.LIVE_PROD === '1';
    const base = seed.waters[0] as Water;
    const owner: Water = {
      ...base,
      slug: OLT_OWNER,
      name: 'Râul Olt și afluenții săi',
      bbox: [25.1853946, 45.8778532, 25.5471524, 46.0518861],
      coordinates: [OLT_POINT.lon, OLT_POINT.lat],
      geometry: { type: 'MultiLineString', coordinates: [[[25.8, 46.04], [25.84, 46.02]]] },
      riverGroup: 'olt',
    };
    if (!live) {
      await routeData(page, seed);
      await page.route('**/data/waters.json', (route) => route.fulfill({ json: [...seed.waters, owner] }));
    }
    await page.goto('/');
    await waitForMapReady(page);

    const before = await setView(page, OLT_POINT.lat, 25.70);
    const afterRight = await setView(page, OLT_POINT.lat, OLT_POINT.lon);
    const afterBack = await setView(page, OLT_POINT.lat, 25.70);
    const control = await setView(page, 46.03, 27.0);
    const evidence = { project: testInfo.project.name, before, afterRight, afterBack, control };
    await testInfo.attach('olt-viewport-culling-diagnostics.json', {
      body: JSON.stringify(evidence, null, 2),
      contentType: 'application/json',
    });

    expect(before.zoom).toBe(11);
    expect(afterRight.bounds.west).toBeLessThanOrEqual(OLT_POINT.lon);
    expect(afterRight.bounds.east).toBeGreaterThanOrEqual(OLT_POINT.lon);
    expect(afterRight.ownerPathCount).toBeGreaterThan(0);
    expect(afterRight.ownerLayers.some((layer) => layer.pane.includes('leaflet-overlay-pane'))).toBe(true);
    expect(afterRight.ownerLayers.map((layer) => layer.color || layer.stroke)).toContain('#3b82f6');
    expect(afterRight.bluePathCount).toBeGreaterThan(0);
    expect(afterBack.ownerPathCount).toBeGreaterThan(0);
    expect(control.ownerPathCount).toBe(0);
  });
});
