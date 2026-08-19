/// <reference lib="webworker" />
import { defaultCache } from "@serwist/next/worker";
import type { PrecacheEntry, SerwistGlobalConfig } from "serwist";
import {
  CacheFirst,
  NetworkFirst,
  ExpirationPlugin,
  CacheableResponsePlugin,
  Serwist,
} from "serwist";
import {
  BASEMAP_CACHE_NAME,
  DEFAULT_BASEMAP_CACHE_LIMIT_BYTES,
  boundedCachePlugin,
  cleanupObsoleteBasemapCaches,
} from "@/lib/bounded-cache";

declare global {
  interface WorkerGlobalScope extends SerwistGlobalConfig {
    __SW_MANIFEST: (PrecacheEntry | string)[] | undefined;
  }
}
declare const self: ServiceWorkerGlobalScope;

const DAY = 24 * 60 * 60;

const serwist = new Serwist({
  precacheEntries: self.__SW_MANIFEST,
  skipWaiting: true,
  clientsClaim: true,
  navigationPreload: true,
  disableDevLogs: true,
  runtimeCaching: [
    {
      // OSM raster tiles — ONLY tiles the user already viewed. Cache-first,
      // 7-day TTL to honour OSM Tile Usage Policy §3.2 (server sends ~6d + 7d
      // stale-while-revalidate). DO NOT extend past 7d; no prefetch/offline
      // download (policy §4 prohibits it).
      matcher: ({ url }) => url.hostname === "tile.openstreetmap.org",
      handler: new CacheFirst({
        cacheName: BASEMAP_CACHE_NAME,
        plugins: [
          boundedCachePlugin({
            // Tiles are cached only as viewed; never prefetch or fill the map.
            limitBytes: DEFAULT_BASEMAP_CACHE_LIMIT_BYTES,
            maxEntries: 1000,
          }),
          new ExpirationPlugin({ maxAgeSeconds: 7 * DAY }),
          new CacheableResponsePlugin({ statuses: [200] }),
        ],
      }),
    },
    {
      // Static data — fresh-first, fall back to cache when offline.
      matcher: ({ url, sameOrigin }) =>
        sameOrigin && url.pathname.startsWith("/data/"),
      handler: new NetworkFirst({
        cacheName: "app-data",
        networkTimeoutSeconds: 4,
        plugins: [
          new ExpirationPlugin({ maxEntries: 20, maxAgeSeconds: 7 * DAY }),
          new CacheableResponsePlugin({ statuses: [200] }),
        ],
      }),
    },
    ...defaultCache,
  ],
  fallbacks: {
    entries: [
      {
        url: "/",
        matcher({ request }) {
          return request.mode === "navigate";
        },
      },
    ],
  },
});

serwist.addEventListeners();

// Runtime caches are not part of Serwist's precache cleanup. Remove old
// versions during activation so deployments cannot strand obsolete tiles.
self.addEventListener("activate", (event) => {
  event.waitUntil(cleanupObsoleteBasemapCaches());
});