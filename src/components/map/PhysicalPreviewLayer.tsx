'use client';

import { useMemo, useState } from 'react';
import L from 'leaflet';
import { useMap, useMapEvents } from 'react-leaflet';
import { ManagedGeoJSONLayer } from './use-managed-geojson';
import { useMapStore } from '@/stores/map-store';
import { waterToGeoJSON } from '@/utils/geo';
import { bboxInBounds } from '@/utils/lod';
import type { Water, WaterFeature } from '@/types/data';

/** Preview-only physical lines. This layer never participates in legal contract resolution. */
export function PhysicalPreviewLayer({ waters }: { waters: Water[] }) {
  const map = useMap();
  const selectWater = useMapStore((s) => s.selectWater);
  const selected = useMapStore((s) => s.selectedWaterSlug);
  const [view, setView] = useState({ zoom: map.getZoom(), bounds: map.getBounds() });
  useMapEvents({ moveend: () => setView({ zoom: map.getZoom(), bounds: map.getBounds() }) });
  const visible = useMemo(() => waters.filter((w) => bboxInBounds(w.bbox, view.bounds)), [waters, view]);
  const data = useMemo(() => ({ type: 'FeatureCollection', features: visible.map(waterToGeoJSON) }) as GeoJSON.FeatureCollection, [visible]);
  return <ManagedGeoJSONLayer data={data} style={(feature) => {
    const f = feature as WaterFeature | undefined;
    const focused = f?.properties.slug === selected;
    return { color: focused ? '#f97316' : '#7c3aed', weight: focused ? 5 : 3, opacity: 0.9, dashArray: focused ? undefined : '7 5' };
  }} onEachFeature={(feature, layer: L.Path) => {
    const f = feature as WaterFeature;
    layer.on('click', () => selectWater(f.properties.slug));
    layer.bindTooltip(`${f.properties.name} · traseu fizic Preview`, { sticky: true });
  }} />;
}
