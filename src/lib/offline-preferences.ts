import { invalidateOfflineDataset } from './offline-data';

export const OFFLINE_PREFERENCE_KEY = 'undepescuim.offline-preference.v1';
export const OFFLINE_CACHE_NAMES = ['app-data', 'osm-tiles-v2', 'osm-tiles', 'serwist-expiration', 'serwist-precache-v2'];
export type OfflinePreference = 'unknown' | 'enabled' | 'disabled';

export function getOfflinePreference(): OfflinePreference {
  if (typeof window === 'undefined') return 'unknown';
  try {
    const value = window.localStorage.getItem(OFFLINE_PREFERENCE_KEY);
    return value === 'enabled' || value === 'disabled' ? value : 'unknown';
  } catch {
    return 'unknown';
  }
}

export function setOfflinePreference(preference: Exclude<OfflinePreference, 'unknown'>): void {
  try {
    window.localStorage.setItem(OFFLINE_PREFERENCE_KEY, preference);
    window.dispatchEvent(new Event('offline-preference-change'));
  } catch {
    // A blocked preference store means optional offline storage stays unusable.
  }
}

export async function clearOfflineCaches(): Promise<void> {
  if (typeof caches === 'undefined') return;
  await Promise.all(OFFLINE_CACHE_NAMES.map((name) => caches.delete(name)));
}

export async function clearOfflineStorage(): Promise<void> {
  await Promise.all([clearOfflineCaches(), invalidateOfflineDataset()]);
}

/** Revoke consent before clearing data, so concurrent loads cannot repopulate it. */
export async function disableOffline(): Promise<void> {
  setOfflinePreference('disabled');
  await Promise.all([
    clearOfflineStorage(),
    ...(typeof navigator !== 'undefined' && 'serviceWorker' in navigator
      ? [navigator.serviceWorker.getRegistrations().then((registrations) => Promise.all(registrations.map((registration) => {
        registration.active?.postMessage({ type: 'undepescuim-offline-revoked' });
        return registration.unregister();
      })))]
      : []),
  ]);
}

export async function registerOfflineServiceWorker(): Promise<void> {
  if (typeof navigator === 'undefined' || !('serviceWorker' in navigator) || process.env.NODE_ENV !== 'production') return;
  try {
    await navigator.serviceWorker.register('/sw.js', { updateViaCache: 'none' });
  } catch {
    // Offline is an enhancement; a blocked worker must never break the app.
  }
}