import { describe, expect, it } from 'vitest';
import { emptyPilotCollection, validatePhysicalCourseArtifacts, validatePilotArtifacts } from './pilot-geofabrik';

describe('pilot geofabrik artifact gate', () => {
  it('fails closed for malformed collections', () => {
    expect(validatePilotArtifacts({ type: 'FeatureCollection', features: [] }, {})).toEqual(emptyPilotCollection);
  });
  it('accepts only provenance-complete reviewed physical courses', () => {
    const feature = { type: 'Feature', geometry: { type: 'LineString', coordinates: [[25, 45], [25.1, 45.1]] }, properties: {
      slug: 'control', pilotStatus: 'accepted-reviewed', confidence: 'reviewed-physical-course', osmIds: ['way/1'], geometryHash: 'h', sourceUrl: 'https://download.geofabrik.de/x', snapshotSha256: '1234567890abcdef', legalContractGeometry: false,
    } };
    expect(validatePilotArtifacts({ type: 'FeatureCollection', features: [feature] }, { control: { geometryHash: 'h', osmIds: ['way/1'] } }).features).toHaveLength(1);
    expect(validatePilotArtifacts({ type: 'FeatureCollection', features: [{ ...feature, properties: { ...feature.properties, pilotStatus: 'candidate' } }] }, { control: { geometryHash: 'h', osmIds: ['way/1'] } })).toEqual(emptyPilotCollection);
  });
  it('keeps an unverified physical line separate from legal geometry', () => {
    const result = validatePhysicalCourseArtifacts({ type: 'FeatureCollection', features: [{ type: 'Feature', geometry: { type: 'LineString', coordinates: [[25, 46], [25.1, 46.1]] }, properties: {
      slug: 'anpa-anpa-0333', courseStatus: 'experimental-physical-course', label: 'experimental physical course — legal sector unverified', confidence: 'source-traceable physical-course candidate',
      provenance: { source: 'tier1_premap', sourceFile: 'data/premapped/tarnava-mare.geojson', generatedAt: '2026-08-11', geometryHash: 'hash' },
      contract: { declaredLengthKm: 5, limits: 'Aval baraj lac Zetea – pod Desag', legalEndpoints: 'unverified', legalSectorGeometry: false },
    } }] });
    expect(result.features).toHaveLength(1);
    expect(result.features[0].properties.contract.legalSectorGeometry).toBe(false);
    expect(validatePhysicalCourseArtifacts({ type: 'FeatureCollection', features: [{ ...result.features[0], properties: { ...result.features[0].properties, label: 'orange legal sector' } }] }).features).toHaveLength(0);
  });
});
