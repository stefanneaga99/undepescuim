import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  DATA_STALE_AFTER_MS,
  OFFLINE_DATA_KEY,
  isDataStale,
  makeOfflineDataset,
  readOfflineDataset,
  syncOfflineDataset,
} from './offline-data';
import {
  disableOffline,
  getOfflinePreference,
  setOfflinePreference,
} from './offline-preferences';

const water = { slug: 'w', name: 'W', judet: 'Cluj', type: 'ape', subtype: 'lac', coordinates: [23, 46], bbox: [23, 46, 23, 46], asociatie: null } as never;

beforeEach(() => localStorage.clear());

describe('offline dataset snapshots', () => {
  it('does not opt into optional storage until explicitly enabled', () => {
    expect(getOfflinePreference()).toBe('unknown');
    setOfflinePreference('disabled');
    expect(getOfflinePreference()).toBe('disabled');
    setOfflinePreference('enabled');
    expect(getOfflinePreference()).toBe('enabled');
  });

  it('revoking offline access clears the snapshot and preference', async () => {
    const existing = makeOfflineDataset({ dataUpdatedAt: null, associations: [], waters: [], uncontracted: [] });
    localStorage.setItem(OFFLINE_DATA_KEY, JSON.stringify(existing));
    setOfflinePreference('enabled');
    await disableOffline();
    expect(getOfflinePreference()).toBe('disabled');
    expect(localStorage.getItem(OFFLINE_DATA_KEY)).toBeNull();
  });

  it('marks the exact 30-day boundary stale', () => {
    const now = Date.parse('2026-01-31T00:00:00.000Z');
    expect(isDataStale(new Date(now - DATA_STALE_AFTER_MS).toISOString(), now)).toBe(true);
    expect(isDataStale(new Date(now - DATA_STALE_AFTER_MS + 1).toISOString(), now)).toBe(false);
  });

  it('drops corrupt and schema-mismatched snapshots', async () => {
    localStorage.setItem(OFFLINE_DATA_KEY, '{not-json');
    expect((await readOfflineDataset())).toBeNull();
    localStorage.setItem(OFFLINE_DATA_KEY, JSON.stringify({ schemaVersion: 99 }));
    expect((await readOfflineDataset())).toBeNull();
  });

  it('syncs all pools and does not persist a partial response', async () => {
    const response = (body: unknown, ok = true) => ({ ok, json: async () => body }) as Response;
    const fetcher = vi.fn()
      .mockResolvedValueOnce(response([]))
      .mockResolvedValueOnce(response([water]))
      .mockResolvedValueOnce(response([water]))
      .mockResolvedValueOnce(response([water]));
    const snapshot = await syncOfflineDataset(fetcher as typeof fetch);
    expect(snapshot.waters).toHaveLength(1);
    expect(snapshot.uncontracted).toHaveLength(2);
    expect((await readOfflineDataset())?.schemaVersion).toBe(1);
    expect(fetcher).toHaveBeenCalledTimes(4);
  });

  it('rejects failed sync without replacing the previous snapshot', async () => {
    const existing = makeOfflineDataset({ dataUpdatedAt: null, associations: [], waters: [], uncontracted: [] });
    localStorage.setItem(OFFLINE_DATA_KEY, JSON.stringify(existing));
    const fetcher = vi.fn().mockResolvedValue({ ok: false, status: 503 });
    await expect(syncOfflineDataset(fetcher as typeof fetch)).rejects.toThrow();
    expect((await readOfflineDataset())?.syncedAt).toBe(existing.syncedAt);
  });
});
