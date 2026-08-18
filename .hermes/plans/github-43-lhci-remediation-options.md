# Issue #43 — remediere minimă pentru vulnerabilitățile Lighthouse CI

## Scop

Stabilește cea mai mică schimbare de dependențe care reduce riscul fără să înlocuiască fluxul existent Lighthouse CI. Planul se aplică la revizia locală `cfe25e2`; nu modifică în sine manifestul sau lockfile-ul.

## Arhitectură și constrângeri confirmate

- Manager: **npm 10.9.8**, cu `package-lock.json` `lockfileVersion: 3`; nu există Yarn/pnpm, deci se folosesc numai `package.json#overrides` și lockfile-ul npm, nu `resolutions`.
- Node folosit local: 22.23.2. Workflow-urile Lighthouse CI și E2E rulează cu **Node 20**, iar workflow-ul unit test rulează cu Node 22.
- `@lhci/cli` este devDependency (`^0.15.1`, rezolvat la 0.15.1) și este apelat de `npm run perf:lhci`; workflow-ul `.github/workflows/perf.yml` rulează `npx lhci autorun --config=lighthouserc.json` după `npm ci`, build și serverul de producție.
- Configurația LHCI testează `/`, `/specii`, `/permis`, de trei ori, în emulare mobilă, și păstrează assertion-urile LCP/TBT/CLS/FCP/byte-weight din `lighthouserc.json`.
- `@lhci/cli@0.15.1` cere exact `lighthouse@12.6.1`, plus `tmp:^0.1.0`, `uuid:^8.3.1` și `inquirer:^6.3.1`; nu există release public mai nou al CLI. `lighthouse@13.4.1` declarat separat la root nu înlocuiește copiile `lighthouse@12.6.1` ale LHCI.
- `lighthouse@13.4.1` declară Node `>=22.19`; acesta este deja incompatibil formal cu joburile Node 20, deși fluxul LHCI utilizează arborele LHCI/Lighthouse 12. Orice schimbare trebuie testată explicit atât pe Node 20, cât și pe Node 22; nu se presupune că auditul sau instalarea pe Node 22 validează jobul LHCI Node 20.

## Cele patru alerte și limita locală

| Advisory | Pachet actual | Versiune reparată | Decizie locală |
|---|---:|---:|---|
| GHSA-ph9p-34f9-6g65 (high) | `tmp@0.1.0` și `tmp@0.0.33` | `0.2.6+` | Poate fi suprascris la root, dar încalcă range-urile upstream LHCI/inquirer; necesită validare funcțională. |
| GHSA-52f5-9888-hmc6 (low) | aceleași două `tmp` | `0.2.4+` | Este acoperită de același override `tmp@0.2.7`. |
| GHSA-w5hq-g745-h8pq (medium) | `uuid@8.3.2` | `11.1.1+` | Poate fi suprascris la root, peste contractul `^8.3.1` al LHCI; necesită validare funcțională. |
| GHSA-jmr9-qjv8-65gv (high) | `extract-zip@2.0.1` | **niciuna** | Nu poate fi remediată responsabil numai printr-un upgrade/override npm: `2.0.1` este încă latest și advisory-ul nu are `first_patched_version`. |

## Evaluarea opțiunilor

### 1. Upgrade direct — respins momentan

Nu există o versiune npm a `@lhci/cli` mai nouă decât 0.15.1. Ridicarea `lighthouse` de la root la 13.4.1 (deja instalat) nu poate schimba `lighthouse: 12.6.1` fixat în `@lhci/cli`; deci nu remediază cele patru alerte.

**Risc:** un `npm audit fix --force` propune în mod eronat `@lhci/cli@0.1.0`; nu se rulează automat, deoarece ar fi regresie de funcționalitate.

### 2. Override npm selectiv — cea mai mică schimbare candidată pentru alertele reparabile

Dacă proprietarul acceptă abaterea temporară de la range-urile upstream, singura schimbare minimă este în rădăcina `package.json`:

```json
"overrides": {
  "tmp": "0.2.7",
  "uuid": "11.1.1"
}
```

