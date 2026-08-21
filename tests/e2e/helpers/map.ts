/**
 * Map-level helpers (docs/e2e-test-plan.md §4.3 `helpers/map.ts`).
 *
 * All SVG/pixel math lives HERE — POMs and specs never touch Leaflet
 * internals. Two click paths:
 *  - `clickWaterBySlug` (primary): deterministic — finds the water's feature
 *    layer via the test bridge (`window.__UNDEPESCUIM_MAP__`, added in
 *    MapView) and fires the click Leaflet would dispatch, with the layer's
 *    real center latlng. No pixel math, immune to dashes/overlaps/LOD culls.
 *  - `clickWaterByPixel` (pipeline check): a REAL pointer click at a screen
 *    point on the water's path (elementFromPoint hit), exercising the actual
 *    Leaflet hit-testing chain. Used sparingly to guard the click pipeline.
 */
import { expect, type Page } from '@playwright/test';
import { Selectors } from './selectors';

/* eslint-disable @typescript-eslint/no-explicit-any */

/** Live Leaflet zoom level (via the test bridge — DPR/UA agnostic). */
export async function mapZoom(page: Page): Promise<number> {
  const z = await page.evaluate(() => (window as any).__UNDEPESCUIM_MAP__?.getZoom() ?? -1);
  if (z < 0) throw new Error('mapZoom: leaflet map bridge not available');
  return z;
}

/** Wait for Leaflet's animated fit/fly transition to settle before reading view state. */
export async function waitForMapIdle(page: Page): Promise<void> {
  await page.waitForFunction(() => {
    const map = (window as any).__UNDEPESCUIM_MAP__;
    return Boolean(map) && !map._animatingZoom && !map._panAnim?._inProgress;
  });
}

/** Set the map zoom programmatically (LOD tests need zoom ≥ 8). */
export async function setMapZoom(page: Page, zoom: number): Promise<void> {
  await page.evaluate(
    (z) => (window as any).__UNDEPESCUIM_MAP__?.setZoom(z),
    zoom,
  );
  await page.waitForFunction(
    (z) => (window as any).__UNDEPESCUIM_MAP__?.getZoom() === z,
    zoom,
  );
}

/** Wait until the map root + the vector overlay are rendered. */
export async function waitForMapReady(page: Page): Promise<void> {
  await expect(page.getByTestId(Selectors.mapRoot)).toBeVisible();
  await expect(page.getByTestId(Selectors.watersDrawn)).toBeAttached();
  await page.waitForFunction(
    () => document.querySelectorAll('.leaflet-overlay-pane path').length > 0,
  );
}

/**
 * Deterministic water click: fire the feature layer's click at its geographic
 * center. Returns nothing — throws when the slug cannot be resolved.
 */
export async function clickWaterBySlug(page: Page, slug: string): Promise<void> {
  const res = await page.evaluate((slug) => {
    const map = (window as any).__UNDEPESCUIM_MAP__;
    if (!map) return { ok: false as const, reason: 'no-map-bridge' };
    let target: any = null;
    map.eachLayer((layer: any) => {
      if (target) return;
      const f = layer.feature;
      if (f && f.properties && f.properties.slug === slug && layer._path) target = layer;
    });
    if (!target) return { ok: false as const, reason: `no-layer:${slug}` };
    // bbox-fallback dots are L.circleMarker (no getBounds) — use getLatLng.
    const center = target.getBounds ? target.getBounds().getCenter() : target.getLatLng();
    target.fire('click', { latlng: center, originalEvent: {} });
    return { ok: true as const };
  }, slug);
  if (!res.ok) throw new Error(`clickWaterBySlug failed: ${res.reason}`);
}

