import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MapAttribution } from './MapAttribution';

describe('MapAttribution', () => {
  it('keeps a legible OSM copyright link visible in every map state', () => {
    render(<MapAttribution />);
    const link = screen.getByRole('link', { name: /openstreetmap/i });
    expect(link).toHaveAttribute('href', 'https://www.openstreetmap.org/copyright');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveClass('underline');
  });
});
