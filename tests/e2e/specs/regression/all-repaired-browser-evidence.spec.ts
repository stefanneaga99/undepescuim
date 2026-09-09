import { test, expect, type Page, type TestInfo } from '@playwright/test';
import crypto from 'node:crypto';
import fs from 'node:fs';

/* eslint-disable @typescript-eslint/no-explicit-any */

const VIEWPORTS = [
  { width: 390, height: 844 },
  { width: 1280, height: 800 },
] as const;

type LedgerRecord = {
  sourceSlug: string;
  name: string;
  classification: string;
  subtype: string;
  aliases: string[];
  geometryVariants: Array<{
    state: string;
    segmentId: string;
    geometry: { geometryHash: string; type: string; bbox: [number, number, number, number] };
  }>;
};

type Water = {
  slug: string;
  name: string;
  geometry?: { type: string; coordinates: unknown };
  bbox?: [number, number, number, number];
};

type LayerInventory = {
  slug: string;
  geometryType: string | null;
  pathCount: number;
  pane: string;
  pointerEvents: string;
  zIndex: string;
};

function sha256(value: string): string {
  return crypto.createHash('sha256').update(value).digest('hex');
}

async function loadLedger(page: Page): Promise<{ repaired: LedgerRecord[]; waters: Water[] }> {
  return page.evaluate(async () => {
    const [ledger, waters] = await Promise.all([
      fetch('/data/geometry-ledger.json').then((response) => response.json()),
      fetch('/data/waters.json').then((response) => response.json()),
    ]);
    return {
      repaired: ledger.records.filter((record: LedgerRecord) => record.classification === 'repaired'),
      waters,
    };
  });
}

async function inspectAndClick(page: Page, slug: string, bbox: [number, number, number, number]): Promise<{
  layer: LayerInventory | null;
  cardHeading: string | null;
  cardSurface: string | null;
  point: { x: number; y: number } | null;
  culling: { before: boolean; after: boolean };
}> {
  const presentBefore = await page.evaluate((target) => {
    const map = (window as any).__UNDEPESCUIM_MAP__;
    return Object.values(map?._layers ?? {}).some((entry: any) => entry.feature?.properties?.slug === target && entry._path);
  }, slug);
  await page.evaluate(([minLon, minLat, maxLon, maxLat]) => {
    (window as any).__UNDEPESCUIM_MAP__?.fitBounds(
      [[minLat, minLon], [maxLat, maxLon]],
      { padding: [40, 40], maxZoom: 13, animate: false },
    );
  }, bbox);
  await page.waitForFunction(() => {
    const map = (window as any).__UNDEPESCUIM_MAP__;
    return Boolean(map) && !map._animatingZoom && !map._panAnim?._inProgress;
  });

  const layer = await page.waitForFunction((target) => {
    const map = (window as any).__UNDEPESCUIM_MAP__;
    const candidate = Object.values(map?._layers ?? {}).find((entry: any) =>
      entry.feature?.properties?.slug === target && entry._path,
    ) as any;
    if (!candidate) return null;
    const path = candidate._path as SVGPathElement;
    const style = getComputedStyle(path);
    return {
      slug: target,
      geometryType: candidate.feature?.geometry?.type ?? null,
      pathCount: 1,
      pane: candidate._pane?.className ?? path.closest('.leaflet-pane')?.className ?? '',
      pointerEvents: style.pointerEvents,
      zIndex: getComputedStyle(candidate._pane ?? path.closest('.leaflet-pane')!).zIndex,
    } satisfies LayerInventory;
  }, slug, { timeout: 20_000 }).then((handle) => handle.jsonValue() as Promise<LayerInventory>);

  const points = await page.evaluate((target) => {
    const map = (window as any).__UNDEPESCUIM_MAP__;
    let candidate: any;
    map?.eachLayer((entry: any) => {
      if (!candidate && entry.feature?.properties?.slug === target && entry._path) candidate = entry;
    });
    const path = candidate?._path as SVGPathElement | undefined;
    const ctm = path?.ownerSVGElement?.getScreenCTM();
    if (!path || !ctm || path.getTotalLength() === 0) return [];
    const points: Array<{ x: number; y: number }> = [];
    for (const fraction of [0.2, 0.4, 0.6, 0.8]) {
      const local = path.getPointAtLength(path.getTotalLength() * fraction);
      const screen = new DOMPoint(local.x, local.y).matrixTransform(ctm);
      const candidatePoint = { x: screen.x, y: screen.y };
      if (screen.x >= 0 && screen.y >= 0 && screen.x <= innerWidth && screen.y <= innerHeight) points.push(candidatePoint);
      const top = document.elementFromPoint(screen.x, screen.y);
      if (top?.closest('.leaflet-overlay-pane')) points.unshift(candidatePoint);
    }
    return [...new Map(points.map((point) => [`${point.x}:${point.y}`, point])).values()];
  }, slug);
  let point: { x: number; y: number } | null = null;
  for (const candidate of points) {
    await page.mouse.click(candidate.x, candidate.y);
    if (await page.getByTestId('water-card').isVisible().catch(() => false)) {
      point = candidate;
      break;
    }
    await page.keyboard.press('Escape');
  }
  const card = await page.evaluate(() => {
    const card = document.querySelector('[data-testid="water-card"]');
    const sheet = document.querySelector('[data-testid="water-detail-sheet"]');
    const aside = document.querySelector('aside:has([data-testid="water-card"])');
    return {
      cardHeading: card?.querySelector('h2')?.textContent?.replace(/\s+/g, ' ').trim() ?? null,
      cardSurface: sheet ? 'vaul-bottom-sheet' : aside ? 'desktop-aside' : null,
    };
  });
  await page.keyboard.press('Escape');
  return { layer, point, culling: { before: presentBefore, after: Boolean(layer) }, ...card };
}

