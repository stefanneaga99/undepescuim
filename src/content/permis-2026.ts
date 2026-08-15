/**
 * Fapte pentru pagina „Permis & Reguli 2026" (roadmap F5).
 *
 * Surse: docs/permis-reguli-2026-sources.md (verificat 15.08.2026).
 * REGULĂ DE ÎNTREȚINERE: re-verifică trimestrial (madr.ro, portalul de permise,
 * Monitorul Oficial). Dacă un fapt s-a schimbat, actualizează DOAR acest fișier —
 * JSX-ul din src/app/permis/page.tsx rămâne neschimbat. Nu inventa date noi:
 * fiecare afirmație are o sursă în PERMIS_SOURCES.
 */

export const PERMIS_LAST_UPDATED = '2026-08-15';

export const PERMIS_PORTAL_URL = 'https://permise.anpa.ro:12443/portal-public/permis';

/** §1 Ce s-a schimbat: ANPA → ANADSPA */
export const PERMIS_WHAT_CHANGED = {
  lead:
    'Până la finalul lui 2025, permisul de pescuit recreativ era emis de ANPA — Agenția ' +
    'Națională pentru Pescuit și Acvacultură. În ședința din 30 decembrie 2025, Guvernul a ' +
    'adoptat OUG nr. 92/2025 (publicată în Monitorul Oficial nr. 1225 / 31.12.2025) de ' +
    'reorganizare a Ministerului Agriculturii (MADR). Prin aceasta, ANPA a fost desființată și ' +
    'absorbită prin fuziune de Agenția Domeniilor Statului (ADS). Instituția rezultată poartă ' +
    'numele de ANADSPA — Autoritatea Națională pentru Administrarea Domeniilor Statului, ' +
    'Pescuit și Acvacultură.',
  bullets: [
    'Documentul rămâne oficial „Permis de pescuit recreativ" — același permis, doar că emitentul s-a schimbat. În limbaj curent lumea încă îi spune „permis ANPA"; îl vei mai auzi numit și „permis ANADSPA" sau „permis ADS".',
    'Rămâne gratuit și se obține exclusiv online, pe platforma de permise.',
    'Platforma online existentă este păstrată și operată în continuare (urmează să fie rebranduită pentru a scoate referirile la ANPA).',
  ],
  unchanged:
    'Ce NU s-a schimbat: permisul e nominal și netransferabil, valabil un an calendaristic ' +
    '(1 ianuarie – 31 decembrie), și trebuie prezentat împreună cu actul de identitate la control.',
};

/** §2 Cum obții permisul în 2026 — trei situații */
export const PERMIS_GET_STATE = {
  title: 'Permisul de stat (ANADSPA/ADS, fostul „permis ANPA")',
  intro:
    'Acoperă apele naturale necontractate: râurile și lacurile care nu sunt concesionate de o ' +
    'asociație, Dunărea cu brațele sale și Marea Neagră.',
  items: [
    'Unde: online, pe portalul de permise → permise.anpa.ro',
    'Cost: gratuit.',
    'Valabilitate: un an calendaristic.',
    'Pași: îți creezi/autentifici contul → completezi datele personale → răspunzi la un scurt chestionar de legislație (2–3 întrebări) → generezi permisul → îl descarci în format PDF/digital.',
  ],
};

export const PERMIS_GET_ASSOCIATION = {
  title: 'Permisul asociației (AJVPS / AVPS / cluburi)',
  intro:
    'Multe ape (în special lacuri și sectoare de râu) sunt contractate de asociații locale de ' +
    'pescari recreativi. Acolo, pe lângă permisul de stat, trebuie să devii membru al asociației ' +
    'care administrează apa și să plătești cotizația/permisul acesteia.',
  items: [
    'Cost: variabil după județ, tip de apă și statut (adult, elev, pensionar) — orientativ 150–250+ lei/an, poate fi mai mult.',
    'Unde: direct la asociația care administrează apa. Pe harta UndePescuim.ro vezi care asociație gestionează fiecare apă.',
  ],
};

export const PERMIS_GET_DELTA = {
  title: 'Delta Dunării (ARBDD)',
  intro:
    'Delta Dunării este rezervație a biosferei și are regim separat. Acolo e nevoie de permisul ' +
    'emis de ARBDD (Administrația Rezervației Biosferei Delta Dunării), separat de permisul de stat.',
  items: [
    'Cost: orientativ ~30 lei/an pentru adulți (+ taxe de acces în rezervație).',
    'Unde: online, prin SMS sau de la automatele ARBDD.',
  ],
};

export const PERMIS_GOLDEN_RULE =
  'Regula de aur: chiar dacă permisul de stat e gratuit, pescuitul pe multe ape locale nu e ' +
  'permis fără cotizația asociației care le administrează. Verifică înainte să pleci.';

