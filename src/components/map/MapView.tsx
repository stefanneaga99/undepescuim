'use client';

import { useEffect, useMemo, useRef } from 'react';
import { MapContainer, TileLayer, ZoomControl, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { useMapStore } from '@/stores/map-store';
import { useFilteredWaters } from '@/hooks/use-filtered-waters';
import { useFilteredUncontracted } from '@/hooks/use-filtered-uncontracted';
import { WaterFeatureLayer, contractInterval } from '@/components/map/WaterFeatureLayer';
import { UncontractedWaterLayer } from '@/components/map/UncontractedWaterLayer';
import { FOCUS_COLOR } from '@/utils/colors';

/**
 * Leaflet map wrapper — loaded via dynamic(ssr:false) from MapShell.
 * (react-leaflet v5 is ESM-only and touches window at module eval.)
 *
 * Default view: full Romania [45.95, 24.95] zoom 7 (user-confirmed).
 * Auto-center/zoom on association select (FlyToController).
 */
export function MapView() {
  const filteredWaters = useFilteredWaters();
  const filteredUncontracted = useFilteredUncontracted();
  const coverageSlug = useMapStore((s) => s.selectedAssociationSlug);
  const selectedWaterSlug = useMapStore((s) => s.selectedWaterSlug);
  const allWaters = useMapStore((s) => s.waters);
  const uncontracted = useMapStore((s) => s.uncontracted);

  // Focus: when a water/contract is selected from the detail card, highlight
  // the water in orange. t_b1547e24: EVERY water gets the highlight —
  // contracted (sector-sliced) AND uncontracted (whole feature). The
  // selection resolves across BOTH pools; uncontracted waters (teal overlay /
  // private ponds) live in the separate `uncontracted` pool, so resolving only
  // against `allWaters` yielded null → no highlight at all (the original bug).
  const selected =
    allWaters.find((w) => w.slug === selectedWaterSlug) ??
    uncontracted.find((w) => w.slug === selectedWaterSlug) ??
    null;
  const focusKey = selected?.name ? selected.name : null;
  const focusColor = selected ? FOCUS_COLOR : null;

  // Compute the contract's [start, end] fraction of the river course
  // (t_b6a0e2fe: shared helper — exact sector intervals win, else the
  // Voronoi interval over course_frac; single-contract rivers = [0, 1]).
  const focusRange = useMemo<[number, number] | null>(() => {
    if (!selected) return null;
    // Uncontracted waters have no contracts/sectors — highlight the whole
    // feature, never slice (t_b1547e24).
    if (selected.uncontracted) return null;
    return contractInterval(selected, allWaters);
  }, [selected, allWaters]);

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
      {/* Uncontracted overlay renders BELOW contracted waters so clicks on a
          contracted river always win over the teal background layer. */}
      <UncontractedWaterLayer waters={filteredUncontracted} focusColor={focusColor} />
      <WaterFeatureLayer
        waters={filteredWaters}
        allWaters={allWaters}
        coverageSlug={coverageSlug}
        focusKey={focusKey}
        focusColor={focusColor}
        focusRange={focusRange}
      />
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
    // bbox can be null (associations without a geocoded bbox — e.g.
    // AJVPS Covasna, Direcția Silvică Brașov): destructuring null crashes
    // the whole app, so stay on the current view instead (t_b6a0e2fe).
    if (!assoc || !assoc.bbox) return;
    const [minLon, minLat, maxLon, maxLat] = assoc.bbox;
    map.flyTo([(minLat + maxLat) / 2, (minLon + maxLon) / 2], 9, { duration: 0.8 });
  }, [slug, associations, dataLoaded, map]);

  return null;
}
