# Issue #43 — inventar factual al alertelor Dependabot Lighthouse CI

## Scop și limite

Acest document inventariază cele patru alerte declarate în GitHub issue [#43](https://github.com/neagastefan99/undepescuim/issues/43), la revizia locală `cfe25e2`. Nu schimbă manifestele, lockfile-ul sau configurația de dependențe.

Observație de acces: endpointul GitHub Dependabot Alerts a răspuns `401 Unauthorized` fără autentificare. Prin urmare, faptul că alertele sunt încă deschise și asocierea lor exactă cu manifestul provin din issue #43; versiunile, lanțurile și advisory-urile au fost verificate independent din `package-lock.json`, npm registry, GitHub Advisory API și `npm audit`.

## Rezumat factual

| Alertă / severitate | Pachet instalat și versiune vulnerabilă | Versiune minimă remediată | Lanț tranzitiv exact din lockfile | Directă? / fișiere relevante | Dovezi și stare upstream |
|---|---|---|---|---|---|
| [GHSA-jmr9-qjv8-65gv](https://github.com/advisories/GHSA-jmr9-qjv8-65gv) / CVE-2026-56876 — **High** | `extract-zip@2.0.1` | **Niciuna** (`first_patched_version: null`; interval afectat `<=2.0.1`) | `@lhci/cli@0.15.1` → `lighthouse@12.6.1` (și prin `@lhci/utils@0.15.1` → al doilea `lighthouse@12.6.1`) → `puppeteer-core@24.43.1` → `@puppeteer/browsers@2.13.2` → `extract-zip@2.0.1` | Tranzitivă, dev-only; root `package.json` declară `@lhci/cli: ^0.15.1`; rezoluțiile sunt în `package-lock.json` (`node_modules/extract-zip`, `node_modules/@puppeteer/browsers`, copii nested ale `lighthouse`/`puppeteer-core`). | GitHub Advisory API confirmă că toate versiunile publicate ale `extract-zip` până la `2.0.1` sunt vulnerabile și nu indică patch. npm registry are `2.0.1` ca latest. Aceasta este blocată upstream chiar înainte de compatibilitatea LHCI. |
| [GHSA-ph9p-34f9-6g65](https://github.com/advisories/GHSA-ph9p-34f9-6g65) / CVE-2026-44705 — **High** | Două instanțe afectate: `tmp@0.1.0` (la root, cerut de CLI) și `tmp@0.0.33` (nested sub `external-editor`) | `0.2.6` | (1) `@lhci/cli@0.15.1` → `tmp@0.1.0`; (2) `@lhci/cli@0.15.1` → `inquirer@6.5.2` → `external-editor@3.1.0` → `tmp@0.0.33` | Tranzitivă, dev-only; `package.json`/`package-lock.json`. În lock, CLI cere `tmp: ^0.1.0`; `external-editor` cere `tmp: ^0.0.33`. | Advisory confirmă intervalul `<0.2.6`, patch `0.2.6`. Ambele range-uri npm sunt incompatibile cu `0.2.6` (`^0.1.0` permite doar `<0.2.0`, iar `^0.0.33` doar `<0.0.34`). npm registry confirmă că `tmp@0.2.6`/`0.2.7` există, dar latest `@lhci/cli` rămâne `0.15.1` și își păstrează range-urile vechi. Blocajul este deci la metadatele/release-ul LHCI, nu lipsa patch-ului `tmp`. |
| [GHSA-w5hq-g745-h8pq](https://github.com/advisories/GHSA-w5hq-g745-h8pq) / CVE-2026-41907 — **Medium** (npm o afișează `moderate`) | `uuid@8.3.2` | `11.1.1` pentru ramura `<11.1.1` (advisory-ul mai listează `12.0.1` și `13.0.1` pentru intervalele lor distincte) | `@lhci/cli@0.15.1` → `uuid@8.3.2` | Tranzitivă, dev-only; root `package.json`/`package-lock.json`. CLI declară `uuid: ^8.3.1`; lock rezolvă `8.3.2`. | Advisory confirmă intervalul `<11.1.1` și patch `11.1.1`. `^8.3.1` nu poate selecta compatibil `11.1.1`. npm registry și GitHub releases arată că `@lhci/cli@0.15.1` este cea mai nouă versiune publicată; metadatele acelei versiuni încă cer `^8.3.1`. Blocaj upstream LHCI. |
| [GHSA-52f5-9888-hmc6](https://github.com/advisories/GHSA-52f5-9888-hmc6) / CVE-2025-54798 — **Low** | Aceleași două instanțe `tmp@0.1.0` și `tmp@0.0.33` | `0.2.4` | (1) `@lhci/cli@0.15.1` → `tmp@0.1.0`; (2) `@lhci/cli@0.15.1` → `inquirer@6.5.2` → `external-editor@3.1.0` → `tmp@0.0.33` | Tranzitivă, dev-only; aceleași `package.json` și `package-lock.json` ca alerta GHSA-ph9p-34f9-6g65. | Advisory confirmă intervalul `<=0.2.3`, patch `0.2.4`. Nici `^0.1.0`, nici `^0.0.33` nu admite `0.2.4`; astfel, aceeași versiune LHCI publicată blochează actualizarea compatibilă. |

## Manifest, lockfile și lanțuri relevante

- Manifestul root: `package.json`, devDependency `@lhci/cli: "^0.15.1"` (linia 45).
- Lockfile: `package-lock.json` (lockfileVersion 3); intrările relevante sunt:
  - `node_modules/@lhci/cli` — `0.15.1`, cu `lighthouse: 12.6.1`, `inquirer: ^6.3.1`, `tmp: ^0.1.0`, `uuid: ^8.3.1`;
  - `node_modules/@lhci/utils` — `0.15.1`, cu `lighthouse: 12.6.1`;
  - două copii ale `lighthouse@12.6.1`, sub CLI și utils; fiecare rezolvă `puppeteer-core@24.43.1`;
  - `node_modules/@puppeteer/browsers` — `2.13.2`, cu `extract-zip: ^2.0.1`;
  - `node_modules/inquirer` — `6.5.2` → `external-editor@3.1.0` → nested `tmp@0.0.33`;
  - rădăcina hoisted `node_modules/tmp` — `0.1.0`, și `node_modules/uuid` — `8.3.2`.
- `package.json` declară separat `lighthouse: ^13.4.1`, rezolvat ca `13.4.1`; aceasta folosește propriul arbore modern (`puppeteer-core@25.7.0` → nested `@puppeteer/browsers@3.2.0`) și **nu înlocuiește** copiile `lighthouse@12.6.1` cerute exact de LHCI.
- `.github/dependabot.yml` scanează npm la `/` săptămânal. Nu conține excluderi pentru aceste patru alerte.

## Verificări executate

```text
npm audit --omit=dev --audit-level=moderate
=> found 0 vulnerabilities

npm audit --json
=> 10 vulnerabilități totale în arborele complet; pachetele relevante confirmate:
   extract-zip (high), tmp (high, include și low), uuid (moderate)
```

Rezultatul `--omit=dev` confirmă afirmația issue-ului că aceste pachete nu sunt în runtime-ul de producție. Nu înseamnă că alertele Dependabot de development pot fi ignorate.

## Dovezi ale blocajului upstream

1. npm registry a raportat `@lhci/cli@0.15.1` drept latest; ultima publicare este 2025-06-25. GitHub Releases pentru `GoogleChrome/lighthouse-ci` indică de asemenea `v0.15.1` drept cea mai recentă release publicată.
2. Metadatele npm ale `@lhci/cli@0.15.1` fixează exact dependențele problematice/range-urile incompatibile: `lighthouse: 12.6.1`, `tmp: ^0.1.0`, `uuid: ^8.3.1`, `inquirer: ^6.3.1`.
3. Pentru `extract-zip`, GHSA are `first_patched_version: null`; npm registry nu oferă o versiune mai nouă de `2.0.1`. Un override nu poate produce o remediere publicată.
4. Pentru `tmp` și `uuid`, versiunile reparate există în registry, însă cer depășirea major/minor incompatibilă a contractului manifestat de LHCI. Orice `overrides` trebuie evaluat ca schimbare de compatibilitate, nu ca simplu refresh al lockfile-ului.

## Incertitudini / întrebări obligatorii pentru planul de implementare

1. Endpointul Dependabot nu poate fi citit fără token cu permisiunea potrivită. Înainte de închidere, executorul trebuie să confirme în UI/API autentificat ID-urile alertelor, statusul lor final și dacă GitHub grupează cele două copii `tmp` într-o singură alertă per GHSA (issue-ul declară exact patru alerte).
2. `npm audit --json` oferă un `fixAvailable` aparent eronat pentru unele noduri (`@lhci/cli@0.1.0`, regresie). Nu trebuie urmat automat: npm registry confirmă că `0.15.1` este latest.
3. Nu s-a demonstrat compatibilitatea runtime/CLI a override-urilor `tmp@0.2.6+` sau `uuid@11.1.1+`. Planul trebuie să decidă între un fork/patch upstream LHCI, override testat, înlocuirea LHCI sau acceptarea documentată a riscului development-only pentru `extract-zip` fără patch.
4. Alerta `extract-zip` nu are remediere publicată la sursele consultate; criteriul issue-ului „nicio vulnerabilitate remediabilă high/medium” trebuie interpretat separat de această excepție blocată upstream.

## Surse primare

- Issue: https://github.com/neagastefan99/undepescuim/issues/43
- Advisory APIs: https://api.github.com/advisories/GHSA-jmr9-qjv8-65gv ; https://api.github.com/advisories/GHSA-ph9p-34f9-6g65 ; https://api.github.com/advisories/GHSA-w5hq-g745-h8pq ; https://api.github.com/advisories/GHSA-52f5-9888-hmc6
- Lighthouse CI releases: https://api.github.com/repos/GoogleChrome/lighthouse-ci/releases?per_page=10
- Local lockfile/manifest: `package.json`, `package-lock.json`, `.github/dependabot.yml`
- Local commands: `npm audit --json`, `npm audit --omit=dev --audit-level=moderate`, `npm view @lhci/cli version time --json`, `npm view @lhci/cli@0.15.1 dependencies --json`.
