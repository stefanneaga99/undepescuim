'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import L from 'leaflet';
import { CircleMarker, GeoJSON as LeafletGeoJSON, useMap, useMapEvents } from 'react-leaflet';
import { useMapStore } from '@/stores/map-store';
import { watersToFeatureCollection } from '@/utils/geo';
import { getFeatureStyle, getPointFallbackStyle, COVERED_COLOR } from '@/utils/colors';

import { bboxInBounds, lodThresholds, passesLod, renderBbox, viewSuffix } from '@/utils/lod';
import {
  contractAtFraction,
  contractGroup,
  contractInterval,
  fractionAtPoint,
  groupKeyOf,
  sliceMultiLine,
  waterKey,
} from '@/utils/river-course';
import type { Water, WaterFeature, WaterFeatureProperties } from '@/types/data';
import type { MapSelectionFocus } from '@/utils/contract-sector';

interface WaterFeatureLayerProps {
  waters: Water[];
  /** all waters (unfiltered, UN-culled) — focus/association slices MUST resolve
   * against this full pool so selecting an association off-screen keeps its
   * highlight even when viewport culling drops the feature from the base layer
   * (plan §4.4 / §7.3 risk 3). */
  allWaters: Water[];
  /** selected association slug — colors features green/grey (or all blue when null) */
  coverageSlug: string | null;
  /** contract selected from the detail card — highlight the river in its association color */
  focusKey?: string | null;
  focusColor?: string | null;
  /** Semantic focus intent; inferred sectors are marker-only. */
  focus: MapSelectionFocus;
}

/**
 *
 * Hitbox strategy: rivers/lakes are drawn TWICE —
 * 1. an invisible 16px-wide "hit" polyline/polygon underneath (weight 16,
 *    opacity 0) that catches clicks/taps on thin rivers,
 * 2. the visible thin line (weight 2-3) on top.
 * This makes clicking a river reliable on both desktop and mobile.
 *
 * Performance (P1 §4.4): the contracted layer mirrors the uncontracted overlay
 * pattern:
 *  1. VIEWPORT CULLING — only features whose bbox intersects the current map
 *     viewport are added as Leaflet layers; re-evaluated on every moveend.
 *  2. ZOOM LOD — at low zoom only big waters render (shared {@link lodThresholds}).
 *  3. The invisible 16px hit layer is dropped at zoom < 10 (rivers are too
 *     dense to tap individually at national view — plan §4.4 item 3).
 * CRITICAL: the focus + association slices are computed from `allWaters`
 * (unculled) so a selected association OFF-SCREEN still keeps its highlight.
 */
