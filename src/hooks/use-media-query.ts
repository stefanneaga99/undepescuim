'use client';

import { useCallback, useSyncExternalStore } from 'react';

/**
 * SSR-safe media query hook (matchMedia via useSyncExternalStore).
 * Server snapshot is false → no hydration mismatch; the UI settles on the
 * first client snapshot. Queries must be module-level constants.
 */
export function useMediaQuery(query: string): boolean {
  const subscribe = useCallback(
    (onStoreChange: () => void) => {
      const mq = window.matchMedia(query);
      mq.addEventListener('change', onStoreChange);
      return () => mq.removeEventListener('change', onStoreChange);
    },
    [query],
  );
  const getSnapshot = useCallback(() => window.matchMedia(query).matches, [query]);
  const getServerSnapshot = () => false;
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
