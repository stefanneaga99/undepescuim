'use client';

import { useEffect, useMemo, useRef } from 'react';
import L from 'leaflet';
import { MapContainer, TileLayer, ZoomControl, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { useMapStore } from '@/stores/map-store';
import { useFilteredWaters } from '@/hooks/use-filtered-waters';
import { useFilteredUncontracted } from '@/hooks/use-filtered-uncontracted';
import { WaterFeatureLayer } from '@/components/map/WaterFeatureLayer';
import { contractInterval } from '@/utils/river-course';
import { UncontractedWaterLayer } from '@/components/map/UncontractedWaterLayer';
import { UserPositionLayer } from '@/components/map/UserPositionLayer';
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
        // F6 (t_0618943a): single host, no {s}. subdomain — OSM Tile Usage
        // Policy §1 (offline-pwa-feasibility.md §2.6); the SW's osm-tiles
        // cache matcher keys on tile.openstreetmap.org (src/app/sw.ts).
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        // CORS: without this the <img> loads are no-cors → opaque responses
        // (status 0) in the SW fetch handler, which CacheableResponsePlugin
        // (statuses [200]) drops → tiles never enter the osm-tiles cache.
        // OSM sends Access-Control-Allow-Origin: * so anonymous is safe.
        crossOrigin="anonymous"
        // Offline pan: failed tile loads fire 'tileerror' — dim the tile to a
        // neutral grey instead of leaving the broken-image icon + console
        // error flood (offline-pwa-feasibility.md §4 / risk table).
        eventHandlers={{
          tileerror: (e) => {
            const tile = e.tile as HTMLElement;
            tile.style.opacity = "0.3";
            tile.style.filter = "grayscale(1)";
            tile.setAttribute("data-tileerror", "1");
          },
        }}
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
      <UserPositionLayer />
      <FlyToController />
      <LocalityViewportController />
      <MapTestBridge />
    </MapContainer>
  );
}

/**
 * t_9529e678: selecting a LOCALITY must visibly change the map. The county
 * filter keeps the current (national) view, so the locality's waters — a
 * handful of small ponds/short rivers — render as sub-pixel specks (or are
 * LOD-culled at z7): the user saw "nothing happens". This controller flies
 * to the filtered set's bounds when a locality is picked, and restores the
 * pre-locality view when the locality filter is cleared (undo semantics —
 * the county/type/contract view the user had before is exactly where they
 * expect to land back).
 *
 * Only reacts to localityFilter CHANGES (like FlyToController does for the
 * association slug) — panning/zooming after a selection is never fought.
 */
function LocalityViewportController() {
  const map = useMap();
  const localityFilter = useMapStore((s) => s.localityFilter);
  const selectedWaterSlug = useMapStore((s) => s.selectedWaterSlug);
  const filteredWaters = useFilteredWaters();
  const filteredUncontracted = useFilteredUncontracted();
  // null = not initialized yet (skip the mount render).
  const prevLocality = useRef<string[] | null>(null);
  // View to restore on clear — captured ONCE when locality goes [] → non-[],
  // so clearing a multi-locality selection returns to the pre-locality view.
  const savedView = useRef<{ center: L.LatLng; zoom: number } | null>(null);

  useEffect(() => {
    const prev = prevLocality.current;
    prevLocality.current = localityFilter;
    if (prev === null) return; // initial mount — data gate already open, nothing to fly
    if (prev.length === localityFilter.length && prev.every((l, i) => l === localityFilter[i])) {
      return; // array identity changed, contents didn't
    }
    if (localityFilter.length === 0) {
      // Cleared → restore the view captured before the first locality pick.
      if (savedView.current) {
        map.flyTo(savedView.current.center, savedView.current.zoom, { duration: 0.5 });
      }
      return;
    }
    // t_21d2f68d: the selected water is PINNED into the filtered sets even
    // when it is outside the picked locality — it must NOT pull the fitBounds
    // away from the locality (the pin is a focus convenience, not part of the
    // locality's geography).
    const all = [...filteredWaters, ...filteredUncontracted].filter(
      (w) => w.slug !== selectedWaterSlug,
    );
    const boxes = all
      .map((w) => w.bbox)
      .filter((b): b is [number, number, number, number] => Array.isArray(b) && b.length === 4);
    if (boxes.length === 0) return;
    if (prev.length === 0) {
      savedView.current = { center: map.getCenter(), zoom: map.getZoom() };
    }
    const [minLon, minLat, maxLon, maxLat] = boxes.reduce<[number, number, number, number]>(
      (acc, b) => [
        Math.min(acc[0], b[0]),
        Math.min(acc[1], b[1]),
        Math.max(acc[2], b[2]),
        Math.max(acc[3], b[3]),
      ],
      [180, 90, -180, -90],
    );
    map.fitBounds(
      [
        [minLat, minLon],
        [maxLat, maxLon],
      ],
      { padding: [48, 48], maxZoom: 12, animate: true, duration: 0.6 },
    );
  }, [localityFilter, filteredWaters, filteredUncontracted, selectedWaterSlug, map]);

  return null;
}