export function WaterFeatureLayer({
  waters,
  allWaters,
  coverageSlug,
  focusKey,
  focusColor,
  focus,
}: WaterFeatureLayerProps) {
  const selectWater = useMapStore((s) => s.selectWater);
  const countyFilter = useMapStore((s) => s.countyFilter);
  const selectedWaterSlug = useMapStore((s) => s.selectedWaterSlug);
  // t_9529e678 (mirrored from the uncontracted layer): an active locality
  // filter is an explicit "show me THIS place" — the matched set is small, so
  // the zoom LOD must NOT cull its small contracted waters/ponds either.
  const localityActive = useMapStore((s) => s.localityFilter.length > 0);

  const map = useMap();
  // Keep focus rendering in a stable pane instead of relying on React/Leaflet
  // sibling insertion order.  The report dialog and mobile sheets are portaled
  // above the map; z-index 450 wins over ordinary/association paths while
  // remaining below those UI layers.
  const focusPane = useMemo(() => {
    const pane = map.getPane('water-focus') ?? map.createPane('water-focus');
    pane.classList.add('water-focus-pane');
    pane.style.zIndex = '450';
    return 'water-focus';
  }, [map]);
  const associationPane = useMemo(() => {
    const pane = map.getPane('water-association') ?? map.createPane('water-association');
    pane.classList.add('water-association-pane');
    pane.style.zIndex = '440';
    return 'water-association';
  }, [map]);
  const unverifiedPane = useMemo(() => {
    const pane = map.getPane('water-unverified-focus') ?? map.createPane('water-unverified-focus');
    pane.classList.add('water-unverified-focus-pane');
    pane.style.zIndex = '455';
    return 'water-unverified-focus';
  }, [map]);
  const focusPaneElement = map.getPane(focusPane);
  if (focusPaneElement) focusPaneElement.dataset.focusSlug = selectedWaterSlug ?? '';
  const [view, setView] = useState<{ zoom: number; bounds: L.LatLngBounds }>(() => ({
    zoom: map.getZoom(),
    bounds: map.getBounds(),
  }));

  useMapEvents({
    moveend: () => setView({ zoom: map.getZoom(), bounds: map.getBounds() }),
  });

  // Viewport culling: only contracted waters whose bbox intersects the padded
  // viewport AND pass the shared zoom-LOD gate become Leaflet features.
  // A selected association's members + the selected water are PINNED through
  // the cull so their highlight/the orange focus never vanish on pan/zoom
  // (plan §4.4 — focus/assoc must survive culling).
  const lod = lodThresholds(view.zoom, localityActive);
  const visibleWaters = useMemo(() => {
    const pinned = new Set<string>();
    if (selectedWaterSlug) pinned.add(selectedWaterSlug);
    if (coverageSlug) {
      for (const w of allWaters) {
        if (w.asociatie?.slug === coverageSlug) pinned.add(w.slug);
      }
    }
    return waters.filter(
      (w) => pinned.has(w.slug) || (passesLod(w, lod) && bboxInBounds(renderBbox(w), view.bounds)),
    );
  }, [waters, allWaters, view, lod, coverageSlug, selectedWaterSlug]);

  const featureCollection = useMemo(() => watersToFeatureCollection(visibleWaters), [visibleWaters]);

  const layerKey = `${viewSuffix(view.zoom, view.bounds)}|${coverageSlug ?? 'neutral'}|${visibleWaters.map((w) => w.slug).join(',')}`;

  // Exact river-group key of the focused contract (t_ac697770) — matches
  // focus slices across name variants ('Râul Oltul superior' / 'Râul Olt').
  // t_b1547e24: focus applies to EVERY water (contracted + uncontracted), so
  // no asociatie gate here — only focusKey gates the focus path.
  const focusGroupKey = useMemo(() => {
    if (!focusKey) return null;
    const w = allWaters.find((x) => x.name === focusKey);
    return w ? groupKeyOf(w) : waterKey(focusKey);
  }, [allWaters, focusKey]);

  // Click on a river: resolve the fraction along the course, then select the
  // contract (association) that owns that sector — not just the first one.
  // NOTE: the rendered geometry may be the per-county clip (t_117f0b99), whose
  // fractions are NOT full-course fractions — always resolve against the
  // ORIGINAL full-course geometry (allWaters) so sectorStart/sectorEnd
  // intervals stay correct.
  const handleClick = useCallback(
    (feature: WaterFeature, latlng?: L.LatLng) => {
      if (latlng) {
        const original = allWaters.find((w) => w.slug === feature.properties.slug);
        const g = original?.geometry ?? feature.geometry;
        if (g && (g.type === 'MultiLineString' || g.type === 'LineString')) {
          const parts =
            g.type === 'MultiLineString'
              ? (g.coordinates as [number, number][][])
              : [g.coordinates as [number, number][]];
          const frac = fractionAtPoint(parts, [latlng.lng, latlng.lat]);
          if (frac !== null) {
            const contract = contractAtFraction(
              { slug: feature.properties.slug, name: feature.properties.name },
              frac,
              allWaters,
            );
            if (contract) {
              selectWater(contract.slug);
              return;
            }
          }
        }
      }
      selectWater(feature.properties.slug);
    },
    [selectWater, allWaters],
  );

  const handleEachFeature = useCallback(
    (feature: GeoJSON.Feature, layer: L.Path) => {
      const f = feature as WaterFeature;
      // All styling (incl. the association coverage weights) lives in the
      // `style` prop — react-leaflet v5 re-applies it on every re-render,
      // while per-feature setStyle here would be wiped (t_b6a0e2fe).
      layer.on('click', (e: L.LeafletMouseEvent) => handleClick(f, e.latlng));
      layer.bindTooltip(f.properties.name, { sticky: true, direction: 'top' });
    },
    [handleClick],
  );

  // Focus slice: when a contract owns a km-range of a multi-contract river,
  // render ONLY that sector as a thick colored line (the shared course is
  // sliced by fraction). Single-contract rivers use the full-course style above.
  //
  // P1 §4.4 (plan §7.3 risk 3): the slice is computed from `allWaters`
  // (UNCULLED), NOT the viewport-culled `featureCollection` — a focused
  // contract whose shared course is off-screen must keep its orange highlight.
  const focusFeatures = useMemo(() => {
    if (!focusGroupKey || (focus.kind !== 'verified-sector-focus' && focus.kind !== 'whole-feature-focus')) return null;
    const [f0, f1] = focus.kind === 'verified-sector-focus' ? focus.interval : [0, 1];
    const features: GeoJSON.Feature[] = [];
    for (const x of allWaters) {
      if (groupKeyOf(x) !== focusGroupKey) continue;
      const g = x.geometry;
      if (!g) continue;
      if (g.type === 'MultiLineString') {
        const sliced = sliceMultiLine(g.coordinates as [number, number][][], f0, f1);
        if (sliced.length) {
          features.push({
            type: 'Feature',
            properties: { slug: x.slug, name: x.name },
            geometry: { type: 'MultiLineString', coordinates: sliced },
          });
        }
      } else if (g.type === 'LineString') {
        const sliced = sliceMultiLine([g.coordinates as [number, number][]], f0, f1);
        if (sliced.length) {
          features.push({
            type: 'Feature',
            properties: { slug: x.slug, name: x.name },
            geometry: { type: 'MultiLineString', coordinates: sliced },
          });
        }
      }
    }
    return features.length ? features : null;
  }, [focusGroupKey, focus, allWaters]);

  // react-leaflet v5 does not reliably replace a GeoJSON layer when only its
  // data prop changes.  The base layer already has a lifecycle key; the focus
  // slice needs the same treatment or a fast A → B selection can leave A's
  // SVG geometry mounted in the focus pane.
  const focusLayerKey = [
    selectedWaterSlug ?? 'none',
    focusKey ?? 'none',
    focus.kind === 'verified-sector-focus' ? focus.interval.join(':') : focus.kind,
    countyFilter.join(','),
    focusFeatures?.map((f) => JSON.stringify(f.geometry)).join('|') ?? 'empty',
  ].join('|');

  // Association highlight slices (t_b6a0e2fe + t_5f5f2cce): every member of
  // the selected association that belongs to a MULTI-CONTRACT group is drawn
  // as its contract interval SLICE of the group's shared course, in the
  // covered color. Two cases:
  //  - geometry-less sector members (Pârâu Buzăul Mijlociu / AJVPS Covasna,
  //    Râul Buzăul superior / D.S. Brașov) are INVISIBLE in the base layer —
  //    they carry no own geometry and no bbox, only a riverGroup + fraction;
  //  - geometry-bearing members of a multi-contract group (the 'jiu' group's
  //    owner holding the FULL shared course, e.g. Râul Jiu / AJVPS GORJ) are
  //    deliberately NOT base-covered by focusAwareStyle — painting the whole
  //    geometry green would highlight every other county's/association's
  //    sector (the whole-Jiu-highlight bug). The slice paints ONLY the
  //    member's own sector.
  // P1 §4.4 (plan §7.3 risk 3): computed from `allWaters` (UNCULLED) so an
  // association selected with its waters off-screen still draws its highlight.
  // Skipped under a county filter: the rendered geometry is a per-county
  // clip, which full-course fractions must not slice.
  const assocHighlightFeatures = useMemo(() => {
    if (!coverageSlug) return null;
    if (countyFilter.length > 0) return null;
    const out: GeoJSON.Feature[] = [];
    for (const w of allWaters) {
      if ((w.asociatie?.slug ?? null) !== coverageSlug) continue;
      const gk = groupKeyOf(w);
      if (!gk) continue;
      const group = contractGroup(w, allWaters);
      if (group.length <= 1) continue; // single-contract → base layer colors it
      // owner = the group member carrying the shared course (prefer another
      // member; a geometry-bearing member slices its OWN course)
      const owner =
        allWaters.find(
          (x) =>
            x.slug !== w.slug &&
            groupKeyOf(x) === gk &&
            !!x.geometry &&
            (x.geometry.type === 'LineString' || x.geometry.type === 'MultiLineString'),
        ) ||
        (w.geometry &&
        (w.geometry.type === 'LineString' || w.geometry.type === 'MultiLineString')
          ? w
          : null);
      if (!owner) continue;
      const [f0, f1] = contractInterval(w, allWaters);
      const g = owner.geometry as GeoJSON.LineString | GeoJSON.MultiLineString;
      const parts =
        g.type === 'MultiLineString'
          ? (g.coordinates as [number, number][][])
          : [g.coordinates as [number, number][]];
      const sliced = sliceMultiLine(parts, f0, f1);
      if (!sliced.length) continue;
      out.push({
        type: 'Feature',
        properties: { slug: w.slug, name: w.name, asociatieSlug: coverageSlug },
        geometry: { type: 'MultiLineString', coordinates: sliced },
      });
    }
    return out.length ? out : null;
  }, [coverageSlug, allWaters, countyFilter]);

  // Focus-aware style (t_b1547e24): the orange highlight for ALL waters.
  // react-leaflet v5 re-applies the `style` prop on every re-render
  // (updateGeoJSON → layer.setStyle) but onEachFeature only runs at mount —
  // so whole-feature focus styling MUST live in this style function or the
  // next re-render wipes it and the highlight never shows (the original bug).
  // Matching is slug-exact: only the selected water's own feature turns
  // orange. When the focus-slice layer already draws the orange (contracted
  // river sector / county clip), keep the base style to avoid double-painting.
  // t_5f5f2cce: a member of a multi-contract group (e.g. the 'jiu' group's
  // geometry owner holding the FULL shared course) must NOT be base-covered
  // by its asociatie — the whole shared course would turn green including
  // other counties'/associations' sectors. Its sector is painted by the
  // covered-slices layer instead; the base keeps the whole course neutral.
  const focusAwareStyle = useCallback(
    (feature?: GeoJSON.Feature<GeoJSON.Geometry, GeoJSON.GeoJsonProperties>): L.PathOptions => {
      const props = feature?.properties as WaterFeatureProperties | undefined;
      const water = props?.slug ? allWaters.find((x) => x.slug === props.slug) : undefined;
      const lineGeom =
        !!water?.geometry &&
        (water.geometry.type === 'LineString' || water.geometry.type === 'MultiLineString');
      const multiContractMember =
        coverageSlug !== null &&
        countyFilter.length === 0 &&
        lineGeom &&
        !!water &&
        contractGroup(water, allWaters).length > 1;
      // t_cdb614de: bbox-fallback waters (no real OSM geometry) render as
      // discreet point dots — distinct style (violet dot, coverage-aware).
      const base =
        props?._bboxFallback === true
          ? getPointFallbackStyle(props.asociatieSlug ?? null, coverageSlug)
          : getFeatureStyle(
              multiContractMember ? null : (props?.asociatieSlug ?? null),
              coverageSlug,
              // t_14463aec: county-filtered waters (neutral view, no
              // association) get a heavier blue so the county visibly "pops".
              countyFilter.length > 0,
            );
      if (!focusColor || !selectedWaterSlug) return base;
      const f = feature as WaterFeature | undefined;
      if (f?.properties?.slug !== selectedWaterSlug) return base;
      if (focus.kind === 'feature-selected-unverified-sector') return base;
      if (focus.kind === 'verified-sector-focus' && focusFeatures && focusFeatures.length > 0) return base;
      return {
        ...base,
        color: focusColor,
        weight: Math.max(base.weight ?? 2, 3),
        opacity: 1,
      };
    },
    [coverageSlug, countyFilter, focusColor, selectedWaterSlug, focus, focusFeatures, allWaters],
  );

  const unverifiedFocus = focus.kind === 'feature-selected-unverified-sector' ? focus : null;
  const unverifiedMarkerRef = useRef<L.CircleMarker | null>(null);
  useEffect(() => {
    const path = unverifiedMarkerRef.current?.getElement() as SVGElement | undefined;
    if (!path || !unverifiedFocus || !selectedWaterSlug) return;
    path.setAttribute('role', 'button');
    path.setAttribute('tabindex', '0');
    path.setAttribute('aria-label', unverifiedFocus.accessibleLabel);
    path.setAttribute('data-focus-kind', unverifiedFocus.kind);
    path.setAttribute('data-focus-slug', selectedWaterSlug);
    path.onkeydown = (event: KeyboardEvent) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        selectWater(selectedWaterSlug);
      }
    };
  }, [unverifiedFocus, selectedWaterSlug, selectWater]);

  // Invisible wide hit layers for lines (added after the visible layer).
  // react-leaflet's GeoJSON doesn't expose each layer for extra additions, so
  // we add the hit layer inside onEachFeature via layer.bringToBack after
  // cloning is too late — instead we render a SECOND GeoJSON purely for hits.
  // t_cdb614de: bbox-fallback POINTS get a fat invisible circle hit too, so a
  // small dot is still tappable on mobile.
  // P1 §4.4 item 3: the hit layer is DROPPED at zoom < 10 (rivers are too
  // dense to tap individually at national view; hiding it halves the SVG
  // node count — M14). The visible layer still carries its own click handler.
  const hitCollection = useMemo(() => {
    if (view.zoom < 10) return null;
    const fc = featureCollection;
    return {
      ...fc,
      features: fc.features.filter(
        (f) =>
          f.geometry.type === 'LineString' ||
          f.geometry.type === 'MultiLineString' ||
          ((f.properties as WaterFeatureProperties)._bboxFallback === true &&
            f.geometry.type === 'Point'),
      ),
    };
  }, [featureCollection, view.zoom]);

  return (
    <>
      {/* e2e ready-signal (docs/e2e-test-plan.md §5.1): attached only when this
          layer mounts with features — i.e. the vector overlay has been fed. */}
      {featureCollection.features.length > 0 && (
        <div data-testid="waters-drawn" hidden aria-hidden />
      )}
      {/* key forces remount on filter change — react-leaflet v5 ignores data
          prop changes without a key change (stale hit targets otherwise). */}
      {hitCollection && (
        <GeoJSONHits key={`hits-${layerKey}`} data={hitCollection} onFeatureClick={handleClick} />
      )}
      <LeafletGeoJSON
        key={layerKey}
        data={featureCollection}
        style={focusAwareStyle}
        pointToLayer={(feature, latlng) =>
          // bbox-fallback dots: small filled circle, styled by focusAwareStyle
          L.circleMarker(latlng, {
            radius: (feature.properties as WaterFeatureProperties)._bboxFallback ? 5 : 4,
          })
        }
        onEachFeature={handleEachFeature}
      />
      {/* Focus slice on top: only the selected contract's sector, thick + colored */}
      {focusFeatures && focusColor && (
        <LeafletGeoJSON
          key={`focus-${focusLayerKey}`}
          pane={focusPane}
          data={
            {
              type: 'FeatureCollection',
              features: focusFeatures,
            } as GeoJSON.FeatureCollection
          }
          style={() => ({
            color: focusColor,
            weight: 7,
            opacity: 1,
            fillOpacity: 0,
          })}
          onEachFeature={(feature, layer: L.Path) => {
            const f = feature as WaterFeature;
            layer.on('click', (e: L.LeafletMouseEvent) => handleClick(f, e.latlng));
            layer.bindTooltip(f.properties.name, { sticky: true, direction: 'top' });
          }}
        />
      )}
      {focus.kind === 'feature-selected-unverified-sector' && focus.referencePoint && selectedWaterSlug && (
        <CircleMarker
          pane={unverifiedPane}
          center={[focus.referencePoint[1], focus.referencePoint[0]]}
          radius={10}
          pathOptions={{ color: '#8b5cf6', weight: 4, opacity: 1, fillOpacity: 0 }}
          eventHandlers={{ click: () => selectWater(selectedWaterSlug) }}
          ref={unverifiedMarkerRef}
        />
      )}
      {focus.kind === 'feature-selected-unverified-sector' && (
        <div data-testid="water-focus-status" role="status" aria-live="polite" className="sr-only">
          {focus.accessibleLabel}
        </div>
      )}
      {/* Association highlight: the selected association's geometry-less sector
          slices (Pârâu Buzăul Mijlociu, Râul Buzăul superior, …) in bold
          covered green — rendered UNDER the click-focus slice so a focused
          sector's orange still wins (t_b6a0e2fe). Click selects the sector's
          water directly (the slice is a sub-course, fraction resolution would
          mis-map it). */}
      {assocHighlightFeatures && (
        <LeafletGeoJSON
          pane={associationPane}
          data={
            {
              type: 'FeatureCollection',
              features: assocHighlightFeatures,
            } as GeoJSON.FeatureCollection
          }
          style={() => ({
            color: COVERED_COLOR,
            weight: 5,
            opacity: 1,
            fillOpacity: 0,
          })}
          onEachFeature={(feature, layer: L.Path) => {
            const f = feature as WaterFeature;
            layer.on('click', () => selectWater(f.properties.slug));
            layer.bindTooltip(f.properties.name, { sticky: true, direction: 'top' });
          }}
        />
      )}
    </>
  );
}

/** Renders invisible wide polylines solely to enlarge the click target. */
function GeoJSONHits({
  data,
  onFeatureClick,
}: {
  data: GeoJSON.FeatureCollection;
  onFeatureClick: (f: WaterFeature, latlng?: L.LatLng) => void;
}) {
  return (
    <LeafletGeoJSON
      data={data}
      style={() => ({ color: '#000', weight: 16, opacity: 0, fillOpacity: 0 })}
      pointToLayer={(_feature, latlng) =>
        // t_cdb614de: bbox-fallback dots need a fat invisible hit circle so a
        // 5px dot is still tappable on mobile.
        L.circleMarker(latlng, { radius: 14 })
      }
      onEachFeature={(feature, layer: L.Path) => {
        const f = feature as WaterFeature;
        layer.on('click', (e: L.LeafletMouseEvent) => onFeatureClick(f, e.latlng));
      }}
    />
  );
}
