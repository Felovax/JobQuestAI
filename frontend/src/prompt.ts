// Lager en ferdig prompt til Claude.ai (eller en annen KI) for å skrive et
// søknadsutkast. Gratis: dere limer den inn selv, ingen API-kostnad.

import type { Job } from "./types";

export function buildPrompt(job: Job, cv: string): string {
  const shortAd = job.description.length < 300;

  return `Hjelp meg å skrive et utkast til jobbsøknad på norsk for stillingen under.

Regler:
- Bruk BARE erfaring, utdanning og ferdigheter som står i CV-en min. Ikke dikt opp noe.
- Koble konkrete ting fra CV-en til kravene i annonsen.
- 250–350 ord, konkret og personlig tone. Unngå floskler som «brennende engasjement».
- Mangler det noe viktig, skriv [FYLL INN: ...] der det trengs.
- Etter søknaden: gi meg 3 ting fra annonsen jeg bør trekke frem i et intervju.

STILLING: ${job.title}
ARBEIDSGIVER: ${job.company || "(ikke oppgitt)"}
STED: ${job.location || "(ikke oppgitt)"}
SØKNADSFRIST: ${job.deadline || "(ikke oppgitt)"}
LENKE: ${job.apply_url}

ANNONSETEKST:
${job.description || "(mangler)"}
${shortAd ? "\n(Annonseteksten over er kort. Åpne lenken og lim inn hele annonsen her for et bedre utkast.)\n" : ""}
MIN CV:
${cv.trim() || "[Lim inn CV-en din her – eller legg den inn under «Min CV» på JobQuestAI, så kommer den med automatisk]"}
`;
}

export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // Reserveløsning for nettlesere som ikke tillater utklippstavle-API-et
    const area = document.createElement("textarea");
    area.value = text;
    document.body.appendChild(area);
    area.select();
    const ok = document.execCommand("copy");
    area.remove();
    return ok;
  }
}