/** Click a specific fraction of a rendered LineString (for sector contracts). */
export async function clickWaterBySlugAtFraction(page: Page, slug: string, fraction: number): Promise<void> {
  const res = await page.evaluate(({ slug, fraction }) => {
    const map = (window as any).__UNDEPESCUIM_MAP__;
    let target: any = null;
    map?.eachLayer((layer: any) => {
      if (!target && layer.feature?.properties?.slug === slug && layer._path) target = layer;
    });
    const coords = target?.feature?.geometry?.coordinates;
    if (!target || !Array.isArray(coords) || coords.length < 2) return { ok: false as const };
    const line = coords[0]?.[0] instanceof Array ? coords[0] : coords;
    const scaled = Math.max(0, Math.min(0.999999, fraction)) * (line.length - 1);
    const i = Math.floor(scaled);
    const t = scaled - i;
    const a = line[i];
    const b = line[i + 1];
    target.fire('click', { latlng: { lat: a[1] + (b[1] - a[1]) * t, lng: a[0] + (b[0] - a[0]) * t }, originalEvent: {} });
    return { ok: true as const };
  }, { slug, fraction });
  if (!res.ok) throw new Error(`clickWaterBySlugAtFraction failed: ${slug}`);
}

/** Real-pointer sector click with hit-chain diagnostics for transition tests. */
export async function clickWaterBySlugAtFractionWithProbe(page: Page, slug: string, fraction: number): Promise<{
  x: number;
  y: number;
  tagName: string;
  className: string;
  pane: string;
  pointerEvents: string;
  zIndex: string;
}> {
  const result = await page.evaluate(({ slug, fraction }) => {
    const map = (window as any).__UNDEPESCUIM_MAP__;
    let target: any = null;
    map?.eachLayer((layer: any) => {
      if (!layer.feature?.properties || layer.feature.properties.slug !== slug || !layer._path) return;
      // After A is selected, the focus slice also carries the owner's slug.
      // Prefer the ordinary overlay path so the next fraction is measured
      // against the full shared course, not A's already-focused slice.
      if (!target || layer._pane?.classList?.contains('leaflet-overlay-pane')) target = layer;
    });
    const path = target?._path as SVGPathElement | undefined;
    const ctm = path?.ownerSVGElement?.getScreenCTM();
    if (!path || !ctm) return { ok: false as const, reason: `no-path:${slug}` };
    const point = path.getPointAtLength(path.getTotalLength() * Math.max(0.05, Math.min(0.95, fraction)));
    const screen = new DOMPoint(point.x, point.y).matrixTransform(ctm);
    const element = document.elementFromPoint(screen.x, screen.y);
    const pane = element?.closest<HTMLElement>('.leaflet-pane');
    if (!element || !pane || !element.closest('.leaflet-overlay-pane, .water-focus-pane, .water-association-pane')) {
      return { ok: false as const, reason: `not-in-leaflet-hit-chain:${slug}` };
    }
    const style = getComputedStyle(element);
    return {
      ok: true as const,
      x: screen.x,
      y: screen.y,
      tagName: element.tagName,
      className: typeof element.className === 'string' ? element.className : '',
      pane: pane.className,
      pointerEvents: style.pointerEvents,
      zIndex: getComputedStyle(pane).zIndex,
    };
  }, { slug, fraction });
  if (!result.ok) throw new Error(`clickWaterBySlugAtFractionWithProbe failed: ${result.reason}`);
  await page.mouse.click(result.x, result.y);
  return result;
}

/**
 * REAL pointer click on the water's rendered path — the full user gesture
 * through Leaflet's hit-testing. Samples the SVG path (handling thin/dashed
 * rivers via the invisible 16px hit layer below), then dispatches a mouse
 * click at the first screen point whose topmost element is inside the
 * leaflet overlay pane.
 */
export async function clickWaterByPixel(page: Page, slug: string): Promise<void> {
  const pt = await page.evaluate((slug) => {
    const map = (window as any).__UNDEPESCUIM_MAP__;
    if (!map) return null;
    let target: any = null;
    map.eachLayer((layer: any) => {
      if (target) return;
      const f = layer.feature;
      if (f && f.properties && f.properties.slug === slug && layer._path) target = layer;
    });
    if (!target) return null;
    const path = target._path as SVGPathElement;
    const ctm = path.ownerSVGElement?.getScreenCTM();
    if (!ctm) return null;
    const len = path.getTotalLength();
    if (!len) return null;
    const fracs = [0.15, 0.3, 0.45, 0.6, 0.75, 0.85];
    for (const frac of fracs) {
      const p = path.getPointAtLength(len * frac);
      const sp = new DOMPoint(p.x, p.y).matrixTransform(ctm);
      const top = document.elementFromPoint(sp.x, sp.y);
      if (top && top.closest && top.closest('.leaflet-overlay-pane')) {
        return { x: sp.x, y: sp.y };
      }
    }
    return null;
  }, slug);
  if (!pt) throw new Error(`clickWaterByPixel: no hittable point for ${slug}`);
  await page.mouse.click(pt.x, pt.y);
}

