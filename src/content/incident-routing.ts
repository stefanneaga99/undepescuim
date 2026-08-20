/**
 * Verified incident-routing contacts. This is deliberately separate from the
 * ANADSPA permit content: ANPA is the verified non-urgent fisheries-report
 * contact, while GNM's county directory remains the source of local numbers.
 */
export type IncidentKind = 'poaching' | 'pollution' | 'illegal_gear_or_sale';
export type Urgency = 'active_emergency' | 'non_urgent';

export interface OfficialContact {
  authority: '112' | 'ANPA' | 'GNM';
  label: string;
  phone?: string;
  telephoneHref?: `tel:${string}`;
  email?: string;
  emailHref?: `mailto:${string}`;
  url?: string;
  role: 'primary' | 'fallback' | 'directory' | 'secondary';
  verifiedAt: '2026-08-20';
  sourceUrl: string;
}

export interface IncidentRoute {
  kind: IncidentKind;
  urgency: Urgency;
  contactIds: string[];
}

export const OFFICIAL_CONTACTS: Record<string, OfficialContact> = {
  emergency112: { authority: '112', label: 'Serviciul de urgență 112', phone: '112', telephoneHref: 'tel:112', role: 'primary', verifiedAt: '2026-08-20', sourceUrl: 'https://sts.ro/ro/servicii/despre-112/' },
  anpaOne: { authority: 'ANPA', label: 'Agenția Națională pentru Pescuit și Acvacultură', phone: '0374 466 139', telephoneHref: 'tel:0374466139', role: 'primary', verifiedAt: '2026-08-20', sourceUrl: 'https://www.anpa.ro/?p=1949' },
  anpaTwo: { authority: 'ANPA', label: 'Agenția Națională pentru Pescuit și Acvacultură', phone: '0374 466 140', telephoneHref: 'tel:0374466140', role: 'primary', verifiedAt: '2026-08-20', sourceUrl: 'https://www.anpa.ro/?p=1949' },
  anpaEmail: { authority: 'ANPA', label: 'ANPA email', email: 'anpa@anpa.ro', emailHref: 'mailto:anpa@anpa.ro', role: 'primary', verifiedAt: '2026-08-20', sourceUrl: 'https://www.anpa.ro/?p=1949' },
  gnmDirectory: { authority: 'GNM', label: 'Comisariatele județene ale Gărzii Naționale de Mediu', url: 'https://www.gnm.ro/contact/', role: 'directory', verifiedAt: '2026-08-20', sourceUrl: 'https://www.gnm.ro/contact/' },
  gnmFallback: { authority: 'GNM', label: 'Garda Națională de Mediu — Comisariatul General', phone: '021 326 89 70', telephoneHref: 'tel:0213268970', email: 'gardamediu@gnm.ro', emailHref: 'mailto:gardamediu@gnm.ro', role: 'fallback', verifiedAt: '2026-08-20', sourceUrl: 'https://www.gnm.ro/contact/' },
};

export const INCIDENT_ROUTES: IncidentRoute[] = [
  { kind: 'poaching', urgency: 'active_emergency', contactIds: ['emergency112'] },
  { kind: 'poaching', urgency: 'non_urgent', contactIds: ['anpaOne', 'anpaTwo', 'anpaEmail'] },
  { kind: 'pollution', urgency: 'active_emergency', contactIds: ['emergency112', 'gnmDirectory'] },
  { kind: 'pollution', urgency: 'non_urgent', contactIds: ['gnmDirectory', 'gnmFallback'] },
  { kind: 'illegal_gear_or_sale', urgency: 'non_urgent', contactIds: ['anpaOne', 'anpaTwo', 'anpaEmail'] },
];

export const INCIDENT_VERIFIED_AT = '2026-08-20' as const;
