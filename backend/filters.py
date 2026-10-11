"""Filtrerer bort stillinger som ikke passer, og gir resten en score fra 0 til 100.

Alle innstillinger hentes fra 'filters' i config.yaml.
"""
import re

import experience

# Kilder der vi stoler på at varselet allerede er filtrert på fagfelt og sted
PREFILTERED_PREFIX = "email:"


def contains(text: str, word: str) -> bool:
    """Sjekker om et ord finnes i teksten. Korte ord (som 'it' og 'ai') må stå alene,
    ellers ville 'it' truffet 'kvalitet'."""
    word = word.lower().strip()
    if not word:
        return False
    if len(word) <= 3 and word.isalnum():
        return re.search(rf"(?<!\w){re.escape(word)}(?!\w)", text) is not None
    return word in text


def check(job: dict, filters: dict) -> tuple[bool, int, list[str]]:
    """Returnerer (behold?, score, grunner). Legger også erfaringsvurderingen på jobben."""
    title = job["title"].lower()
    description = job["description"].lower()
    everything = f"{title} {description}"
    prefiltered = job["id"].startswith(PREFILTERED_PREFIX)

    # ── Harde filtre: stillingen forkastes ───────────────────
    location = job["location"].lower()
    if location and not any(loc.lower() in location for loc in filters["locations"]):
        return False, 0, [f"Feil sted: {job['location']}"]

    extent = (job.get("extent") or "").lower()
    if filters.get("full_time_only") and extent and not ("heltid" in extent or "full" in extent):
        return False, 0, [f"Ikke heltid: {job['extent']}"]

    for word in filters["exclude_title_words"]:
        if contains(title, word):
            return False, 0, [f"Utelukket ord i tittel: {word}"]

    if not prefiltered:
        it_words = filters["fields"] + filters["boost_keywords"]
        if not any(contains(title, w) for w in it_words):
            return False, 0, ["Ser ikke ut som en IT-stilling"]

    # Erfaringskrav: vi er nyutdannede, så stillinger med klare krav sorteres bort
    exp = experience.analyze(job["description"], job["title"])
    exp.junior_ok = exp.junior_ok or any(contains(everything, w) for w in filters["include_levels"])
    max_years = filters.get("max_experience_years", 2)
    if exp.years is not None and exp.years > max_years and not exp.junior_ok:
        return False, 0, [f"Krever {exp.years} års erfaring"]
    if exp.demanding and not exp.junior_ok and filters.get("hide_demanding", True):
        return False, 0, ["Krever mye erfaring"]
    # E-postvarsler har bare tittel, så der vet vi ikke noe om kravene
    job["experience"] = "" if prefiltered else ("Passer nyutdannede" if exp.junior_ok else exp.note)

    # ── Poeng ────────────────────────────────────────────────
    score = 20
    reasons = []

    title_hits = [k for k in filters["boost_keywords"] if contains(title, k)]
    body_hits = [k for k in filters["boost_keywords"] if k not in title_hits and contains(description, k)]
    score += min(30, 15 * len(title_hits))
    score += min(25, 5 * len(body_hits))
    if title_hits:
        reasons.append("Tittel: " + ", ".join(title_hits))
    if body_hits:
        reasons.append("Nevner: " + ", ".join(body_hits))

    # Mest poeng til stillinger som sier at nyutdannede passer, litt til dem som ikke
    # nevner erfaring, og trekk for dem som ønsker 1–2 års erfaring.
    # (Selve vurderingen vises som eget merke på nettsiden, så den står ikke i «reasons».)
    if job["experience"] == "Passer nyutdannede":
        score += 25
    elif exp.years is not None:   # her er years alltid 1–2, ellers ble stillingen skjult over
        score -= 5
    elif not prefiltered:
        score += 5

    score = max(0, min(100, score))
    return score >= filters.get("min_score", 0), score, reasons


def apply(jobs: list[dict], filters: dict) -> list[dict]:
    """Beholder bare stillingene som passer, med score og grunner lagt til."""
    kept = []
    for job in jobs:
        keep, score, reasons = check(job, filters)
        if keep:
            kept.append({**job, "score": score, "reasons": reasons})
    return kept
