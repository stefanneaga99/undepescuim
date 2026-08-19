'use client';

import { ExternalLink, Mail, MapPin, Phone } from 'lucide-react';
import { useI18n } from '@/i18n/provider';
import { safeEmail, safeExternalUrl, safeTelephone } from '@/lib/safe-url';
import type { AssociationLocation, AssociationLocationType } from '@/types/data';

const TYPE_KEYS: Record<AssociationLocationType, 'headquarters' | 'registeredOffice' | 'branch' | 'office' | 'clubContactPoint' | 'permitPickupPoint' | 'partnerLocation'> = {
  headquarters: 'headquarters', registered_office: 'registeredOffice', branch: 'branch', office: 'office',
  club_contact_point: 'clubContactPoint', permit_pickup_point: 'permitPickupPoint', partner_location: 'partnerLocation',
};

function contact(location: AssociationLocation, kind: 'phone' | 'email' | 'url') {
  return location.contacts?.find((item) => item.kind === kind)?.value;
}

export function AssociationLocations({ locations }: { locations?: AssociationLocation[] }) {
  const { t } = useI18n();
  const visibleLocations = locations ?? [];
  return (
    <section className="border-t pt-3" data-testid="association-locations">
      <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">{t('assoc.locationsTitle')}</h3>
      {visibleLocations.length === 0 ? <p className="text-sm text-muted-foreground">{t('assoc.noLocations')}</p> : (
        <ul className="flex flex-col gap-3" aria-label={t('assoc.locationsTitle')}>
          {visibleLocations.map((location) => {
            const phone = contact(location, 'phone'); const email = contact(location, 'email'); const site = contact(location, 'url');
            const source = location.sources[0]; const typeLabel = t(`assoc.locationTypes.${TYPE_KEYS[location.type]}`);
            return (
              <li key={location.id} className="rounded-md border px-3 py-2 text-sm">
                <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5"><p className="font-medium">{location.label || typeLabel}</p><span className="text-xs text-muted-foreground">{typeLabel}</span></div>
                <p className="mt-1 flex items-start gap-2 text-muted-foreground"><MapPin aria-hidden className="mt-0.5 h-3.5 w-3.5 shrink-0" /><span>{location.address}, {location.locality}, {location.county}</span></p>
                {safeTelephone(phone) && <a aria-label={`${t('assoc.phone')}: ${phone}`} href={safeTelephone(phone)!} className="mt-1 flex items-center gap-2 text-primary hover:underline"><Phone aria-hidden className="h-3.5 w-3.5 shrink-0" />{phone}</a>}
                {safeEmail(email) && <a aria-label={`${t('assoc.email')}: ${email}`} href={safeEmail(email)!} className="mt-1 flex items-center gap-2 text-primary hover:underline"><Mail aria-hidden className="h-3.5 w-3.5 shrink-0" />{email}</a>}
                {safeExternalUrl(site) && <a aria-label={`${t('assoc.site')}: ${site}`} href={safeExternalUrl(site)!} target="_blank" rel="noopener noreferrer" className="mt-1 inline-flex items-center gap-1 text-primary hover:underline"><ExternalLink aria-hidden className="h-3.5 w-3.5" />{t('assoc.site')}</a>}
                <div className="mt-2 flex flex-wrap gap-x-2 gap-y-1 text-xs text-muted-foreground"><span>{t(`assoc.freshness.${location.freshness}`)}</span>{location.freshness === 'needs_confirmation' && <span>{t('assoc.needsConfirmation')}</span>}{safeExternalUrl(source?.url) && <a href={safeExternalUrl(source.url)!} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">{t('assoc.source')}</a>}</div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
