export const BASEMAP_CACHE_NAME = 'osm-tiles-v2';
export const DEFAULT_BASEMAP_CACHE_LIMIT_BYTES = 25 * 1024 * 1024;

export type CacheLike = {
  keys(): Promise<readonly Request[]>;
  match(request: Request): Promise<Response | undefined>;
  delete(request: Request): Promise<boolean>;
};

type CacheEntry = { request: Request; size: number; lastUsed: number };

/** Response size without consuming the response used by the cache handler. */
export async function estimateResponseBytes(response: Response): Promise<number> {
  const length = response.headers.get('content-length');
  if (length && Number.isFinite(Number(length))) return Math.max(0, Number(length));
  try {
    return (await response.clone().arrayBuffer()).byteLength;
  } catch {
    // Opaque responses cannot be inspected. Keep them in the cache; the entry
    // cap still provides a hard bound for the normal tile response path.
    return 0;
  }
}

/** Evict the oldest entries until both configured limits are satisfied. */
export async function evictToBudget(
  cache: CacheLike,
  entries: Map<string, CacheEntry>,
  limitBytes: number,
  maxEntries = Infinity,
): Promise<void> {
  const requests = await cache.keys();
  const current: CacheEntry[] = [];
  let total = 0;
  for (const request of requests) {
    let entry = entries.get(request.url);
    if (!entry) {
      const response = await cache.match(request);
      entry = { request, size: response ? await estimateResponseBytes(response) : 0, lastUsed: 0 };
      entries.set(request.url, entry);
    }
    current.push(entry);
    total += entry.size;
  }
  current.sort((a, b) => a.lastUsed - b.lastUsed);
  while (current.length > maxEntries || total > limitBytes) {
    const victim = current.shift();
    if (!victim) break;
    try {
      if (await cache.delete(victim.request)) {
        total -= victim.size;
        entries.delete(victim.request.url);
      }
    } catch {
      // Quota/storage failures are non-fatal. The next request can retry.
      break;
    }
  }
}

export function boundedCachePlugin({
  limitBytes = DEFAULT_BASEMAP_CACHE_LIMIT_BYTES,
  maxEntries = 1000,
  now = () => Date.now(),
}: {
  limitBytes?: number;
  maxEntries?: number;
  now?: () => number;
} = {}) {
  const entries = new Map<string, CacheEntry>();
  const touch = async (request: Request, response?: Response) => {
    const previous = entries.get(request.url);
    const size = response ? await estimateResponseBytes(response) : previous?.size ?? 0;
    entries.set(request.url, { request, size, lastUsed: now() });
  };
  return {
    async cachedResponseWillBeUsed({ request, cachedResponse }: { request: Request; cachedResponse?: Response }) {
      if (cachedResponse) await touch(request, cachedResponse);
      return cachedResponse;
    },
    async cacheDidUpdate({ request, response }: { request: Request; response?: Response }) {
      if (!response) return;
      await touch(request, response);
      try {
        const cache = await caches.open(BASEMAP_CACHE_NAME);
        await evictToBudget(cache, entries, limitBytes, maxEntries);
      } catch {
        // Private browsing and disabled Cache Storage must never break maps.
      }
    },
  };
}

export async function cleanupObsoleteBasemapCaches(): Promise<void> {
  try {
    const names = await caches.keys();
    await Promise.all(
      names
        .filter((name) => name.startsWith('osm-tiles') && name !== BASEMAP_CACHE_NAME)
        .map((name) => caches.delete(name)),
    );
  } catch {
    // Cache Storage is optional (private browsing / restricted environments).
  }
}
