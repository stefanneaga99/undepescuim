import { describe, expect, it } from 'vitest';
import type { Water } from '@/types/data';
import { dedupePhysicalPreviewWaters, physicalPreviewSelection } from './physical-preview';

const geometry = {
  type: 'LineString' as const,
  coordinates: [[26, 45], [27, 46], [28, 45]],
};

function preview(slug: string, sourceSlug: string, hash = 'shared-buzau') {
  return {
    slug: `class2-preview-${slug}`,
    name: slug,
    judet: slug === 'anpa-anpa-0261' ? 'Covasna' : 'Buzău',
    type: 'ape' as const,
    subtype: 'rau' as const,
    coordinates: [27, 45.5] as [number, number],
    bbox: [26, 45, 28, 46] as [number, number, number, number],
    asociatie: null,
    geometry,
    physicalPreview: true,
    physicalSourceSlug: sourceSlug,
    physicalRiverGroup: 'buzau',
    physicalGeometryHash: hash,
  } satisfies Water;
}

describe('physical preview aliases', () => {
  it('paints one full shared course while retaining every source-record alias', () => {
    const records = dedupePhysicalPreviewWaters([
      preview('anpa-anpa-0214', 'anpa-anpa-0214'),
      preview('anpa-anpa-0261', 'anpa-anpa-0261'),
    ]);

    expect(records).toHaveLength(1);
    expect(records[0].geometry).toEqual(geometry);
    expect(records[0].physicalAliases).toEqual(['anpa-anpa-0214', 'anpa-anpa-0261']);
    expect(physicalPreviewSelection(records[0], 'anpa-anpa-0261')).toBe(true);
    expect(physicalPreviewSelection(records[0], 'anpa-anpa-0214')).toBe(true);
  });

  it('does not merge identical hashes from different river groups', () => {
    const records = dedupePhysicalPreviewWaters([
      preview('buzau', 'anpa-anpa-0214', 'same-hash'),
      preview('other', 'other-water', 'same-hash'),
      { ...preview('other-group', 'other-group', 'same-hash'), physicalRiverGroup: 'other' },
    ]);

    expect(records).toHaveLength(2);
    expect(records.map((record) => record.physicalAliases)).toEqual([
      ['anpa-anpa-0214', 'other-water'],
      ['other-group'],
    ]);
  });
});
