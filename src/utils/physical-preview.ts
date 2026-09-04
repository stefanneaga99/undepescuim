import type {
  ExplicitPhysicalSegmentVariant,
  GeometryLedger,
  GeometryLedgerRecord,
  PhysicalFullCoursePreviewVariant,
} from '@/types/geometry-ledger';
import type { PhysicalSegmentProjection, Water } from '@/types/data';
import { geometryBbox } from '@/utils/lod';

interface PhysicalPreviewArtifact {
  schemaVersion?: number;
  records?: unknown[];
}

interface PreviewCandidate {
  id: string;
  geometry: NonNullable<Water['geometry']>;
  geometryHash: string;
  sourceCommit?: string;
}

function coordinateCount(value: unknown): number {
  if (!Array.isArray(value) || value.length === 0) return 0;
  if (value.length >= 2 && typeof value[0] === 'number' && typeof value[1] === 'number') return 1;
  return value.reduce((total: number, item) => total + coordinateCount(item), 0);
}

function object(value: unknown, label: string): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error(`${label} must be an object`);
  return value as Record<string, unknown>;
}

function exactString(value: unknown, label: string): string {
  if (typeof value !== 'string' || value.length === 0) throw new Error(`${label} must be a non-empty string`);
  return value;
}

function geometryIdentityToken(value: unknown): string {
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) throw new Error('geometry values must be finite');
    const bytes = new Uint8Array(8);
    new DataView(bytes.buffer).setFloat64(0, value, false);
    return `d${[...bytes].map((byte) => byte.toString(16).padStart(2, '0')).join('')}`;
  }
  if (typeof value === 'string') return `s${JSON.stringify(value)}`;
  if (typeof value === 'boolean') return value ? 'b1' : 'b0';
  if (value === null) return 'n';
  if (Array.isArray(value)) return `[${value.map(geometryIdentityToken).join(',')}]`;
  const raw = object(value, 'canonical geometry value');
  return `{${Object.keys(raw).sort().map((key) => `${geometryIdentityToken(key)}:${geometryIdentityToken(raw[key])}`).join(',')}}`;
}

