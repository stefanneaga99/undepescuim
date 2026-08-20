import type { BrowserContext, Page, TestInfo } from '@playwright/test';

export type RequestRecord = { url: string; method: string; timestamp: number };
export type RequestRecorder = {
  requests: RequestRecord[];
  dataRequests: () => RequestRecord[];
  reportPosts: () => RequestRecord[];
  byPath: (path: string) => RequestRecord[];
};

/** Capture only request metadata; never persist headers, bodies, or credentials. */
export async function installRequestRecorder(page: Page): Promise<RequestRecorder> {
  const requests: RequestRecord[] = [];
  page.on('request', (request) => {
    try {
      requests.push({ url: new URL(request.url()).pathname, method: request.method(), timestamp: Date.now() });
    } catch { /* ignore malformed third-party requests */ }
  });
  return {
    requests,
    dataRequests: () => requests.filter((r) => r.url.startsWith('/data/')),
    reportPosts: () => requests.filter((r) => r.url === '/api/report' && r.method === 'POST'),
    byPath: (path) => requests.filter((r) => r.url === path),
  };
}

export async function storageMetrics(page: Page) {
  return page.evaluate(async () => {
    const cacheEntries: Record<string, number> = {};
    const cacheBytes: Record<string, number> = {};
    for (const name of await caches.keys()) {
      const cache = await caches.open(name);
      const entries = await cache.keys();
      cacheEntries[name] = entries.length;
      let bytes = 0;
      for (const request of entries) {
        const response = await cache.match(request);
        bytes += Number(response?.headers.get('content-length') ?? 0);
      }
      cacheBytes[name] = bytes;
    }
    const estimate = await navigator.storage?.estimate?.();
    return { storage: estimate ?? null, cacheEntries, cacheBytes, cacheNames: Object.keys(cacheEntries) };
  });
}

/** Reset all browser-owned state so each matrix run starts from a known baseline. */
export async function resetBrowserState(context: BrowserContext): Promise<void> {
  await context.clearCookies();
  await context.clearPermissions();
  const page = context.pages()[0] ?? await context.newPage();
  await page.goto('about:blank');
  await page.evaluate(async () => {
    localStorage.clear();
    sessionStorage.clear();
    if ('indexedDB' in window) {
      for (const db of await indexedDB.databases()) if (db.name) indexedDB.deleteDatabase(db.name);
    }
    if ('caches' in window) for (const name of await caches.keys()) await caches.delete(name);
    for (const registration of await navigator.serviceWorker?.getRegistrations?.() ?? []) await registration.unregister();
  });
}

/** Match network state in both CDP and the UI-facing navigator.onLine property. */
export async function setDeviceOnline(page: Page, online: boolean): Promise<void> {
  // Update the page before toggling CDP connectivity. Chromium may dispatch a
  // navigation/reload while going offline (especially with a service worker);
  // doing the evaluate first avoids racing a destroyed execution context.
  await page.evaluate((value) => {
    Object.defineProperty(navigator, 'onLine', { configurable: true, get: () => value });
    window.dispatchEvent(new Event(value ? 'online' : 'offline'));
  }, online);
  await page.context().setOffline(!online);
}

export async function waitForOnlineState(page: Page, online: boolean): Promise<void> {
  await page.waitForFunction((expected) => navigator.onLine === expected, online);
  if (online) await page.getByTestId('offline-banner').waitFor({ state: 'hidden' }).catch(() => undefined);
  else await page.getByTestId('offline-banner').waitFor({ state: 'visible' });
}

export async function attachMobileMetrics(page: Page, testInfo: TestInfo, recorder?: RequestRecorder): Promise<void> {
  const metrics = { requests: recorder?.requests ?? [], ...(await storageMetrics(page)).storage };
  await testInfo.attach('mobile-metrics.json', { body: JSON.stringify(metrics, null, 2), contentType: 'application/json' });
}
