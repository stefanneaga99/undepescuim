# Plan: Google Form Crowdsourced Water Reporting for UndePescuim.ro

**Date:** 2026-08-11
**Task:** t_c21762e3
**Repo:** `/home/stefan/undepescuim`
**Deployment:** GitHub Pages (static Next.js export)

---

## Assumptions (Open Questions Still Unanswered)

The following assumptions are made for planning purposes. Each has a "default" that can be changed later with minimal rework.

| # | Question | Assumed Default | Impact if Changed |
|---|----------|----------------|-------------------|
| 1 | Report volume | ~5-10/week (low) | Only affects moderation workflow; no code change |
| 2 | Reporter email | Optional | Changing to required is a 1-field toggle in Google Forms |
| 3 | Moderation visibility | Private (no public log) | Adding a public log page is +1 component |
| 4 | Report types | 3 core: date incorecte, apă lipsă, confirmare pescuit | Adding more is a form edit + optional filter in moderation sheet |
| 5 | Language | Romanian only | Bilingual would mean duplicating form fields |
| 6 | Deployment | GitHub Pages confirmed | No impact — plan assumes static export |

**Default position: build for Romanian-only, low volume, private moderation.**

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  UndePescuim.ro (static Next.js site on GitHub Pages)       │
│                                                             │
│  ┌─────────┐    ┌──────────────┐    ┌───────────────────┐  │
│  │ Footer  │    │ Water Detail │    │ /raporteaza page  │  │
│  │ "Raport-│    │ Cards        │    │ (optional landing  │  │
│  │ ează o  │    │ [Raportează] │    │  page with info)  │  │
│  │ problemă│    │ per-card btn │    │                   │  │
│  └────┬────┘    └──────┬───────┘    └────────┬──────────┘  │
│       │                │                     │              │
│       └────────────────┼─────────────────────┘              │
│                        │                                    │
│                external link                                │
│                        ▼                                    │
│         https://forms.gle/xxxxxxxxxxxx                      │
│         (Google Form, opens in new tab)                     │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ responses flow into
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Google Workspace                                           │
│                                                             │
│  ┌─────────────────┐     ┌──────────────────────────────┐  │
│  │  Google Form    │────▶│  Google Sheets               │  │
│  │  (Romanian UI)  │     │  (Moderation Queue)          │  │
│  │                 │     │                              │  │
│  │  • Report type  │     │  Cols: Timestamp, Type,      │  │
│  │  • Water name   │     │  Water, Description,         │  │
│  │  • Description  │     │  Email, Status, Moderator    │  │
│  │  • Email (opt)  │     │  Notes, Resolution           │  │
│  └─────────────────┘     └──────────────────────────────┘  │
│                                      │                      │
│                                      │ email notification   │
│                                      ▼                      │
│                              maintainer@ inbox              │
└─────────────────────────────────────────────────────────────┘
```

**Data flow:** User report → Google Form → Google Sheets → maintainer reviews → maintainer updates static JSON in repo → redeploy

---

## Step-by-Step Implementation Plan

### Phase 1: Google Form Setup (Manual, ~15 min)

**Owner: human (maintainer with Google account)**

#### 1.1 Create the Form

Go to https://forms.google.com and create a new form.

**Form settings:**
- Title: `Raportează o problemă — UndePescuim.ro`
- Description: `Folosește acest formular pentru a raporta informații incorecte sau probleme legate de apele de pescuit listate pe UndePescuim.ro.`
- Collect email addresses: OFF (collect manually as optional field below)
- Limit to 1 response: OFF (people may report multiple issues)
- Show progress bar: OFF (short form)
- Confirmation message: `Mulțumim! Raportul tău a fost înregistrat. Îl vom verifica în cel mult 7 zile.`

#### 1.2 Form Fields

**Section 1: Tipul raportului (Report Type)**

| # | Field | Type | Required | Options / Notes |
|---|-------|------|----------|-----------------|
| 1 | `Tipul raportului` | Dropdown (Multiple choice) | YES | `"Date incorecte (nume, limite, dimensiune greșită)"`, `"Apă dispărută / nelistată"`, `"Confirmare pescuit (se poate pescui aici)"`, `"Altă problemă"` |
| 2 | `Numele apei` | Short answer | YES | Help text: `"Numele lacului sau râului, așa cum apare pe hartă (ex: Lacul Tarnița, Râul Someș)"` |
| 3 | `Descrierea problemei` | Paragraph (Long answer) | YES | Help text: `"Descrie cât mai precis problema: ce date sunt greșite, ce ai observat la fața locului, etc."` |
| 4 | `Email (opțional)` | Short answer → with "Email validation" | NO | Help text: `"Lasă-ți adresa de email dacă dorești să te contactăm pentru clarificări."` |

**Section 2: Conditional fields (per report type) — use Google Forms "Go to section based on answer"**

| Report Type | Follow-up Question | Type |
|-------------|-------------------|------|
| "Date incorecte" | `Ce date sunt greșite?` | Checkboxes: Nume, Județ, Limite sector, Dimensiune, Asociație, Altele |
| "Apă dispărută / nelistată" | `Unde se află apa?` | Short answer (county/locality) |
| "Confirmare pescuit" | `Data observației` | Date picker |

#### 1.3 reCAPTCHA (Optional, Recommended)

In Google Forms settings → "Presentation" → enable "Collect email addresses" is not needed. For spam protection:

- **Option A (simple):** Google Forms has built-in reCAPTCHA for public forms when "Limit to 1 response" is OFF — it auto-enables for forms not requiring sign-in
- **Option B (explicit):** No additional setup needed; Google's anti-spam is automatic for public forms

**Decision:** Use built-in Google Forms spam protection. Not bulletproof but good enough for ~5-10 reports/week.

#### 1.4 Response Destination → Google Sheets

1. In the form, go to "Responses" tab
2. Click "Link to Sheets" (green Sheets icon)
3. Create a new spreadsheet: `UndePescuim — Rapoarte (Moderation Queue)`
4. This auto-creates column headers matching form questions
5. Add these extra columns manually (right of auto-generated columns):

| Extra Column | Purpose |
|-------------|---------|
| `Status` | Dropdown: `Nou`, `În verificare`, `Rezolvat`, `Respins`, `Duplicat` |
| `Notă moderator` | Free text for internal notes |
| `Rezoluție` | What was done (e.g., "Actualizat JSON #142", "Confirmat pe teren") |
| `Moderator` | Name/initials of who handled it |
| `Data rezolvare` | Date resolved |

#### 1.5 Email Notifications

In the linked Google Sheet:
1. Tools → Notification rules (or Extensions → Apps Script)
2. **Option A (simple):** "Notify me when a user submits a form" → email digest (daily or immediately)
3. **Option B (Apps Script, better):** Add a Google Apps Script trigger that sends an email on form submit:

```javascript
// Tools → Script Editor, paste this:
function onFormSubmit(e) {
  var sheet = e.range.getSheet();
  var row = e.range.getRow();
  var values = sheet.getRange(row, 1, 1, sheet.getLastColumn()).getValues()[0];
  var type = values[2]; // Column C = report type
  var water = values[3]; // Column D = water name

  MailApp.sendEmail({
    to: "maintainer@example.com",  // ← CHANGE THIS
    subject: "[UndePescuim] Raport nou: " + type + " — " + water,
    body: "Un raport nou a fost trimis.\n\nTip: " + type +
          "\nApă: " + water +
          "\n\nVezi foaia: " + sheet.getParent().getUrl()
  });
}
```

Then: Edit → Current project's triggers → Add trigger → `onFormSubmit` → On form submit.

---

### Phase 2: Site Integration (Code Changes, ~30 min)

#### 2.1 Create Footer Component with Report Link

**File:** `src/components/layout/footer.tsx`

```tsx
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

