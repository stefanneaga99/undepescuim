'use client';
import type { PhysicalCourseFeature, PilotFeature } from '@/lib/pilot-geofabrik';
export function ExperimentalPilotBadge({ accepted, unresolved, features, physicalCourses }: { accepted: number; unresolved: number; features: PilotFeature[]; physicalCourses: PhysicalCourseFeature[] }) {
  return <section data-testid="pilot-experimental-badge" aria-label="Experimental pilot notice" className="absolute inset-x-3 top-3 z-[2000] max-w-3xl rounded-xl border border-teal-300/60 bg-slate-950/95 p-4 shadow-xl">
    <h1 className="text-lg font-bold">Experimental Covasna physical-course candidates</h1>
    <p className="mt-1 text-sm">Pinned Geofabrik/OSM snapshot; reviewed physical-course confidence only. Accepted legal geometry: {accepted}. Unresolved: {unresolved}.</p>
    <p className="mt-1 text-sm font-semibold text-amber-300">Physical lines are not legal contract/ownership/endpoints; canonical data and Production are unchanged.</p>
    {physicalCourses.map((feature) => <div key={feature.properties.slug} className="mt-2 border-l-2 border-teal-400 pl-2 text-xs" data-testid="pilot-physical-course-provenance" data-pilot-slug={feature.properties.slug}>
      <p className="font-semibold text-teal-300">{feature.properties.label}</p>
      <p>Confidence: {feature.properties.confidence}; provenance: {feature.properties.provenance.sourceFile} ({feature.properties.provenance.source}).</p>
      <p>Contract card preserved: {feature.properties.contract.declaredLengthKm} Km — {feature.properties.contract.limits}; legal endpoints: <strong>unverified</strong>.</p>
    </div>)}
    {accepted === 0 && <p className="mt-1 text-sm">No reviewed candidates cleared the legal-geometry gate; no orange legal focus is rendered.</p>}
    {features.map((feature) => <p key={feature.properties.slug} className="mt-1 text-xs" data-pilot-slug={feature.properties.slug}>OSM IDs: {feature.properties.osmIds.join(', ')} — <a className="underline" href={`${feature.properties.sourceUrl}`} target="_blank" rel="noreferrer">source snapshot</a></p>)}
  </section>;
}
