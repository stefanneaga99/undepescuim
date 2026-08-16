// @vitest-environment node
import { describe, it, expect } from 'vitest';
import { NATIONAL_PERMIT_URL, NATIONAL_PERMIT_LABEL } from '@/lib/permit';

describe('national permit constant', () => {
  it('points at the ANADSPA portal (guards accidental edits)', () => {
    expect(NATIONAL_PERMIT_URL).toBe('https://permise.anpa.ro/portal-public/permis');
  });

  it('has a descriptive Romanian label', () => {
    expect(NATIONAL_PERMIT_LABEL).toContain('Permis național');
  });
});