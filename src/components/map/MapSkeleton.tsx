'use client';

/** Loading state while /data/*.json is fetched (map-state-data-flow §7.1). */
import { useI18n } from '@/i18n/provider';

export function MapSkeleton() {
  const { t } = useI18n();
  return (
    <div className="flex h-full w-full animate-pulse items-center justify-center bg-muted/40">
      <span className="text-sm text-muted-foreground">{t('map.loading')}</span>
    </div>
  );
}
