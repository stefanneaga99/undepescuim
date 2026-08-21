'use client';

import { useEffect, useState } from 'react';
import { emptyPhysicalCourseCollection, validatePhysicalCourseArtifacts, validatePilotArtifacts, emptyPilotCollection, type PhysicalCourseCollection, type PilotCollection } from '@/lib/pilot-geofabrik';
import { AcceptedGeometryLayer } from './AcceptedGeometryLayer';
import { ExperimentalPilotBadge } from './ExperimentalPilotBadge';

export function GeofabrikPreviewShell() {
  const [collection, setCollection] = useState<PilotCollection>(emptyPilotCollection);
  const [physicalCourses, setPhysicalCourses] = useState<PhysicalCourseCollection>(emptyPhysicalCourseCollection);
  const [ledger, setLedger] = useState<{ accepted: number; unresolved: number }>({ accepted: 0, unresolved: 0 });
  const [error, setError] = useState(false);
  useEffect(() => {
    void Promise.all([
      fetch('/pilot/geofabrik/accepted_geometry.geojson').then((r) => r.json()),
      fetch('/pilot/geofabrik/pilot_ledger.json').then((r) => r.json()),
      fetch('/pilot/geofabrik/physical_course_candidates.geojson').then((r) => r.json()),
    ]).then(([geo, raw, physical]) => {
      const rows = Object.fromEntries((raw.records ?? []).map((r: { slug: string; geometryHash?: string; osm?: { ways?: number[] } }) => [r.slug, { geometryHash: r.geometryHash, osmIds: (r.osm?.ways ?? []).map((id) => `way/${id}`) }]));
      const safe = validatePilotArtifacts(geo, rows);
      const safePhysical = validatePhysicalCourseArtifacts(physical);
      setCollection(safe);
      setPhysicalCourses(safePhysical);
      setLedger({ accepted: safe.features.length, unresolved: (raw.records ?? []).filter((r: { review?: { status?: string } }) => r.review?.status !== 'ACCEPTED_REVIEWED').length });
    }).catch(() => setError(true));
  }, []);
  return <main className="relative flex h-dvh min-h-0 flex-col bg-slate-950 text-white" data-testid="pilot-geofabrik-preview">
    <ExperimentalPilotBadge accepted={ledger.accepted} unresolved={ledger.unresolved} features={collection.features} physicalCourses={physicalCourses.features} />
    {error && <p role="alert" className="absolute left-4 top-32 z-[2000] rounded bg-red-900 p-3">Pilot artifacts unavailable; nothing rendered.</p>}
    <div className="relative min-h-0 flex-1 pt-24"><AcceptedGeometryLayer collection={collection} physicalCourses={physicalCourses} /></div>
  </main>;
}
