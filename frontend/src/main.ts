// Nettsiden: leser jobs.json og viser stillingene med søk og filtre.
// Ingen rammeverk – bare TypeScript og vanlig DOM, så det er lett å følge.

import type { Job, JobsFile } from "./types";
import { loadCv, loadMarks, saveCv, saveMarks } from "./storage";
import { buildPrompt, copyText } from "./prompt";
import "./style.css";

const CITIES = ["Bergen", "Oslo", "Kristiansand", "Stavanger"];
const NEW_DAYS = 3;    // stillinger nyere enn dette får "Ny"-merke
const SOON_DAYS = 7;   // frister nærmere enn dette får et varselmerke

// ── Tilstand: alt som styrer hva som vises ───────────────────
const state = {
  data: null as JobsFile | null,
  query: "",
  city: "Alle",
  source: "Alle",
  sort: "score" as "score" | "newest" | "deadline",
  show: "open" as "open" | "applied" | "hidden",
  marks: loadMarks(),
  expanded: new Set<string>(),
};

// ── Hjelpefunksjoner ─────────────────────────────────────────
const $ = <T extends HTMLElement>(sel: string) => document.querySelector(sel) as T;

function escape(text: string): string {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function daysAgo(isoDate: string): number {
  return (Date.now() - new Date(isoDate).getTime()) / 86_400_000;
}

// Antall dager til fristen (0 = i dag). null hvis fristen ikke er en dato.
function daysLeft(job: Job): number | null {
  if (!job.deadline_date) return null;
  const today = new Date(new Date().toISOString().slice(0, 10)).getTime();
  return Math.round((new Date(job.deadline_date).getTime() - today) / 86_400_000);
}

function deadlineBadge(job: Job): string {
  const days = daysLeft(job);
  if (days === null || days > SOON_DAYS) return "";
  const text = days === 0 ? "Frist i dag" : days === 1 ? "Frist i morgen" : `Frist om ${days} dager`;
  return `<span class="badge ${days <= 2 ? "urgent" : "soon"}">${text}</span>`;
}

function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString("no-NO", { day: "numeric", month: "short" });
}

// ── Filtrering og sortering ──────────────────────────────────
function visibleJobs(): Job[] {
  const q = state.query.toLowerCase();
  const jobs = state.data!.jobs.filter((job) => {
    const mark = state.marks[job.id];
    const left = daysLeft(job);
    if (left !== null && left < 0) return false; // fristen gikk ut etter siste oppdatering
    if (state.show === "open" && mark) return false;
    if (state.show === "applied" && mark !== "applied") return false;
    if (state.show === "hidden" && mark !== "hidden") return false;
    if (state.city !== "Alle" && !job.location.toLowerCase().includes(state.city.toLowerCase())) return false;
    if (state.source !== "Alle" && !job.sources.includes(state.source)) return false;
    if (q && !`${job.title} ${job.company} ${job.description}`.toLowerCase().includes(q)) return false;
    return true;
  });
  if (state.sort === "newest") {
    jobs.sort((a, b) => (b.published || "").localeCompare(a.published || ""));
  } else if (state.sort === "deadline") {
    // Nærmeste frist først. Stillinger uten dato ("Snarest", "Løpende") havner sist.
    jobs.sort((a, b) => (a.deadline_date || "9999").localeCompare(b.deadline_date || "9999"));
  }
  return jobs; // ellers: allerede sortert på score fra backend
}

// ── Tegning ──────────────────────────────────────────────────
function renderCard(job: Job): string {
  const mark = state.marks[job.id];
  const isNew = job.published && daysAgo(job.published) <= NEW_DAYS;
  const open = state.expanded.has(job.id);
  const scoreClass = job.score >= 60 ? "high" : job.score >= 40 ? "mid" : "low";

  const meta = [job.company, job.location || "Sted ikke oppgitt"].filter(Boolean).map(escape).join(" · ");
  const dates = [
    job.published ? `Publisert ${formatDate(job.published)}` : "",
    job.deadline_date ? `Frist: ${formatDate(job.deadline_date)}` : job.deadline ? `Frist: ${escape(job.deadline)}` : "",
  ].filter(Boolean).join(" · ");

  const links = job.links
    .map((l, i) => `<a class="btn ${i === 0 ? "primary" : ""}" href="${escape(l.url)}" target="_blank" rel="noopener">
        ${i === 0 ? "Les og søk" : "Også på"} · ${escape(l.source)} ↗</a>`)
    .join("");

  return `
    <article class="card ${mark ?? ""}" data-id="${escape(job.id)}">
      <div class="score ${scoreClass}" title="Match-score">${job.score}</div>
      <div class="body">
        <h2>${escape(job.title)} ${isNew ? '<span class="badge new">Ny</span>' : ""} ${deadlineBadge(job)}
            ${mark === "applied" ? '<span class="badge applied">Søkt</span>' : ""}</h2>
        <p class="meta">${meta}</p>
        ${dates ? `<p class="meta small">${dates}</p>` : ""}
        ${job.reasons.length ? `<ul class="reasons">${job.reasons.map((r) => `<li>${escape(r)}</li>`).join("")}</ul>` : ""}
        ${job.description ? `<button class="link toggle">${open ? "Skjul beskrivelse" : "Vis beskrivelse"}</button>` : ""}
        ${open ? `<div class="desc">${escape(job.description)}</div>` : ""}
        <div class="actions">
          ${links}
          <button class="btn prompt" title="Kopierer en ferdig prompt med annonsen og CV-en din – lim den inn i Claude.ai">Søknadsprompt</button>
          <button class="btn mark" data-mark="applied">${mark === "applied" ? "Angre søkt" : "Merk som søkt"}</button>
          <button class="btn ghost mark" data-mark="hidden">${mark === "hidden" ? "Vis igjen" : "Skjul"}</button>
        </div>
      </div>
    </article>`;
}

