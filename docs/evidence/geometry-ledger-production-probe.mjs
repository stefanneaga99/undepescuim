import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const ROOT = path.resolve(import.meta.dirname, '../..');
const BASE = 'https://unde-pescuim.ro';
const OUT = path.join(ROOT, 'docs/evidence');
const TARGETS = [
  'anpa-anpa-0207', 'anpa-anpa-0210', 'anpa-anpa-0211', 'anpa-anpa-0214',
  'anpa-anpa-0261', 'romsilva-brasov-buzaul-superior',
  'romsilva-bacau-barzauta', 'romsilva-covasna-sugo',
  'romsilva-maramures-crasna-frumusaua', 'vb2p0152',
];
const DEPLOYMENT = {
  id: 'dpl_BhofeXcCTCBWEqdZeYfzjGSJd1hf',
  url: 'https://undepescuim-kwnwwz56y-stefan-a190.vercel.app',
  target: 'production',
  aliases: ['https://unde-pescuim.ro', 'https://www.unde-pescuim.ro', 'https://undepescuim.vercel.app'],
  createdAtEpochMs: 1788506499507,
  commit: null,
};
const HTTP = [
  { url: `${BASE}/`, sha256: '5540f61a46d1e893c57c2fc46d857cd0c5c89f32e05548e119c32d88bd85171d', bytes: 28128 },
  { url: `${BASE}/data/waters.json`, sha256: '56380740bbc6a9f91a49b1f4f57ee8465821e9d144eaa39822e9d19d8caab7c0', bytes: 10599467 },
  { url: `${BASE}/data/waters_county_clips.json`, sha256: '4bf26bb9d352bc112782f5dc2bc9950e5c341ee369493d39b7b84ebe2eda5e92', bytes: 1821636 },
  { url: `${BASE}/data/preview_class2_physical.json`, sha256: '8e5a548340d59187b5c02233889541375661f846cf9da2cb53a026bff37a4576', bytes: 10393036 },
];

function digest(file) {
  return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}

async function inspectTarget(page, slug, waters) {
  const water = waters.find((item) => item.slug === slug);
  const before = await page.evaluate((target) => {
    const map = window.__UNDEPESCUIM_MAP__;
    return Object.values(map?._layers ?? {}).some((layer) => {
      const p = layer.feature?.properties;
      return p?.slug === target || p?.physicalAliases?.includes(target);
    });
  }, slug);
  const bbox = (() => {
    const points = [];
    const visit = (value) => {
      if (!Array.isArray(value)) return;
      if (value.length >= 2 && typeof value[0] === 'number' && typeof value[1] === 'number') points.push(value);
      else value.forEach(visit);
    };
    visit(water?.geometry?.coordinates);
    if (points.length) return [Math.min(...points.map((p) => p[0])), Math.min(...points.map((p) => p[1])), Math.max(...points.map((p) => p[0])), Math.max(...points.map((p) => p[1]))];
    return water?.bbox ?? null;
  })();
  if (bbox) {
    await page.evaluate(([minLon, minLat, maxLon, maxLat]) => {
      window.__UNDEPESCUIM_MAP__?.fitBounds([[minLat, minLon], [maxLat, maxLon]], { padding: [40, 40], maxZoom: 12, animate: false });
    }, bbox);
    await page.waitForTimeout(800);
  }
  const layerSnapshot = await page.evaluate((target) => {
    const map = window.__UNDEPESCUIM_MAP__;
    const matches = Object.values(map?._layers ?? {}).filter((layer) => {
      const p = layer.feature?.properties;
      return p?.slug === target || p?.physicalAliases?.includes(target);
    });
    return matches.map((layer) => ({
      properties: layer.feature?.properties ?? null,
      style: {
        color: layer.options?.color ?? null, weight: layer.options?.weight ?? null,
        opacity: layer.options?.opacity ?? null, dashArray: layer.options?.dashArray ?? null,
        fillColor: layer.options?.fillColor ?? null, fillOpacity: layer.options?.fillOpacity ?? null,
      },
    }));
  }, slug);
  let card = null;
  if (layerSnapshot.length) {
    await page.evaluate((target) => {
      const map = window.__UNDEPESCUIM_MAP__;
      const layer = Object.values(map?._layers ?? {}).find((candidate) => {
        const p = candidate.feature?.properties;
        return p?.slug === target || p?.physicalAliases?.includes(target);
      });
      layer?.fire('click', { latlng: map?.getCenter() });
    }, slug);
    await page.locator('[data-testid="water-card"]').waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
    card = await page.evaluate(() => {
      const node = document.querySelector('[data-testid="water-card"]');
      const sheet = document.querySelector('[data-testid="water-detail-sheet"]');
      const aside = document.querySelector('aside:has([data-testid="water-card"])');
      return node ? {
        text: node.textContent?.replace(/\s+/g, ' ').trim() ?? '',
        surface: sheet ? 'vaul-bottom-sheet' : aside ? 'desktop-aside' : 'unknown',
        disclosure: document.querySelector('[data-testid="physical-preview-disclosure"]')?.textContent?.replace(/\s+/g, ' ').trim() ?? null,
        sheetSnapHeight: getComputedStyle(document.documentElement).getPropertyValue('--sheet-snap-h').trim(),
      } : null;
    });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(150);
  }
  return {
    targetSlug: slug,
    canonicalName: water?.name ?? null,
    canonicalCounty: water?.judet ?? null,
    canonicalGeometryPresent: Boolean(water?.geometry),
    canonicalBbox: water?.bbox ?? null,
    culling: { presentAtPriorView: before, fitUsed: bbox, presentAfterFit: layerSnapshot.length > 0 },
    featureCount: layerSnapshot.length,
    features: layerSnapshot,
    card,
  };
}

