// @vitest-environment node
import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import type { GeometryLedger, GeometryLedgerVariant } from '@/types/geometry-ledger';
import type { Water } from '@/types/data';
import {
  dedupePhysicalPreview,
  isUnverifiedPhysicalPreview,
  physicalPreviewSelection,
  physicalPreviewWaters,
  reportWaterSlug,
} from './physical-preview';
import { parseGeometryLedger } from './geometry-ledger';

const hash = 'bb7852c0acf008ddaf2c08025f479400d4062de7276f5f89ca46c52b509dcd4f';
const segmentId = 'b'.repeat(64);
const explicitSegmentId = 'c'.repeat(64);
const geometry = { type: 'LineString' as const, coordinates: [[25.9, 45.1], [27.7, 45.67]] };

function ledgerRecord(sourceSlug: string, aliases = [sourceSlug], riverGroup: string | null = 'buzau') {
  return {
    sourceSlug,
    name: sourceSlug,
    county: 'Buzău',
    subtype: 'rau' as const,
    aliases,
    riverGroup,
    classification: 'preview-only' as const,
    geometryVariants: [{
      state: 'physical-full-course-preview' as const,
      start: null,
      end: null,
      evidenceSourceId: 'commit:path#candidate',
      segmentId,
      geometry: {
        geometryHash: hash,
        type: 'LineString' as const,
        bbox: [25.9, 45.1, 27.7, 45.67] as [number, number, number, number],
        coordinateCount: 2,
        valid: true as const,
        validityEvidence: 'finite',
      },
    }] as GeometryLedgerVariant[],
  };
}

function ledger(records = [ledgerRecord('anpa-anpa-0214')]): GeometryLedger {
  return {
    artifact: 'public-geometry-ledger',
    schemaVersion: 1,
    lockedCommit: '1'.repeat(40),
    records,
  };
}

function artifact(records: Array<Record<string, unknown>>) {
  return { schemaVersion: 1, records };
}

function artifactRecord(slug: string, candidates: Array<Record<string, unknown>> = [{ id: 'candidate', geometry, geometryHash: hash }]) {
  return {
    slug,
    name: slug,
    county: 'Buzău',
    subtype: 'rau',
    riverGroup: 'buzau',
    sourceBranch: 'local/class2-03',
    sourceCommit: 'abc',
    physicalCandidates: candidates,
  };
}

const preview = (slug: string, riverGroup = 'buzau', geometryHash = hash): Water => ({
  slug,
  name: slug,
  judet: 'Buzău',
  type: 'ape',
  subtype: 'rau',
  coordinates: [26, 45],
  bbox: [25, 45, 27, 46],
  asociatie: null,
  geometry,
  riverGroup,
  physicalPreview: true,
  physicalSourceSlug: slug,
  physicalRiverGroup: riverGroup,
  physicalGeometryHash: geometryHash,
  physicalSegmentId: segmentId,
  legalStatus: 'legal sector unverified',
  physicalProvenance: { sourceBranch: 'local/class2-03', sourceCommit: 'abc', geometryHash },
});