function render(): void {
  const data = state.data!;
  const jobs = visibleJobs();

  $("#count").textContent = `${jobs.length} stillinger`;
  $("#list").innerHTML = jobs.length
    ? jobs.map(renderCard).join("")
    : `<p class="empty">Ingen stillinger her. Prøv et annet filter.</p>`;

  // Kilde-knapper bygges fra dataene
  const sources = ["Alle", ...new Set(data.jobs.flatMap((j) => j.sources))];
  $("#sources").innerHTML = sources
    .map((s) => `<button class="chip ${state.source === s ? "on" : ""}" data-source="${escape(s)}">${escape(s)}</button>`)
    .join("");

  $("#cities").innerHTML = ["Alle", ...CITIES]
    .map((c) => `<button class="chip ${state.city === c ? "on" : ""}" data-city="${c}">${c}</button>`)
    .join("");

  document.querySelectorAll<HTMLButtonElement>("#tabs button").forEach((b) =>
    b.classList.toggle("on", b.dataset.show === state.show));
}

function renderFooter(): void {
  const data = state.data!;
  const updated = new Date(data.updated).toLocaleString("no-NO", { dateStyle: "medium", timeStyle: "short" });
  const status = data.sources
    .map((s) => `<span class="${s.ok ? "ok" : "fail"}" title="${escape(s.error ?? "")}">${escape(s.name)}: ${s.ok ? s.count : "feilet"}</span>`)
    .join("");
  $("#footer").innerHTML = `Oppdatert ${updated}<div class="status">${status}</div>`;
}

// ── Søknadsprompt og CV ──────────────────────────────────────
let toastTimer = 0;
function toast(html: string): void {
  const el = $("#toast");
  el.innerHTML = html;
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => el.classList.remove("show"), 6000);
}

async function copyPrompt(id: string): Promise<void> {
  const job = state.data!.jobs.find((j) => j.id === id);
  if (!job) return;
  const cv = loadCv();
  const ok = await copyText(buildPrompt(job, cv));
  if (!ok) {
    toast("Klarte ikke å kopiere. Prøv en annen nettleser.");
    return;
  }
  toast(`Prompt kopiert! Lim den inn i <a href="https://claude.ai/new" target="_blank" rel="noopener">Claude.ai ↗</a>` +
    (cv.trim() ? "" : `<br><small>Tips: legg inn CV-en din under «Min CV», så kommer den med automatisk.</small>`));
}

function setupCvDialog(): void {
  const dialog = $<HTMLDialogElement>("#cv-dialog");
  const text = $<HTMLTextAreaElement>("#cv-text");
  $("#cv-open").addEventListener("click", () => {
    text.value = loadCv();
    dialog.showModal();
  });
  $("#cv-save").addEventListener("click", () => {
    saveCv(text.value);
    dialog.close();
    toast("CV lagret i denne nettleseren.");
  });
  $("#cv-close").addEventListener("click", () => dialog.close());
}

// ── Hendelser: klikk og skriving ─────────────────────────────
function setupEvents(): void {
  $("#search").addEventListener("input", (e) => {
    state.query = (e.target as HTMLInputElement).value;
    render();
  });
  $("#sort").addEventListener("change", (e) => {
    state.sort = (e.target as HTMLSelectElement).value as typeof state.sort;
    render();
  });

  // Én lytter for hele siden – sjekker hva som ble klikket
  document.addEventListener("click", (e) => {
    const target = e.target as HTMLElement;
    const card = target.closest<HTMLElement>(".card");
    const id = card?.dataset.id;

    if (target.dataset.city) state.city = target.dataset.city;
    else if (target.dataset.source) state.source = target.dataset.source;
    else if (target.dataset.show) state.show = target.dataset.show as typeof state.show;
    else if (id && target.classList.contains("toggle")) {
      state.expanded.has(id) ? state.expanded.delete(id) : state.expanded.add(id);
    } else if (id && target.classList.contains("prompt")) {
      copyPrompt(id);
      return;
    } else if (id && target.dataset.mark) {
      const mark = target.dataset.mark as "hidden" | "applied";
      if (state.marks[id] === mark) delete state.marks[id];
      else state.marks[id] = mark;
      saveMarks(state.marks);
    } else return;

    render();
  });
}

// ── Oppstart ─────────────────────────────────────────────────
async function main(): Promise<void> {
  try {
    // ?t=… hindrer at nettleseren viser en gammel versjon fra cache
    const response = await fetch(`./jobs.json?t=${Date.now()}`);
    state.data = await response.json();
  } catch {
    $("#list").innerHTML = `<p class="empty">Fant ingen stillinger ennå. Kjør "Oppdater stillinger" under Actions på GitHub.</p>`;
    return;
  }
  if (!state.data?.jobs) {
    $("#list").innerHTML = `<p class="empty">Ingen data ennå – første kjøring har ikke skjedd.</p>`;
    return;
  }
  setupEvents();
  setupCvDialog();
  renderFooter();
  render();
}

main();
