'use client';
import type { PilotFeature } from '@/lib/pilot-geofabrik';
export function ExperimentalPilotBadge({ accepted, unresolved, features }: { accepted: number; unresolved: number; features: PilotFeature[] }) {
  return <section data-testid="pilot-experimental-badge" aria-label="Experimental pilot notice" className="absolute inset-x-3 top-3 z-[2000] max-w-3xl rounded-xl border border-purple-300/60 bg-slate-950/95 p-4 shadow-xl">
    <h1 className="text-lg font-bold">Experimental Covasna physical-course candidates</h1>
    <p className="mt-1 text-sm">Pinned Geofabrik/OSM snapshot; reviewed physical-course confidence only. Accepted: {accepted}. Unresolved: {unresolved}.</p>
    <p className="mt-1 text-sm font-semibold text-amber-300">Not legal contract/ownership/endpoints; canonical data and Production are unchanged.</p>
    {accepted === 0 && <p className="mt-1 text-sm">No reviewed candidates cleared the gate.</p>}
    {features.map((feature) => <p key={feature.properties.slug} className="mt-1 text-xs" data-pilot-slug={feature.properties.slug}>OSM IDs: {feature.properties.osmIds.join(', ')} — <a className="underline" href={`${feature.properties.sourceUrl}`} target="_blank" rel="noreferrer">source snapshot</a></p>)}
  </section>;
}
