'use client';

import { useMemo, useState } from 'react';
import L from 'leaflet';
import { GeoJSON as LeafletGeoJSON, useMap, useMapEvents } from 'react-leaflet';
import { waterToGeoJSON } from '@/utils/geo';
import { bboxInBounds, viewSuffix } from '@/utils/lod';
import { dedupePhysicalPreview, isUnverifiedPhysicalPreview, physicalPreviewSelection } from '@/utils/physical-preview';
import { getPhysicalPreviewStyle } from '@/utils/colors';
import { useMapStore } from '@/stores/map-store';
import type { Water, WaterFeature } from '@/types/data';

/** Preview-only physical lines. This layer never participates in legal contract resolution. */
export function PhysicalPreviewLayer({ waters }: { waters: Water[] }) {
  const map = useMap();
  const [view, setView] = useState({ zoom: map.getZoom(), bounds: map.getBounds() });
  useMapEvents({ moveend: () => setView({ zoom: map.getZoom(), bounds: map.getBounds() }) });
  const visible = useMemo(
    () => dedupePhysicalPreview(waters.filter(isUnverifiedPhysicalPreview)).filter((w) => bboxInBounds(w.bbox, view.bounds)),
    [waters, view],
  );
  const data = useMemo(() => ({ type: 'FeatureCollection', features: visible.map(waterToGeoJSON) }) as GeoJSON.FeatureCollection, [visible]);
  const key = `${viewSuffix(view.zoom, view.bounds)}|${visible.map((w) => w.slug).join(',')}`;
  const selectWater = useMapStore((s) => s.selectWater);
  const selected = useMapStore((s) => s.selectedWaterSlug);
  return <LeafletGeoJSON key={key} data={data} style={(feature) => {
    const water = visible.find((w) => w.slug === (feature as WaterFeature).properties.slug);
    return water && physicalPreviewSelection(water, selected)
      ? { color: '#f97316', weight: 5, opacity: 1, dashArray: [] }
      : getPhysicalPreviewStyle();
  }} onEachFeature={(feature, layer: L.Path) => {
    const f = feature as WaterFeature;
    const sourceSlug = visible.find((w) => w.slug === f.properties.slug)?.physicalSourceSlug ?? f.properties.slug;
    layer.on('click', () => selectWater(sourceSlug));
    layer.bindTooltip(`${f.properties.name} · traseu fizic (previzualizare; sector legal neverificat)`, { sticky: true });
  }} />;
}