async function canonicalGeometryHash(geometry: NonNullable<Water['geometry']>): Promise<string> {
  if (!globalThis.crypto?.subtle) throw new Error('Web Crypto is required to validate physical geometry');
  const normalized = { type: geometry.type, coordinates: geometry.coordinates };
  const digest = await globalThis.crypto.subtle.digest('SHA-256', new TextEncoder().encode(geometryIdentityToken(normalized)));
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

function candidate(value: unknown, label: string): PreviewCandidate {
  const raw = object(value, label);
  const geometry = object(raw.geometry, `${label}.geometry`) as unknown as NonNullable<Water['geometry']>;
  const bbox = geometryBbox(geometry);
  if (!bbox) throw new Error(`${label}.geometry must contain finite supported coordinates`);
  return {
    id: exactString(raw.id, `${label}.id`),
    geometry,
    geometryHash: exactString(raw.geometryHash, `${label}.geometryHash`),
    sourceCommit: typeof raw.sourceCommit === 'string' ? raw.sourceCommit : undefined,
  };
}

function sameBbox(left: readonly number[], right: readonly number[]): boolean {
  return left.length === right.length && left.every((value, index) => value === right[index]);
}

function explicitSegments(record: GeometryLedgerRecord, geometryHash: string): PhysicalSegmentProjection[] {
  return record.geometryVariants
    .filter((entry): entry is ExplicitPhysicalSegmentVariant =>
      entry.state === 'explicit-physical-segment' && entry.geometry.geometryHash === geometryHash,
    )
    .map((entry) => ({
      sourceSlug: record.sourceSlug,
      segmentId: entry.segmentId,
      geometryHash,
      start: entry.start,
      end: entry.end,
    }));
}

/**
 * Join the isolated geometry artifact to the validated public ledger by exact
 * source slug + canonical geometry hash, then verify the matching geometry's
 * type/bbox/coordinate count. Unsupported candidates are ignored and malformed
 * candidates reject the artifact.
 */
export async function physicalPreviewWaters(
  artifact: PhysicalPreviewArtifact,
  ledger?: GeometryLedger,
): Promise<Water[]> {
  if (artifact.schemaVersion !== 1 || !Array.isArray(artifact.records)) return [];
  if (!ledger) return [];

  const ledgerBySlug = new Map(ledger.records.map((record) => [record.sourceSlug, record]));
  const aliasesByIdentity = new Map<string, Set<string>>();
  for (const record of ledger.records) {
    for (const variant of record.geometryVariants) {
      if (variant.state !== 'physical-full-course-preview') continue;
      const key = `${record.riverGroup ?? `source:${record.sourceSlug}`}:${variant.geometry.geometryHash}`;
      const aliases = aliasesByIdentity.get(key) ?? new Set<string>();
      aliases.add(record.sourceSlug);
      aliasesByIdentity.set(key, aliases);
    }
  }
  const seenSourceSlugs = new Set<string>();
  const waters: Water[] = [];

  for (const [recordIndex, value] of artifact.records.entries()) {
    const raw = object(value, `physical preview records[${recordIndex}]`);
    const sourceSlug = exactString(raw.slug, `physical preview records[${recordIndex}].slug`);
    if (seenSourceSlugs.has(sourceSlug)) throw new Error(`duplicate physical preview source slug: ${sourceSlug}`);
    seenSourceSlugs.add(sourceSlug);
    const ledgerRecord = ledgerBySlug.get(sourceSlug);
    if (!ledgerRecord) continue;
    if (!Array.isArray(raw.physicalCandidates)) throw new Error(`${sourceSlug}.physicalCandidates must be an array`);

    const variants = ledgerRecord.geometryVariants.filter(
      (entry): entry is PhysicalFullCoursePreviewVariant => entry.state === 'physical-full-course-preview',
    );
    const variantsByHash = new Map(variants.map((entry) => [entry.geometry.geometryHash, entry]));
    const matchedHashes = new Set<string>();

    for (const [candidateIndex, candidateValue] of raw.physicalCandidates.entries()) {
      const matched = candidate(candidateValue, `${sourceSlug}.physicalCandidates[${candidateIndex}]`);
      const computedHash = await canonicalGeometryHash(matched.geometry);
      if (computedHash !== matched.geometryHash) {
        throw new Error(`${sourceSlug}:${matched.id} does not match its canonical geometryHash`);
      }
      const ledgerVariant = variantsByHash.get(matched.geometryHash);
      if (!ledgerVariant) continue;
      const bbox = geometryBbox(matched.geometry);
      if (!bbox) throw new Error(`${sourceSlug} physical candidate has malformed geometry`);
      const count = coordinateCount(matched.geometry.coordinates);
      const geometryHash = ledgerVariant.geometry.geometryHash;
      const identityKey = `${ledgerRecord.riverGroup ?? `source:${sourceSlug}`}:${geometryHash}`;
      if (!sameBbox(bbox, ledgerVariant.geometry.bbox) ||
          matched.geometry.type !== ledgerVariant.geometry.type ||
          count !== ledgerVariant.geometry.coordinateCount) {
        throw new Error(`${sourceSlug}:${geometryHash} geometry conflicts with its canonical ledger summary`);
      }
      if (matchedHashes.has(geometryHash)) throw new Error(`duplicate physical candidate identity: ${sourceSlug}:${geometryHash}`);
      matchedHashes.add(geometryHash);
      const sourceBranch = typeof raw.sourceBranch === 'string' ? raw.sourceBranch : 'ledger';
      const sourceCommit = matched.sourceCommit ?? (typeof raw.sourceCommit === 'string' ? raw.sourceCommit : ledger.lockedCommit);
      waters.push({
        slug: sourceSlug,
        name: ledgerRecord.name,
        judet: ledgerRecord.county,
        type: 'ape',
        subtype: ledgerRecord.subtype,
        coordinates: [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2],
        bbox,
        asociatie: null,
        geometry: matched.geometry,
        physicalSourceSlug: sourceSlug,
        physicalRiverGroup: ledgerRecord.riverGroup ?? undefined,
        physicalGeometryHash: geometryHash,
        physicalSegmentId: ledgerVariant.segmentId,
        physicalAliases: [...(aliasesByIdentity.get(identityKey) ?? new Set([sourceSlug]))].sort(),
        physicalSegments: explicitSegments(ledgerRecord, geometryHash),
        riverGroup: ledgerRecord.riverGroup ?? undefined,
        physicalPreview: true,
        legalStatus: 'legal sector unverified',
        physicalProvenance: { sourceBranch, sourceCommit, geometryHash },
      });
    }
  }

  return waters;
}

/** Keep one rendered line per (explicit river group, canonical hash). */
export function dedupePhysicalPreview(waters: Water[]): Water[] {
  const byKey = new Map<string, Water>();
  const segmentKeys = new Map<string, string>();
  const sorted = [...waters].sort((left, right) =>
    `${left.physicalSourceSlug ?? left.slug}\0${left.physicalGeometryHash ?? ''}`.localeCompare(
      `${right.physicalSourceSlug ?? right.slug}\0${right.physicalGeometryHash ?? ''}`,
    ),
  );

  for (const water of sorted) {
    const hash = water.physicalGeometryHash ?? water.physicalProvenance?.geometryHash;
    const sourceSlug = water.physicalSourceSlug ?? water.slug;
    const group = water.physicalRiverGroup ?? water.riverGroup;
    if (!hash || !water.physicalSegmentId) throw new Error(`physical preview ${sourceSlug} has no ledger identity`);
    const key = `${group ?? `source:${sourceSlug}`}:${hash}`;
    const previousSegmentKey = segmentKeys.get(water.physicalSegmentId);
    if (previousSegmentKey && previousSegmentKey !== key) {
      throw new Error(`conflicting physical segment identity: ${water.physicalSegmentId}`);
    }
    segmentKeys.set(water.physicalSegmentId, key);

    const aliases = [...new Set([...(water.physicalAliases ?? []), sourceSlug])].sort();
    const existing = byKey.get(key);
    if (!existing) {
      byKey.set(key, {
        ...water,
        slug: `physical-preview-${hash}-${encodeURIComponent(group ?? sourceSlug)}`,
        physicalAliases: aliases,
        physicalSegments: [...(water.physicalSegments ?? [])].sort((a, b) => a.segmentId.localeCompare(b.segmentId)),
      });
      continue;
    }
    const mergedAliases = [...new Set([...(existing.physicalAliases ?? []), ...aliases])].sort();
    const mergedSegments = new Map(
      [...(existing.physicalSegments ?? []), ...(water.physicalSegments ?? [])].map((entry) => [entry.segmentId, entry]),
    );
    byKey.set(key, {
      ...existing,
      physicalAliases: mergedAliases,
      physicalSegments: [...mergedSegments.values()].sort((a, b) => a.segmentId.localeCompare(b.segmentId)),
    });
  }
  return [...byKey.values()];
}

export function physicalPreviewSelection(water: Water, selectedSlug: string | null): boolean {
  if (!selectedSlug) return false;
  return (water.physicalAliases ?? [water.physicalSourceSlug ?? water.slug]).includes(selectedSlug);
}

/** Resolve reports back to a canonical source alias, never a synthetic layer slug. */
export function reportWaterSlug(water: Water, selectedSlug: string | null): string {
  if (!water.physicalPreview) return water.slug;
  if (selectedSlug && water.physicalAliases?.includes(selectedSlug)) return selectedSlug;
  return water.physicalSourceSlug ?? water.slug;
}

/** A physical preview is never a legal-sector claim. */
export function isUnverifiedPhysicalPreview(water: Water): boolean {
  return water.physicalPreview === true && water.legalStatus === 'legal sector unverified';
}

export const dedupePhysicalPreviewWaters = dedupePhysicalPreview;
