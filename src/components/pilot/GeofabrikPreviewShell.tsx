'use client';

import { useEffect, useState } from 'react';
import { validatePilotArtifacts, emptyPilotCollection, type PilotCollection } from '@/lib/pilot-geofabrik';
import { AcceptedGeometryLayer } from './AcceptedGeometryLayer';
import { ExperimentalPilotBadge } from './ExperimentalPilotBadge';

export function GeofabrikPreviewShell() {
  const [collection, setCollection] = useState<PilotCollection>(emptyPilotCollection);
  const [ledger, setLedger] = useState<{ accepted: number; unresolved: number; rows: Record<string, { geometryHash?: string; osmIds?: string[] }> }>({ accepted: 0, unresolved: 0, rows: {} });
  const [error, setError] = useState(false);
  useEffect(() => {
    void Promise.all([fetch('/pilot/geofabrik/accepted_geometry.geojson').then((r) => r.json()), fetch('/pilot/geofabrik/pilot_ledger.json').then((r) => r.json())])
      .then(([geo, raw]) => {
        const rows = Object.fromEntries((raw.records ?? []).map((r: { slug: string; geometryHash?: string; osm?: { ways?: number[] } }) => [r.slug, { geometryHash: r.geometryHash, osmIds: (r.osm?.ways ?? []).map((id) => `way/${id}`) }]));
        const safe = validatePilotArtifacts(geo, rows);
        setCollection(safe);
        setLedger({ accepted: safe.features.length, unresolved: (raw.records ?? []).filter((r: { review?: { status?: string } }) => r.review?.status !== 'ACCEPTED_REVIEWED').length, rows });
      }).catch(() => setError(true));
  }, []);
  return <main className="relative h-dvh bg-slate-950 text-white" data-testid="pilot-geofabrik-preview">
    <ExperimentalPilotBadge accepted={ledger.accepted} unresolved={ledger.unresolved} features={collection.features} />
    {error && <p role="alert" className="absolute left-4 top-32 z-[2000] rounded bg-red-900 p-3">Pilot artifacts unavailable; nothing rendered.</p>}
    <div className="h-full w-full pt-24"><AcceptedGeometryLayer collection={collection} /></div>
  </main>;
}
