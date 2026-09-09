'use client';

import { useEffect, useState } from 'react';
import { Database } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { useI18n } from '@/i18n/provider';
import { disableOffline, getOfflinePreference, registerOfflineServiceWorker, setOfflinePreference, type OfflinePreference } from '@/lib/offline-preferences';

export function OfflineControls() {
  const { t } = useI18n();
  const [preference, setPreference] = useState<OfflinePreference>('unknown');
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const update = () => setPreference(getOfflinePreference());
    update();
    window.addEventListener('offline-preference-change', update);
    return () => window.removeEventListener('offline-preference-change', update);
  }, []);

  const enable = () => {
    setOfflinePreference('enabled');
    setPreference('enabled');
    void registerOfflineServiceWorker();
    setOpen(false);
  };
  const disable = async () => {
    await disableOffline();
    setPreference('disabled');
    setOpen(false);
  };

  return (
    <>
      {preference === 'unknown' && (
        <div role="region" aria-label={t('privacy.offlineTitle')} data-testid="offline-choice" className="fixed bottom-3 left-3 z-[1250] max-w-[min(28rem,calc(100vw-1.5rem))] rounded-lg border bg-background p-3 text-xs shadow-lg">
          <p className="font-semibold">{t('privacy.offlineTitle')}</p>
          <p className="mt-1 text-muted-foreground">{t('privacy.offlineDescription')}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <Button type="button" size="sm" onClick={enable}>{t('privacy.enableOffline')}</Button>
            <Button type="button" size="sm" variant="outline" onClick={() => { setOfflinePreference('disabled'); setPreference('disabled'); }}>{t('privacy.continueOnline')}</Button>
          </div>
        </div>
      )}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <Button type="button" variant="ghost" size="icon-sm" aria-label={t('privacy.preferences')} title={t('privacy.preferences')} data-testid="offline-preferences"><Database className="h-4 w-4" /></Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader><DialogTitle>{t('privacy.preferences')}</DialogTitle><DialogDescription>{t('privacy.offlineDescription')}</DialogDescription></DialogHeader>
          <p className="text-sm">{preference === 'enabled' ? t('privacy.offlineEnabled') : t('privacy.offlineDisabled')}</p>
          <DialogFooter>
            {preference === 'enabled' ? <Button type="button" variant="destructive" onClick={() => void disable()} data-testid="disable-offline">{t('privacy.disableOffline')}</Button> : <Button type="button" onClick={enable}>{t('privacy.enableOffline')}</Button>}
            <DialogClose asChild><Button type="button" variant="outline">{t('common.close')}</Button></DialogClose>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