/** Count overlay paths stroked with any of the given colors. */
export async function countPathsByColor(page: Page, colors: readonly string[]): Promise<number> {
  return page.evaluate((colors) => {
    const set = new Set(colors.map((c) => c.toLowerCase()));
    return [...document.querySelectorAll('.leaflet-overlay-pane path, .water-focus-pane path, .water-association-pane path')].filter(
      (p) => set.has((p.getAttribute('stroke') || '').toLowerCase()),
    ).length;
  }, colors as string[]);
}

/** Total vector overlay paths (contracted + uncontracted + slices). */
export async function countAllPaths(page: Page): Promise<number> {
  return page.evaluate(() => document.querySelectorAll('.leaflet-overlay-pane path, .water-focus-pane path, .water-association-pane path').length);
}

/** Semantic snapshot of the dedicated focus pane (style + geometry, not store state). */
export async function focusSnapshot(page: Page): Promise<{
  kind: 'verified-sector-focus' | 'feature-selected-unverified-sector' | 'whole-feature-focus' | 'none';
  slug: string;
  zIndex: string;
  orangePaths: number;
  unverifiedMarkerCount: number;
  markerPanePaths: string[];
  markerAriaLabels: string[];
  paths: string[];
  map: {
    center: { lat: number; lon: number };
    zoom: number;
    bounds: { south: number; west: number; north: number; east: number };
  };
  pathOwners: Array<{ slug: string; pane: string }>;
}> {
  return page.evaluate(() => {
    const map = (window as any).__UNDEPESCUIM_MAP__;
    const pane = document.querySelector<HTMLElement>('.water-focus-pane');
    const paths = [...(pane?.querySelectorAll('path') ?? [])];
    const markerPane = document.querySelector<HTMLElement>('.water-unverified-focus-pane');
    const markerPaths = [...(markerPane?.querySelectorAll('path') ?? [])];
    const markerAriaLabels = markerPaths.map((p) => p.getAttribute('aria-label') ?? '');
    const center = map?.getCenter();
    const bounds = map?.getBounds();
    const pathOwners: Array<{ slug: string; pane: string }> = [];
    map?.eachLayer((layer: any) => {
      if (!layer._path || !layer.feature?.properties?.slug) return;
      pathOwners.push({
        slug: layer.feature.properties.slug,
        pane: layer._pane?.className ?? '',
      });
    });
    return {
      kind: markerPaths.length > 0
        ? 'feature-selected-unverified-sector'
        : paths.some((p) => p.getAttribute('stroke')?.toLowerCase() === '#f97316')
          ? 'verified-sector-focus'
          : pane?.dataset.focusSlug ? 'whole-feature-focus' : 'none',
      slug: pane?.dataset.focusSlug ?? '',
      zIndex: pane ? getComputedStyle(pane).zIndex : '',
      orangePaths: paths.filter((p) => p.getAttribute('stroke')?.toLowerCase() === '#f97316').length,
      unverifiedMarkerCount: markerPaths.length,
      markerPanePaths: markerPaths.map((p) => p.getAttribute('d') ?? ''),
      markerAriaLabels,
      paths: paths.map((p) => p.getAttribute('d') ?? ''),
      map: {
        center: { lat: center?.lat ?? 0, lon: center?.lng ?? 0 },
        zoom: map?.getZoom() ?? 0,
        bounds: {
          south: bounds?.getSouth() ?? 0,
          west: bounds?.getWest() ?? 0,
          north: bounds?.getNorth() ?? 0,
          east: bounds?.getEast() ?? 0,
        },
      },
      pathOwners,
    };
  });
}
/* eslint-enable @typescript-eslint/no-explicit-any */
