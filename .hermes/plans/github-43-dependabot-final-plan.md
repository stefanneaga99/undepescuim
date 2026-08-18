# GitHub issue #43 — plan final: alerte Dependabot din Lighthouse CI

## Statutul acestui ticket

**Acest ticket documentează exclusiv planul. Nu aplică modificări în repository, nu modifică `package.json`, `package-lock.json`, workflow-uri sau configurația Lighthouse CI și nu introduce un review gate.** Orice implementare ulterioară se face într-un ticket/PR separat, numai după acceptarea explicită a riscului de compatibilitate al override-urilor.

Planul păstrează fluxul actual Lighthouse CI: `@lhci/cli`, scriptul `npm run perf:lhci`, `lighthouserc.json` și jobul `.github/workflows/perf.yml` rămân neschimbate ca funcționalitate, URL-uri, assertion-uri și mecanism de upload.

## Scop și context tehnic

La revizia investigată `cfe25e2`, repository-ul folosește npm (`package-lock.json`, `lockfileVersion: 3`) și declară `@lhci/cli: ^0.15.1` ca devDependency în `package.json`. Versiunea publică curentă a CLI este `0.15.1`; ea fixează `lighthouse@12.6.1` și declară `tmp:^0.1.0`, `uuid:^8.3.1` și `inquirer:^6.3.1`. `lighthouse@13.4.1` declarat separat la root nu înlocuiește copiile Lighthouse 12 instalate pentru LHCI.

Alertele sunt development-only: `npm audit --omit=dev --audit-level=moderate` a raportat 0 vulnerabilități. Aceasta nu elimină nevoia de a trata/documenta alertele de development. Starea/ID-urile exacte ale alertelor Dependabot trebuie reconfirmate în UI GitHub sau prin API autentificat înainte de închidere: API-ul neautentificat a răspuns 401.

## Cele patru alerte și lanțurile tranzitive

