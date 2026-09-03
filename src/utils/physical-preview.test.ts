// @vitest-environment node
import { describe, expect, it } from 'vitest';
import { dedupePhysicalPreview, isUnverifiedPhysicalPreview, physicalPreviewWaters } from '@/utils/physical-preview';
import type { Water } from '@/types/data';

const geometry = {
  type: 'LineString' as const,
  coordinates: [[25.9, 45.1], [27.7, 45.67]],
};

const preview = (slug: string, riverGroup: string, geometryHash: string): Water => ({
  slug,
  name: slug,
  judet: 'Buzău',
  type: 'ape',
  subtype: 'rau',
  coordinates: [26, 45],
  bbox: [25, 45, 27, 46],
  asociatie: null,
  riverGroup,
  physicalPreview: true,
  legalStatus: 'legal sector unverified',
  physicalProvenance: { sourceBranch: 'local/class2-03', sourceCommit: 'abc', geometryHash },
});

describe('physical preview rendering', () => {
  it('keeps canonical slug and derives geometry bbox', () => {
    const [water] = physicalPreviewWaters({
      schemaVersion: 1,
      records: [{ slug: 'anpa-anpa-0211', name: 'Valea Buzăului inferior', county: 'Buzău', subtype: 'rau', sourceBranch: 'local/class2-09', sourceCommit: 'commit', physicalCandidates: [{ geometry, geometryHash: 'hash' }] }],
    });
    expect(water.slug).toBe('anpa-anpa-0211');
    expect(water.bbox).toEqual([25.9, 45.1, 27.7, 45.67]);
    expect(water.geometry).toEqual(geometry);
    expect(water.physicalPreview).toBe(true);
    expect(water.legalStatus).toBe('legal sector unverified');
  });

  it('renders the shared Buzău candidate once while retaining distinct river groups', () => {
    const result = dedupePhysicalPreview([
      preview('buzau-covasna', 'buzau', 'same-course'),
      preview('buzau-buzau', 'buzau', 'same-course'),
      preview('buzau-brasov', 'buzau', 'same-course'),
      preview('other-river', 'other', 'same-course'),
    ]);
    expect(result.map((water) => water.slug)).toEqual(['buzau-covasna', 'other-river']);
  });

  it('recognizes only explicitly marked unverified previews', () => {
    expect(isUnverifiedPhysicalPreview(preview('preview', 'buzau', 'hash'))).toBe(true);
    expect(isUnverifiedPhysicalPreview({ ...preview('normal', 'buzau', 'hash'), physicalPreview: false })).toBe(false);
  });
});
