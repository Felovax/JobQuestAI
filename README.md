# JobQuestAI
Gjøre det lettere for IT-student å finne og søke på jobber

Henter IT-stillinger fra flere kilder hver natt, filtrerer og rangerer dem etter
`config.yaml`, fjerner duplikater og viser alt på én nettside (GitHub Pages).
Helt gratis: ingen database, ingen innlogging, ingen betalte tjenester.

## Struktur

```
config.yaml               ← søkefiltre og selskaper (det eneste dere redigerer til vanlig)
backend/
  main.py                 ← kjører alt og skriver frontend/public/jobs.json
  filters.py              ← filtrering og rangering (score 0–100)
  dedupe.py               ← slår sammen like stillinger fra ulike kilder
  utils.py                ← små hjelpefunksjoner (HTML → tekst, datoer)
  sources/                ← én fil per kilde, alle gir samme format
    nav.py                ← NAV (åpent API)
    jobbnorge.py          ← Jobbnorge (åpent API)
    teamtailor.py         ← karrieresider på Teamtailor (RSS)
    smartrecruiters.py    ← karrieresider på SmartRecruiters (API)
    email_alerts.py       ← jobbvarsler fra FINN, LinkedIn m.fl. via egen Gmail
  tests/                  ← tester (kjør: cd backend && python -m pytest)
frontend/                 ← TypeScript + Vite, uten rammeverk
  src/main.ts             ← liste, søk, filtre, "søkt"/"skjult"
.github/workflows/
  update.yml              ← hver natt: hent → bygg → publiser til Pages
```

**Flyt:** `sources/*` → `filters.py` → `dedupe.py` → `jobs.json` → nettsiden

## Oppsett
1. **Settings → Pages → Source: GitHub Actions**
2. **Settings → Secrets and variables → Actions** (valgfritt, for e-postvarsler):
   - `GMAIL_ADDRESS` – Gmail-kontoen varslene går til
   - `GMAIL_APP_PASSWORD` – app-passord (krever totrinnsbekreftelse på kontoen)
3. **Actions → Oppdater stillinger → Run workflow**
4. Siden ligger på `https://felovax.github.io/JobQuestAI/`

## Legge til et selskap
Finn karrieresiden. Ligger den på Teamtailor (adressen slutter ofte på
`teamtailor.com`, eller `<side>/jobs.rss` virker), legg til i `config.yaml`:

```yaml
  - name: Firmanavn
    source: teamtailor
    url: https://karriere.firma.no
```

## Kjøre lokalt
```bash
pip install -r backend/requirements.txt pytest
python backend/main.py                 # skriver frontend/public/jobs.json
cd backend && python -m pytest         # tester
cd frontend && npm install && npm run dev
```

"Søkt" og "Skjult" lagres bare i nettleseren til den som bruker siden.