Apoi se regenerează strict `package-lock.json` cu npm, fără a modifica `@lhci/cli` ori fișierele LHCI. Se preferă `tmp@0.2.7` deoarece este latest și acoperă ambele advisory-uri `tmp`; se preferă `uuid@11.1.1`, prima versiune reparată pentru ramura afectată, pentru a reduce saltul inutil.

**Dovadă de fezabilitate (probă izolată, nu în repository):** un proiect temporar cu manifestul/lockfile-ul actual și override-urile de mai sus a trecut `npm install --package-lock-only`, `npm ci --ignore-scripts`, a rezolvat ambele copii `tmp` la 0.2.7 și `uuid` la 11.1.1. `npm audit` nu a mai raportat `tmp` sau `uuid`, iar `@lhci/cli@0.15.1 --version` a răspuns `0.15.1` executat cu Node 20. `tmp@0.2.7` declară Node `>=14.14`.

**Riscuri:**

- npm acceptă override-ul chiar dacă semver-ul părintelui nu îl acceptă; aceasta nu este o garanție contractuală LHCI. `tmp` 0.1→0.2 și `uuid` 8→11 pot schimba comportamente/API/export-uri.
- `tmp` este folosit atât direct de LHCI, cât și nested de `external-editor`; override-ul global schimbă ambele consumatoare.
- testul de versiune dovedește doar încărcarea CLI, nu `autorun`, colectarea Chrome sau assertion-urile de performanță. Nu se consideră remediere până nu trece matricea de verificare de mai jos.
- override-ul nu elimină `extract-zip` și nici pachetele LHCI/Lighthouse 12 care pot rămâne vulnerabile în auditul complet.

### 3. Patch/fork temporar — nu este remedierea minimă

Un fork publicat/consumat prin tarball sau git dependency al `@lhci/cli` ar putea actualiza `tmp`, `uuid`, `inquirer` și Lighthouse/Puppeteer împreună. Este justificat numai dacă override-ul selectiv eșuează testele funcționale sau dacă upstream livrează un patch care poate fi preluat înaintea unei release npm.

Nu se recomandă `patch-package` pentru `extract-zip`: nu există o versiune sau un diff upstream reparat pe care să se poată baza patch-ul, iar schimbarea manuală a codului de extragere de arhive este un patch de securitate cu risc ridicat. Un fork trebuie să aibă owner, pin prin commit/SHA, revizie de licență și plan de eliminare după release upstream.

### 4. Așteptare după upstream — singura cale sigură pentru `extract-zip`

Pentru GHSA-jmr9-qjv8-65gv, păstrarea LHCI actual, documentarea excepției development-only și monitorizarea `extract-zip`, Puppeteer și Lighthouse CI sunt singura poziție defensabilă până la un patch public sau până la migrarea LHCI la un arbore fără acest pachet. Nu se închide alerta ca „reparată local”.

Dacă override-ul de la opțiunea 2 nu trece matricea, se revine la lockfile-ul actual și se așteaptă upstream; nu se înlocuiește LHCI cu un script bazat direct pe `lighthouse` ca hotfix. Acea înlocuire ar schimba comportamentul `autorun`/upload/assert și este un proiect separat.

## Recomandare

1. Păstrați `@lhci/cli@0.15.1` și configurația/fluxurile LHCI actuale.
2. Propuneți doar override-ul temporar `tmp@0.2.7` + `uuid@11.1.1`, cu lockfile regenerat de npm, ca remediere minimă pentru trei din patru advisories (ambele `tmp` și `uuid`).
3. Nu introduceți override pentru `extract-zip`; deschideți/mențineți tracking upstream și documentați excepția cu severitate high, development-only, nepatchabilă local.
4. Dacă orice test LHCI eșuează, abandonați override-urile și nu faceți un patch ad-hoc; escaladați către fork/migrare ca task separat, cu review de securitate.

## Pași de implementare pentru executor (numai după aprobare)

1. În worktree curat, verificați că npm este managerul activ și că versiunea de Node este una din matricea 20/22:

```bash
node --version
npm --version
npm ci
```

2. Adăugați blocul `overrides` din secțiunea 2 la root-ul `package.json`. Nu mutați `@lhci/cli` la `dependencies` și nu modificați `lighthouserc.json`.

3. Regenerați numai lockfile-ul cu npm și inspectați diff-ul pentru a confirma că nu s-au produs actualizări accidentale:

