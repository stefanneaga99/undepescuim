'use client';

import type { Association } from '@/types/data';

/**
 * Permit-validity statement (F2a, docs/f2a-permit-validity.md §4 step 4).
 *
 * Renders the "Permisul {X} este valabil pe N ape în județele: ..." sentence
 * plus the reciprocity status line. Pure presentational — data comes from
 * the association record (counties computed by scripts/recompute_assoc_validity.py).
 */
export function AssociationValidity({ association }: { association: Association }) {
  const n = association.ape ?? 0;
  const counties = association.counties ?? [];
  const reciprocity = association.reciprocity ?? 'neconfirmată';

  // TODO(i18n): hardcoded RO strings — next-intl is a documented follow-up milestone.
  if (n === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Asociația nu are ape contractate afișate pe site.
      </p>
    );
  }

  const isAnpa = association.slug === 'anpa';

  return (
    <div className="flex flex-col gap-2 text-sm">
      <p>
        Permisul <strong>{association.name}</strong> este valabil pe{' '}
        <strong>
          {n} {n === 1 ? 'apă' : 'ape'}
        </strong>
        {!isAnpa && counties.length > 0 && (
          <>
            {' '}
            în județele: <strong>{counties.join(', ')}</strong>
          </>
        )}
        {isAnpa && (
          <>
            {' '}
            administrate direct de ANPA / necontractate
          </>
        )}
        .
      </p>
      {association.contract_ref && (
        <p className="text-xs text-muted-foreground">Contract: {association.contract_ref}</p>
      )}
      {reciprocity === 'confirmată' ? (
        <p className="text-xs text-muted-foreground">Reciprocitate: confirmată.</p>
      ) : (
        <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-relaxed text-amber-900">
          <p>
            Reciprocitate: <strong>neconfirmată</strong> — nu am găsit o sursă publică care să
            confirme că permisul acestei asociații este acceptat și de alte asociații. Legea
            prevede valabilitatea pe bază de reciprocitate între asociațiile afiliate AGVPS;
            verifică cu asociația înainte de a pescui.
          </p>
        </div>
      )}
    </div>
  );
}
