'use client';

import { useEffect, useMemo, useState } from 'react';
import { GeoJSON as LeafletGeoJSON, MapContainer, TileLayer, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import {
  CLASS2_LEGAL_STATUS,
  previewBounds,
  previewFeatures,
  type Class2PhysicalCandidate,
  type Class2PreviewArtifact,
  type Class2PreviewRecord,
} from '@/utils/class2-preview';

function FitPreview({ bounds }: { bounds: [number, number, number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.fitBounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]], { padding: [24, 24], maxZoom: 8 });
  }, [bounds, map]);
  return null;
}

function DetailCard({ record, candidate, onClose }: { record: Class2PreviewRecord; candidate: Class2PhysicalCandidate; onClose: () => void }) {
  return (
    <aside data-testid="class2-physical-card" className="absolute bottom-3 left-3 right-3 z-[1100] max-h-[48vh] overflow-auto rounded-xl border border-slate-200 bg-white/95 p-4 shadow-xl backdrop-blur md:bottom-4 md:left-auto md:right-4 md:w-[390px]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">Experimental physical geometry</p>
          <h2 className="text-lg font-bold text-slate-900">{record.name}</h2>
        </div>
        <button type="button" onClick={onClose} className="rounded px-2 py-1 text-xl text-slate-500 hover:bg-slate-100" aria-label="Close physical geometry card">×</button>
      </div>
      <p className="mt-2 rounded bg-amber-50 px-2 py-1 text-sm font-semibold text-amber-900">{CLASS2_LEGAL_STATUS}</p>
      <dl className="mt-3 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm text-slate-700">
        <dt className="font-semibold">Slug</dt><dd className="break-all">{record.slug}</dd>
        <dt className="font-semibold">County</dt><dd>{record.county}</dd>
        <dt className="font-semibold">Association</dt><dd>{record.association ?? 'Unavailable'}</dd>
        <dt className="font-semibold">Physical source URL</dt><dd className="break-all">{candidate.physicalSourceUrl ?? 'Unavailable in pinned evidence'}</dd>
        <dt className="font-semibold">OSM ID</dt><dd>{candidate.osmId ?? 'Unavailable'}</dd>
        <dt className="font-semibold">Geofabrik ID</dt><dd>{candidate.geofabrikId ?? 'Unavailable'}</dd>
        <dt className="font-semibold">Geometry hash</dt><dd className="break-all font-mono text-xs">{candidate.geometryHash}</dd>
        <dt className="font-semibold">Confidence</dt><dd>{candidate.confidence}</dd>
      </dl>
      <p className="mt-3 text-xs leading-5 text-slate-600">{record.disclosure} Canonical contract geometry, selectedWaterSlug, ownership, endpoints, and dimensions are not changed by this layer.</p>
    </aside>
  );
}

export function Class2PreviewMap({ artifactUrl = '/data/preview_class2_physical.json' }: { artifactUrl?: string }) {
  const [artifact, setArtifact] = useState<Class2PreviewArtifact | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selection, setSelection] = useState<{ record: Class2PreviewRecord; candidate: Class2PhysicalCandidate } | null>(null);
  useEffect(() => {
    fetch(artifactUrl)
      .then((response) => { if (!response.ok) throw new Error(`Preview artifact failed: ${response.status}`); return response.json() as Promise<Class2PreviewArtifact>; })
      .then((value) => setArtifact(value))
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : 'Preview artifact unavailable'));
  }, [artifactUrl]);

  const features = useMemo(() => artifact ? previewFeatures(artifact) : [], [artifact]);
  const recordsByKey = useMemo(() => {
    const map = new Map<string, { record: Class2PreviewRecord; candidate: Class2PhysicalCandidate }>();
    artifact?.records.forEach((record) => record.physicalCandidates.forEach((candidate) => map.set(`${record.slug}:${candidate.id}`, { record, candidate })));
    return map;
  }, [artifact]);
  if (error) return <div className="p-6 text-red-700">{error}</div>;
  if (!artifact) return <div className="p-6 text-slate-600">Se încarcă Preview-ul fizic…</div>;
  const bounds = previewBounds(artifact);
  return (
    <div className="relative h-[calc(100dvh-64px)] min-h-[520px] overflow-hidden bg-slate-100">
      <div className="absolute left-3 top-3 z-[1100] rounded-xl bg-white/95 px-4 py-3 shadow-lg backdrop-blur">
        <h1 className="font-bold text-slate-900">Geofabrik Preview · Class 2</h1>
        <p className="text-sm text-slate-600">{artifact.recordCount} records · {artifact.candidateCount} physical candidates</p>
        <p className="mt-1 text-xs font-semibold text-teal-700">Teal = experimental physical geometry only</p>
      </div>
      <MapContainer center={[45.95, 24.95]} zoom={7} zoomControl className="h-full w-full">
        <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <FitPreview bounds={bounds} />
        <LeafletGeoJSON
          data={{ type: 'FeatureCollection', features } as GeoJSON.FeatureCollection}
          style={() => ({ color: '#0f766e', weight: 3, opacity: 0.8, fillColor: '#14b8a6', fillOpacity: 0.24 })}
          onEachFeature={(feature, layer) => {
            const props = feature.properties as { slug: string; candidateId: string };
            const item = recordsByKey.get(`${props.slug}:${props.candidateId}`);
            if (!item) return;
            layer.bindTooltip(item.record.name, { sticky: true });
            layer.on('click', () => setSelection(item));
          }}
        />
      </MapContainer>
      {selection && <DetailCard {...selection} onClose={() => setSelection(null)} />}
    </div>
  );
}
