import { describe, expect, it } from 'vitest';
import { physicalPreviewWaters } from './physical-preview';

const geometry = {
  type: 'LineString' as const,
  coordinates: [[25.9, 45.1], [27.7, 45.67]],
};

describe('physicalPreviewWaters', () => {
  it('keeps the canonical slug and derives the physical geometry bbox', () => {
    const [water] = physicalPreviewWaters({
      schemaVersion: 1,
      records: [{
        slug: 'anpa-anpa-0211',
        name: 'Valea Buzăului inferior',
        county: 'Buzău',
        subtype: 'rau',
        sourceBranch: 'local/class2-09',
        sourceCommit: 'commit',
        physicalCandidates: [{ geometry, geometryHash: 'hash' }],
      }],
    });

    expect(water.slug).toBe('anpa-anpa-0211');
    expect(water.bbox).toEqual([25.9, 45.1, 27.7, 45.67]);
    expect(water.geometry).toEqual(geometry);
    expect(water.physicalPreview).toBe(true);
    expect(water.legalStatus).toBe('legal sector unverified');
  });
});