/** §3 Cum reînnoiești permisul */
export const PERMIS_RENEW = {
  intro:
    'Permisul de stat e anual — la începutul fiecărui an trebuie să îți generezi unul nou. ' +
    'Pentru a obține permisul nou, depunerea „fișei de captură" din sezonul anterior este obligatorie.',
  currentRule:
    'Termenul fișei de captură (regula în vigoare): până la 28 februarie a anului în curs, pentru anul precedent.',
  changing:
    'În schimbare: un proiect de ordin MADR (mai 2026) propune ca fișa de captură să fie ' +
    'completată după fiecare partidă și transmisă până la 31 decembrie, iar dacă nu o trimiți la ' +
    'termen nu mai poți obține permisul anul următor. Vezi secțiunea „Ce se pregătește".',
};

/** §4 Capcane cunoscute (gotchas) */
export const PERMIS_GOTCHAS: { title: string; body: string }[] = [
  {
    title: 'Bug-ul de 1 ianuarie (reînnoire la început de an)',
    body:
      'La începutul fiecărui an platforma e supraîncărcată de cereri. S-a întâmplat ca permise ' +
      'generate în primele ore ale anului să iasă cu anul greșit (ex. un permis emis în ianuarie ' +
      '2023 a apărut „valid 31.12.2022 – 31.12.2022"). Ce faci: intră în cont, șterge permisele ' +
      'emise greșit și reemite-le. Dacă serverul încă „trage", mai așteaptă câteva zile.',
  },
  {
    title: '„Permisul deja expirat"',
    body:
      'Permisul e valabil strict pe an calendaristic. Dacă încerci să pescuiești în ianuarie cu ' +
      'permisul de anul trecut, ești în afara legii. Reînnoiește-l la început de an, nu aștepta ' +
      'prima ieșire la apă.',
  },
  {
    title: 'Chestionarul de legislație e obligatoriu',
    body:
      'La emitere trebuie să răspunzi la 2–3 întrebări de legislație. Momentan un răspuns greșit ' +
      'nu blochează emiterea, dar autoritățile au anunțat că în viitor răspunsurile greșite vor ' +
      'bloca temporar procesul. Învață regulile de bază din secțiunea următoare.',
  },
  {
    title: 'Fișa de captură — dacă n-o trimiți, rămâi fără permis',
    body:
      'Fișa de captură („catch sheet") e documentul în care raportezi capturile pe specii. Se ' +
      'depune online, în contul tău de pe platformă. Fără ea, nu poți obține permisul anului următor.',
  },
];

/** §5 Reguli esențiale */
export const PERMIS_RULES: string[] = [
  'Captura maximă reținută: maximum 5 kg/zi, sau un singur pește dacă depășește 5 kg (ape colinare/șes, Dunăre cu brațele, Delta, ape maritime).',
  'Unelte, zona de munte (salmonide): o singură undiță cu max. 2 cârlige, sau o lansetă; pescuit la muscă cu max. 3 muște artificiale; max. 10 exemplare/zi (păstrăvi, lipan etc.).',
  'Unelte, colinar/șes, Dunăre, Delta: max. 4 undițe sau 4 lansete, cu câte 2 cârlige fiecare.',
  'Unelte, Marea Neagră: max. 2 undițe / 2 lansete sau o țaparină cu câte 10 cârlige.',
  'Captura nu se comercializează — pescuitul recreativ e doar pentru consum propriu.',
  'Fără permis = contravenție (amendă, posibilă confiscare a uneltelor/capturii).',
  'Exemplare subdimensiune reținute: amendă 300–600 lei (conform sursei de quiz).',
  'Legea-cadru e Legea nr. 176/2024 a pescuitului și protecției resursei acvatice vii.',
  'Perioadele de prohibiție și dimensiunile minime se schimbă anual prin ordin de ministru — verifică-le înainte de fiecare sezon.',
];

/** §6 Ce se pregătește (proiect de ordin MADR, mai 2026 — NU în vigoare) */
export const PERMIS_UPCOMING = {
  status:
    'Un proiect de ordin publicat de MADR în consultare (mai 2026) propune înlocuirea ' +
    'Ordinului 60/2017. Cele mai importante noutăți (încă NU în vigoare):',
  bullets: [
    'Permisul se eliberează exclusiv online (formalizează practica actuală).',
    'Fișa de captură după fiecare partidă, transmisă până la 31 decembrie; nerespectarea blochează permisul anului următor.',
    'Reciprocitatea dintre asociații se face doar prin acord scris (bilateral/multilateral).',
    'Planurile de management se elaborează de institute de cercetare (valabile 10 ani).',
    'Asociațiile raportează și semestrial (membri + balanță), nu doar anual.',
  ],
  unchanged:
    'Rămân neschimbate: permisul gratuit, contractele pe 10 ani, contractele în derulare rămân ' +
    'valabile, asociațiile continuă paza și controlul.',
};

