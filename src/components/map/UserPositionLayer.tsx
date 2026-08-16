'use client';

import { useEffect, useMemo, useRef } from 'react';
import { Circle, Marker, useMap } from 'react-leaflet';
import L from 'leaflet';
import { useMapStore } from '@/stores/map-store';

/**
 * User position overlay — geolocation MVP (docs/geolocation-feasibility.md
 * §7.2 `UserPositionLayer`). Rendered inside <MapContainer> when a one-shot
 * fix is in the store:
 *  - blue pulsing CSS dot (divIcon — Leaflet's default marker images break
 *    under bundlers, and this codebase renders no bitmap markers at all);
 *  - radius circle drawn with the ADAPTIVE radius actually used;
 *  - one flyTo on each new fix (zoom ≥ 12) so the user sees where they are.
 *
 * Re-fix / re-locate: a new granted position updates the store → the effect
 * flies again. Clearing (clearUserPosition) unmounts everything.
 */

const USER_DOT_ICON = L.divIcon({
  className: 'user-position-dot',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

export function UserPositionLayer() {
  const map = useMap();
  const userPosition = useMapStore((s) => s.userPosition);
  const nearbyRadiusKm = useMapStore((s) => s.nearbyRadiusKm);
  const lastLon = useRef<number | null>(null);
  const lastLat = useRef<number | null>(null);

  const icon = useMemo(() => USER_DOT_ICON, []);

  // Fly to each NEW fix once (a re-render with the same coords must not
  // re-trigger a flyTo).
  useEffect(() => {
    if (!userPosition) return;
    if (lastLat.current === userPosition.lat && lastLon.current === userPosition.lon) return;
    lastLat.current = userPosition.lat;
    lastLon.current = userPosition.lon;
    map.flyTo([userPosition.lat, userPosition.lon], 12, { duration: 0.8 });
  }, [userPosition, map]);

  if (!userPosition) return null;

  return (
    <>
      <Marker position={[userPosition.lat, userPosition.lon]} icon={icon} />
      <Circle
        center={[userPosition.lat, userPosition.lon]}
        radius={nearbyRadiusKm * 1000}
        pathOptions={{
          color: '#2563eb',
          weight: 1,
          fillColor: '#2563eb',
          fillOpacity: 0.06,
          interactive: false,
        }}
      />
    </>
  );
}
