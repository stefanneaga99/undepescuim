/** URLs accepted by user-facing external links. */
export function safeExternalUrl(value: unknown): string | null {
  if (typeof value !== 'string' || !value.trim()) return null;
  try {
    const url = new URL(value.trim());
    return url.protocol === 'https:' ? url.href : null;
  } catch {
    return null;
  }
}

export function safeTelephone(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  const digits = value.replace(/\s+/g, '');
  if (digits === '112') return 'tel:112';
  return /^\+?[0-9().-]{7,20}$/.test(digits) ? `tel:${digits}` : null;
}

export function safeEmail(value: unknown): string | null {
  if (typeof value !== 'string' || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return null;
  return `mailto:${value}`;
}