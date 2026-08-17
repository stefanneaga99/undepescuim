'use client';

import { useEffect, useRef, useState } from 'react';
import { Crosshair, ExternalLink, Loader2 } from 'lucide-react';
import { useGeolocation } from '@/hooks/use-geolocation';
import { useMapStore } from '@/stores/map-store';
import { useI18n } from '@/i18n/provider';
import { cn } from '@/lib/utils';

/**
 * "Localizează-mă" FAB — geolocation MVP (docs/geolocation-feasibility.md
 * §7.1 `LocateButton`). Opt-in, never fires on load. One-shot
 * getCurrentPosition via useGeolocation; on success the fix is pushed into
 * the store (applyUserPosition recomputes nearest waters + adaptive radius),
 * on deny/timeout a graceful localized bubble shows and the map is untouched.
 *
 * Position: bottom-left, floating above the open bottom sheet via the same
 * --sheet-snap-h trick ColorLegend uses (avoids the bottom-right legend and
 * the top filter bar on both breakpoints).
 */

function isIOS() {
  if (typeof navigator === 'undefined') return false;
  return /iPhone|iPad|iPod/.test(navigator.userAgent);
}

export function LocateButton() {
  const { state, locate } = useGeolocation();
  const applyUserPosition = useMapStore((s) => s.applyUserPosition);
  const { t } = useI18n();
  const [dismissed, setDismissed] = useState(false);
  const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const granted = state.status === 'granted';
  const requesting = state.status === 'requesting';
  const denied = state.status === 'denied';
  const errored = state.status === 'error';
  const showBubble = (denied || errored) && !dismissed;

  // Push the granted fix into the store (nearest waters recompute).
  // (dismissed is reset in onLocate, not here — no setState in effects.)
  useEffect(() => {
    if (state.status !== 'granted') return;
    applyUserPosition({ lat: state.lat, lon: state.lon, accuracy: state.accuracy });
  }, [state, applyUserPosition]);

  // Auto-dismiss the deny/error bubble after a few seconds.
  useEffect(() => {
    if (!showBubble) return;
    if (hideTimer.current) clearTimeout(hideTimer.current);
    hideTimer.current = setTimeout(() => setDismissed(true), 6000);
    return () => {
      if (hideTimer.current) clearTimeout(hideTimer.current);
    };
  }, [showBubble]);

  const onLocate = () => {
    setDismissed(false);
    locate();
  };

  return (
    <div
      className="absolute left-3 z-[1000] flex flex-col items-start gap-2"
      style={{ bottom: 'calc(var(--sheet-snap-h, 0vh) + 16px)' }}
    >
      {showBubble && (
        <div
          role="status"
          data-testid="geolocation-bubble"
          className="max-w-[240px] rounded-lg border bg-background/95 px-3 py-2 text-xs shadow-md backdrop-blur"
        >
          {denied ? (
            <>
              <p className="font-medium">{t('locate.deniedTitle')}</p>
              <p className="mt-0.5 text-muted-foreground">
                {isIOS() ? t('locate.deniedIos') : t('locate.deniedDefault')}
              </p>
              {isIOS() && (
                <a
                  href="App-Prefs:Privacy?path=LOCATION"
                  className="mt-1 inline-flex items-center gap-1 font-medium text-primary hover:underline"
                >
                  {t('locate.openIosSettings')}
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </>
          ) : (
            <>
              <p className="font-medium">{t('locate.errorTitle')}</p>
              <p className="mt-0.5 text-muted-foreground">{t('locate.errorBody')}</p>
            </>
          )}
        </div>
      )}

      <button
        type="button"
        onClick={onLocate}
        disabled={requesting}
        aria-label={t('locate.ariaLabel')}
        data-testid="locate-button"
        className={cn(
          'map-touch inline-flex items-center gap-2 rounded-full border bg-background/95 py-2 pl-3 pr-3.5 text-sm font-medium shadow-md backdrop-blur transition-colors hover:bg-accent disabled:opacity-70',
          granted && 'text-primary',
        )}
      >
        {requesting ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Crosshair className={cn('h-4 w-4', granted ? 'text-primary' : 'text-muted-foreground')} />
        )}
        <span>{granted ? t('locate.positionSet') : t('locate.locate')}</span>
      </button>
    </div>
  );
}