/**
 * Test-only bridge (docs/e2e-test-plan.md §5): exposes the Leaflet map
 * instance on `window.__UNDEPESCUIM_MAP__` so the e2e suite can click a
 * water by slug (find the feature layer → fire its click with the real
 * latlng) and read the live zoom without pixel/tile math. No UI effect.
 */
function MapTestBridge() {
  const map = useMap();
  useEffect(() => {
    (window as unknown as Record<string, unknown>).__UNDEPESCUIM_MAP__ = map;
    return () => {
      delete (window as unknown as Record<string, unknown>).__UNDEPESCUIM_MAP__;
    };
  }, [map]);
  return null;
}

/**
 * User-confirmed behavior: auto-center/zoom on association select.
 * Selecting an association → fit its bbox with padding (maxZoom 12 cap —
 * t_d987cdb7: a hardcoded zoom 9 ignored how big/small the association's
 * area actually is; fitBounds shows the waters with padding and never
 * over-zooms).
 * Clearing → fly back to the full-Romania default view.
 *
 * t_697ba939: EXCEPT when the association was cleared by CLICKING a water
 * that does not belong to it (selectWater) — that clear is a side effect of
 * the click, so the map must NOT re-fit / zoom out to the full dataset; it
 * stays put and just shows the clicked water's card. Only an explicit
 * "Toate asociațiile" clear (selectAssociation(null)) flies to the national
 * view. Sibling of t_abccfd6c (covered clicks keep the association entirely).
 *
 * NOTE: this controller ONLY reacts to selectedAssociationSlug changes —
 * focusing/typing in the association search never touches it (t_d987cdb7).
 */
function FlyToController() {
  const map = useMap();
  const dataLoaded = useMapStore((s) => s.dataLoaded);
  const associations = useMapStore((s) => s.associations);
  const slug = useMapStore((s) => s.selectedAssociationSlug);
  const consumeSuppression = useMapStore((s) => s.consumeAssociationFlyToSuppression);
  const firstRun = useRef(true);

  useEffect(() => {
    if (!dataLoaded) return;
    if (firstRun.current) {
      // Initial view is already the Romania default — skip the first flyTo.
      firstRun.current = false;
      return;
    }
    if (!slug) {
      // t_697ba939: the association was cleared by a water click → consume
      // the one-shot suppression and keep the current view. Read the flag
      // via getState() (NOT a subscription) so the consume does not trigger
      // a re-render/re-run of this effect.
      if (useMapStore.getState().suppressAssociationFlyTo) {
        consumeSuppression();
        return;
      }
      map.flyTo([45.95, 24.95], 7, { duration: 0.8 });
      return;
    }
    const assoc = associations.find((a) => a.slug === slug);
    // bbox can be null (associations without a geocoded bbox — e.g.
    // AJVPS Covasna, Direcția Silvică Brașov): destructuring null crashes
    // the whole app, so stay on the current view instead (t_b6a0e2fe).
    if (!assoc || !assoc.bbox) return;
    const [minLon, minLat, maxLon, maxLat] = assoc.bbox;
    // t_d987cdb7: fit the association's area with padding instead of a
    // hardcoded zoom — a large association (whole county) still gets the
    // overview, a small one gets a close-but-sane view, and the maxZoom cap
    // guarantees the map never lands over-zoomed (the iPhone complaint).
    map.fitBounds(
      [
        [minLat, minLon],
        [maxLat, maxLon],
      ],
      { padding: [48, 48], maxZoom: 12, animate: true, duration: 0.8 },
    );
  }, [slug, associations, dataLoaded, map, consumeSuppression]);

  return null;
}