async function run() {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const probes = [];
  const observations = Object.fromEntries(TARGETS.map((slug) => [slug, []]));
  for (const viewport of [{ width: 390, height: 844 }, { width: 1280, height: 800 }]) {
    for (const serviceWorkers of ['block', 'allow']) {
      const context = await browser.newContext({ viewport, serviceWorkers });
      const page = await context.newPage();
      const consoleErrors = [];
      page.on('console', (message) => { if (message.type() === 'error') consoleErrors.push(message.text()); });
      page.on('pageerror', (error) => consoleErrors.push(`pageerror: ${error.message}`));
      const response = await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await page.locator('.leaflet-container').waitFor({ state: 'visible', timeout: 45000 });
      await page.waitForFunction(() => window.__UNDEPESCUIM_MAP__, undefined, { timeout: 45000 });
      await page.waitForTimeout(1500);
      const actualViewport = await page.evaluate(() => ({ width: innerWidth, height: innerHeight }));
      const sw = await page.evaluate(async () => ({
        controller: Boolean(navigator.serviceWorker?.controller),
        registrations: navigator.serviceWorker ? (await navigator.serviceWorker.getRegistrations()).map((r) => ({ scope: r.scope, active: r.active?.scriptURL ?? null })) : [],
      }));
      const waters = await page.evaluate(async () => (await fetch('/data/waters.json')).json());
      const targetResults = [];
      for (const slug of TARGETS) {
        const result = await inspectTarget(page, slug, waters);
        targetResults.push(result);
        observations[slug].push({
          viewport: `${viewport.width}x${viewport.height}`,
          serviceWorkers,
          featureCount: result.featureCount,
          featureProperties: result.features.map((item) => item.properties),
          styles: result.features.map((item) => item.style),
          card: result.card,
          culling: result.culling,
        });
      }
      const stem = `production-${viewport.width}x${viewport.height}-sw-${serviceWorkers}`;
      const screenshotPath = path.join(OUT, `${stem}.png`);
      await page.screenshot({ path: screenshotPath, fullPage: false });
      probes.push({
        viewport: `${viewport.width}x${viewport.height}`,
        actualViewport,
        serviceWorkers,
        url: page.url(),
        httpStatus: response?.status() ?? null,
        serviceWorkerState: sw,
        consoleErrors,
        map: await page.evaluate(() => ({
          center: window.__UNDEPESCUIM_MAP__?.getCenter(),
          zoom: window.__UNDEPESCUIM_MAP__?.getZoom(),
          renderedPathCount: document.querySelectorAll('.leaflet-overlay-pane path').length,
          visibleControlsText: [...document.querySelectorAll('button')].filter((node) => node.offsetParent !== null).map((node) => node.textContent?.replace(/\s+/g, ' ').trim()).filter(Boolean).slice(0, 30),
        })),
        targets: targetResults,
        evidencePath: `docs/evidence/${stem}.png`,
        evidenceSha256: digest(screenshotPath),
      });
      await context.close();
    }
  }
  await browser.close();
  const payload = {
    artifact: 'geometry-ledger-production-observations', schemaVersion: 1,
    productionUrl: BASE, deployment: DEPLOYMENT, immutableHttpArtifacts: HTTP,
    probes, observations,
    limitations: [
      'Vercel inspect verified deployment ID, URL, aliases and creation time but did not expose a git commit field; commit mapping is therefore not asserted.',
      'Physical-preview aliases share one deduplicated feature; clicking that feature opens its representative source card, so non-representative alias card text is not independently observable from the map layer.',
      'Browser observations describe rendering only and are never legal ownership, association or endpoint evidence.',
    ],
  };
  const output = path.join(OUT, 'geometry-ledger-production-observations.json');
  fs.writeFileSync(output, `${JSON.stringify(payload, null, 2)}\n`);
  console.log(JSON.stringify({ output, probes: probes.length, observations: Object.keys(observations).length, sha256: digest(output) }));
}

await run();
