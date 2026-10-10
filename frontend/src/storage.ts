// Huske "skjult" og "søkt" per stilling i nettleseren.
// Lagres bare lokalt hos den som bruker siden – ingen database.

type Marks = Record<string, "hidden" | "applied">;
const KEY = "jobquest-marks";

export function loadMarks(): Marks {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? "{}");
  } catch {
    return {}; // privat vindu eller blokkert lagring: start tomt
  }
}

export function saveMarks(marks: Marks): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(marks));
  } catch {
    // ikke kritisk – merkingen varer da bare til siden lastes på nytt
  }
}

// CV-teksten brukes i søknadsprompten. Den lagres bare i nettleseren din,
// aldri i repoet (som er offentlig).
const CV_KEY = "jobquest-cv";

export function loadCv(): string {
  try {
    return localStorage.getItem(CV_KEY) ?? "";
  } catch {
    return "";
  }
}

export function saveCv(cv: string): void {
  try {
    localStorage.setItem(CV_KEY, cv);
  } catch {
    // privat vindu: CV-en må limes inn på nytt neste gang
  }
}
