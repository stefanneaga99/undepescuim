/**
 * Datele pentru pagina „Specii — dimensiuni minime de reținere".
 *
 * Sursa valorilor: data/species.json (construit de task-ul de verificare a
 * datelor, t_561dc7e8 — fiecare valoare verificată față de Monitorul Oficial).
 * Acest modul doar importă JSON-ul, îl normalizează și îl expune tipizat;
 * NU inventează valori — orice lipsă din fișier rămâne „neconfirmat".
 *
 * REGULĂ DE ÎNTREȚINERE: re-verifică trimestrial (Monitorul Oficial, ANADSPA).
 * Când se schimbă un fapt, actualizează data/species.json — JSX-ul din
 * src/app/specii/page.tsx rămâne neschimbat.
 */
import rawSpecies from '../../data/species.json';

export type SpeciesRetention = 'min-size' | 'interzis' | 'fara-limita' | 'neconfirmat';

export interface Species {
  slug: string; // 'somn', 'crap', 'stiu-ca' ...
  nameRo: string; // 'Somn'
  nameScientific: string; // 'Silurus glanis'
  minSizeCm: number | null; // null când nu există dimensiune confirmată
  retention: SpeciesRetention; // derivat din min_cm / câmpul explicit
  prohibition?: string; // perioadă de prohibiție, dacă e menționată
  dailyLimit?: string; // limită de captură, dacă e menționată
  notes?: string; // observații (invaziv, protejat etc.)
  sourceRef: string; // sursa valorii (din data/species.json)
  lastUpdated?: string; // ultima verificare a valorii, dacă e per-specie
}

