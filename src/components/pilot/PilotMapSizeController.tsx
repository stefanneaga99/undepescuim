'use client';

import { useEffect } from 'react';
import { useMap } from 'react-leaflet';

/** Leaflet measures its container once at mount. The pilot is mounted below a
 * client-rendered badge and a mobile dynamic route, so make size invalidation
 * deterministic instead of relying on a one-off timeout. */
export function PilotMapSizeController() {
  const map = useMap();

  useEffect(() => {
    const invalidate = () => map.invalidateSize({ pan: false, animate: false });
    const frame = requestAnimationFrame(invalidate);
    const observer = new ResizeObserver(invalidate);
    observer.observe(map.getContainer());
    window.addEventListener('orientationchange', invalidate);
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      window.removeEventListener('orientationchange', invalidate);
    };
  }, [map]);

  return null;
}