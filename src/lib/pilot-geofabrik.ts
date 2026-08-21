export type PilotGeometry = { type: 'LineString' | 'MultiLineString'; coordinates: unknown };
export type PilotFeature = { type: 'Feature'; geometry: PilotGeometry; properties: {
  slug: string; pilotStatus: 'accepted-reviewed'; confidence: 'reviewed-physical-course'; osmIds: string[];
  geometryHash: string; sourceUrl: string; snapshotSha256: string; legalContractGeometry: false;
} };
export type PilotCollection = { type: 'FeatureCollection'; features: PilotFeature[] };
export type PhysicalCourseFeature = { type: 'Feature'; geometry: PilotGeometry; properties: {
  slug: string; courseStatus: 'experimental-physical-course'; label: string; confidence: string;
  provenance: { source: string; sourceFile: string; generatedAt: string; geometryHash: string };
  contract: { declaredLengthKm: number; limits: string; legalEndpoints: 'unverified'; legalSectorGeometry: false };
} };
export type PhysicalCourseCollection = { type: 'FeatureCollection'; features: PhysicalCourseFeature[] };
export const emptyPilotCollection: PilotCollection = { type: 'FeatureCollection', features: [] };
export const emptyPhysicalCourseCollection: PhysicalCourseCollection = { type: 'FeatureCollection', features: [] };

function isSafeHttps(value: unknown): value is string {
  return typeof value === 'string' && value.startsWith('https://') && !/[<>"']/.test(value);
}
function isFeature(value: unknown, ledger: Record<string, { geometryHash?: string; osmIds?: string[] }>): value is PilotFeature {
  if (!value || typeof value !== 'object') return false;
  const p = (value as { properties?: unknown }).properties;
  const geometry = (value as { geometry?: unknown }).geometry;
  if (!p || !geometry || typeof p !== 'object' || typeof geometry !== 'object') return false;
  const props = p as Record<string, unknown>;
  const shape = geometry as Record<string, unknown>;
  const expected = ledger[String(props.slug)];
  return (shape.type === 'LineString' || shape.type === 'MultiLineString')
    && props.pilotStatus === 'accepted-reviewed' && props.confidence === 'reviewed-physical-course'
    && Array.isArray(props.osmIds) && props.osmIds.length > 0 && props.osmIds.every((id) => typeof id === 'string' && /^(way|relation)\/\d+$/.test(id))
    && typeof props.geometryHash === 'string' && expected?.geometryHash === props.geometryHash
    && JSON.stringify(expected.osmIds) === JSON.stringify(props.osmIds)
    && isSafeHttps(props.sourceUrl) && typeof props.snapshotSha256 === 'string' && props.snapshotSha256.length >= 16
    && props.legalContractGeometry === false;
}

export function validatePilotArtifacts(value: unknown, ledger: unknown): PilotCollection {
  if (!value || typeof value !== 'object' || (value as { type?: unknown }).type !== 'FeatureCollection' || !Array.isArray((value as { features?: unknown }).features) || !ledger || typeof ledger !== 'object') return emptyPilotCollection;
  const rows = ledger as Record<string, { geometryHash?: string; osmIds?: string[] }>;
  const features = (value as { features: unknown[] }).features;
  if (!features.every((feature) => isFeature(feature, rows))) return emptyPilotCollection;
  return { type: 'FeatureCollection', features: features as PilotFeature[] };
}

export function validatePhysicalCourseArtifacts(value: unknown): PhysicalCourseCollection {
  if (!value || typeof value !== 'object' || (value as { type?: unknown }).type !== 'FeatureCollection' || !Array.isArray((value as { features?: unknown }).features)) return emptyPhysicalCourseCollection;
  const features = (value as { features: unknown[] }).features.filter((feature): feature is PhysicalCourseFeature => {
    if (!feature || typeof feature !== 'object') return false;
    const { geometry, properties } = feature as { geometry?: unknown; properties?: unknown };
    if (!geometry || typeof geometry !== 'object' || !properties || typeof properties !== 'object') return false;
    const shape = geometry as Record<string, unknown>; const p = properties as Record<string, unknown>;
    const provenance = p.provenance as Record<string, unknown> | undefined; const contract = p.contract as Record<string, unknown> | undefined;
    return (shape.type === 'LineString' || shape.type === 'MultiLineString') && p.courseStatus === 'experimental-physical-course'
      && typeof p.label === 'string' && p.label.includes('legal sector unverified') && typeof p.confidence === 'string'
      && !!provenance && typeof provenance.source === 'string' && typeof provenance.sourceFile === 'string' && typeof provenance.geometryHash === 'string'
      && !!contract && contract.legalEndpoints === 'unverified' && contract.legalSectorGeometry === false && typeof contract.declaredLengthKm === 'number';
  });
  return { type: 'FeatureCollection', features };
}
