// @vitest-environment node
import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { parseGeometryLedger } from '@/utils/geometry-ledger';

const hash = 'a'.repeat(64);
const variant = {
  state: 'physical-full-course-preview',
  start: null,
  end: null,
  evidenceSourceId: 'commit:path#candidate',
  segmentId: 'b'.repeat(64),
  geometry: {
    geometryHash: hash,
    type: 'LineString',
    bbox: [25, 45, 26, 46],
    coordinateCount: 2,
    valid: true,
    validityEvidence: 'finite supported GeoJSON coordinates; structural audit only',
  },
};

function artifact(overrides: Record<string, unknown> = {}) {
  return {
    artifact: 'public-geometry-ledger',
    schemaVersion: 1,
    lockedCommit: '62974d0f050b265a27dcc7ea30c6b356eb3a3454',
    records: [{
      sourceSlug: 'water-a',
      name: 'Râul A',
      county: 'Buzău',
      subtype: 'rau',
      aliases: ['water-a'],
      riverGroup: 'a',
      classification: 'preview-only',
      geometryVariants: [variant],
    }],
    ...overrides,
  };
}

describe('parseGeometryLedger', () => {
  it('validates every identity in the checked-in public ledger', () => {
    const ledger = parseGeometryLedger(JSON.parse(readFileSync('public/data/geometry-ledger.json', 'utf8')));
    expect(ledger.records).toHaveLength(1013);
    expect(new Set(ledger.records.map((record) => record.sourceSlug)).size).toBe(1013);
  });

  it('returns exact immutable identities for a valid public ledger', () => {
    const ledger = parseGeometryLedger(artifact());
    expect(ledger.records[0].sourceSlug).toBe('water-a');
    expect(ledger.records[0].aliases).toEqual(['water-a']);
    expect(ledger.records[0].geometryVariants[0]).toMatchObject({
      state: 'physical-full-course-preview',
      segmentId: 'b'.repeat(64),
      geometry: { geometryHash: hash },
    });
  });

  it.each([
    ['duplicate source slugs', artifact({ records: [artifact().records[0], artifact().records[0]] })],
    ['unsorted aliases', artifact({ records: [{ ...artifact().records[0], aliases: ['water-z', 'water-a'] }] })],
    ['missing source alias', artifact({ records: [{ ...artifact().records[0], aliases: ['water-z'] }] })],
    ['duplicate segment identities', artifact({ records: [{ ...artifact().records[0], geometryVariants: [variant, variant] }] })],
    ['nonfinite geometry bbox', artifact({ records: [{ ...artifact().records[0], geometryVariants: [{ ...variant, geometry: { ...variant.geometry, bbox: [25, 45, Number.NaN, 46] } }] }] })],
  ])('rejects %s', (_name, value) => {
    expect(() => parseGeometryLedger(value)).toThrow();
  });

  it('rejects malformed explicit physical segments', () => {
    const value = artifact({ records: [{ ...artifact().records[0], geometryVariants: [{ ...variant, state: 'explicit-physical-segment', start: 0.8, end: 0.2 }] }] });
    expect(() => parseGeometryLedger(value)).toThrow(/explicit segment/i);
  });

  it('rejects unknown identity fields and malformed locked commits', () => {
    expect(() => parseGeometryLedger(artifact({ lockedCommit: 'not-a-commit' }))).toThrow(/lockedCommit/);
    const value = artifact({
      records: [{
        ...artifact().records[0],
        geometryVariants: [{
          ...variant,
          geometry: { ...variant.geometry, geometryHahs: hash },
        }],
      }],
    });
    expect(() => parseGeometryLedger(value)).toThrow(/unknown field/);
  });
});
