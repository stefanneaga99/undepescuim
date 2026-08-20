import { expect, type Page } from '@playwright/test';
import type { OfflineDataset } from '../../../src/lib/offline-data';
import { OFFLINE_SCHEMA_VERSION } from '../../../src/lib/offline-data';

export const MOBILE_FIXTURE_NOW = '2026-08-20T12:00:00.000Z';
export const MOBILE_FIXTURE_29_DAYS = '2026-07-22T12:00:00.000Z';
export const MOBILE_FIXTURE_30_DAYS = '2026-07-21T12:00:00.000Z';

export function offlineDataset(dataUpdatedAt: string): OfflineDataset {
  return {
    schemaVersion: OFFLINE_SCHEMA_VERSION,
    syncedAt: MOBILE_FIXTURE_NOW,
    dataUpdatedAt,
    associations: [],
    waters: [],
    uncontracted: [],
  };
}

/** Seed the same IndexedDB snapshot used by the production offline reader. */
export async function seedOfflineSnapshot(page: Page, dataUpdatedAt: string): Promise<void> {
  await page.evaluate(async (dataset) => {
    const request = indexedDB.open('undepescuim-offline', 1);
    await new Promise<void>((resolve, reject) => {
      request.onupgradeneeded = () => request.result.createObjectStore('snapshots');
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve();
    });
    const db = request.result;
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction('snapshots', 'readwrite');
      tx.objectStore('snapshots').put(dataset, 'undepescuim.offline-data.v1');
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
    db.close();
  }, offlineDataset(dataUpdatedAt));
}

export async function expectStaleMarker(page: Page, stale: boolean): Promise<void> {
  const marker = page.getByText('Necesită reîmprospătare', { exact: false });
  if (stale) await expect(marker).toBeVisible();
  else await expect(marker).toBeHidden();
}

/** Stable, cacheable map regions; callers request each region explicitly. */
export const CACHE_REGIONS = Array.from({ length: 12 }, (_, index) => ({
  id: `region-${String(index + 1).padStart(2, '0')}`,
  tileUrls: Array.from({ length: 8 }, (_, tile) => `/__mobile-fixture__/tiles/${index + 1}/${tile + 1}.png`),
}));
