/**
 * UndePescuim.ro — i18n message dictionary (t_920a7b7b).
 *
 * Lightweight custom i18n (no dependency): RO is the source of truth and the
 * DEFAULT locale; `en` is type-checked against the RO shape (a missing key
 * is a compile error — no runtime missing-key fallbacks). UI chrome only;
 * species names + latin data stay RO (task scope §5), URLs stay RO (content
 * switch without path change — task scope §4).
 *
 * `t(key, params)` interpolates `{name}` placeholders; `MessageKey` is a
 * dot-path union derived from the RO tree, so every call site is checked at
 * compile time.
 */

export const locales = ['ro', 'en'] as const;
export type Locale = (typeof locales)[number];

export const STORAGE_KEY = 'undepescuim.locale';

const ro = {
  common: {
    back: 'Înapoi',
    close: 'Închide',
  },
  header: {
    logoAria: 'UndePescuim.ro — acasă',
    menu: 'Meniu',
    navPermis: 'Permis 2026',
    navSpecii: 'Specii',
    sheetSpeciiDesc: 'Dimensiuni de reținere',
    sheetPermisDesc: 'Acte și taxe de pescuit',
    switchLanguage: 'Schimbă limba',
    chooseLanguage: 'Alege limba',
    langRomana: 'Română',
    langEnglish: 'English',
    themeLight: 'Treci la tema luminoasă',
    themeDark: 'Treci la tema întunecată',
    themeLightTitle: 'Tema luminoasă',
    themeDarkTitle: 'Tema întunecată',
  },
  search: {
    placeholder: 'Caută asociația…',
    empty: 'Nicio asociație găsită',
    groupHeading: 'Asociații',
    all: 'Toate asociațiile',
    ariaSearch: 'Caută asociația',
    ariaBack: 'Înapoi',
    overlayTitle: 'Caută asociația',
  },
  filters: {
    countyLabel: 'Județ',
    allCounties: 'Toate județele',
    clipsLoading: 'Se încarcă județele…',
    localityLabel: 'Localitate',
    allLocalities: 'Toate localitățile',
    localitiesCount: '{n} localități',
    searchLocality: 'Caută localitate...',
    noLocalities: 'Fără localități',
    reset: 'Resetează',
    typeLabel: 'Tip',
    typeAria: 'Tipul apei',
    all: 'Toate',
    lakes: 'Lacuri',
    rivers: 'Râuri',
    contractLabel: 'Contract',
    contractAria: 'Statusul contractului',
    contracted: 'Contractate',
    uncontracted: 'Necontractate',
  },
  legend: {
    neutralView: 'Vedere neutră',
    covered: 'Acoperit',
    uncovered: 'Neacoperit',
    uncontractedRivers: 'Râuri necontractate',
    uncontractedLakes: 'Bălți / iazuri necontractate',
  },
  locate: {
    deniedTitle: 'Accesul la locație este blocat.',
    deniedIos: 'Activează Serviciile de localizare pentru browser din Setări.',
    deniedDefault: 'Activează-l din setările browserului.',
    openIosSettings: 'Deschide Setările iPhone',
    errorTitle: 'Nu am putut determina locația.',
    errorBody: 'Continuă să explorezi harta manual.',
    ariaLabel: 'Localizează-mă',
    positionSet: 'Poziție setată',
    locate: 'Localizează-mă',
  },
  map: {
    loading: 'Se încarcă harta…',
  },
  card: {
    lake: 'Lac',
    river: 'Râu',
    privateUncontracted: 'Privat / Necontractat',
    uncontracted: 'Necontractat',
    fishingBanned: 'Pescuit interzis',
    uncontractedTitle: 'Apă necontractată',
    uncontractedBody:
      'Pescuitul aici nu este acoperit de niciun permis afișat pe acest site. Verifică legislația locală înainte de a pescui.',
    seePermitGuide: 'Vezi ghidul „Permis & Reguli 2026” →',
    sector: 'Sector',
    size: 'Dimensiune',
    association: 'Asociație',
    noAssociation: 'Fără asociație',
    nationalPermitLabel: 'Permis național de pescuit (ANADSPA)',
    permitAnadspa: 'Permis ANADSPA',
    permitRomsilva: 'Permis Romsilva',
    buyPermitOnline: 'Cumpără permis online',
    permitCheckAssociation: 'Permis: verifică cu asociația',
    permitValidOnSector: 'Permisul {name} este valabil pe acest sector.',
    reference: 'Referință',
    dataCorrect: 'Datele sunt corecte',
    reportProblem: 'Raportează o problemă',
    permisLink: 'Permis & Reguli 2026',
    retentionLink: 'Dimensiuni de reținere',
  },
  detailSheet: {
    detailsWater: 'Detalii apă',
    detailsAria: 'Detalii: {name}',
    close: 'Închide',
  },
  nearby: {
    title: 'Ape în apropiere',
    closeList: 'Închide lista',
    freshness: 'Poziția ta este live; datele despre ape sunt anuale (date 2026).',
    radius: 'Rază: {km} km.',
    noAssociation: 'Fără asociație',
    ariaTitle: 'Ape în apropiere',
    footer:
      'Doar apele contractate sunt listate aici — pentru râuri/bălți necontractate folosește filtrul „Necontractate”.',
    issuerAssociation: 'Asociație',
  },
  assoc: {
    detailsTitle: 'Detalii asociație',
    detailsAria: 'Detalii: {name}',
    contact: 'Contact',
    locationsTitle: 'Locații publice și contacte',
    noLocations: 'Nu există locații publice aprobate pentru această asociație.',
    phone: 'Telefon',
    email: 'Email',
    site: 'Site',
    source: 'Sursa datelor',
    needsConfirmation: 'Necesită reconfirmare',
    freshness: { current: 'Actual', needs_confirmation: 'Necesită reconfirmare', historical: 'Istoric' },
    locationTypes: { headquarters: 'Sediu', registeredOffice: 'Sediu social', branch: 'Filială', office: 'Birou', clubContactPoint: 'Punct de contact al clubului', permitPickupPoint: 'Punct de ridicare permis', partnerLocation: 'Locație partener' },
  },
  validity: {
    noWaters: 'Asociația nu are ape contractate afișate pe site.',
    validPrefix: 'Permisul {name} este valabil pe',
    oneWater: 'apă',
    manyWaters: 'ape',
    inCounties: 'în județele:',
    anpaDirect: 'administrate direct de ANPA / necontractate',
    contract: 'Contract: {ref}',
    reciprocityConfirmed: 'Reciprocitate: confirmată.',
    reciprocityUnconfirmedTitle: 'Reciprocitate: neconfirmată',
    reciprocityUnconfirmedBody:
      '— nu am găsit o sursă publică care să confirme că permisul acestei asociații este acceptat și de alte asociații. Legea prevede valabilitatea pe bază de reciprocitate între asociațiile afiliate AGVPS; verifică cu asociația înainte de a pescui.',
  },
  report: {
    title: 'Raportează o problemă',
    descriptionWater: 'Raportezi date pentru {name}.',
    descriptionGeneric: 'Ajută-ne să ținem harta corectă.',
    successTitle: 'Mulțumim! Raportul a fost trimis.',
    successBody: 'Îl verificăm în cel mult 7 zile și actualizăm datele.',
    viewIssue: 'Vezi raportul pe GitHub',
    reasonLegend: 'Motivul raportului',
    reasons: {
      data_correct: 'Datele sunt corecte (am pescuit aici)',
      water_invalid: 'Această apă nu mai există / nu se poate pescui',
      association_changed: 'Asociația s-a schimbat',
      wrong_coordinates: 'Coordonatele sunt greșite',
      other: 'Altă problemă',
    },
    detailsLabel: 'Detalii (opțional)',
    detailsPlaceholder: 'Descrie ce e greșit, ce ai observat la fața locului…',
    emailLabel: 'Email (opțional, pentru clarificări)',
    emailPlaceholder: 'tu@exemplu.ro',
    consent: 'Dacă îl completezi, adresa va fi vizibilă în raportul public de pe GitHub.',
    contextConsent: 'Include contextul aproximativ al hărții în raportul public (opțional). Nu se încarcă screenshot-uri și GPS-ul nu este solicitat.',
    error: 'Nu am putut trimite raportul. Încearcă din nou.',
    close: 'Închide',
    submitting: 'Se trimite…',
    submit: 'Trimite raportul',
  },
  pwa: {
    lastUpdatedTitle: 'Ultima actualizare a datelor de pescuit',
    lastUpdatedLabel: 'Date actualizate: ',
    offline: 'Fără conexiune',
    offlineFrom: '— date din {date}',
  },
  speciesSearch: {
    placeholder: 'Caută după nume sau dimensiune (ex. somn, 40)…',
    empty: 'Nicio specie găsită',
    heading: 'Specii',
    ariaSearch: 'Caută o specie',
    trigger: 'Caută o specie…',
    overlayTitle: 'Caută o specie',
  },
  specii: {
    backToMap: 'Înapoi la hartă',
    title: 'Dimensiuni minime de reținere, pe specii',
    introLastChecked: 'Ultima verificare a faptelor: {date}.',
    introIssuer: 'Emitent: {issuer}.',
    introRest:
      'Informațiile se pot schimba anual prin ordin de ministru — verifică sursele oficiale (linkuri la finalul paginii) înainte de o decizie. Conținut sensibil la timp: se re-verifică trimestrial.',
    nationalTitle: 'Valori naționale',
    nationalBody:
      'Dimensiunile de mai jos sunt minimele legale naționale. Bălțile private sau asociațiile pot impune limite mai mari, niciodată mai mici. În Delta Dunării (ARBDD) regimul poate diferi.',
    withSizeHeading: 'Specii cu dimensiune minimă ({n})',
    withoutSizeHeading: 'Protejate / interzise / neconfirmate ({n})',
    noConfirmed: 'Momentan nicio dimensiune confirmată — datele sunt în verificare.',
    dailyLimitHeading: 'Limita generală de captură',
    moreRules: 'Mai multe reguli (permis, unelte, capcane) sunt pe pagina',
    moreRulesLink: 'Permis & Reguli 2026',
    sourcesHeading: 'Surse',
    sourcesIntro:
      'Valorile din tabel au fost verificate față de sursele oficiale (data verificării: {date}). Re-verifică-le trimestrial — conținutul este sensibil la timp.',
    tableValuesLabel: 'Valorile din tabel:',
    footer:
      'Ultima verificare a faptelor: {date}. Conținutul se re-verifică trimestrial (Monitorul Oficial, ANADSPA).',
    retentionInterzis: 'Interzis',
    retentionNeconfirmat: 'Neconfirmat',
    retentionFaraLimita: 'Fără limită',
    retentionInterzisSentence: 'Reținerea este interzisă.',
    retentionFaraLimitaSentence: 'Fără dimensiune minimă stabilită.',
    retentionNeconfirmatSentence: 'Dimensiune neconfirmată — vezi sursa.',
    minSizeSuffix: 'dimensiune minimă de reținere',
    sourceLabel: 'Sursă: {ref}',
    verifiedLabel: '· verificat {date}',
  },
  permis: {
    backToMap: 'Înapoi la hartă',
    title: 'Permis & Reguli 2026',
    intro:
      'Ultima verificare a faptelor: {date}. Informațiile se pot schimba — verifică sursele oficiale (linkuri la finalul paginii) înainte de o decizie. Conținut sensibil la timp: se re-verifică trimestrial.',
    whatChangedHeading: 'Ce s-a schimbat: ANPA → ANADSPA',
    whatChangedLead2: 'Ce înseamnă asta pentru tine, ca pescar recreativ, practic:',
    getPermitHeading: 'Cum obții permisul în 2026',
    getPermitIntro: 'Există trei situații diferite, în funcție de unde pescuiești:',
    openPortal: 'Deschide portalul de permise',
    goldenRuleTitle: 'Regula de aur',
    retentionQuestion: 'Cât de mare trebuie să fie peștele ca să-l poți reține?',
    retentionAnswer:
      'Dimensiunile minime de reținere, pe specii, cu surse și ultima verificare.',
    retentionLink: 'Vezi dimensiunile minime pe specii →',
    renewHeading: 'Cum reînnoiești permisul',
    gotchasHeading: 'Capcane cunoscute (gotchas)',
    rulesHeading: 'Reguli esențiale (pe scurt)',
    rulesIntro: 'Acestea sunt și regulile din care se dau întrebările de la chestionar:',
    upcomingHeading: 'Ce se pregătește (proiect de ordin MADR, mai 2026)',
    notInForce: 'Încă NU în vigoare',
    faqHeading: 'FAQ',
    sourcesHeading: 'Surse',
    sourcesIntro:
      'Fiecare afirmație de pe această pagină se bazează pe sursele de mai jos (verificate la {date}). Re-verifică-le trimestrial — conținutul este sensibil la timp.',
    footer:
      'Ultima verificare a faptelor: {date}. Conținutul se re-verifică trimestrial (portalul de permise, madr.ro, Monitorul Oficial).',
  },
};

