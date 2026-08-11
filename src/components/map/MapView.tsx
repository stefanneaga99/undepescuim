'use client';

import { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, ZoomControl, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { useMapStore } from '@/stores/map-store';
import { useFilteredWaters } from '@/hooks/use-filtered-waters';
import { WaterFeatureLayer } from '@/components/map/WaterFeatureLayer';

/**
 * Leaflet map wrapper — loaded via dynamic(ssr:false) from MapShell.
 * (react-leaflet v5 is ESM-only and touches window at module eval.)
 *
 * Default view: full Romania [45.95, 24.95] zoom 7 (user-confirmed).
 * Auto-center/zoom on association select (FlyToController).
 */
export function MapView() {
  const filteredWaters = useFilteredWaters();
  const coverageSlug = useMapStore((s) => s.selectedAssociationSlug);

  return (
    <MapContainer
      center={[45.95, 24.95]}
      zoom={7}
      zoomControl={false}
      className="map-touch z-0 h-full w-full"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <ZoomControl position="topright" />
      <WaterFeatureLayer waters={filteredWaters} coverageSlug={coverageSlug} />
      <FlyToController />
    </MapContainer>
  );
}

/**
 * User-confirmed behavior: auto-center/zoom on association select.
 * Selecting an association → fly to its bbox center (zoom 9).
 * Clearing → fly back to the full-Romania default view.
 */
function FlyToController() {
  const map = useMap();
  const dataLoaded = useMapStore((s) => s.dataLoaded);
  const associations = useMapStore((s) => s.associations);
  const slug = useMapStore((s) => s.selectedAssociationSlug);
  const firstRun = useRef(true);

  useEffect(() => {
    if (!dataLoaded) return;
    if (firstRun.current) {
      // Initial view is already the Romania default — skip the first flyTo.
      firstRun.current = false;
      return;
    }
    if (!slug) {
      map.flyTo([45.95, 24.95], 7, { duration: 0.8 });
      return;
    }
    const assoc = associations.find((a) => a.slug === slug);
    if (!assoc) return;
    const [minLon, minLat, maxLon, maxLat] = assoc.bbox;
    map.flyTo([(minLat + maxLat) / 2, (minLon + maxLon) / 2], 9, { duration: 0.8 });
  }, [slug, associations, dataLoaded, map]);

  return null;
}