const GOOGLE_FORM_URL = "https://forms.gle/XXXXXXXX"; // ← Replace with real URL

export function Footer() {
  return (
    <footer className="border-t bg-muted/30 mt-auto">
      <div className="mx-auto max-w-7xl px-4 py-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="text-sm text-muted-foreground">
          © {new Date().getFullYear()} UndePescuim.ro — Harta apelor de pescuit din România
        </div>
        <a
          href={GOOGLE_FORM_URL}
          target="_blank"
          rel="noopener noreferrer"
        >
          <Button variant="outline" size="sm">
            <AlertTriangle className="mr-1.5 size-3.5" />
            Raportează o problemă
          </Button>
        </a>
      </div>
    </footer>
  );
}
```

#### 2.2 Integrate Footer into Root Layout

**File:** `src/app/layout.tsx`

Add the Footer import and render:

```tsx
import { Footer } from "@/components/layout/footer";
// ...
export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ro" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">
        {children}
        <Footer />
      </body>
    </html>
  );
}
```

**Note:** Change `lang="en"` to `lang="ro"` for Romanian.

#### 2.3 Optional: Water Detail Card "Report" Link

When water detail cards exist (future task), add a "Raportează" link that pre-fills the water name via the Google Form URL parameter:

```tsx
// In WaterDetailCard component
const reportUrl = `${GOOGLE_FORM_URL}?usp=pp_url&entry.XXXXXXXX=${encodeURIComponent(water.name)}`;

