'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useSyncExternalStore,
  type ReactNode,
} from 'react';
import { locales, messages, t as translate, type Locale, type MessageKey, STORAGE_KEY } from './messages';

interface I18nContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  /** Translate a dot-path key with optional {param} interpolation. */
  t: (key: MessageKey, params?: Record<string, string | number>) => string;
}

export type I18nT = I18nContextValue['t'];

const I18nContext = createContext<I18nContextValue | null>(null);

/**
 * Infer the current locale: persisted choice → RO. RO is the HARD default —
 * the browser language is deliberately ignored (t_5a65abcf user mandate:
 * "never auto-switch to EN"). A user must explicitly click the EN flag to
 * switch; nothing else may flip the UI language.
 */
function detectLocale(): Locale {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === 'ro' || stored === 'en') return stored;
  } catch {
    // localStorage unavailable (private mode / storage blocked) — fall through.
  }
  return 'ro';
}

/* Tiny external store (same no-FOUC pattern ThemeToggle uses for `mounted`):
   the SERVER snapshot is always 'ro' (matches the SSR HTML — no hydration
   mismatch), and the client snapshot re-reads localStorage live.
   useSyncExternalStore swaps to the client value after hydration without a
   mismatch error (unlike a useState initializer that reads localStorage). */
type Listener = () => void;
const listeners = new Set<Listener>();

function subscribe(listener: Listener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function getSnapshot(): Locale {
  return detectLocale();
}

function getServerSnapshot(): Locale {
  return 'ro';
}

function commitLocale(next: Locale): void {
  document.documentElement.lang = next;
  try {
    window.localStorage.setItem(STORAGE_KEY, next);
  } catch {
    // ignore persistence failures — the choice just won't survive reloads.
  }
  listeners.forEach((l) => l());
}

/**
 * Lightweight i18n provider (t_920a7b7b). RO is the SSR default (matches the
 * server-rendered HTML — no hydration mismatch); the persisted locale (RO
 * unless the user explicitly switched) is applied after hydration via
 * useSyncExternalStore and persists on change. Browser language is NEVER
 * auto-detected (t_5a65abcf hard-RO-default mandate).
 */
export function I18nProvider({ children }: { children: ReactNode }) {
  const locale = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  // Sync <html lang> on mount once (the browser-detected locale may differ
  // from the SSR 'ro'); storage writes happen in commitLocale on change.
  useEffect(() => {
    commitLocale(detectLocale());
  }, []);

  const setLocale = useCallback((next: Locale) => {
    if (locales.includes(next)) commitLocale(next);
  }, []);

  const value = useMemo<I18nContextValue>(
    () => ({
      locale,
      setLocale,
      t: (key, params) => translate(locale, key, params),
    }),
    [locale, setLocale],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error('useI18n must be used inside <I18nProvider>');
  return ctx;
}

export { messages };