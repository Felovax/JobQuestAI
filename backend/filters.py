"""Filtrerer bort stillinger som ikke passer, og gir resten en score fra 0 til 100.

Alle innstillinger hentes fra 'filters' i config.yaml.
"""
import re

# Tegn på at stillingen krever mye erfaring (trekker ned scoren)
SENIOR_SIGNALS = ["senior", "erfaren", "lang erfaring", "minimum 5 år", "minst 5 år",
                  "5+ år", "5 års erfaring", "tech lead", "teamleder"]

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
    """Returnerer (behold?, score, grunner)."""
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

    levels = [w for w in filters["include_levels"] if contains(everything, w)]
    if levels:
        score += 20
        reasons.append("Passer nyutdannede (" + ", ".join(levels) + ")")

    senior = [w for w in SENIOR_SIGNALS if contains(description, w)]
    if senior:
        score -= 15
        reasons.append("Kan kreve erfaring (" + ", ".join(senior[:2]) + ")")

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
