import type {
  ExplicitPhysicalSegmentVariant,
  GeometryLedger,
  GeometryLedgerClassification,
  GeometryLedgerRecord,
  GeometryLedgerState,
  GeometryLedgerSummary,
  GeometryLedgerVariant,
} from '@/types/geometry-ledger';

const HASH = /^[0-9a-f]{64}$/;
const COMMIT = /^[0-9a-f]{40}$/;
const STATES = new Set<GeometryLedgerState>([
  'canonical-legal-sector',
  'physical-full-course-preview',
  'explicit-physical-segment',
  'unresolved',
]);
const CLASSIFICATIONS = new Set<GeometryLedgerClassification>(['repaired', 'preview-only', 'unresolved']);
const GEOMETRY_TYPES = new Set(['Point', 'LineString', 'MultiLineString', 'Polygon', 'MultiPolygon']);

function object(value: unknown, label: string): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error(`${label} must be an object`);
  return value as Record<string, unknown>;
}

function string(value: unknown, label: string): string {
  if (typeof value !== 'string' || value.length === 0) throw new Error(`${label} must be a non-empty string`);
  return value;
}

function rejectUnknown(raw: Record<string, unknown>, allowed: readonly string[], label: string): void {
  const allowedSet = new Set(allowed);
  const unknown = Object.keys(raw).find((key) => !allowedSet.has(key));
  if (unknown) throw new Error(`${label} contains unknown field: ${unknown}`);
}

function nullableFraction(value: unknown, label: string): number | null {
  if (value === null) return null;
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0 || value > 1) {
    throw new Error(`${label} must be a finite fraction or null`);
  }
  return value;
}

function summary(value: unknown, label: string): GeometryLedgerSummary {
  const raw = object(value, label);
  rejectUnknown(raw, ['geometryHash', 'type', 'bbox', 'coordinateCount', 'valid', 'validityEvidence'], label);
  const geometryHash = string(raw.geometryHash, `${label}.geometryHash`);
  if (!HASH.test(geometryHash)) throw new Error(`${label}.geometryHash must be a lowercase SHA-256`);
  if (typeof raw.type !== 'string' || !GEOMETRY_TYPES.has(raw.type)) throw new Error(`${label}.type is unsupported`);
  if (!Array.isArray(raw.bbox) || raw.bbox.length !== 4 || !raw.bbox.every((item) => typeof item === 'number' && Number.isFinite(item))) {
    throw new Error(`${label}.bbox must contain four finite numbers`);
  }
  const [minLon, minLat, maxLon, maxLat] = raw.bbox;
  if (minLon > maxLon || minLat > maxLat) throw new Error(`${label}.bbox is inverted`);
  if (!Number.isInteger(raw.coordinateCount) || (raw.coordinateCount as number) <= 0) {
    throw new Error(`${label}.coordinateCount must be positive`);
  }
  if (raw.valid !== true) throw new Error(`${label}.valid must be true`);
  return {
    geometryHash,
    type: raw.type as GeometryLedgerSummary['type'],
    bbox: [minLon, minLat, maxLon, maxLat],
    coordinateCount: raw.coordinateCount as number,
    valid: true,
    validityEvidence: string(raw.validityEvidence, `${label}.validityEvidence`),
  };
}

function variant(value: unknown, label: string, segmentIds: Set<string>): GeometryLedgerVariant {
  const raw = object(value, label);
  rejectUnknown(raw, ['state', 'start', 'end', 'evidenceSourceId', 'segmentId', 'geometry', 'reason', 'citation'], label);
  if (typeof raw.state !== 'string' || !STATES.has(raw.state as GeometryLedgerState)) {
    throw new Error(`${label}.state is unsupported`);
  }
  const state = raw.state as GeometryLedgerState;
  const evidenceSourceId = string(raw.evidenceSourceId, `${label}.evidenceSourceId`);
  if (state === 'unresolved') {
    if (raw.start !== null || raw.end !== null || raw.segmentId !== null || raw.geometry !== null) {
      throw new Error(`${label} unresolved identity must not contain geometry or segment bounds`);
    }
    return {
      state,
      start: null,
      end: null,
      evidenceSourceId,
      segmentId: null,
      geometry: null,
      reason: string(raw.reason, `${label}.reason`),
    };
  }

  const segmentId = string(raw.segmentId, `${label}.segmentId`);
  if (!HASH.test(segmentId)) throw new Error(`${label}.segmentId must be a lowercase SHA-256`);
  if (segmentIds.has(segmentId)) throw new Error(`duplicate segment identity: ${segmentId}`);
  segmentIds.add(segmentId);
  const geometry = summary(raw.geometry, `${label}.geometry`);
  const start = nullableFraction(raw.start, `${label}.start`);
  const end = nullableFraction(raw.end, `${label}.end`);

  if (state === 'physical-full-course-preview') {
    if (start !== null || end !== null) throw new Error(`${label} full-course preview cannot contain segment bounds`);
    return { state, start: null, end: null, evidenceSourceId, segmentId, geometry };
  }
  if (state === 'explicit-physical-segment') {
    if (start === null || end === null || start >= end) throw new Error(`${label} explicit segment must have ordered endpoints`);
    return { state, start, end, evidenceSourceId, segmentId, geometry };
  }
  if ((start === null) !== (end === null) || (start !== null && end !== null && start >= end)) {
    throw new Error(`${label} canonical sector endpoints must be null or ordered`);
  }
  return { state, start, end, evidenceSourceId, segmentId, geometry };
}

