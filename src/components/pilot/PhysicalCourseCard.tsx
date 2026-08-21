'use client';

import type { PhysicalCourseFeature } from '@/lib/pilot-geofabrik';

export function PhysicalCourseCard({ feature, mobile = false, onClose }: { feature: PhysicalCourseFeature; mobile?: boolean; onClose: () => void }) {
  const { properties } = feature;
  const osmIds = properties.provenance.osmIds ?? [];
  const geofabrikIds = properties.provenance.geofabrikIds ?? [];
  return (
    <section
      data-testid="pilot-physical-course-card"
      aria-label={`${properties.slug} physical course details`}
      className={mobile
        ? 'fixed inset-x-0 bottom-0 z-[2100] max-h-[68dvh] overflow-y-auto rounded-t-2xl border border-teal-300/60 bg-slate-950 p-5 text-white shadow-2xl lg:hidden'
        : 'absolute right-4 top-4 z-[2100] hidden w-[min(360px,calc(100%-2rem))] max-h-[calc(100%-2rem)] overflow-y-auto rounded-2xl border border-teal-300/60 bg-slate-950 p-5 text-white shadow-2xl lg:block'}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-teal-300">Experimental physical candidate</p>
          <h2 className="mt-1 text-lg font-bold">{properties.slug}</h2>
        </div>
        <button type="button" onClick={onClose} aria-label="Close candidate details" className="rounded px-2 py-1 text-xl leading-none text-slate-300 hover:bg-slate-800">×</button>
      </div>
      <dl className="mt-4 space-y-3 text-sm">
        <div><dt className="text-xs text-slate-400">Name / contract card</dt><dd className="font-medium">{properties.contract.declaredLengthKm} Km — {properties.contract.limits}</dd></div>
        <div><dt className="text-xs text-slate-400">Source / provenance</dt><dd>{properties.provenance.source} · {properties.provenance.sourceFile}</dd></div>
        <div><dt className="text-xs text-slate-400">OSM / Geofabrik IDs</dt><dd data-testid="pilot-geometry-ids">{osmIds.concat(geofabrikIds).join(', ') || 'Unavailable in the pinned snapshot'}</dd></div>
        <div><dt className="text-xs text-slate-400">Geometry hash / confidence</dt><dd className="break-all">{properties.provenance.geometryHash} · {properties.confidence}</dd></div>
      </dl>
      <p data-testid="pilot-legal-unverified" className="mt-4 rounded-lg border border-amber-300/60 bg-amber-950/40 px-3 py-2 text-sm font-semibold text-amber-200">
        Legal sector unverified — physical course only; no inferred orange legal focus.
      </p>
    </section>
  );
}