/** FAQ */
export const PERMIS_FAQ: { q: string; a: string }[] = [
  { q: 'Cât costă permisul de stat în 2026?', a: 'Gratuit.' },
  { q: 'Unde îl obțin?', a: 'Online, pe portalul de permise (linkul din secțiunea „Cum obții permisul").' },
  {
    q: 'Trebuie să plătesc ceva la asociație?',
    a: 'Da, dacă pescuiești pe o apă contractată — cotizația asociației, pe lângă permisul de stat.',
  },
  {
    q: 'Ce e fișa de captură?',
    a: 'Documentul în care raportezi capturile pe specii; obligatorie pentru permisul următor.',
  },
  { q: 'Pot pescui fără permis?', a: 'Nu — e contravenție.' },
  { q: 'Delta Dunării e acoperită de permisul de stat?', a: 'Nu, are permis separat (ARBDD).' },
];

/** Surse (verificate 15.08.2026). Fiecare afirmație de pe pagină are sursa de mai jos. */
export const PERMIS_SOURCES: { label: string; url: string; note: string }[] = [
  {
    label: 'Portalul oficial de permise de pescuit',
    url: 'https://permise.anpa.ro:12443/portal-public/permis',
    note: 'Emiterea online a permisului de pescuit recreativ (flux „Obține permis" + „Recuperare permis / Note de captură"). Verificat live 15.08.2026.',
  },
  {
    label: 'MADR — proiect de ordin (acces resurse acvatice vii, pescuit recreativ)',
    url: 'https://www.madr.ro/proiecte-de-acte-normative/proiect-de-omadr-privind-accesul-la-resursele-acvatice-vii-din-domeniul-public-al-statului-in-vederea-practicarii-pescuitului-recreativ-in-habitatele-acvatice-naturale.html',
    note: 'Proiect de ordin care înlocuiește Ordinul 60/2017 (mai 2026, în consultare — NU în vigoare).',
  },
  {
    label: 'ANPA — acte normative aprobate',
    url: 'https://www.anpa.ro/?p=39',
    note: 'Ordin MADR nr. 56/2026 (MO 179/09.03.2026) privind efortul de pescuit și cotele.',
  },
  {
    label: 'ANPA — ghid video generare permise',
    url: 'https://www.anpa.ro/?p=4421',
    note: 'Ghid oficial de utilizare a aplicației de generare permise (primul permis + reînnoire).',
  },
  {
    label: 'Info-Delta.ro — „ANPA se desființează..."',
    url: 'https://www.info-delta.ro/anpa-s-a-desfiintat-ce-se-intampla-cu-permisele-de-pescuit-in-2026/',
    note: 'OUG adoptată 30.12.2025; fuziune prin absorbție ANPA→ADS; denumirea ANADSPA; OUG 92/2025, MO 1225/31.12.2025; platforma online păstrată.',
  },
  {
    label: 'Pescuit la Somn — „Permisul de pescuit în România 2026"',
    url: 'https://pescuitlasomn.ro/news/permisul_de_pescuit_in_romania_2026_tot_ce_trebuie_sa_stii/2026-01-21-13',
    note: 'Permis stat (ANADSPA/ADS) gratuit + online; permise AJVPS; ARBDD ~30 lei/an; fișa de captură obligatorie; limite unelte.',
  },
  {
    label: 'Crapmania.ro — „Permis de Pescuit Online ANPA — Ghid 2026"',
    url: 'https://www.crapmania.ro/articole/legislatie-pescuit/permis-pescuit-anpa-1',
    note: 'Permis 2026 gratuit, disponibil online; tipuri de permise (Dunăre+necontractate, Marea Neagră).',
  },
  {
    label: 'Info-Delta.ro — „Întrebări și răspunsuri legislație..."',
    url: 'https://www.info-delta.ro/intrebari-si-raspunsuri-legislatie-pescuit-pentru-permisul-de-pescuit-recreativ-emis-de-anpa/',
    note: 'Chestionar 2–3 întrebări; fișa de captură termen 28 februarie; limită 5 kg/zi; unelte; răspuns greșit nu blochează (încă).',
  },
  {
    label: 'Grupul Pescarilor — „Permis de pescuit ANPA: Întrebări și răspunsuri"',
    url: 'https://grupulpescarilor.ro/revista/chestionar-anpa',
    note: 'Setul complet de întrebări/răspunsuri de legislație; citează Legea 176/2024; amendă subdimensiune 300–600 lei; limite pe zone.',
  },
  {
    label: 'Info-Delta.ro — „Regulile pescuitului recreativ se schimbă"',
    url: 'https://www.info-delta.ro/regulile-pescuitului-recreativ-se-schimba-madr-a-publicat-un-nou-proiect-de-ordin/',
    note: 'Detaliile proiectului de ordin: permis exclusiv online; fișă de captură după fiecare partidă / termen 31 dec; reciprocitate scrisă; planuri management; raportare semestrială; rămâne gratuit; înlocuiește Ordin 60/2017; baza = Legea 176/2024.',
  },
  {
    label: 'Poliția de Frontieră — formular avizare pescuit zonă de frontieră',
    url: 'https://www.politiadefrontiera.ro/ro/main/pg-formular-de-avizare-a-activitatilor-de-pescuit-recreativ--sportiv-in-zona-de-frontiera-pentru-persoane-fizice-250.html',
    note: 'Context: avizare separată în zona de frontieră; se elimină condiția dovezii permisului ANPA pentru aviz.',
  },
];
