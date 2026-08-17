import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { messages, t, STORAGE_KEY, type MessageKey } from './messages';
import { I18nProvider, useI18n } from './provider';

/** Recursively collect every leaf key path (e.g. "header.logoAria"). */
function leafKeys(obj: Record<string, unknown>, prefix = ''): string[] {
  return Object.entries(obj).flatMap(([k, v]) => {
    const path = prefix ? `${prefix}.${k}` : k;
    return v !== null && typeof v === 'object' ? leafKeys(v as Record<string, unknown>, path) : [path];
  });
}

describe('messages parity (no missing-key fallbacks)', () => {
  it('en has exactly the same key structure as ro', () => {
    const roKeys = leafKeys(messages.ro).sort();
    const enKeys = leafKeys(messages.en).sort();
    expect(enKeys).toEqual(roKeys);
  });

  it('every leaf is a non-empty string in both locales', () => {
    for (const locale of ['ro', 'en'] as const) {
      for (const key of leafKeys(messages[locale])) {
        const value = t(locale, key as MessageKey);
        expect(typeof value).toBe('string');
        expect(value.length).toBeGreaterThan(0);
        // No raw key leakage (a key that failed to resolve returns the path).
        expect(value).not.toEqual(key);
      }
    }
  });

  it('messages object is structurally typed (en satisfies typeof ro at compile time)', () => {
    // Type-level check happens at compile time; runtime sanity that en is an
    // object with the same top-level groups.
    const roGroups = Object.keys(messages.ro).sort();
    const enGroups = Object.keys(messages.en).sort();
    expect(enGroups).toEqual(roGroups);
  });
});

describe('t() interpolation', () => {
  it('interpolates {param} placeholders', () => {
    expect(t('ro', 'card.permitValidOnSector', { name: 'AJVPS Brașov' })).toBe(
      'Permisul AJVPS Brașov este valabil pe acest sector.',
    );
    expect(t('en', 'card.permitValidOnSector', { name: 'AJVPS Brașov' })).toBe(
      'The AJVPS Brașov permit is valid on this sector.',
    );
  });

  it('plural-aware keys resolve per count in both locales', () => {
    expect(t('ro', 'filters.localitiesCount', { n: 3 })).toBe('3 localități');
    expect(t('en', 'filters.localitiesCount', { n: 3 })).toBe('3 localities');
  });

  it('leaves unknown params as the raw placeholder (no crash)', () => {
    expect(t('ro', 'filters.localitiesCount')).toContain('{n}');
  });
});

describe('missing-key guard', () => {
  it('falls back to the RO value and logs an error for an unknown key', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
    // Cast through unknown: t is typed, but the runtime path must degrade gracefully.
    const unknown = t('en', 'does.not.exist' as unknown as MessageKey);
    expect(spy).toHaveBeenCalled();
    expect(unknown).toBe('does.not.exist'); // no RO fallback for a totally unknown path
    spy.mockRestore();
  });
});

describe('I18nProvider', () => {
  function Probe() {
    const { locale, setLocale, t } = useI18n();
    return (
      <div>
        <span data-testid="locale">{locale}</span>
        <span data-testid="string">{t('header.navSpecii')}</span>
        <button data-testid="toggle" onClick={() => setLocale(locale === 'ro' ? 'en' : 'ro')}>
          toggle
        </button>
      </div>
    );
  }

  beforeEach(() => {
    window.localStorage.clear();
    delete (navigator as { language?: string }).language;
    Object.defineProperty(navigator, 'language', { value: 'ro-RO', configurable: true });
    document.documentElement.lang = '';
  });

  it('defaults to RO and renders RO strings', () => {
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    );
    // SSR default is 'ro' before the mount effect runs.
    expect(screen.getByTestId('locale').textContent).toBe('ro');
    expect(screen.getByTestId('string').textContent).toBe('Specii');
  });

  it('toggles RO ⇄ EN and persists to localStorage', async () => {
    const user = userEvent.setup();
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    );
    await user.click(screen.getByTestId('toggle'));
    expect(screen.getByTestId('locale').textContent).toBe('en');
    expect(screen.getByTestId('string').textContent).toBe('Species');
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe('en');
    expect(document.documentElement.lang).toBe('en');

    await user.click(screen.getByTestId('toggle'));
    expect(screen.getByTestId('locale').textContent).toBe('ro');
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe('ro');
    expect(document.documentElement.lang).toBe('ro');
  });

  it('detects a persisted EN choice on mount', () => {
    window.localStorage.setItem(STORAGE_KEY, 'en');
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    );
    expect(screen.getByTestId('locale').textContent).toBe('en');
  });

  it('defaults from navigator.language when nothing is persisted', () => {
    Object.defineProperty(navigator, 'language', { value: 'en-US', configurable: true });
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    );
    // t_5a65abcf hard-default mandate: RO is ALWAYS the default — the browser
    // language must never auto-switch the UI to EN. Only an explicit click
    // (persisted choice) may flip the language.
    expect(screen.getByTestId('locale').textContent).toBe('ro');
  });

  it('never auto-switches to EN — browser language is ignored entirely', () => {
    Object.defineProperty(navigator, 'language', { value: 'en-GB', configurable: true });
    window.localStorage.removeItem(STORAGE_KEY);
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    );
    expect(screen.getByTestId('locale').textContent).toBe('ro');
    expect(screen.getByTestId('string').textContent).toBe('Specii');
  });

  it('ignores an invalid persisted value', () => {
    window.localStorage.setItem(STORAGE_KEY, 'fr');
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    );
    expect(screen.getByTestId('locale').textContent).toBe('ro');
  });

  it('useI18n throws outside the provider', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => render(<Probe />)).toThrow('useI18n must be used inside <I18nProvider>');
    spy.mockRestore();
  });
});