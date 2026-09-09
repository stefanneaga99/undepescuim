export const LEGAL_PLACEHOLDERS = {
  entity: '[LEGAL ENTITY]',
  address: '[ADDRESS]',
  email: '[OFFICIAL EMAIL]',
  dataProtection: '[DATA PROTECTION CONTACT]',
} as const;

export const LEGAL_NAV_ITEMS = [
  { href: '/confidentialitate', label: 'Confidențialitate și stocare' },
  { href: '/termeni', label: 'Termeni și utilizare' },
  { href: '/contact', label: 'Contact și drepturi' },
  { href: '/licente', label: 'Licențe și surse date' },
] as const;

export const legalSections = {
  privacy: `Operatorul provizoriu al serviciului este ${LEGAL_PLACEHOLDERS.entity}, cu adresa ${LEGAL_PLACEHOLDERS.address}. Contact pentru confidențialitate: ${LEGAL_PLACEHOLDERS.email}; contactul responsabilului cu protecția datelor, dacă există unul desemnat, este ${LEGAL_PLACEHOLDERS.dataProtection}. Aceste câmpuri sunt intenționat necompletate și trebuie verificate înainte de publicare.`,
  purposes: 'Folosim datele strict pentru afișarea hărții și a paginilor, securitatea tehnică și limitarea abuzului, primirea și verificarea rapoartelor și, numai dacă alegi explicit, funcțiile offline. Temeiul fiecărui scop trebuie documentat de operator: interes legitim pentru securitate și funcționarea serviciului, respectiv alegerea expresă pentru funcția offline și preferințele opționale.',
  recipients: 'Destinatarii pot include furnizorul de găzduire Vercel, OpenStreetMap Foundation pentru dalele hărții și GitHub pentru rapoarte publice structurate. Regiunile, subcontractanții, rolurile și transferurile în afara SEE trebuie verificate în contractele efective și nu sunt presupuse aici. Nu pretindem că serviciul este conform legal sau că un transfer este aprobat fără această verificare.',
  retention: 'Păstrăm datele numai cât este necesar scopului documentat: starea tehnică anti-abuz expiră rapid, rapoartele publice au nevoie de criterii de închidere și ștergere, iar cache-ul offline are versiune și expirare. Perioadele exacte pentru operator, Vercel și GitHub rămân de adoptat și trebuie înlocuite cu perioade verificate; copiile externe, notificările, fork-urile și backup-urile pot avea limite distincte.',
  rights: 'Drepturi: poți cere acces, rectificare, ștergere, restricționare, portabilitate când se aplică și te poți opune prelucrării sau îți poți retrage alegerea. Scrie la adresa de contact de mai sus; verificăm identitatea proporțional și răspundem, de regulă, în cel mult o lună. Poți depune o plângere la ANSPDCP după ce te-ai adresat operatorului: https://www.dataprotection.ro/?page=Plangeri_pagina_principala.',
  geolocation: 'Geolocația pornește doar la apăsarea butonului, este folosită în memoria paginii pentru hartă și nu este salvată sau trimisă implicit. Un raport nu trebuie să conțină coordonate sau context de hartă decât dacă există o alegere separată, clară și revocabilă; refuzul nu blochează folosirea hărții.',
  storage: 'Nu folosim cookie-uri de marketing sau analiză. Preferințele și stocarea offline pe dispozitiv trebuie activate printr-o alegere clară; poți refuza fără pierderea funcțiilor online. Dezactivarea trebuie să oprească viitoarele scrieri și să șteargă stocarea offline controlată de aplicație. Nu numim stocarea „necesară” doar pentru că este tehnic convenabilă.',
  reports: 'Rapoartele publice automate sunt limitate la motivul enumerat, identificatorul/numele normalizat al apei și diagnostice generate de operator. Nu trimite nume, emailuri, acuzații despre persoane identificabile, date sensibile, parole sau coordonate. Pentru corectare, ștergere sau takedown folosește contactul; ștergerea poate să nu elimine copiile controlate de GitHub, notificările, cache-urile sau fork-urile.',
  terms: 'Serviciul este informativ și necomercial: nu este o autoritate, nu vinde permise și nu înlocuiește sursele oficiale sau regulile locale. fără garanții privind exhaustivitatea, actualitatea, disponibilitatea, eligibilitatea la pescuit sau rezultatul unei sesizări. Verifică sursele oficiale înainte de a lua o decizie și nu folosi serviciul pentru urgențe; sună la 112.',
  licence: 'Harta folosește OpenStreetMap și contribuții OpenStreetMap. Datele sunt disponibile sub Open Database License (ODbL); vezi https://www.openstreetmap.org/copyright și https://opendatacommons.org/licenses/odbl/1-0/. Dalele standard OSM sunt un serviciu separat, cu politica https://operations.osmfoundation.org/policies/tiles/. Nu oferim descărcare în masă sau prefetch de dale. Pentru fiecare set de date publicat trebuie păstrat un registru de sursă, data extragerii, clasificarea ODbL și oferta de date derivate, când se aplică.',
} as const;