export type Messages = typeof ro;

/** English mirror — typed against the RO shape; missing/extra keys are compile errors. */
const en: Messages = {
  common: {
    back: 'Back',
    close: 'Close',
  },
  header: {
    logoAria: 'UndePescuim.ro — home',
    menu: 'Menu',
    navPermis: 'Permit 2026',
    navSpecii: 'Species',
    sheetSpeciiDesc: 'Retention sizes',
    sheetPermisDesc: 'Permits and fishing fees',
    switchLanguage: 'Change language',
    chooseLanguage: 'Choose language',
    langRomana: 'Română',
    langEnglish: 'English',
    themeLight: 'Switch to light theme',
    themeDark: 'Switch to dark theme',
    themeLightTitle: 'Light theme',
    themeDarkTitle: 'Dark theme',
  },
  search: {
    placeholder: 'Search association…',
    empty: 'No association found',
    groupHeading: 'Associations',
    all: 'All associations',
    ariaSearch: 'Search association',
    ariaBack: 'Back',
    overlayTitle: 'Search association',
  },
  filters: {
    countyLabel: 'County',
    allCounties: 'All counties',
    clipsLoading: 'Loading counties…',
    localityLabel: 'Locality',
    allLocalities: 'All localities',
    localitiesCount: '{n} localities',
    searchLocality: 'Search locality...',
    noLocalities: 'No localities',
    reset: 'Reset',
    typeLabel: 'Type',
    typeAria: 'Water type',
    all: 'All',
    lakes: 'Lakes',
    rivers: 'Rivers',
    contractLabel: 'Contract',
    contractAria: 'Contract status',
    contracted: 'Contracted',
    uncontracted: 'Uncontracted',
  },
  legend: {
    neutralView: 'Neutral view',
    covered: 'Covered',
    uncovered: 'Not covered',
    uncontractedRivers: 'Uncontracted rivers',
    uncontractedLakes: 'Uncontracted ponds / lakes',
  },
  locate: {
    deniedTitle: 'Location access is blocked.',
    deniedIos: 'Enable Location Services for your browser in Settings.',
    deniedDefault: 'Enable it in your browser settings.',
    openIosSettings: 'Open iPhone Settings',
    errorTitle: "Couldn't determine your location.",
    errorBody: 'Keep exploring the map manually.',
    ariaLabel: 'Locate me',
    positionSet: 'Position set',
    locate: 'Locate me',
  },
  map: {
    loading: 'Loading map…',
  },
  card: {
    lake: 'Lake',
    river: 'River',
    privateUncontracted: 'Private / Uncontracted',
    uncontracted: 'Uncontracted',
    fishingBanned: 'Fishing banned',
    uncontractedTitle: 'Uncontracted water',
    uncontractedBody:
      'Fishing here is not covered by any permit shown on this site. Check local regulations before fishing.',
    seePermitGuide: 'See the “Permit & Rules 2026” guide →',
    sector: 'Sector',
    size: 'Size',
    association: 'Association',
    noAssociation: 'No association',
    nationalPermitLabel: 'National fishing permit (ANADSPA)',
    permitAnadspa: 'ANADSPA permit',
    permitRomsilva: 'Romsilva permit',
    buyPermitOnline: 'Buy permit online',
    permitCheckAssociation: 'Permit: check with the association',
    permitValidOnSector: 'The {name} permit is valid on this sector.',
    reference: 'Reference',
    dataCorrect: 'Data is correct',
    reportProblem: 'Report a problem',
    permisLink: 'Permit & Rules 2026',
    retentionLink: 'Retention sizes',
  },
  detailSheet: {
    detailsWater: 'Water details',
    detailsAria: 'Details: {name}',
    close: 'Close',
  },
  nearby: {
    title: 'Nearby waters',
    closeList: 'Close list',
    freshness: 'Your position is live; water data is annual (2026 data).',
    radius: 'Radius: {km} km.',
    noAssociation: 'No association',
    ariaTitle: 'Nearby waters',
    footer:
      'Only contracted waters are listed here — for uncontracted rivers/ponds use the “Uncontracted” filter.',
    issuerAssociation: 'Association',
  },
  assoc: {
    detailsTitle: 'Association details',
    detailsAria: 'Details: {name}',
    contact: 'Contact',
    locationsTitle: 'Public locations and contacts',
    noLocations: 'No approved public locations are available for this association.',
    phone: 'Phone',
    email: 'Email',
    site: 'Website',
    source: 'Data source',
    needsConfirmation: 'Needs confirmation',
    freshness: { current: 'Current', needs_confirmation: 'Needs confirmation', historical: 'Historical' },
    locationTypes: { headquarters: 'Headquarters', registeredOffice: 'Registered office', branch: 'Branch', office: 'Office', clubContactPoint: 'Club contact point', permitPickupPoint: 'Permit pickup point', partnerLocation: 'Partner location' },
  },
  validity: {
    noWaters: 'The association has no contracted waters shown on this site.',
    validPrefix: 'The {name} permit is valid on',
    oneWater: 'water',
    manyWaters: 'waters',
    inCounties: 'in the counties:',
    anpaDirect: 'administered directly by ANPA / uncontracted',
    contract: 'Contract: {ref}',
    reciprocityConfirmed: 'Reciprocity: confirmed.',
    reciprocityUnconfirmedTitle: 'Reciprocity: unconfirmed',
    reciprocityUnconfirmedBody:
      '— we could not find a public source confirming this association\u2019s permit is accepted by other associations. The law provides validity on a reciprocity basis between AGVPS-affiliated associations; check with the association before fishing.',
  },
  report: {
    title: 'Report a problem',
    descriptionWater: 'You are reporting data for {name}.',
    descriptionGeneric: 'Help us keep the map accurate.',
    successTitle: 'Thank you! The report was sent.',
    successBody: "We'll review it within 7 days and update the data.",
    viewIssue: 'View the report on GitHub',
    reasonLegend: 'Report reason',
    reasons: {
      data_correct: 'Data is correct (I fished here)',
      water_invalid: 'This water no longer exists / cannot be fished',
      association_changed: 'The association has changed',
      wrong_coordinates: 'The coordinates are wrong',
      other: 'Other issue',
    },
    detailsLabel: 'Details (optional)',
    detailsPlaceholder: 'Describe what is wrong, what you noticed on site…',
    emailLabel: 'Email (optional, for clarifications)',
    emailPlaceholder: 'you@example.com',
    consent:
      'If you fill it in, the address will be visible in the public GitHub report.',
    contextConsent: 'Include approximate map context in the public report (optional). Screenshots are not uploaded and GPS is never requested.',
    error: "Couldn't send the report. Try again.",
    close: 'Close',
    submitting: 'Sending…',
    submit: 'Send report',
  },
  pwa: {
    lastUpdatedTitle: 'Last update of fishing data',
    lastUpdatedLabel: 'Data updated: ',
    offline: 'Offline',
    offlineFrom: '— data from {date}',
  },
  speciesSearch: {
    placeholder: 'Search by name or size (e.g. catfish, 40)…',
    empty: 'No species found',
    heading: 'Species',
    ariaSearch: 'Search a species',
    trigger: 'Search a species…',
    overlayTitle: 'Search a species',
  },
  specii: {
    backToMap: 'Back to map',
    title: 'Minimum retention sizes by species',
    introLastChecked: 'Last fact-checked: {date}.',
    introIssuer: 'Issuer: {issuer}.',
    introRest:
      'Information can change annually by ministerial order — check the official sources (links at the bottom of the page) before deciding. Time-sensitive content: re-verified quarterly.',
    nationalTitle: 'National values',
    nationalBody:
      'The sizes below are the national legal minimums. Private ponds or associations may impose higher limits, never lower. In the Danube Delta (ARBDD) the regime may differ.',
    withSizeHeading: 'Species with minimum size ({n})',
    withoutSizeHeading: 'Protected / prohibited / unconfirmed ({n})',
    noConfirmed: 'No confirmed size yet — data is being verified.',
    dailyLimitHeading: 'General catch limit',
    moreRules: 'More rules (permit, tackle, traps) are on the',
    moreRulesLink: 'Permit & Rules 2026',
    sourcesHeading: 'Sources',
    sourcesIntro:
      'The table values were verified against official sources (check date: {date}). Re-verify them quarterly — content is time-sensitive.',
    tableValuesLabel: 'Table values:',
    footer:
      'Last fact-checked: {date}. Content is re-verified quarterly (Official Gazette, ANADSPA).',
    retentionInterzis: 'Prohibited',
    retentionNeconfirmat: 'Unconfirmed',
    retentionFaraLimita: 'No limit',
    retentionInterzisSentence: 'Retention is prohibited.',
    retentionFaraLimitaSentence: 'No minimum size set.',
    retentionNeconfirmatSentence: 'Unconfirmed size — see source.',
    minSizeSuffix: 'minimum retention size',
    sourceLabel: 'Source: {ref}',
    verifiedLabel: '· checked {date}',
  },
  permis: {
    backToMap: 'Back to map',
    title: 'Permit & Rules 2026',
    intro:
      'Last fact-checked: {date}. Information may change — check the official sources (links at the bottom of the page) before deciding. Time-sensitive content: re-verified quarterly.',
    whatChangedHeading: 'What changed: ANPA → ANADSPA',
    whatChangedLead2: 'What this means for you as a recreational angler, in practice:',
    getPermitHeading: 'How to get your permit in 2026',
    getPermitIntro: 'There are three different situations, depending on where you fish:',
    openPortal: 'Open the permit portal',
    goldenRuleTitle: 'The golden rule',
    retentionQuestion: 'How big must a fish be to keep it?',
    retentionAnswer:
      'Minimum retention sizes by species, with sources and the last check date.',
    retentionLink: 'See minimum sizes by species →',
    renewHeading: 'How to renew your permit',
    gotchasHeading: 'Known gotchas',
    rulesHeading: 'Essential rules (in short)',
    rulesIntro: 'These are also the rules the quiz questions come from:',
    upcomingHeading: "What's coming (draft MADR order, May 2026)",
    notInForce: 'NOT yet in force',
    faqHeading: 'FAQ',
    sourcesHeading: 'Sources',
    sourcesIntro:
      'Every claim on this page is based on the sources below (checked on {date}). Re-verify them quarterly — content is time-sensitive.',
    footer:
      'Last fact-checked: {date}. Content is re-verified quarterly (permit portal, madr.ro, Official Gazette).',
  },
};

