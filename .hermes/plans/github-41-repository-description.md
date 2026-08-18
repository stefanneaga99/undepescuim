# Plan — GitHub #41: descrierea repository-ului

## Goal

Completează exclusiv metadatele GitHub ale repository-ului
`neagastefan99/undepescuim`, astfel încât câmpul **Description** să fie exact:

> Hartă interactivă a apelor de pescuit din România.

Nu se modifică fișiere versionate, cod, README, topic-uri, homepage sau alte
setări ale repository-ului.

## Context verificat

- Issue-ul [#41](https://github.com/neagastefan99/undepescuim/issues/41)
  propune exact formularea de mai sus.
- `README.md:3-4` începe cu aceeași poziționare, apoi detaliază informațiile
  despre ape contractate/necontractate, asociații, permise și reguli. Descrierea
  scurtă este deci coerentă fără a duplica detaliile.
- Înainte de schimbare, API-ul public GitHub raportează `description: null` și
  `homepage: "https://undepescuim.vercel.app"`.
- URL-ul live `https://undepescuim.vercel.app` răspunde HTTP 200.

## Architecture / tech stack

Schimbare exclusivă de metadate GitHub, efectuată din interfața repository-ului
sau prin GitHub CLI/API autentificat. Nu există schimbări de aplicație Next.js,
nu este necesar commit și nu se rulează suite de teste.

## Pași de execuție

1. Autentifică o sesiune GitHub cu drept de administrare pentru
   `neagastefan99/undepescuim` (de exemplu `gh auth login`, dacă este necesar).

2. Actualizează numai câmpul Description. Varianta CLI preferată:

   ```bash
   gh repo edit neagastefan99/undepescuim \
     --description "Hartă interactivă a apelor de pescuit din România."
   ```

   Alternativ, în GitHub: repository → **Settings** → **General** →
   **Description** → introdu exact textul de mai sus → **Save changes**.

   Nu transmite `--homepage`, `--add-topic`, `--visibility` sau alte opțiuni:
   acestea nu fac parte din issue și pot altera metadate existente.

3. Verifică API-ul public după salvare:

   ```bash
   python3 - <<'PY'
   import json, urllib.request
   request = urllib.request.Request(
       "https://api.github.com/repos/neagastefan99/undepescuim",
       headers={"User-Agent": "undepescuim-issue-41-check"},
   )
   with urllib.request.urlopen(request, timeout=20) as response:
       repo = json.load(response)
   assert repo["description"] == "Hartă interactivă a apelor de pescuit din România."
   assert repo["homepage"] == "https://undepescuim.vercel.app"
   print("Description și homepage verificate.")
   PY
   ```

4. Verifică manual pagina principală publică a repository-ului. Description
   trebuie să apară în panoul **About**, iar linkul de homepage trebuie să
   rămână `https://undepescuim.vercel.app`.

5. Confirmă coerența documentară fără editare: compară textul cu
   `README.md:1-7`; primul enunț trebuie să rămână extensia naturală a
   descrierii, nu o formulare contradictorie.

6. Adaugă pe GitHub issue #41 un comentariu cu formularea aplicată și dovezile
   verificărilor (Description, homepage neschimbat, link live accesibil), apoi
   închide issue-ul.

## Verification / acceptance checklist

- [ ] Description API/UI este exact `Hartă interactivă a apelor de pescuit din România.`
- [ ] Description este vizibilă pe pagina principală GitHub a repository-ului.
- [ ] `homepage` este încă `https://undepescuim.vercel.app`.
- [ ] `https://undepescuim.vercel.app` rămâne accesibil (HTTP 200 sau navigare reușită).
- [ ] README-ul nu este modificat și formularea sa de la început rămâne coerentă.
- [ ] Issue #41 are comentariu de dovadă și este închis.

## Risks and trade-offs

- Repository-ul poate cere autentificare/permisiune de administrator pentru
  editarea metadatelor. Aceasta este o dependență de acces, nu un motiv de a
  schimba codul sau fișierele locale.
- Propunerea issue-ului este intenționat concisă. Extinderea cu funcționalități
  (asociații, permise, reguli) ar devia de la formularea explicit acceptată și
  poate reduce lizibilitatea câmpului About.
- Metadatele GitHub nu sunt păstrate în Git; nu există diff, commit sau test de
  aplicație asociat acestei schimbări.
