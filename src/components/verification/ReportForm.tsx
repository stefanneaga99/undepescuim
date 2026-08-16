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
import type { ReportReason } from '@/types/data';

const REASON_OPTIONS: { value: ReportReason; label: string }[] = [
  { value: 'data_correct', label: 'Datele sunt corecte (am pescuit aici)' },
  { value: 'water_invalid', label: 'Această apă nu mai există / nu se poate pescui' },
  { value: 'association_changed', label: 'Asociația s-a schimbat' },
  { value: 'wrong_coordinates', label: 'Coordonatele sunt greșite' },
  { value: 'other', label: 'Altă problemă' },
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
          <DialogTitle>Raportează o problemă</DialogTitle>
          <DialogDescription>
            {waterName ? <>Raportezi date pentru <strong>{waterName}</strong>.</> : 'Ajută-ne să ținem harta corectă.'}
          </DialogDescription>
        </DialogHeader>

        {phase === 'success' ? (
          <div className="flex flex-col gap-2 py-2 text-sm">
            <p className="font-medium text-green-700">Mulțumim! Raportul a fost trimis.</p>
            <p className="text-muted-foreground">Îl verificăm în cel mult 7 zile și actualizăm datele.</p>
            {issueUrl && (
              <a href={issueUrl} target="_blank" rel="noopener noreferrer" className="text-primary underline">
                Vezi raportul pe GitHub
              </a>
            )}
            <Button className="mt-2" onClick={() => { reset(); onOpenChange(false); }}>Închide</Button>
          </div>
        ) : (
          <form
            className="flex flex-col gap-4"
            onSubmit={(e) => { e.preventDefault(); void submit(); }}
          >
            <fieldset className="flex flex-col gap-2">
              <legend className="text-sm font-medium">Motivul raportului</legend>
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
                  {opt.label}
                </label>
              ))}
            </fieldset>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="report-details">Detalii (opțional)</Label>
              <Textarea
                id="report-details"
                value={details}
                onChange={(e) => setDetails(e.target.value)}
                placeholder="Descrie ce e greșit, ce ai observat la fața locului…"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="report-email">Email (opțional, pentru clarificări)</Label>
              <Input
                id="report-email"
                type="email"
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
                placeholder="tu@exemplu.ro"
              />
              {/* REM-4: explicit consent notice — the address is published in a
                  PUBLIC GitHub issue when provided. */}
              <p className="text-xs text-muted-foreground">
                Dacă îl completezi, adresa va fi vizibilă în raportul public de pe GitHub.
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
              <p className="text-sm text-destructive">Nu am putut trimite raportul. Încearcă din nou.</p>
            )}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Anulează</Button>
              <Button type="submit" disabled={!reason || phase === 'submitting'}>
                <Flag className="size-4" />
                {phase === 'submitting' ? 'Se trimite…' : 'Trimite raportul'}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
