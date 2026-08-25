import { describe, expect, it } from 'vitest';
import { CLASS2_LEGAL_STATUS, previewBounds, previewFeatures, type Class2PreviewArtifact } from '@/utils/class2-preview';

const artifact = {
  schemaVersion: 1,
  artifact: 'class2-physical-preview',
  class: 2,
  recordCount: 1,
  candidateCount: 1,
  chunkId: 'CLASS2-01',
  slugs: ['physical-only'],
  sourceInventorySha256: 'source-lock',
  records: [{
    slug: 'physical-only', name: 'Physical only', county: 'Alba', locality: null,
    association: 'Example association', associationSlug: 'example', riverGroup: null, subtype: 'rau',
    physicalCandidates: [{
      id: 'candidate-1', kind: 'line', rating: 'pinned_osm_candidate', source: 'snapshot', sourceId: null,
      physicalSourceUrl: null, osmId: null, geofabrikId: null, geometryHash: 'geometry-lock',
      geometry: { type: 'LineString', coordinates: [[23, 46], [24, 47]] }, measuredLengthKm: 1,
      componentCount: 1, componentIds: [], confidence: 'pinned_osm_candidate', countyMatch: { status: 'not_verified' }, topology: null,
    }], legalStatus: CLASS2_LEGAL_STATUS, disclosure: 'unverified', canonicalMutation: false,
  }],
} as Class2PreviewArtifact;

describe('Class 2 physical preview', () => {
  it('keeps preview features separate and marks legal status unverified', () => {
    const features = previewFeatures(artifact);
    expect(features).toHaveLength(1);
    expect(features[0].properties).toMatchObject({ slug: 'physical-only', legalStatus: CLASS2_LEGAL_STATUS, geometryHash: 'geometry-lock' });
    expect(features[0].properties).not.toHaveProperty('selectedWaterSlug');
    expect(features[0].properties).not.toHaveProperty('sectorStart');
  });

  it('computes bounds from physical geometry only', () => {
    expect(previewBounds(artifact)).toEqual([23, 46, 24, 47]);
  });
});
