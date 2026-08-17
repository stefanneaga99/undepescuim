'use client';

import { useI18n } from '@/i18n/provider';
import type { Association } from '@/types/data';

/**
 * Permit-validity statement (F2a, docs/f2a-permit-validity.md §4 step 4).
 *
 * Renders the "Permisul {X} este valabil pe N ape în județele: ..." sentence
 * plus the reciprocity status line. Pure presentational — data comes from
 * the association record (counties computed by scripts/recompute_assoc_validity.py).
 * Text is i18n-driven (t_920a7b7b).
 */
export function AssociationValidity({ association }: { association: Association }) {
  const { t } = useI18n();
  const n = association.ape ?? 0;
  const counties = association.counties ?? [];
  const reciprocity = association.reciprocity ?? 'neconfirmată';

  if (n === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        {t('validity.noWaters')}
      </p>
    );
  }

  const isAnpa = association.slug === 'anpa';

  return (
    <div className="flex flex-col gap-2 text-sm">
      <p>
        {t('validity.validPrefix', { name: association.name })}{' '}
        <strong>
          {n} {n === 1 ? t('validity.oneWater') : t('validity.manyWaters')}
        </strong>
        {!isAnpa && counties.length > 0 && (
          <>
            {' '}
            {t('validity.inCounties')} <strong>{counties.join(', ')}</strong>
          </>
        )}
        {isAnpa && (
          <>
            {' '}
            {t('validity.anpaDirect')}
          </>
        )}
        .
      </p>
      {association.contract_ref && (
        <p className="text-xs text-muted-foreground">{t('validity.contract', { ref: association.contract_ref })}</p>
      )}
      {reciprocity === 'confirmată' ? (
        <p className="text-xs text-muted-foreground">{t('validity.reciprocityConfirmed')}</p>
      ) : (
        <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-relaxed text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
          <p>
            {t('validity.reciprocityUnconfirmedTitle')}{' '}
            {t('validity.reciprocityUnconfirmedBody')}
          </p>
        </div>
      )}
    </div>
  );
}