describe('ledger-backed physical preview rendering', () => {
  it('projects every checked-in ledger-supported candidate deterministically', async () => {
    const publicLedger = parseGeometryLedger(JSON.parse(readFileSync('public/data/geometry-ledger.json', 'utf8')));
    const previewArtifact = JSON.parse(readFileSync('public/data/preview_class2_physical.json', 'utf8'));
    const projected = dedupePhysicalPreview(await physicalPreviewWaters(previewArtifact, publicLedger));
    expect(projected).toHaveLength(76);
    for (const water of projected) {
      const exactAliases = publicLedger.records.filter((record) =>
        record.riverGroup === (water.physicalRiverGroup ?? null) &&
        record.geometryVariants.some((variant) =>
          variant.state === 'physical-full-course-preview' &&
          variant.geometry.geometryHash === water.physicalGeometryHash,
        ),
      ).map((record) => record.sourceSlug).sort();
      expect(water.physicalAliases).toEqual(exactAliases);
    }
    const buzau = projected.find((water) => water.physicalAliases?.includes('anpa-anpa-0207'));
    expect(buzau?.physicalAliases).toEqual([
      'anpa-anpa-0207', 'anpa-anpa-0210', 'anpa-anpa-0211',
      'anpa-anpa-0214', 'anpa-anpa-0261', 'romsilva-brasov-buzaul-superior',
    ]);
    expect(buzau?.physicalSegments?.map((segment) => segment.sourceSlug).sort()).toEqual([
      'anpa-anpa-0261', 'romsilva-brasov-buzaul-superior',
    ]);
  });

  it('uses the ledger identity, aliases and actual geometry bbox', async () => {
    const aliases = ['anpa-anpa-0207', 'anpa-anpa-0214'];
    const [water] = await physicalPreviewWaters(
      artifact([artifactRecord('anpa-anpa-0214')]),
      ledger([
        ledgerRecord('anpa-anpa-0207', aliases),
        ledgerRecord('anpa-anpa-0214', aliases),
      ]),
    );
    expect(water).toMatchObject({
      slug: 'anpa-anpa-0214',
      bbox: [25.9, 45.1, 27.7, 45.67],
      geometry,
      physicalSourceSlug: 'anpa-anpa-0214',
      physicalAliases: aliases,
      physicalGeometryHash: hash,
      physicalSegmentId: segmentId,
    });
  });

  it('selects candidates by exact ledger hash rather than incidental array position', async () => {
    const wrong = { id: 'wrong', geometry: { type: 'LineString', coordinates: [[20, 40], [21, 41]] }, geometryHash: 'b8ddfa8d54a2686d6cbeb9e67eb3793ecca1c98eb535cd43e876c90440b19f26' };
    const matching = { id: 'candidate', geometry, geometryHash: hash };
    const waters = await physicalPreviewWaters(
      artifact([artifactRecord('anpa-anpa-0214', [wrong, matching])]),
      ledger(),
    );
    expect(waters).toHaveLength(1);
    expect(waters[0].geometry).toEqual(geometry);
  });

  it('rejects malformed and nonfinite candidate geometry', async () => {
    const malformed = artifact([artifactRecord('anpa-anpa-0214', [{ id: 'candidate', geometry: { type: 'LineString', coordinates: [[25, Number.NaN]] }, geometryHash: hash }])]);
    await expect(physicalPreviewWaters(malformed, ledger())).rejects.toThrow(/finite|geometry/i);
  });

  it('rejects candidate bytes that claim a canonical ledger hash', async () => {
    const forgedGeometry = { type: 'LineString', coordinates: [[27.7, 45.67], [25.9, 45.1]] };
    const forged = artifact([artifactRecord('anpa-anpa-0214', [{ id: 'candidate', geometry: forgedGeometry, geometryHash: hash }])]);
    await expect(physicalPreviewWaters(forged, ledger())).rejects.toThrow(/canonical geometryHash/i);
  });

  it('validates a candidate hash before deciding that the ledger does not support it', async () => {
    const unsupported = artifact([artifactRecord('anpa-anpa-0214', [{
      id: 'unsupported', geometry, geometryHash: '0'.repeat(64),
    }])]);
    await expect(physicalPreviewWaters(unsupported, ledger())).rejects.toThrow(/canonical geometryHash/i);
  });

  it('carries an explicit physical projection without coloring the neutral full course', async () => {
    const record = ledgerRecord('anpa-anpa-0261');
    record.geometryVariants.push({
      state: 'explicit-physical-segment',
      start: 0.0774,
      end: 0.1641,
      evidenceSourceId: 'commit:path#candidate',
      segmentId: explicitSegmentId,
      geometry: record.geometryVariants[0].geometry!,
    });
    const [water] = await physicalPreviewWaters(artifact([artifactRecord('anpa-anpa-0261')]), ledger([record]));
    expect(water.physicalSegments).toEqual([{
      sourceSlug: 'anpa-anpa-0261',
      segmentId: explicitSegmentId,
      geometryHash: hash,
      start: 0.0774,
      end: 0.1641,
    }]);
    expect(isUnverifiedPhysicalPreview(water)).toBe(true);
  });

  it('paints a shared course once while retaining sorted aliases and projections', () => {
    const records = dedupePhysicalPreview([
      { ...preview('anpa-anpa-0214'), physicalAliases: ['anpa-anpa-0214', 'anpa-anpa-0261'] },
      { ...preview('anpa-anpa-0261'), judet: 'Covasna', physicalAliases: ['anpa-anpa-0214', 'anpa-anpa-0261'] },
    ]);
    expect(records).toHaveLength(1);
    expect(records[0].physicalAliases).toEqual(['anpa-anpa-0214', 'anpa-anpa-0261']);
    expect(physicalPreviewSelection(records[0], 'anpa-anpa-0214')).toBe(true);
    expect(physicalPreviewSelection(records[0], 'anpa-anpa-0261')).toBe(true);
  });

  it('does not merge identical hashes from different explicit river groups', () => {
    const records = dedupePhysicalPreview([
      preview('buzau'),
      { ...preview('other', 'other'), physicalSegmentId: 'd'.repeat(64) },
    ]);
    expect(records).toHaveLength(2);
    expect(new Set(records.map((record) => record.slug)).size).toBe(2);
    expect(records.every((record) => record.slug.startsWith('physical-preview-'))).toBe(true);
  });

  it('rejects conflicting duplicate identities instead of silently choosing one', () => {
    expect(() => dedupePhysicalPreview([
      preview('same', 'buzau', hash),
      { ...preview('same', 'buzau', 'd'.repeat(64)), physicalSegmentId: segmentId },
    ])).toThrow(/conflicting/i);
  });

  it('reports the selected canonical alias rather than a synthetic preview slug', () => {
    const rendered = {
      ...preview('source-a'),
      slug: `physical-preview-${hash}-buzau`,
      physicalAliases: ['source-a', 'source-b'],
    };
    expect(reportWaterSlug(rendered, 'source-b')).toBe('source-b');
    expect(reportWaterSlug(rendered, null)).toBe('source-a');
    expect(reportWaterSlug({ ...rendered, physicalPreview: false }, 'source-b')).toBe(rendered.slug);
  });
});