| Advisory / severitate | Pachet vulnerabil | Patch minim | Lanț tranzitiv din `package-lock.json` | Concluzie |
|---|---|---:|---|---|
| [GHSA-jmr9-qjv8-65gv](https://github.com/advisories/GHSA-jmr9-qjv8-65gv) / CVE-2026-56876 — High | `extract-zip@2.0.1` | Nu există (`first_patched_version: null`) | `@lhci/cli@0.15.1` → `lighthouse@12.6.1` (inclusiv prin `@lhci/utils@0.15.1`) → `puppeteer-core@24.43.1` → `@puppeteer/browsers@2.13.2` → `extract-zip@2.0.1` | Blocată upstream: `2.0.1` este latest public și nu există patch public. |
| [GHSA-ph9p-34f9-6g65](https://github.com/advisories/GHSA-ph9p-34f9-6g65) / CVE-2026-44705 — High | `tmp@0.1.0`, plus `tmp@0.0.33` nested | `0.2.6+` | (1) `@lhci/cli@0.15.1` → `tmp@0.1.0`; (2) `@lhci/cli@0.15.1` → `inquirer@6.5.2` → `external-editor@3.1.0` → `tmp@0.0.33` | Remediabilă doar prin override temporar, în afara range-urilor upstream. |
| [GHSA-w5hq-g745-h8pq](https://github.com/advisories/GHSA-w5hq-g745-h8pq) / CVE-2026-41907 — Medium (moderate în npm) | `uuid@8.3.2` | `11.1.1+` pentru ramura afectată | `@lhci/cli@0.15.1` → `uuid@8.3.2` | Remediabilă doar prin override temporar, în afara range-ului `^8.3.1` al LHCI. |
| [GHSA-52f5-9888-hmc6](https://github.com/advisories/GHSA-52f5-9888-hmc6) / CVE-2025-54798 — Low | Aceleași `tmp@0.1.0` și `tmp@0.0.33` | `0.2.4+` | Aceleași două lanțuri `tmp` de mai sus | Este acoperită de override-ul `tmp@0.2.7`. |

`^0.1.0`/`^0.0.33` nu permit `tmp@0.2.x`, iar `^8.3.1` nu permite `uuid@11.1.1`; de aceea un upgrade semver compatibil nu este disponibil prin LHCI. Nu se rulează `npm audit fix --force`: propunerea auditului de a coborî la `@lhci/cli@0.1.0` ar fi o regresie și nu este o remediere validă.

## Remedierea minimă recomandată pentru un viitor PR

Păstrați `@lhci/cli@0.15.1` și introduceți exclusiv următorul bloc în `package.json` la root:

```json
"overrides": {
  "tmp": "0.2.7",
  "uuid": "11.1.1"
}
```

Apoi regenerați doar `package-lock.json` cu npm. Nu modificați `@lhci/cli`, `lighthouserc.json`, scripturile npm sau `.github/workflows/perf.yml`.

Motivație:

- `tmp@0.2.7` este versiunea publică latest verificată și acoperă ambele advisory-uri `tmp` (praguri 0.2.4 și 0.2.6).
- `uuid@11.1.1` este primul patch pentru ramura afectată, limitând saltul la minimul necesar.
- O probă izolată a confirmat că npm poate genera lockfile-ul, `npm ci --ignore-scripts` reușește, toate copiile `tmp` se rezolvă la 0.2.7, `uuid` la 11.1.1, auditul nu mai listează `tmp`/`uuid`, iar `@lhci/cli@0.15.1 --version` funcționează pe Node 20.
- Aceasta este însă o abatere temporară de la contractele semver publicate de LHCI/inquirer. Nu devine remediere acceptată până când testele funcționale LHCI nu trec.

## Pașii de implementare, în ordine

1. Creați un worktree curat pentru PR și înregistrați baseline-ul, fără `npm audit fix`:

   ```bash
   node --version
   npm --version
   npm ci
   npm ls @lhci/cli lighthouse tmp uuid extract-zip --all
   npm audit --omit=dev --audit-level=moderate
   npm audit --audit-level=high --json > audit-before.json || true
   ```

2. În `package.json`, adăugați numai `overrides.tmp = "0.2.7"` și `overrides.uuid = "11.1.1"`. Nu mutați LHCI din `devDependencies`, nu actualizați direct Lighthouse și nu schimbați configurația de performanță.

3. Regenerați lockfile-ul strict prin npm și inspectați schimbarea înainte de instalarea finală:

   ```bash
   npm install --package-lock-only --ignore-scripts
   git diff --check -- package.json package-lock.json
   git diff -- package.json package-lock.json
   rm -rf node_modules
   npm ci
   npm ls @lhci/cli lighthouse tmp uuid extract-zip --all
   ```

   Rezultatul așteptat este `@lhci/cli@0.15.1` neschimbat, toate instanțele `tmp@0.2.7`, `uuid@11.1.1` și persistența explicită a `extract-zip@2.0.1`.

4. Rulați auditul și salvați rezultatul în logul PR/CI, nu ca pretext pentru a declara auditul complet verde:

   ```bash
   npm audit --omit=dev --audit-level=moderate
   npm audit --audit-level=high --json > audit-after.json || true
   node - <<'NODE'
   const audit = require('./audit-after.json');
   for (const name of ['tmp', 'uuid', 'extract-zip']) {
     console.log(name, audit.vulnerabilities[name]?.severity ?? 'absent');
   }
   NODE
   ```

5. Validați LHCI pe un runner care are Chrome/Chromium și repetați jobul de performanță cu Node 20, care este versiunea din `.github/workflows/perf.yml`:

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

6. Executați regresiile generale și CI-ul relevant; nu modificați praguri sau workflow-uri pentru a face testele să treacă:

   ```bash
   npm test -- --coverage
   npm run lint
   npx playwright install --with-deps chromium
   CI=true npx playwright test --grep-invert @data
   ```

   Rulați și instalarea/auditul pe Node 22. Jobul unit test folosește Node 22, iar `lighthouse@13.4.1` de la root declară `>=22.19`; faptul că LHCI rulează pe arborele Lighthouse 12 nu elimină necesitatea de a testa explicit Node 20 și 22.

7. După push, verificați autentificat alertele Dependabot. Confirmați că cele trei advisories remediabile (`tmp` high/low și `uuid` medium) sunt închise sau actualizate conform lockfile-ului. Nu pretindeți închiderea lui `extract-zip` fără patch upstream.

## Vulnerabilitatea blocată upstream: `extract-zip`

GHSA-jmr9-qjv8-65gv rămâne excepție documentată, cu severitate High, development-only și fără remediere publică. `extract-zip@2.0.1` este latest iar advisory-ul nu oferă `first_patched_version`; nu adăugați un override arbitrar și nu aplicați `patch-package` fără un patch de securitate upstream verificabil.

În viitorul PR, documentați în descriere/comentariu:

- advisory-ul, CVE-ul, lanțul complet și faptul că pachetul este accesibil numai prin toolchain-ul LHCI de development;
- data verificării, owner-ul responsabil și un termen de reevaluare;
- linkuri către upstream: `GoogleChrome/lighthouse-ci`, dependențele Lighthouse/Puppeteer și advisory;
- decizia că alerta nu este marcată „reparată local” și nu este ignorată/suprimată în Dependabot ca substitut al patch-ului.

Monitorizarea trebuie să urmărească release-urile `@lhci/cli`, `lighthouse`, `@puppeteer/browsers` și `extract-zip`, precum și actualizările advisory-ului GitHub. La apariția unei versiuni patch, deschideți un follow-up pentru upgrade normal și eliminați documentația de excepție doar după verificarea auditului și a LHCI.

Dacă override-urile testate eșuează, nu creați un hotfix prin înlocuirea `lhci autorun` cu un script Lighthouse direct. Evaluați separat un fork/pin al LHCI care actualizează coerent `tmp`, `uuid`, `inquirer` și arborele Lighthouse/Puppeteer; acel proiect necesită owner, SHA/tarball pin, analiză de licență/securitate și plan de eliminare după release upstream.

## Teste obligatorii și criterii de acceptare pentru implementarea viitoare

1. `npm ci` reușește atât pe Node 20, cât și pe Node 22; lockfile-ul este determinist și nu conține modificări accidentale de dependențe.
2. `npm ls @lhci/cli lighthouse tmp uuid extract-zip --all` confirmă CLI 0.15.1, `tmp@0.2.7`, `uuid@11.1.1` și excepția `extract-zip@2.0.1`.
3. Auditul production cu `--omit=dev --audit-level=moderate` rămâne verde; auditul complet nu mai enumeră `tmp` și `uuid`. `extract-zip` poate rămâne, dar trebuie raportat ca blocaj upstream. Nu se afirmă că toate vulnerabilitățile din auditul complet au dispărut.
4. `npx lhci healthcheck` și `npm run perf:lhci` trec cu Chrome disponibil, colectează `/`, `/specii` și `/permis` de trei ori, păstrează assertion-urile mobile existente și finalizează upload-ul fără eroare de modul/API. Un laptop fără Chrome nu este o dovadă de regresie; este necesar runner CI sau mediu echivalent cu browser disponibil.
5. `npm test -- --coverage`, `npm run lint`, E2E Playwright seeded și workflow-ul Security sunt verzi. Jobul LHCI are în prezent `continue-on-error`, dar orice eșec apărut după override se investighează și nu se maschează prin acel flag.
6. Dependabot este verificat autentificat: alertele remediabile au statusul așteptat, iar `extract-zip` are documentație și tracking upstream active.
7. Nu sunt schimbate URL-urile, assertion-urile, pragurile, joburile sau comportamentul de upload LHCI.

## Riscuri, incompatibilități și revenire

| Risc | Control |
|---|---|
| `tmp` 0.1→0.2 și `uuid` 8→11 pot schimba API-uri/comportament, iar override-ul depășește range-urile LHCI/inquirer. | Nu acceptați doar instalarea ca dovadă; executați healthcheck, autorun complet și matricea Node 20/22. |
| Override-ul global `tmp` schimbă atât consumatorul direct LHCI, cât și `external-editor` din `inquirer`. | Inspectați arborele cu `npm ls`; păstrați testele LHCI și regresiile generale. |
| `extract-zip` rămâne High și auditul complet poate include și alte vulnerabilități. | Nu pretindeți audit complet verde; documentați excepția și monitorizați upstream. |
| Node 20 în perf/E2E este formal sub cerința `>=22.19` a Lighthouse-ului root 13.4.1. | Mențineți testarea explicită în ambele versiuni; nu modificați versiunea de Node a workflow-ului în acest hotfix. |
| `npm audit fix --force` poate propune downgrade LHCI. | Este interzis pentru acest demers. |

Plan de revenire: dacă `npm ci`, `lhci healthcheck`, `npm run perf:lhci` sau regresiile eșuează, eliminați exact blocul `overrides`, restaurați `package-lock.json` din commitul anterior, apoi rulați `npm ci`, `npm ls` și validarea LHCI pentru a confirma revenirea. Nu utilizați `npm audit fix --force` ca rollback. Păstrați alertele/documentația upstream deschise și escaladați alternativa fork/migrare într-un ticket separat.

## Surse și constatări de referință

- Issue: https://github.com/neagastefan99/undepescuim/issues/43
- Inventarul verificat din taskul părinte `t_74d551de`: `.hermes/plans/github-43-dependabot-alert-inventory.md`.
- Evaluarea de remediere și proba izolată din taskul părinte `t_b3130d4a`: `.hermes/plans/github-43-lhci-remediation-options.md`.
- Advisory-uri GitHub: [GHSA-jmr9-qjv8-65gv](https://github.com/advisories/GHSA-jmr9-qjv8-65gv), [GHSA-ph9p-34f9-6g65](https://github.com/advisories/GHSA-ph9p-34f9-6g65), [GHSA-w5hq-g745-h8pq](https://github.com/advisories/GHSA-w5hq-g745-h8pq), [GHSA-52f5-9888-hmc6](https://github.com/advisories/GHSA-52f5-9888-hmc6).
- Lighthouse CI releases: https://api.github.com/repos/GoogleChrome/lighthouse-ci/releases?per_page=10
- Dovezi locale: `package.json`, `package-lock.json`, `.github/dependabot.yml`, `.github/workflows/perf.yml`, `lighthouserc.json`; comenzile `npm view`, `npm ls` și `npm audit` consemnate în documentele părinte.
