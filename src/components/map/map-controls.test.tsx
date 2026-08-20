import type { ReactElement, ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen } from '@testing-library/react';
import { ColorLegend } from './ColorLegend';
import { MapSkeleton } from './MapSkeleton';
import { SheetGrabber } from '@/components/ui/sheet-grabber';
import { I18nProvider } from '@/i18n/provider';

const store = {
  selectedAssociationSlug: null as string | null,
  contractFilter: 'all' as string,
};

vi.mock('@/stores/map-store', () => ({
  useMapStore: (selector: (state: typeof store) => unknown) => selector(store),
}));

vi.mock('vaul', () => ({
  Drawer: {
    Handle: ({ children, ...props }: { children: ReactNode }) => (
      <button data-vaul-handle="" data-vaul-handle-hitarea="" {...props} type="button">
        {children}
      </button>
    ),
  },
}));

function renderWithI18n(ui: ReactElement) {
  return render(<I18nProvider>{ui}</I18nProvider>);
}

describe('map control regressions', () => {
  beforeEach(() => {
    store.selectedAssociationSlug = null;
    store.contractFilter = 'all';
  });

  it('renders the neutral and uncontracted legend rows, and mobile expansion auto-collapses', async () => {
    vi.useFakeTimers();
    renderWithI18n(<ColorLegend />);

    const toggle = screen.getByRole('button', { name: 'Legendă culori' });
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    act(() => fireEvent.click(toggle));
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getAllByText('Vedere neutră')).toHaveLength(2);
    expect(screen.getAllByText('Râuri necontractate')).toHaveLength(2);
    expect(screen.getAllByText('Bălți / iazuri necontractate')).toHaveLength(2);

    act(() => vi.advanceTimersByTime(5000));
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    vi.useRealTimers();
  });

  it('switches legend rows for association coverage and contract filter', async () => {
    store.selectedAssociationSlug = 'asociatia-alpha';
    store.contractFilter = 'contractate';
    renderWithI18n(<ColorLegend />);

    expect(screen.getByText('Acoperit')).toBeInTheDocument();
    expect(screen.getByText('Neacoperit')).toBeInTheDocument();
    expect(screen.queryByText('Necontractate')).not.toBeInTheDocument();
  });

  it('exposes the loading status contract used before the mounted map settles', () => {
    renderWithI18n(<MapSkeleton />);
    const status = screen.getByRole('status');
    expect(status).toHaveAttribute('aria-busy', 'true');
    expect(status).toHaveTextContent('Se încarcă harta');
  });

  it('keeps the sheet grabber as a full-width handle target', () => {
    render(<SheetGrabber />);
    const handle = document.querySelector('[data-vaul-handle]');
    expect(handle).toHaveAttribute('data-vaul-handle-hitarea', '');
    expect(handle).toHaveClass('shrink-0');
  });
});
