'use client';

import { useMemo, useState } from 'react';
import L from 'leaflet';
import { GeoJSON as LeafletGeoJSON, useMap, useMapEvents } from 'react-leaflet';
import { useMapStore } from '@/stores/map-store';
import { waterToGeoJSON } from '@/utils/geo';
import { bboxInBounds, viewSuffix } from '@/utils/lod';
import { dedupePhysicalPreview, isUnverifiedPhysicalPreview } from '@/utils/physical-preview';
import type { Water, WaterFeature } from '@/types/data';

/** Preview-only physical lines. This layer never participates in legal contract resolution. */
export function PhysicalPreviewLayer({ waters }: { waters: Water[] }) {
  const map = useMap();
  const selectWater = useMapStore((s) => s.selectWater);
  const selected = useMapStore((s) => s.selectedWaterSlug);
  const [view, setView] = useState({ zoom: map.getZoom(), bounds: map.getBounds() });
  useMapEvents({ moveend: () => setView({ zoom: map.getZoom(), bounds: map.getBounds() }) });
  const visible = useMemo(
    () => dedupePhysicalPreview(waters.filter(isUnverifiedPhysicalPreview)).filter((w) => bboxInBounds(w.bbox, view.bounds)),
    [waters, view],
  );
  const data = useMemo(() => ({ type: 'FeatureCollection', features: visible.map(waterToGeoJSON) }) as GeoJSON.FeatureCollection, [visible]);
  const key = `${viewSuffix(view.zoom, view.bounds)}|${visible.map((w) => w.slug).join(',')}`;
  return <LeafletGeoJSON key={key} data={data} style={(feature) => {
    const f = feature as WaterFeature | undefined;
    const focused = f?.properties.slug === selected;
    return { color: focused ? '#f97316' : '#7c3aed', weight: focused ? 5 : 3, opacity: 0.9, dashArray: focused ? undefined : '7 5' };
  }} onEachFeature={(feature, layer: L.Path) => {
    const f = feature as WaterFeature;
    layer.on('click', () => selectWater(f.properties.slug));
    layer.bindTooltip(`${f.properties.name} · traseu fizic Preview`, { sticky: true });
  }} />;
}
