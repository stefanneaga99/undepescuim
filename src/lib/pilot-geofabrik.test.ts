import { describe, expect, it } from 'vitest';
import { emptyPilotCollection, validatePilotArtifacts } from './pilot-geofabrik';

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
});
