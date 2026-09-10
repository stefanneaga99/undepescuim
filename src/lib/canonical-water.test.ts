import { describe, expect, it } from 'vitest';
import { canonicalWater } from './canonical-water';

describe('canonical report water identity', () => {
  it('accepts the exact canonical Romanian name including punctuation', () => {
    expect(canonicalWater('zyvryyuz', 'Acumularea Curtești (Rai)')).toMatchObject({ slug: 'zyvryyuz', name: 'Acumularea Curtești (Rai)' });
  });

  it('rejects invented identifiers and mismatched names', () => {
    expect(canonicalWater('invented-water', 'A apă')).toBeNull();
    expect(canonicalWater('zyvryyuz', 'A apă')).toBeNull();
  });
});