export const messages = { ro, en };

/** Dot-path key union over the RO tree — compile-time key checking for t(). */
export type MessageKey = NestedKeys<Messages>;

type NestedKeys<T> = T extends object
  ? {
      [K in keyof T]-?: K extends string
        ? T[K] extends string
          ? K
          : `${K}.${NestedKeys<T[K]>}`
        : never;
    }[keyof T]
  : never;

export function t(
  locale: Locale,
  key: MessageKey,
  params?: Record<string, string | number>,
): string {
  const value = key.split('.').reduce<unknown>((node, part) => {
    if (node && typeof node === 'object') return (node as Record<string, unknown>)[part];
    return undefined;
  }, messages[locale]);
  if (typeof value !== 'string') {
    // Missing-key guard: fail loud in dev/tests (e2e console-error gate),
    // degrade to the RO value in prod so a page never renders a raw key.
    console.error(`[i18n] missing message key: ${key} (${locale})`);
    const roValue = key.split('.').reduce<unknown>((node, part) => {
      if (node && typeof node === 'object') return (node as Record<string, unknown>)[part];
      return undefined;
    }, messages.ro);
    if (typeof roValue === 'string') return interpolate(roValue, params);
    return key;
  }
  return interpolate(value, params);
}

function interpolate(value: string, params?: Record<string, string | number>): string {
  if (!params) return value;
  return value.replace(/\{(\w+)\}/g, (match, name: string) => {
    const replacement = params[name];
    return replacement === undefined ? match : String(replacement);
  });
}
