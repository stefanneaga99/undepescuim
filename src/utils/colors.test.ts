// @vitest-environment node
import { describe, it, expect } from 'vitest';
import {
  getFeatureStyle,
  getPointFallbackStyle,
  getUncontractedStyle,
  getUncontractedLakeStyle,
  NEUTRAL_COLOR,
  COVERED_COLOR,
  UNCOVERED_COLOR,
  FOCUS_COLOR,
  UNCONTRACTED_COLOR,
  UNCONTRACTED_LAKE_COLOR,
  UNCONTRACTED_LAKE_FILL,
  POINT_FALLBACK_COLOR,
} from '@/utils/colors';

describe('color constants', () => {
  it('exports the 8 documented colors', () => {
    expect(NEUTRAL_COLOR).toBe('#3b82f6');
    expect(COVERED_COLOR).toBe('#22c55e');
    expect(UNCOVERED_COLOR).toBe('#9ca3af');
    expect(FOCUS_COLOR).toBe('#f97316');
    expect(UNCONTRACTED_COLOR).toBe('#14b8a6');
    expect(UNCONTRACTED_LAKE_COLOR).toBe('#2dd4bf');
    expect(UNCONTRACTED_LAKE_FILL).toBe('#14b8a6');
    expect(POINT_FALLBACK_COLOR).toBe('#8b5cf6');
  });
});

describe('getFeatureStyle', () => {
  it('returns neutral blue when no association is selected (coverageSlug null)', () => {
    const s = getFeatureStyle('assoc-1', null);
    expect(s.color).toBe('#3b82f6');
    expect(s.weight).toBe(2);
  });

  it('returns strong green when the feature belongs to the selected association', () => {
    const s = getFeatureStyle('assoc-1', 'assoc-1');
    expect(s.color).toBe('#22c55e');
    expect(s.weight).toBe(4);
  });

  it('dims everything else when an association is selected', () => {
    const s = getFeatureStyle('assoc-2', 'assoc-1');
    expect(s.color).toBe('#9ca3af');
    expect(s.weight).toBe(1);
    expect(s.opacity).toBe(0.35);
  });

  it('dims features with no association when an association is selected', () => {
    const s = getFeatureStyle(null, 'assoc-1');
    expect(s.color).toBe('#9ca3af');
  });
});

describe('getPointFallbackStyle', () => {
  it('uses the violet dot when neutral', () => {
    const s = getPointFallbackStyle('a', null);
    expect(s.color).toBe(POINT_FALLBACK_COLOR);
  });

  it('green dot for a covered bbox-fallback water', () => {
    const s = getPointFallbackStyle('a', 'a');
    expect(s.color).toBe(COVERED_COLOR);
  });

  it('grey dot for an uncovered bbox-fallback water', () => {
    const s = getPointFallbackStyle(null, 'a');
    expect(s.color).toBe(UNCOVERED_COLOR);
  });
});

describe('uncontracted styles', () => {
  it('river overlay: thin dashed teal', () => {
    const s = getUncontractedStyle();
    expect(s.color).toBe(UNCONTRACTED_COLOR);
    expect(s.weight).toBe(1.5);
    expect(s.dashArray).toBe('4 4');
  });

  it('lake overlay: teal outline + light fill', () => {
    const s = getUncontractedLakeStyle();
    expect(s.color).toBe(UNCONTRACTED_LAKE_COLOR);
    expect(s.fillColor).toBe(UNCONTRACTED_LAKE_FILL);
    expect(s.fillOpacity).toBe(0.25);
  });
});