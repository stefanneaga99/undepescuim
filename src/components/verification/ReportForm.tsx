'use client';

import { useState } from 'react';
import { Flag } from 'lucide-react';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { useI18n } from '@/i18n/provider';
import type { ReportReason } from '@/types/data';

const REASON_OPTIONS: { value: ReportReason; labelKey: `report.reasons.${ReportReason}` }[] = [
  { value: 'data_correct', labelKey: 'report.reasons.data_correct' },
  { value: 'water_invalid', labelKey: 'report.reasons.water_invalid' },
  { value: 'association_changed', labelKey: 'report.reasons.association_changed' },
  { value: 'wrong_coordinates', labelKey: 'report.reasons.wrong_coordinates' },
  { value: 'other', labelKey: 'report.reasons.other' },
];

interface ReportFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  waterSlug?: string;
  waterName?: string;
  /** Pre-select a reason when the dialog opens (used by the quick positive-signal tap). */
  initialReason?: ReportReason | null;
}

type Phase = 'idle' | 'submitting' | 'success' | 'error';

export function ReportForm({ open, onOpenChange, waterSlug, waterName, initialReason }: ReportFormProps) {
  const { t } = useI18n();
  const [reason, setReason] = useState<ReportReason | null>(null);
  const [details, setDetails] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [website, setWebsite] = useState(''); // honeypot
  const [phase, setPhase] = useState<Phase>('idle');
  const [issueUrl, setIssueUrl] = useState<string | null>(null);
  const [prevOpen, setPrevOpen] = useState(open);

  // Render-phase adjustment (React docs: "adjusting state when a prop changes"):
  // apply the quick-tap reason each time the dialog opens, without an effect.
  if (open !== prevOpen) {
    setPrevOpen(open);
    if (open && initialReason) setReason(initialReason);
  }

  const reset = () => {
    setReason(null); setDetails(''); setContactEmail(''); setWebsite('');
    setPhase('idle'); setIssueUrl(null);
  };

  const submit = async () => {
    if (!reason) return;
    setPhase('submitting');
    try {
      const res = await fetch('/api/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reason,
          waterSlug: waterSlug ?? '',
          waterName: waterName ?? '',
          details,
          contactEmail,
          website,
        }),
      });
      const data = (await res.json()) as { ok: boolean; issueUrl?: string | null };
      if (data.ok) { setIssueUrl(data.issueUrl ?? null); setPhase('success'); }
      else setPhase('error');
    } catch {
      setPhase('error');
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => { if (!o) reset(); onOpenChange(o); }}
    >
      <DialogContent data-testid="report-dialog" className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{t('report.title')}</DialogTitle>
          <DialogDescription>
            {waterName ? t('report.descriptionWater', { name: waterName }) : t('report.descriptionGeneric')}
          </DialogDescription>
        </DialogHeader>

        {phase === 'success' ? (
          <div className="flex flex-col gap-2 py-2 text-sm">
            <p className="font-medium text-green-700">{t('report.successTitle')}</p>
            <p className="text-muted-foreground">{t('report.successBody')}</p>
            {issueUrl && (
              <a href={issueUrl} target="_blank" rel="noopener noreferrer" className="text-primary underline">
                {t('report.viewIssue')}
              </a>
            )}
            <Button className="mt-2" onClick={() => { reset(); onOpenChange(false); }}>{t('report.cancel')}</Button>
          </div>
        ) : (
          <form
            className="flex flex-col gap-4"
            onSubmit={(e) => { e.preventDefault(); void submit(); }}
          >
            <fieldset className="flex flex-col gap-2">
              <legend className="text-sm font-medium">{t('report.reasonLegend')}</legend>
              {REASON_OPTIONS.map((opt) => (
                <label
                  key={opt.value}
                  data-testid="report-reason"
                  data-value={opt.value}
                  className="flex items-center gap-2 text-sm"
                >
                  <input
                    type="radio"
                    name="reason"
                    value={opt.value}
                    checked={reason === opt.value}
                    onChange={() => setReason(opt.value)}
                    className="size-4"
                  />
                  {t(opt.labelKey)}
                </label>
              ))}
            </fieldset>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="report-details">{t('report.detailsLabel')}</Label>
              <Textarea
                id="report-details"
                value={details}
                onChange={(e) => setDetails(e.target.value)}
                placeholder={t('report.detailsPlaceholder')}
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="report-email">{t('report.emailLabel')}</Label>
              <Input
                id="report-email"
                type="email"
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
                placeholder={t('report.emailPlaceholder')}
              />
              {/* REM-4: explicit consent notice — the address is published in a
                  PUBLIC GitHub issue when provided. */}
              <p className="text-xs text-muted-foreground">
                {t('report.consent')}
              </p>
            </div>

            {/* honeypot — hidden from humans, filled by bots */}
            <input
              type="text"
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
              tabIndex={-1}
              autoComplete="off"
              className="hidden"
              aria-hidden
            />

            {phase === 'error' && (
              <p className="text-sm text-destructive">{t('report.error')}</p>
            )}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>{t('report.cancel')}</Button>
              <Button type="submit" disabled={!reason || phase === 'submitting'}>
                <Flag className="size-4" />
                {phase === 'submitting' ? t('report.submitting') : t('report.submit')}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