/** Parse the public ledger fail-closed so runtime identity never depends on array position. */
export function parseGeometryLedger(value: unknown): GeometryLedger {
  const raw = object(value, 'geometry ledger');
  rejectUnknown(raw, ['artifact', 'schemaVersion', 'lockedCommit', 'totals', 'identityRules', 'sourceArtifacts', 'records'], 'geometry ledger');
  if (raw.artifact !== 'public-geometry-ledger' || raw.schemaVersion !== 1) {
    throw new Error('unsupported geometry ledger artifact');
  }
  if (!Array.isArray(raw.records)) throw new Error('geometry ledger records must be an array');

  const sourceSlugs = new Set<string>();
  const segmentIds = new Set<string>();
  const records: GeometryLedgerRecord[] = raw.records.map((item, recordIndex) => {
    const record = object(item, `records[${recordIndex}]`);
    rejectUnknown(record, [
      'sourceSlug', 'name', 'county', 'subtype', 'aliases', 'riverGroup', 'classification',
      'classificationRationale', 'confidence', 'unresolved', 'canonicalBbox', 'rawSources',
      'geometryVariants', 'countyConsistencyEvidence', 'endpointEvidence', 'historicalAudit',
      'browserObservations',
    ], `records[${recordIndex}]`);
    const sourceSlug = string(record.sourceSlug, `records[${recordIndex}].sourceSlug`);
    if (sourceSlugs.has(sourceSlug)) throw new Error(`duplicate source slug: ${sourceSlug}`);
    sourceSlugs.add(sourceSlug);
    if (!Array.isArray(record.aliases) || !record.aliases.every((alias) => typeof alias === 'string' && alias.length > 0)) {
      throw new Error(`${sourceSlug}.aliases must contain exact slugs`);
    }
    const aliases = [...record.aliases] as string[];
    if (aliases.join('\0') !== [...new Set(aliases)].sort().join('\0')) throw new Error(`${sourceSlug}.aliases must be sorted and unique`);
    if (!aliases.includes(sourceSlug)) throw new Error(`${sourceSlug}.aliases must include sourceSlug`);
    const riverGroup = record.riverGroup === null ? null : string(record.riverGroup, `${sourceSlug}.riverGroup`);
    if (aliases.length > 1 && !riverGroup) throw new Error(`${sourceSlug}.riverGroup is required for shared aliases`);
    if (!CLASSIFICATIONS.has(record.classification as GeometryLedgerClassification)) {
      throw new Error(`${sourceSlug}.classification is unsupported`);
    }
    if (!Array.isArray(record.geometryVariants) || record.geometryVariants.length === 0) {
      throw new Error(`${sourceSlug}.geometryVariants must not be empty`);
    }
    return {
      sourceSlug,
      name: string(record.name, `${sourceSlug}.name`),
      county: string(record.county, `${sourceSlug}.county`),
      subtype: record.subtype === 'lac' ? 'lac' : record.subtype === 'rau' ? 'rau' : (() => { throw new Error(`${sourceSlug}.subtype is unsupported`); })(),
      aliases,
      riverGroup,
      classification: record.classification as GeometryLedgerClassification,
      geometryVariants: record.geometryVariants.map((entry, variantIndex) => variant(entry, `${sourceSlug}.geometryVariants[${variantIndex}]`, segmentIds)),
    };
  });

  const lockedCommit = string(raw.lockedCommit, 'geometry ledger lockedCommit');
  if (!COMMIT.test(lockedCommit)) throw new Error('geometry ledger lockedCommit must be a 40-character commit id');
  return {
    artifact: 'public-geometry-ledger',
    schemaVersion: 1,
    lockedCommit,
    records,
  };
}

export function explicitPhysicalSegment(
  ledger: GeometryLedger,
  sourceSlug: string,
  geometryHash?: string,
): ExplicitPhysicalSegmentVariant | null {
  const record = ledger.records.find((candidate) => candidate.sourceSlug === sourceSlug);
  if (!record) return null;
  return record.geometryVariants.find(
    (candidate): candidate is ExplicitPhysicalSegmentVariant =>
      candidate.state === 'explicit-physical-segment' &&
      (geometryHash === undefined || candidate.geometry.geometryHash === geometryHash),
  ) ?? null;
}
