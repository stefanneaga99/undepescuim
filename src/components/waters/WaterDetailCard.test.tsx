import { afterEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import type { Water } from '@/types/data';
import { I18nProvider } from '@/i18n/provider';

const evidence = vi.fn();
vi.mock('@/hooks/use-sector-evidence', () => ({ useSectorEvidence: () => evidence() }));

import { WaterDetailCard } from './WaterDetailCard';

const water = {
  slug: 'pre', name: 'Râul Geoagiu Inferior', judet: 'Alba', type: 'ape', subtype: 'rau',
  limite: 'Cheile Râmet - conf. Cu Råul Mureş', dimensiune: '28 km', coordinates: [23.4, 46.1],
  bbox: [23.3, 46.0, 23.5, 46.2], asociatie: null, geometryKind: 'sector', sectorStatus: 'resolved',
} as unknown as Water;

const entry = (over = {}) => ({
  from: { kind: 'LOCALITY', label: 'Râmeț', anchor: { type: 'node', id: 1 }, confidence: 0.7 },
  to: { kind: 'CONFLUENCE', label: 'confluența cu Mureș', anchor: { type: 'course', id: 'rel:9' }, confidence: 0.95 },
  lengthKm: 27.5, contractKm: 28, status: 'resolved', confidence: 'medium',
  ...over,
});

function renderCard(onReport = vi.fn()) {
  render(<I18nProvider><WaterDetailCard water={water} association={null} onReport={onReport} /></I18nProvider>);
  return onReport;
}

afterEach(() => evidence.mockReset());

describe('WaterDetailCard — sector limits (T4.3)', () => {
  it('resolved sector: from/to labels, drawn vs contract km, how-we-know and report', () => {
    evidence.mockReturnValue({ entry: entry(), osmDate: '2026-10-16' });
    const onReport = renderCard();
    const block = screen.getByTestId('sector-limits');
    expect(block).toHaveTextContent('Limitele sectorului');
    expect(screen.getByTestId('sector-limits-from')).toHaveTextContent('Râmeț');
    expect(screen.getByTestId('sector-limits-to')).toHaveTextContent('confluența cu Mureș');
    expect(screen.getByTestId('sector-limits-km')).toHaveTextContent('27.5 km desenați / 28 km în contract');
    expect(block).toHaveTextContent('Încredere: medie');
    expect(block).toHaveTextContent('OpenStreetMap (2026-10-16)');
    expect(block).not.toHaveTextContent('Limite de verificat');
    fireEvent.click(screen.getByTestId('report-wrong-sector'));
    expect(onReport).toHaveBeenCalledWith('wrong_sector');
  });

  it('review sector: flagged, contract km unknown, no OSM date', () => {
    evidence.mockReturnValue({ entry: entry({ status: 'review', confidence: 'low', contractKm: null }), osmDate: null });
    renderCard();
    const block = screen.getByTestId('sector-limits');
    expect(block).toHaveTextContent('Limite de verificat');
    expect(screen.getByTestId('sector-limits-km')).toHaveTextContent('27.5 km desenați');
    expect(block).not.toHaveTextContent('OpenStreetMap');
    expect(block).toHaveTextContent('Încredere: scăzută');
  });

  it('missing evidence hides the block; the legal limite text still shows', () => {
    evidence.mockReturnValue(null);
    renderCard();
    expect(screen.queryByTestId('sector-limits')).toBeNull();
    expect(screen.getByText('Cheile Râmet - conf. Cu Råul Mureş')).toBeInTheDocument();
  });

  it('no drawn length hides the km line', () => {
    evidence.mockReturnValue({ entry: entry({ lengthKm: null }), osmDate: null });
    renderCard();
    expect(screen.queryByTestId('sector-limits-km')).toBeNull();
  });
});