```bash
npm install --package-lock-only --ignore-scripts
git diff -- package.json package-lock.json
npm ci
npm ls @lhci/cli tmp uuid extract-zip --all
```

4. Așteptat după override: toate instanțele `tmp` sunt 0.2.7, `uuid` este 11.1.1, CLI rămâne 0.15.1; `extract-zip@2.0.1` rămâne și este explicit acceptat ca excepție upstream.

5. Puneți în PR un comentariu cu URL-urile celor patru advisory-uri, rezultatul auditului și o dată/owner de reevaluare a upstream-ului. Nu adăugați un `ignore` Dependabot pentru `extract-zip` ca substitut al unui patch.

## Matrice obligatorie de verificare

### Instalare și audit

Se rulează în CI sau într-un worktree curat, cel puțin o dată cu Node 20 și o dată cu Node 22:

```bash
rm -rf node_modules
npm ci
npm ls @lhci/cli tmp uuid extract-zip --all
npm audit --omit=dev --audit-level=moderate
npm audit --audit-level=high --json > audit-all.json || true
node - <<'NODE'
const audit = require('./audit-all.json');
for (const name of ['tmp', 'uuid', 'extract-zip']) {
  console.log(name, audit.vulnerabilities[name]?.severity ?? 'absent');
}
NODE
```

Criterii:

- `npm ci` reușește pe Node 20 (workflow LHCI) și Node 22 (workflow test); avertismentul existent pentru `lighthouse@13.4.1`/Node 20 trebuie consemnat și nu trebuie confundat cu validarea LHCI.
- auditul production (`--omit=dev`) rămâne verde la moderate+.
- auditul complet nu mai listează `tmp` și `uuid`; `extract-zip` rămâne listat și este justificat în PR. Se verifică manual și celelalte vulnerabilități high din raport, nu se pretinde că `npm audit` complet devine verde.
- Dependabot Alerts se verifică autentificat după push: cele trei advisories reparabile trebuie să se închidă/actualizeze conform lockfile-ului; GHSA-jmr9-qjv8-65gv trebuie să rămână deschis cu excepția documentată dacă nu există patch upstream.

### Contract CLI și LHCI

Într-un runner cu Chrome/Chromium disponibil:

```bash
npx lhci --version
npx lhci healthcheck
npm run build
PORT=3000 npm run start > /tmp/undepescuim-next.log 2>&1 &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true' EXIT
for i in $(seq 1 60); do curl -sf http://localhost:3000/ >/dev/null && break; sleep 2; done
curl -fsS http://localhost:3000/ >/dev/null
curl -fsS http://localhost:3000/specii >/dev/null
curl -fsS http://localhost:3000/permis >/dev/null
npm run perf:lhci
```

Criterii:

- `healthcheck` găsește configurația, poate scrie `.lighthouseci/` și găsește Chrome; nu se evaluează ca regresie un mediu local fără Chrome. În investigația curentă, probele locale au trecut config/writable dar au eșuat numai la „Chrome installation not found”.
- `perf:lhci` pornește, colectează toate cele trei URL-uri de câte trei ori, aplică assertion-urile existente și finalizează upload-ul `temporary-public-storage` fără erori de modul/API.
- Se rulează exact jobul `.github/workflows/perf.yml` sau echivalentul lui cu Node 20 înainte de merge. Jobul este acum `continue-on-error`, dar un eșec după override trebuie investigat, nu mascat prin acel flag.

### Regresii generale obligatorii

```bash
npm test -- --coverage
npm run lint
npx playwright install --with-deps chromium
CI=true npx playwright test --grep-invert @data
```

Pentru PR, suitele unit/coverage, lint, E2E seeded și Security workflow trebuie să fie verzi; la merge se păstrează și data-contract/nightly conform `.github/workflows/playwright.yml`. Nu este necesară schimbarea pragurilor, URL-urilor, assertion-urilor sau a workflow-urilor pentru acest hotfix de lockfile.

## Rollback

Dacă instalarea, CLI healthcheck sau `autorun` eșuează, eliminați exact blocul `overrides`, restaurați `package-lock.json` din commitul anterior și rulați din nou `npm ci`, `npm ls` și testul LHCI. Nu folosiți `npm audit fix --force` ca rollback sau remediere.