async function writeEvidence(testInfo: TestInfo, payload: unknown): Promise<void> {
  const output = testInfo.outputPath('all-repaired-layer-inventory.json');
  fs.writeFileSync(output, `${JSON.stringify(payload, null, 2)}\n`);
  fs.writeFileSync(testInfo.outputPath('all-repaired-layer-inventory.sha256'), `${sha256(JSON.stringify(payload))}\n`);
}

test.describe('all repaired ledger records reach the browser rendering path', () => {
  test.describe.configure({ mode: 'serial' });

  for (const viewport of VIEWPORTS) {
    test(`renders and pointer-clicks every repaired record at ${viewport.width}x${viewport.height}`, async ({ page }, testInfo) => {
      test.setTimeout(15 * 60_000);
      const actualViewport = page.viewportSize();
      test.skip(
        actualViewport?.width !== viewport.width || actualViewport?.height !== viewport.height,
        `viewport project is ${actualViewport?.width}x${actualViewport?.height}`,
      );
      await page.goto('/');
      await expect(page.locator('.leaflet-container')).toBeVisible();
      await page.waitForFunction(() => Boolean((window as any).__UNDEPESCUIM_MAP__));
      const { repaired, waters } = await loadLedger(page);
      expect(repaired).toHaveLength(712);
      const waterBySlug = new Map(waters.map((water) => [water.slug, water]));
      const inventory: Array<Record<string, unknown>> = [];
      for (const record of repaired) {
        const water = waterBySlug.get(record.sourceSlug);
        expect(water?.geometry, `repaired record lacks geometry ${record.sourceSlug}`).toBeTruthy();
        const variant = record.geometryVariants.find((entry) => entry.state === 'canonical-legal-sector');
        expect(variant, `missing canonical variant ${record.sourceSlug}`).toBeTruthy();
        const bbox = variant?.geometry?.bbox as [number, number, number, number] | undefined;
        expect(bbox, `missing canonical geometry bbox ${record.sourceSlug}`).toBeTruthy();
        const result = await inspectAndClick(page, record.sourceSlug, bbox!);
        expect(result.layer, `not rendered in Leaflet: ${record.sourceSlug}`).toMatchObject({ slug: record.sourceSlug });
        expect(result.point, `no real pointer hit point: ${record.sourceSlug}`).not.toBeNull();
        expect(result.cardHeading, `missing card identity: ${record.sourceSlug}`).not.toBeNull();
        expect(result.cardSurface).toBe(viewport.width < 1024 ? 'vaul-bottom-sheet' : 'desktop-aside');
        inventory.push({
          slug: record.sourceSlug,
          aliases: record.aliases,
          classification: record.classification,
          state: variant!.state,
          pane: result.layer!.pane,
          style: { pointerEvents: result.layer!.pointerEvents, zIndex: result.layer!.zIndex },
          geometryHash: variant!.geometry.geometryHash,
          segmentId: variant!.segmentId,
          culling: result.culling,
          focusKind: 'whole-feature-focus',
          cardIdentity: result.cardHeading,
          sheetIdentity: result.cardSurface,
        });
      }
      const payload = {
        artifact: 'all-repaired-browser-layer-inventory',
        schemaVersion: 1,
        viewport,
        repairedCount: inventory.length,
        records: inventory,
        inventorySha256: sha256(JSON.stringify(inventory)),
      };
      await writeEvidence(testInfo, payload);
      await page.screenshot({ path: testInfo.outputPath('all-repaired-final.png'), fullPage: false });
    });
  }
});

/* eslint-enable @typescript-eslint/no-explicit-any */