/** Normalizează textul pentru slug (fără diacritice, lowercase). */
function slugify(name: string): string {
  return name
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

/** Elimină diacriticele (folosit și pentru căutare). */
export function normalizeText(s: string): string {
  return s
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');
}

/** Extrage numărul din min_cm atunci când vine ca string ('60 cm'). 0/nul = lipsă. */
function parseCm(value: unknown): number | null {
  if (typeof value === 'number') return Number.isFinite(value) && value > 0 ? value : null;
  if (typeof value === 'string') {
    const m = value.trim().match(/(\d+(?:[.,]\d+)?)/);
    if (m) {
      const n = Number.parseFloat(m[1].replace(',', '.'));
      return Number.isFinite(n) && n > 0 ? n : null;
    }
  }
  return null;
}

function stringOr(value: unknown): string | undefined {
  if (typeof value === 'string') {
    const t = value.trim();
    return t.length > 0 ? t : undefined;
  }
  return undefined;
}

/** Derivează statusul de reținere DOAR din conținutul fișierului. */
function deriveRetention(minCm: unknown, explicit: unknown): SpeciesRetention {
  const norm = (v: unknown) => normalizeText(String(v ?? ''));
  // 1. Explicit 'interzis' câștigă întotdeauna (listele oficiale de prohibiție),
  //    chiar dacă anexa 342/2008 păstrează o dimensiune (ex. lipan 25 cm).
  if (explicit !== undefined && norm(explicit).includes('interzis')) return 'interzis';
  // 2. Heuristici pe textul min_cm (ex. 'interzis', 'neconfirmat', 'fără limită').
  const hasCm = minCm !== null && minCm !== undefined && String(minCm).trim() !== '';
  if (hasCm) {
    const txt = String(minCm).trim();
    if (/interzis/i.test(txt)) return 'interzis';
    if (/neconfirmat/i.test(txt)) return 'neconfirmat';
    if (/fara[-\s]?limita|nelimitat|fără limită/i.test(txt) || txt === '—' || txt === '-') {
      return 'fara-limita';
    }
    if (parseCm(minCm) !== null) return 'min-size';
    return 'neconfirmat';
  }
  // 3. min_cm gol → respectă câmpul explicit dacă există, altfel neconfirmat.
  if (explicit !== undefined) {
    const e = norm(explicit);
    if (e.includes('fara') || e.includes('fără') || e.includes('limita')) return 'fara-limita';
    if (e.includes('neconfirmat')) return 'neconfirmat';
  }
  return 'neconfirmat';
}

interface RawEntry {
  species?: unknown;
  latin?: unknown;
  min_cm?: unknown;
  source?: unknown;
  seasonal_notes?: unknown;
  notes?: unknown;
  daily_limit?: unknown;
  retention?: unknown;
  last_updated?: unknown;
}

interface RawFile {
  species?: RawEntry[];
  last_updated?: unknown;
  issuing_body?: unknown;
  [k: string]: unknown;
}

/** Aduce fișierul la o listă plată de intrări (acceptă și obiect cu .species). */
function toEntries(raw: unknown): RawEntry[] {
  if (Array.isArray(raw)) return raw as RawEntry[];
  if (raw && typeof raw === 'object' && Array.isArray((raw as RawFile).species)) {
    return (raw as RawFile).species as RawEntry[];
  }
  return [];
}

const entries = toEntries(rawSpecies);

export const SPECIES: Species[] = entries
  .map((e, i) => {
    const nameRo = stringOr(e.species) ?? `Specie ${i + 1}`;
    const minSizeCm = parseCm(e.min_cm);
    return {
      slug: slugify(nameRo) || `specie-${i}`,
      nameRo,
      nameScientific: stringOr(e.latin) ?? '',
      minSizeCm,
      retention: deriveRetention(e.min_cm, e.retention),
      prohibition: stringOr(e.seasonal_notes) ?? stringOr(e.notes),
      dailyLimit: stringOr(e.daily_limit),
      notes: stringOr(e.notes),
      sourceRef: stringOr(e.source) ?? 'neconfirmat',
      lastUpdated: stringOr(e.last_updated),
    } satisfies Species;
  })
  .filter((s) => s.nameRo !== 'Specie ' && s.nameRo.length > 0);

/** Data ultimei verificări — din fișier (top-level sau per-intrare), altfel fallback. */
export const SPECIES_LAST_UPDATED: string =
  (() => {
    const raw = rawSpecies as unknown as RawFile;
    if (typeof raw.last_updated === 'string' && raw.last_updated.trim()) return raw.last_updated.trim();
    const dates = SPECIES.map((s) => s.lastUpdated).filter((d): d is string => !!d);
    if (dates.length > 0) return dates.sort().slice(-1)[0];
    return '2026-08-16'; // data publicării paginii; se actualizează la re-verificare
  })();

/** Emitentul curent (dacă fișierul îl menționează). */
export const SPECIES_ISSUING_BODY: string | undefined = (() => {
  const raw = rawSpecies as unknown as RawFile;
  return typeof raw.issuing_body === 'string' && raw.issuing_body.trim()
    ? raw.issuing_body.trim()
    : undefined;
})();

/** Limita generală zilnică (națională — verificată pe pagina /permis). */
export const SPECIES_DAILY_LIMIT =
  'Captura maximă reținută: maximum 5 kg/zi, sau un singur pește dacă depășește 5 kg.';

/** Sursele legale/instituționale (aceleași instrumente ca pe /permis). */
export const SPECIES_SOURCES: { label: string; url: string; note: string }[] = [
  {
    label: 'Legea nr. 176/2024 a pescuitului și protecției resursei acvatice vii',
    url: 'https://legislatie.just.ro/public/DetaliiDocument/283479',
    note: 'Legea-cadru; deleagă tabelul dimensiunilor minime către ordin de ministru.',
  },
  {
    label: 'Ordin nr. 23/297/2025 — perioadele de prohibiție',
    url: 'https://legislatie.just.ro/Public/DetaliiDocumentAfis/294196',
    note: 'Perioade anuale de prohibiție pe specii/zone (știucă, șalău etc.).',
  },
];

/** Sursele unice citate pe rânduri — extrase din data/species.json. */
export const SPECIES_ROW_SOURCES: string[] = (() => {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const s of SPECIES) {
    if (s.sourceRef && !seen.has(s.sourceRef)) {
      seen.add(s.sourceRef);
      out.push(s.sourceRef);
    }
  }
  return out;
})();

/** Speciile cu dimensiune minimă efectivă (reținere permisă peste dimensiune). */
export const SPECIES_WITH_SIZE: Species[] = SPECIES.filter((s) => s.retention === 'min-size');

/** Speciile fără reținere permisă / fără dimensiune confirmată (interzise etc.). */
export const SPECIES_WITHOUT_SIZE: Species[] = SPECIES.filter((s) => s.retention !== 'min-size');
