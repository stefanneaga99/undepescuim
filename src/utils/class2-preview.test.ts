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

  it.each([
    ['LineString', { type: 'LineString', coordinates: [[23, 46], [24, 47]] }, 24],
    ['MultiLineString', { type: 'MultiLineString', coordinates: [[[23, 46], [24, 47]]] }, 24],
    ['Polygon', { type: 'Polygon', coordinates: [[[23, 46], [24, 47], [25, 46], [23, 46]]] }, 25],
    ['MultiPolygon', { type: 'MultiPolygon', coordinates: [[[[23, 46], [24, 47], [25, 46], [23, 46]]]] }, 25],
  ])('computes bounds for %s geometry', (_type, geometry, maxLon) => {
    const candidate = artifact.records[0].physicalCandidates[0];
    const geometryArtifact = {
      ...artifact,
      records: [{
        ...artifact.records[0],
        physicalCandidates: [{ ...candidate, geometry }],
      }],
    } as Class2PreviewArtifact;

    expect(previewBounds(geometryArtifact)).toEqual([23, 46, maxLon, 47]);
  });

  it('uses the fallback bounds for invalid or null geometry', () => {
    const candidate = artifact.records[0].physicalCandidates[0];
    const malformedArtifact = {
      ...artifact,
      records: [{
        ...artifact.records[0],
        physicalCandidates: [
          { ...candidate, geometry: null },
          { ...candidate, id: 'invalid', geometry: { type: 'GeometryCollection', geometries: [] } },
        ],
      }],
    } as unknown as Class2PreviewArtifact;

    expect(previewBounds(malformedArtifact)).toEqual([20, 43.5, 30, 48.5]);
  });
});
