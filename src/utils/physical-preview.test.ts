// @vitest-environment node
import { describe, expect, it } from 'vitest';
import type { Water } from '@/types/data';
import { dedupePhysicalPreview, isUnverifiedPhysicalPreview, physicalPreviewSelection, physicalPreviewWaters } from './physical-preview';

const geometry = { type: 'LineString' as const, coordinates: [[25.9, 45.1], [27.7, 45.67]] };

const preview = (slug: string, riverGroup = 'buzau', geometryHash = 'shared-course'): Water => ({
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
  physicalSourceSlug: slug,
  physicalRiverGroup: riverGroup,
  physicalGeometryHash: geometryHash,
  legalStatus: 'legal sector unverified',
  physicalProvenance: { sourceBranch: 'local/class2-03', sourceCommit: 'abc', geometryHash },
});

describe('physical preview rendering', () => {
  it('keeps canonical slug, full geometry, and legal disclosure separate from contracts', () => {
    const [water] = physicalPreviewWaters({
      schemaVersion: 1,
      records: [{ slug: 'anpa-anpa-0214', name: 'Râul Buzăul inferior', county: 'Buzău', subtype: 'rau', riverGroup: 'buzau', sourceBranch: 'local/class2-03', sourceCommit: 'abc', physicalCandidates: [{ geometry, geometryHash: 'hash' }] }],
    });
    expect(water.slug).toBe('anpa-anpa-0214');
    expect(water.bbox).toEqual([25.9, 45.1, 27.7, 45.67]);
    expect(water.geometry).toEqual(geometry);
    expect(water.legalStatus).toBe('legal sector unverified');
    expect(water.physicalSourceSlug).toBe('anpa-anpa-0214');
  });

  it('paints the shared Buzău/Covasna course once while retaining every source alias', () => {
    const records = dedupePhysicalPreview([
      preview('anpa-anpa-0214'),
      { ...preview('anpa-anpa-0261'), judet: 'Covasna' },
    ]);
    expect(records).toHaveLength(1);
    expect(records[0].geometry).toEqual(preview('x').geometry);
    expect(records[0].physicalAliases).toEqual(['anpa-anpa-0214', 'anpa-anpa-0261']);
    expect(physicalPreviewSelection(records[0], 'anpa-anpa-0214')).toBe(true);
    expect(physicalPreviewSelection(records[0], 'anpa-anpa-0261')).toBe(true);
  });

  it('does not merge identical geometry hashes from different river groups', () => {
    const records = dedupePhysicalPreview([preview('buzau'), preview('other', 'other')]);
    expect(records).toHaveLength(2);
  });

  it('recognizes only explicitly disclosed physical previews', () => {
    expect(isUnverifiedPhysicalPreview(preview('preview'))).toBe(true);
    expect(isUnverifiedPhysicalPreview({ ...preview('normal'), physicalPreview: false })).toBe(false);
  });
});
