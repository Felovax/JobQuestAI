# JobQuestAI
Gjøre det lettere for IT-student å finne og søke på jobber

Henter IT-stillinger fra flere kilder hver natt, filtrerer og rangerer dem etter
`config.yaml`, fjerner duplikater og viser alt på én nettside (GitHub Pages).
Helt gratis: ingen database, ingen innlogging, ingen betalte tjenester.

## Struktur

```
config.yaml               ← søkefiltre og selskaper vi følger (det eneste dere trenger å redigere)
backend/                  ← Python: henter, filtrerer, fjerner duplikater
  main.py                 ← kjører alt og skriver frontend/public/jobs.json
  filters.py              ← filtrering og rangering
  dedupe.py               ← slår sammen like stillinger fra ulike kilder
  sources/                ← én fil per kilde
    nav.py                ← NAV (åpent API)
    jobbnorge.py          ← Jobbnorge (åpent API)
    teamtailor.py         ← karrieresider på Teamtailor (RSS)
    smartrecruiters.py    ← karrieresider på SmartRecruiters (API)
    email_alerts.py       ← jobbvarsler fra FINN, LinkedIn m.fl. via egen Gmail
frontend/                 ← TypeScript + Vite: viser stillingene
  public/jobs.json        ← generert av backend
  src/main.ts             ← liste, søk og filtre
.github/workflows/
  update.yml              ← hver natt: hent stillinger → bygg → publiser til Pages
```

## Flyt
`sources/*` → `filters.py` → `dedupe.py` → `jobs.json` → nettsiden
