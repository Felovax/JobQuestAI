import type { Job } from "./types";
import "./style.css";

// TODO: hent jobs.json, vis liste med søk/filtre, beskrivelse og søk-lenke
async function main() {
  const jobs: Job[] = await fetch("./jobs.json").then((r) => r.json());
  document.querySelector("#app")!.textContent = `${jobs.length} stillinger`;
}

main();