// Use entry.XXXXXXXX = the prefill ID for the "Numele apei" field
```

**How to find the prefill entry ID:**
1. Open the Google Form
2. Click ⋮ → "Get pre-filled link"
3. Fill in the water name field
4. Click "Get link"
5. Inspect the URL — it will contain `entry.123456789=...`
6. Extract the entry ID (e.g., `entry.789012345`) and use it in the code

#### 2.4 Google Form URL as Environment Variable

**File:** `next.config.ts`

```ts
const nextConfig: NextConfig = {
  env: {
    NEXT_PUBLIC_GOOGLE_FORM_URL: "https://forms.gle/XXXXXXXX",
  },
};
export default nextConfig;
```

Then use `process.env.NEXT_PUBLIC_GOOGLE_FORM_URL` instead of hardcoding.

#### 2.5 Optional: Landing Page at `/raporteaza`

**File:** `src/app/raporteaza/page.tsx`

A small info page that explains the reporting process before redirecting to the actual Google Form. Good for SEO and user trust.

```tsx
import { AlertTriangle, ExternalLink, CheckCircle, Clock, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";

const FORM_URL = process.env.NEXT_PUBLIC_GOOGLE_FORM_URL!;

export default function RaporteazaPage() {
  return (
    <main className="mx-auto max-w-2xl px-4 py-16">
      <h1 className="text-3xl font-bold mb-6">Raportează o problemă</h1>

      <div className="space-y-6 text-muted-foreground mb-8">
        <div className="flex gap-3">
          <AlertTriangle className="size-5 shrink-0 mt-0.5 text-amber-500" />
          <div>
            <p className="font-medium text-foreground">Ai găsit o eroare?</p>
            <p>Date incorecte despre o apă de pescuit? O apă care lipsește de pe hartă? Folosește formularul de mai jos.</p>
          </div>
        </div>

        <div className="flex gap-3">
          <CheckCircle className="size-5 shrink-0 mt-0.5 text-green-500" />
          <div>
            <p className="font-medium text-foreground">Ce se întâmplă după?</p>
            <p>Raportul tău ajunge într-o coadă de moderare. Îl verificăm în maxim 7 zile și actualizăm datele de pe site.</p>
          </div>
        </div>

        <div className="flex gap-3">
          <Shield className="size-5 shrink-0 mt-0.5 text-blue-500" />
          <div>
            <p className="font-medium text-foreground">Fără cont, fără înscriere</p>
            <p>Formularul este anonim — emailul este opțional și folosit doar pentru clarificări.</p>
          </div>
        </div>
      </div>

      <a href={FORM_URL} target="_blank" rel="noopener noreferrer">
        <Button size="lg" className="w-full sm:w-auto">
          Deschide formularul
          <ExternalLink className="ml-2 size-4" />
        </Button>
      </a>
    </main>
  );
}
```

---

### Phase 3: Moderation Workflow (Operational, No Code)

#### 3.1 Daily/Weekly Moderation Checklist

1. Open Google Sheets moderation queue (`UndePescuim — Rapoarte`)
2. Filter by `Status = "Nou"` or `"În verificare"`
3. For each report:
   - **"Date incorecte":** Cross-reference the water in `/data/waters.json` or the probe data. Fix the field in the JSON source.
   - **"Apă dispărută / nelistată":** Research the water (OSM, ANPA, Google Maps). If verified, add it to the data pipeline.
   - **"Confirmare pescuit":** If multiple confirmations for the same water, consider flagging it as "confirmed" in the data.
   - **"Altă problemă":** Triage manually.
4. Update `Status` → `"Rezolvat"` or `"Respins"` with a note in `Rezoluție`.
5. After fixing data, commit + push to the repo → redeploy via GitHub Pages.

#### 3.2 Data Update Pipeline (Future Enhancement)

For high-volume moderation, consider a semi-automated pipeline:

```bash
# Script that reads resolved rows from Google Sheets and patches waters.json
# Not needed for ~5/week but useful at 50+/week
```

---

### Phase 4: Optional Enhancements (Not in MVP)

| Enhancement | Effort | When |
|-------------|--------|------|
| Public "Rapoarte recente" page | Medium (~2h) | If transparency is desired; needs Google Sheets API or manual JSON export |
| reCAPTCHA v3 on the site itself | Low (~30m) | If spam becomes a problem (>10 spam/week) |
| Bilingual RO/EN form | Medium (~1h) | If English-speaking anglers use the site |
| Auto-pre-fill water name from URL param | Low (~15m) | When water detail cards exist |
| Slack/Discord notification for new reports | Low (~30m) | Via Zapier or Google Apps Script webhook |
| Google Sheets → JSON export for "Rapoarte recente" | Medium (~2h) | Needs Google Sheets API v4 + service account |

---

## File Changes Summary

| File | Action | Purpose |
|------|--------|---------|
| `src/components/layout/footer.tsx` | CREATE | Footer with "Raportează o problemă" link |
| `src/app/layout.tsx` | MODIFY | Add Footer, change lang to "ro" |
| `next.config.ts` | MODIFY | Add `NEXT_PUBLIC_GOOGLE_FORM_URL` env var |
| `src/app/raporteaza/page.tsx` | CREATE (optional) | Info/landing page for reporting |
| `src/components/water/water-detail-card.tsx` | CREATE (future) | Water detail card with pre-filled report link |

**No new dependencies required.** All UI uses existing shadcn/ui Button and lucide-react icons.

---

## Verification Checklist

- [ ] Google Form created with correct Romanian labels and 4 report types
- [ ] Form responses flow into Google Sheets with extra moderation columns
- [ ] Email notification fires on new submission (test with your own email)
- [ ] Footer renders on all pages with "Raportează o problemă" button
- [ ] Button opens Google Form in a new tab
- [ ] `lang="ro"` in HTML tag
- [ ] `next build` succeeds, `next export` works for GitHub Pages
- [ ] No CORS or CSP issues (form is an external link, not embedded)
- [ ] Test submission → appears in Sheets → moderator can change status

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Google Form public URL changes | Broken link | Env var makes single-point update; would need redeploy |
| Spam submissions flood moderation queue | Noise | Built-in Google reCAPTCHA; escalate to reCAPTCHA v3 on site if needed |
| No water name validation (users type free-text) | Hard to match to database | Pre-filled water name from detail cards fixes most cases; for footer submissions, accept fuzzy match |
| Google account dependency | Bus factor | Form + Sheet owned by project Google account; share with multiple maintainers |
| Form submissions not actionable (vague descriptions) | Wasted moderation time | Help text guides users; accept that some reports will be "Respins" |
