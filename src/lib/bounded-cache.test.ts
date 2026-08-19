import { describe, expect, it, vi } from 'vitest';
import { boundedCachePlugin, evictToBudget } from './bounded-cache';

function fakeCache() {
  const values = new Map<string, Response>();
  return {
    values,
    keys: async () => [...values.keys()].map((url) => new Request(url)),
    match: async (request: Request) => values.get(request.url),
    delete: async (request: Request) => values.delete(request.url),
    put: async (request: Request, response: Response) => void values.set(request.url, response),
  };
}

describe('bounded basemap cache', () => {
  it('touches cached hits and misses do not throw', async () => {
    const plugin = boundedCachePlugin({ now: () => 1 });
    const request = new Request('https://tile.openstreetmap.org/1/0/0.png');
    expect(await plugin.cachedResponseWillBeUsed({ request })).toBeUndefined();
    const response = new Response(new Uint8Array([1, 2, 3]));
    expect(await plugin.cachedResponseWillBeUsed({ request, cachedResponse: response })).toBe(response);
  });

  it('evicts least recently used entries before the byte limit', async () => {
    const cache = fakeCache();
    const entries = new Map<string, { request: Request; size: number; lastUsed: number }>();
    const old = new Request('https://tile.openstreetmap.org/1/0/0.png');
    const fresh = new Request('https://tile.openstreetmap.org/1/1/0.png');
    await cache.put(old, new Response('old'));
    await cache.put(fresh, new Response('fresh'));
    entries.set(old.url, { request: old, size: 8, lastUsed: 1 });
    entries.set(fresh.url, { request: fresh, size: 8, lastUsed: 2 });
    await evictToBudget(cache, entries, 10);
    expect(cache.values.has(old.url)).toBe(false);
    expect(cache.values.has(fresh.url)).toBe(true);
  });

  it('handles quota/storage failures without rejecting', async () => {
    const plugin = boundedCachePlugin({ limitBytes: 1 });
    const original = globalThis.caches;
    Object.defineProperty(globalThis, 'caches', { configurable: true, value: { open: vi.fn().mockRejectedValue(new Error('quota')) } });
    await expect(plugin.cacheDidUpdate({
      request: new Request('https://tile.openstreetmap.org/1/0/0.png'),
      response: new Response('tile'),
    })).resolves.toBeUndefined();
    Object.defineProperty(globalThis, 'caches', { configurable: true, value: original });
  });

  it('supports a hard entry cap even when byte sizes are unavailable', async () => {
    const cache = fakeCache();
    const entries = new Map<string, { request: Request; size: number; lastUsed: number }>();
    for (let i = 0; i < 3; i++) {
      const request = new Request(`https://tile.openstreetmap.org/1/${i}/0.png`);
      await cache.put(request, new Response('x'));
      entries.set(request.url, { request, size: 0, lastUsed: i });
    }
    await evictToBudget(cache, entries, 100, 2);
    expect(cache.values.size).toBe(2);
  });
});
