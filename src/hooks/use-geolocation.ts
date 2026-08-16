'use client';

import { useCallback, useState } from 'react';

/**
 * Browser Geolocation API wrapper — geolocation MVP
 * (docs/geolocation-feasibility.md §2a + §7.2).
 *
 * State machine:
 *  - idle:      never requested (opt-in button, never fires on load)
 *  - requesting: getCurrentPosition in flight (10 s timeout)
 *  - granted:   one-shot fix received {lat, lon, accuracy}
 *  - denied:    PERMISSION_DENIED — iOS hard-deny cannot re-prompt, the UI
 *               must surface a "enable Location in Settings" hint
 *  - error:     timeout / unavailable / unsupported — graceful fallback,
 *               map stays in the default view
 *
 * No `watchPosition` (no tracking; battery/privacy risk per feasibility §8).
 */
export type GeoState =
  | { status: 'idle' }
  | { status: 'requesting' }
  | { status: 'granted'; lat: number; lon: number; accuracy: number }
  | { status: 'denied' }
  | { status: 'error' };

export function useGeolocation() {
  const [state, setState] = useState<GeoState>({ status: 'idle' });

  const locate = useCallback(() => {
    if (typeof navigator === 'undefined' || !('geolocation' in navigator)) {
      setState({ status: 'error' });
      return;
    }
    setState({ status: 'requesting' });
    navigator.geolocation.getCurrentPosition(
      (p) =>
        setState({
          status: 'granted',
          lat: p.coords.latitude,
          lon: p.coords.longitude,
          accuracy: p.coords.accuracy,
        }),
      (e) =>
        setState({
          status: e.code === e.PERMISSION_DENIED ? 'denied' : 'error',
        }),
      { enableHighAccuracy: true, timeout: 10_000, maximumAge: 60_000 },
    );
  }, []);

  return { state, locate };
}
