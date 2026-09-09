'use client';

import { useMemo, useState } from 'react';
import L from 'leaflet';
import { GeoJSON as LeafletGeoJSON, useMap, useMapEvents } from 'react-leaflet';
import { waterToGeoJSON } from '@/utils/geo';
import { bboxInBounds, renderBbox, viewSuffix } from '@/utils/lod';
import { dedupePhysicalPreview, isUnverifiedPhysicalPreview } from '@/utils/physical-preview';
import { getPhysicalPreviewStyle } from '@/utils/colors';
import { useMapStore } from '@/stores/map-store';
import type { Water, WaterFeature } from '@/types/data';
import { fractionAtPoint } from '@/utils/river-course';

/** Preview-only physical lines. This layer never participates in legal contract resolution. */
export function PhysicalPreviewLayer({ waters: previewWaters }: { waters: Water[] }) {
  const map = useMap();
  const pane = useMemo(() => {
    const existing = map.getPane('physical-preview');
    const physicalPane = existing ?? map.createPane('physical-preview');
    physicalPane.classList.add('physical-preview-pane');
    physicalPane.style.zIndex = '410';
    return 'physical-preview';
  }, [map]);
  const [view, setView] = useState({ zoom: map.getZoom(), bounds: map.getBounds() });
  useMapEvents({ moveend: () => setView({ zoom: map.getZoom(), bounds: map.getBounds() }) });
  const visible = useMemo(
    () => dedupePhysicalPreview(previewWaters.filter(isUnverifiedPhysicalPreview)).filter((w) => bboxInBounds(renderBbox(w), view.bounds)),
    [previewWaters, view],
  );
  const data = useMemo(() => ({ type: 'FeatureCollection', features: visible.map(waterToGeoJSON) }) as GeoJSON.FeatureCollection, [visible]);
  const key = `${viewSuffix(view.zoom, view.bounds)}|${visible.map((w) => w.slug).join(',')}`;
  const selectWater = useMapStore((s) => s.selectWater);
  const waters = useMapStore((s) => s.waters);
  return <LeafletGeoJSON pane={pane} key={key} data={data} style={() => getPhysicalPreviewStyle()} onEachFeature={(feature, layer: L.Path) => {
    const f = feature as WaterFeature;
    const preview = visible.find((w) => w.slug === f.properties.slug);
    const aliases = f.properties.physicalAliases ?? preview?.physicalAliases ?? [];
    const sourceSlug = preview?.physicalSourceSlug ?? aliases[0] ?? f.properties.slug;
    layer.on('click', (event: L.LeafletMouseEvent) => {
      const hasRealEvent = Boolean(event.originalEvent);
      if (hasRealEvent) L.DomEvent.stopPropagation(event.originalEvent);
      const geometry = preview?.geometry ?? f.geometry;
      const parts = geometry?.type === 'LineString'
        ? [geometry.coordinates as [number, number][]]
        : geometry?.type === 'MultiLineString'
          ? geometry.coordinates as [number, number][][]
          : null;
      const measuredFraction = parts ? fractionAtPoint(parts, [event.latlng.lng, event.latlng.lat]) : null;
      const candidates = waters.filter((water) =>
        water.riverGroup === (preview?.riverGroup ?? f.properties.riverGroup ?? undefined) && aliases.includes(water.slug),
      );
      const selected = measuredFraction === null || candidates.length === 0
        ? null
        : (() => {
            const explicit = candidates
              .filter((water) => typeof water.sectorStart === 'number' && typeof water.sectorEnd === 'number')
              .filter((water) => measuredFraction >= water.sectorStart! && measuredFraction < water.sectorEnd!)
              .sort((a, b) => (a.sectorEnd! - a.sectorStart!) - (b.sectorEnd! - b.sectorStart!))[0];
            if (explicit) return explicit;
            return [...candidates].sort((a, b) =>
              Math.abs((a.course_frac ?? 0.5) - measuredFraction) - Math.abs((b.course_frac ?? 0.5) - measuredFraction),
            )[0] ?? null;
          })();
      const segment = selected && (preview?.physicalSegments ?? f.properties.physicalSegments)?.find((candidate) =>
        candidate.sourceSlug === selected.slug &&
        measuredFraction !== null && measuredFraction >= candidate.start && measuredFraction < candidate.end,
      );
      selectWater(hasRealEvent ? (selected?.slug ?? aliases[0] ?? sourceSlug) : sourceSlug, segment?.segmentId ?? (hasRealEvent && selected ? undefined : preview?.physicalSegmentId ?? f.properties.physicalSegmentId));
    });
    layer.bindTooltip(`${f.properties.name} · traseu fizic (previzualizare; sector legal neverificat)`, { sticky: true });
  }} />;
}
