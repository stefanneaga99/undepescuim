import type { Association, AssociationLocation } from '@/types/data';

const LOCATION_TYPES = new Set([
  'headquarters',
  'registered_office',
  'branch',
  'office',
  'club_contact_point',
  'permit_pickup_point',
  'partner_location',
]);
const FRESHNESS = new Set(['current', 'needs_confirmation', 'historical']);
const LOCATION_STATUS = new Set(['verified', 'ambiguous', 'stale', 'unverified']);
const CONFIDENCE = new Set(['high', 'medium', 'low']);
const CONTACT_KINDS = new Set(['phone', 'email', 'url']);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function isLocation(value: unknown): value is AssociationLocation {
  if (!isRecord(value)) return false;
  if (!isNonEmptyString(value.id) || !isNonEmptyString(value.associationId) || !isNonEmptyString(value.associationSlug)) return false;
  if (!isNonEmptyString(value.address) || !isNonEmptyString(value.locality) || !isNonEmptyString(value.county)) return false;
  if (value.country !== 'RO' || !LOCATION_TYPES.has(String(value.type))) return false;
  if (!FRESHNESS.has(String(value.freshness)) || !LOCATION_STATUS.has(String(value.status))) return false;
  if (!CONFIDENCE.has(String(value.confidence)) || !isNonEmptyString(value.checkedAt)) return false;
  if (value.public !== true || !isRecord(value.review) || !['approved', 'needs_review'].includes(String(value.review.status))) return false;
  if (value.contacts !== undefined && (!Array.isArray(value.contacts) || value.contacts.some((contact) =>
    !isRecord(contact) || !CONTACT_KINDS.has(String(contact.kind)) || !isNonEmptyString(contact.value)))) return false;
  if (!Array.isArray(value.sources) || value.sources.length === 0 || value.sources.some((source) =>
    !isRecord(source) || !isNonEmptyString(source.url) || !isNonEmptyString(source.publisher) ||
    !isNonEmptyString(source.sourceType) || !isNonEmptyString(source.retrievedAt))) return false;
  return true;
}

/**
 * Attach only a complete, approved locations artifact to associations.
 * Any missing, malformed, or unexpected artifact falls back to the legacy
 * association records unchanged; this keeps adresa/telefon/siteUrl usable and
 * avoids manufacturing branches or permit pickup points from generic contacts.
 */
export function mergeAssociationLocations(
  associations: Association[],
  artifact: unknown,
): Association[] {
  if (!isRecord(artifact) || artifact.schemaVersion !== 1 || !Array.isArray(artifact.locations)) {
    return associations;
  }
  const locations = artifact.locations;
  if (!locations.every(isLocation)) return associations;
  const approvedLocations = locations.filter((location) => location.review.status === 'approved');

  const byAssociation = new Map<string, AssociationLocation[]>();
  for (const location of approvedLocations) {
    const key = location.associationId;
    const grouped = byAssociation.get(key) ?? [];
    grouped.push(location);
    byAssociation.set(key, grouped);
  }

  return associations.map((association) => {
    const grouped = byAssociation.get(association.id) ??
      byAssociation.get(approvedLocations.find((location) => location.associationSlug === association.slug)?.associationId ?? '');
    return grouped ? { ...association, locations: grouped } : association;
  });
}
