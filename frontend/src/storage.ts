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
