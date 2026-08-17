/**
 * English mirror of `permis-2026.ts` (t_920a7b7b i18n).
 *
 * RO is the source of truth for FACTS (and the page's default). This module
 * only localizes the prose. The whole object is typed against the RO module's
 * shape (`typeof import('./permis-2026')`), so a missing/mismatched key is a
 * COMPILE error — the two can never drift. Keep RO and EN facts in sync when
 * the quarterly re-verification updates a date or URL.
 */
import type * as RO from './permis-2026';

export const PERMIS_EN: typeof RO = {
  PERMIS_LAST_UPDATED: '2026-08-15',

  PERMIS_PORTAL_URL: 'https://permise.anpa.ro:12443/portal-public/permis',

  /** §1 What changed: ANPA → ANADSPA */
  PERMIS_WHAT_CHANGED: {
    lead:
      'Until the end of 2025, the recreational fishing permit was issued by ANPA — the National ' +
      'Agency for Fishing and Aquaculture. In its 30 December 2025 session, the Government ' +
      'adopted GEO no. 92/2025 (published in the Official Gazette no. 1225 / 31.12.2025) to ' +
      'reorganize the Ministry of Agriculture (MADR). Through it, ANPA was dissolved and ' +
      'absorbed by merger into the State Domains Agency (ADS). The resulting institution is ' +
      'called ANADSPA — the National Authority for the Administration of State Domains, ' +
      'Fishing and Aquaculture.',
    bullets: [
      'The document remains officially the “Permis de pescuit recreativ” — the same permit, only the issuer changed. In everyday speech people still call it the “ANPA permit”; you will also hear “ANADSPA permit” or “ADS permit”.',
      'It stays free and is obtained exclusively online, on the permit platform.',
      'The existing online platform is kept and continues operating (it is due to be rebranded to remove ANPA references).',
    ],
    unchanged:
      'What has NOT changed: the permit is personal and non-transferable, valid for one calendar ' +
      'year (1 January – 31 December), and must be presented together with your ID at a check.',
  },

  /** §2 How to get the 2026 permit — three situations */
  PERMIS_GET_STATE: {
    title: 'The state permit (ANADSPA/ADS, formerly the “ANPA permit”)',
    intro:
      'Covers natural uncontracted waters: rivers and lakes that are not leased to an association, ' +
      'the Danube with its branches and the Black Sea.',
    items: [
      'Where: online, on the permit portal → permise.anpa.ro',
      'Cost: free.',
      'Validity: one calendar year.',
      'Steps: create/log into your account → fill in your personal data → answer a short legislation quiz (2–3 questions) → generate the permit → download it as PDF/digital.',
    ],
  },

  PERMIS_GET_ASSOCIATION: {
    title: 'The association permit (AJVPS / AVPS / clubs)',
    intro:
      'Many waters (especially lakes and river sectors) are leased by local recreational ' +
      'fishing associations. There, besides the state permit, you must become a member of the ' +
      'association that manages the water and pay its membership contribution/permit.',
    items: [
      'Cost: varies by county, water type and status (adult, student, pensioner) — roughly 150–250+ lei/year, sometimes more.',
      'Where: directly at the association that manages the water. On the UndePescuim.ro map you can see which association manages each water.',
    ],
  },

  PERMIS_GET_DELTA: {
    title: 'The Danube Delta (ARBDD)',
    intro:
      'The Danube Delta is a biosphere reserve with a separate regime. There you need the permit ' +
      'issued by ARBDD (the Danube Delta Biosphere Reserve Administration), separate from the state permit.',
    items: [
      'Cost: roughly ~30 lei/year for adults (+ reserve access fees).',
      'Where: online, by SMS, or from ARBDD self-service machines.',
    ],
  },

  PERMIS_GOLDEN_RULE:
    'The golden rule: even though the state permit is free, fishing on many local waters is not ' +
    'allowed without the membership contribution of the association that manages them. Check before you go.',

  /** §3 How to renew */
  PERMIS_RENEW: {
    intro:
      'The state permit is annual — at the start of each year you must generate a new one. ' +
      'To get the new permit, submitting the “catch record” from the previous season is mandatory.',
    currentRule:
      'Catch record deadline (rule in force): by 28 February of the current year, for the previous year.',
    changing:
      'Changing: a draft MADR order (May 2026) proposes that the catch record be completed ' +
      'after every fishing session and submitted by 31 December; if you miss the deadline you can no ' +
      'longer get a permit the following year. See the “What’s coming” section.',
  },

  /** §4 Known gotchas */
  PERMIS_GOTCHAS: [
    {
      title: 'The 1 January bug (renewal at the start of the year)',
      body:
        'At the start of every year the platform is overloaded with requests. Permits generated in ' +
        'the first hours of the year have come out with the wrong year (e.g. a permit issued in ' +
        'January 2023 showed “valid 31.12.2022 – 31.12.2022”). What to do: log in, delete the ' +
        'incorrect permits and re-issue them. If the server is still slow, wait a few days.',
    },
    {
      title: '“Permit already expired”',
      body:
        'The permit is valid strictly for one calendar year. If you try to fish in January with last ' +
        'year\u2019s permit, you are breaking the law. Renew it at the start of the year — do not wait for ' +
        'your first outing.',
    },
    {
      title: 'The legislation quiz is mandatory',
      body:
        'When issuing you must answer 2–3 legislation questions. A wrong answer currently does not ' +
        'block issuance, but the authorities have announced that in the future wrong answers will ' +
        'temporarily block the process. Learn the basic rules from the next section.',
    },
    {
      title: 'The catch record — if you don’t submit it, you lose your permit',
      body:
        'The catch record (“fișă de captură”) is the document in which you report catches by species. ' +
        'It is submitted online, in your account on the platform. Without it, you cannot get a permit the following year.',
    },
  ],

  /** §5 Essential rules */
  PERMIS_RULES: [
    'Maximum retained catch: 5 kg/day at most, or a single fish if it exceeds 5 kg (hill/plain waters, Danube with its branches, Delta, marine waters).',
    'Tackle, mountain zone (salmonids): one single rod with max. 2 hooks, or one casting rod; fly fishing with max. 3 artificial flies; max. 10 fish/day (trout, grayling etc.).',
    'Tackle, hill/plain, Danube, Delta: max. 4 rods or 4 casting rods, each with 2 hooks.',
    'Tackle, Black Sea: max. 2 rods / 2 casting rods or one long-line with 10 hooks each.',
    'Catch cannot be sold — recreational fishing is for personal consumption only.',
    'No permit = an offence (fine, possible confiscation of tackle/catch).',
    'Retained undersized specimens: fine 300–600 lei (per the quiz source).',
    'The framework law is Law no. 176/2024 on fishing and the protection of the living aquatic resource.',
    'Prohibition periods and minimum sizes change annually by ministerial order — check them before each season.',
  ],

  /** §6 What’s coming (draft MADR order, May 2026 — NOT in force) */
  PERMIS_UPCOMING: {
    status:
      'A draft order published by MADR for consultation (May 2026) proposes replacing ' +
      'Order 60/2017. The most important novelties (NOT yet in force):',
    bullets: [
      'The permit is issued exclusively online (formalizes current practice).',
      'Catch record after every session, submitted by 31 December; non-compliance blocks next year\u2019s permit.',
      'Reciprocity between associations only through a written agreement (bilateral/multilateral).',
      'Management plans are drawn up by research institutes (valid 10 years).',
      'Associations also report semiannually (members + balance), not just annually.',
    ],
    unchanged:
      'Unchanged: the free permit, the 10-year contracts, ongoing contracts remain ' +
      'valid, associations continue patrolling and control.',
  },

  /** FAQ */
  PERMIS_FAQ: [
    { q: 'How much does the state permit cost in 2026?', a: 'Free.' },
    { q: 'Where do I get it?', a: 'Online, on the permit portal (link in the “How to get your permit” section).' },
    {
      q: 'Do I have to pay anything to the association?',
      a: 'Yes, if you fish on a contracted water — the association membership contribution, on top of the state permit.',
    },
    {
      q: 'What is the catch record?',
      a: 'The document in which you report catches by species; mandatory for the next permit.',
    },
    { q: 'Can I fish without a permit?', a: 'No — it is an offence.' },
    { q: 'Is the Danube Delta covered by the state permit?', a: 'No, it has a separate permit (ARBDD).' },
  ],

  /** Sources (checked 15.08.2026). Every claim on the page has the source below. */
  PERMIS_SOURCES: [
    {
      label: 'Official fishing permit portal',
      url: 'https://permise.anpa.ro:12443/portal-public/permis',
      note: 'Online issuance of the recreational fishing permit (“Get permit” flow + “Retrieve permit / Catch notes”). Checked live 15.08.2026.',
    },
    {
      label: 'MADR — draft order (access to living aquatic resources, recreational fishing)',
      url: 'https://www.madr.ro/proiecte-de-acte-normative/proiect-de-omadr-privind-accesul-la-resursele-acvatice-vii-din-domeniul-public-al-statului-in-vederea-practicarii-pescuitului-recreativ-in-habitatele-acvatice-naturale.html',
      note: 'Draft order replacing Order 60/2017 (May 2026, in consultation — NOT in force).',
    },
    {
      label: 'ANPA — approved normative acts',
      url: 'https://www.anpa.ro/?p=39',
      note: 'MADR Order no. 56/2026 (OG 179/09.03.2026) on fishing effort and quotas.',
    },
    {
      label: 'ANPA — permit generation video guide',
      url: 'https://www.anpa.ro/?p=4421',
      note: 'Official guide to using the permit generation app (first permit + renewal).',
    },
    {
      label: 'Info-Delta.ro — “ANPA is being dissolved…”',
      url: 'https://www.info-delta.ro/anpa-s-a-desfiintat-ce-se-intampla-cu-permisele-de-pescuit-in-2026/',
      note: 'GEO adopted 30.12.2025; ANPA→ADS merger by absorption; ANADSPA name; GEO 92/2025, OG 1225/31.12.2025; online platform kept.',
    },
    {
      label: 'Pescuit la Somn — “The fishing permit in Romania 2026”',
      url: 'https://pescuitlasomn.ro/news/permisul_de_pescuit_in_romania_2026_tot_ce_trebuie_sa_stii/2026-01-21-13',
      note: 'State permit (ANADSPA/ADS) free + online; AJVPS permits; ARBDD ~30 lei/year; catch record mandatory; tackle limits.',
    },
    {
      label: 'Crapmania.ro — “Online Fishing Permit ANPA — 2026 Guide”',
      url: 'https://www.crapmania.ro/articole/legislatie-pescuit/permis-pescuit-anpa-1',
      note: '2026 permit free, available online; permit types (Danube+uncontracted, Black Sea).',
    },
    {
      label: 'Info-Delta.ro — “Q&A legislation…”',
      url: 'https://www.info-delta.ro/intrebari-si-raspunsuri-legislatie-pescuit-pentru-permisul-de-pescuit-recreativ-emis-de-anpa/',
      note: '2–3 question quiz; catch record deadline 28 February; 5 kg/day limit; tackle; wrong answer does not block (yet).',
    },
    {
      label: 'Grupul Pescarilor — “ANPA fishing permit: Q&A”',
      url: 'https://grupulpescarilor.ro/revista/chestionar-anpa',
      note: 'Full question/answer legislation set; cites Law 176/2024; undersized fine 300–600 lei; zone limits.',
    },
    {
      label: 'Info-Delta.ro — “Recreational fishing rules are changing”',
      url: 'https://www.info-delta.ro/regulile-pescuitului-recreativ-se-schimba-madr-a-publicat-un-nou-proiect-de-ordin/',
      note: 'Draft order details: exclusively online permit; catch record after every session / 31 Dec deadline; written reciprocity; management plans; semiannual reporting; stays free; replaces Order 60/2017; basis = Law 176/2024.',
    },
    {
      label: 'Border Police — fishing permit clearance form (border zone)',
      url: 'https://www.politiadefrontiera.ro/ro/main/pg-formular-de-avizare-a-activitatilor-de-pescuit-recreativ--sportiv-in-zona-de-frontiera-pentru-persoane-fizice-250.html',
      note: 'Context: separate clearance in the border zone; the ANPA permit proof requirement for the clearance is being removed.',
    },
  ],
};