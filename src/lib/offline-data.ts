import type { Association, Water } from '@/types/data';

export const OFFLINE_SCHEMA_VERSION = 1;
export const OFFLINE_DATA_KEY = 'undepescuim.offline-data.v1';
export const DATA_STALE_AFTER_MS = 30 * 24 * 60 * 60 * 1000;
const DB_NAME = 'undepescuim-offline';
const STORE_NAME = 'snapshots';

export interface OfflineDataset {
  schemaVersion: number;
  syncedAt: string;
  dataUpdatedAt: string | null;
  associations: Association[];
  waters: Water[];
  uncontracted: Water[];
}

export function isDataStale(updatedAt: string | null, now = Date.now()): boolean {
  if (!updatedAt) return true;
  const timestamp = Date.parse(updatedAt);
  return !Number.isFinite(timestamp) || now - timestamp >= DATA_STALE_AFTER_MS;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isDataset(value: unknown): value is OfflineDataset {
  if (!isRecord(value) || value.schemaVersion !== OFFLINE_SCHEMA_VERSION) return false;
  if (typeof value.syncedAt !== 'string' || (value.dataUpdatedAt !== null && typeof value.dataUpdatedAt !== 'string')) return false;
  return Array.isArray(value.associations) && Array.isArray(value.waters) && Array.isArray(value.uncontracted);
}

function localStorageOrNull(): Storage | null {
  if (typeof window === 'undefined') return null;
  try { return window.localStorage; } catch { return null; }
}

function indexedDbOrNull(): IDBFactory | null {
  if (typeof indexedDB === 'undefined') return null;
  return indexedDB;
}

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDbOrNull()!.open(DB_NAME, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE_NAME);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error ?? new Error('offline database unavailable'));
  });
}

/** Read only complete, current-schema snapshots. Invalid data is removed deterministically. */
export async function readOfflineDataset(): Promise<OfflineDataset | null> {
  let raw: unknown;
  const idb = indexedDbOrNull();
  if (idb) {
    try {
      const db = await openDatabase();
      raw = await new Promise((resolve, reject) => {
        const request = db.transaction(STORE_NAME, 'readonly').objectStore(STORE_NAME).get(OFFLINE_DATA_KEY);
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
      db.close();
    } catch { raw = undefined; }
  } else {
    const store = localStorageOrNull();
    try { raw = store?.getItem(OFFLINE_DATA_KEY) ? JSON.parse(store.getItem(OFFLINE_DATA_KEY)!) : undefined; } catch { raw = undefined; }
  }
  if (typeof raw === 'string') {
    try { raw = JSON.parse(raw); } catch { raw = undefined; }
  }
  if (isDataset(raw)) return raw;
  await invalidateOfflineDataset();
  return null;
}

/** Replace the snapshot transactionally; quota errors leave the previous snapshot intact. */
export async function writeOfflineDataset(dataset: OfflineDataset): Promise<void> {
  if (!isDataset(dataset)) throw new Error('cannot persist invalid offline dataset');
  const idb = indexedDbOrNull();
  if (idb) {
    const db = await openDatabase();
    await new Promise<void>((resolve, reject) => {
      const transaction = db.transaction(STORE_NAME, 'readwrite');
      transaction.objectStore(STORE_NAME).put(dataset, OFFLINE_DATA_KEY);
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error ?? new Error('offline snapshot write failed'));
      transaction.onabort = () => reject(transaction.error ?? new Error('offline snapshot write aborted'));
    });
    db.close();
    return;
  }
  localStorageOrNull()?.setItem(OFFLINE_DATA_KEY, JSON.stringify(dataset));
}

export async function invalidateOfflineDataset(): Promise<void> {
  const idb = indexedDbOrNull();
  if (idb) {
    try {
      const db = await openDatabase();
      await new Promise<void>((resolve) => {
        const transaction = db.transaction(STORE_NAME, 'readwrite');
        transaction.objectStore(STORE_NAME).delete(OFFLINE_DATA_KEY);
        transaction.oncomplete = () => resolve();
        transaction.onerror = () => resolve();
      });
      db.close();
    } catch { /* already absent */ }
  }
  try { localStorageOrNull()?.removeItem(OFFLINE_DATA_KEY); } catch { /* already absent */ }
}

export function makeOfflineDataset(input: Omit<OfflineDataset, 'schemaVersion' | 'syncedAt'>, now = new Date()): OfflineDataset {
  return { ...input, schemaVersion: OFFLINE_SCHEMA_VERSION, syncedAt: now.toISOString() };
}

export async function syncOfflineDataset(fetcher: typeof fetch = fetch): Promise<OfflineDataset> {
  const responses = await Promise.all([
    fetcher('/data/associations.json'), fetcher('/data/waters.json'),
    fetcher('/data/uncontracted_rivers.json'), fetcher('/data/uncontracted_lakes.json'),
  ]);
  if (!responses.every((response) => response.ok)) throw new Error('offline dataset sync failed');
  const [associations, waters, rivers, lakes] = await Promise.all(responses.map((response) => response.json()));
  if (![associations, waters, rivers, lakes].every(Array.isArray)) throw new Error('offline dataset payload invalid');
  const dataset = makeOfflineDataset({
    associations: associations as Association[], waters: waters as Water[],
    uncontracted: [...(rivers as Water[]), ...(lakes as Water[])], dataUpdatedAt: new Date().toISOString(),
  });
  await writeOfflineDataset(dataset);
  return dataset;
}
