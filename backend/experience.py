"""Finner ut hvor mye erfaring en stillingsannonse krever.

Vi leter etter formuleringer som «minst 3 års erfaring», «2–4 years of experience»
og «lang erfaring», og etter tegn på at nyutdannede passer, som «nyutdannet» eller
«erfaring er en fordel, men ikke et krav».

Resultatet:
    years       – laveste antall år som kreves (None hvis ingen tall står)
    demanding   – True hvis annonsen krever mye erfaring uten å si antall år
    junior_ok   – True hvis annonsen sier at nyutdannede/uerfarne passer
    note        – kort forklaring som vises på nettsiden
"""
import re
from dataclasses import dataclass

# «3 års erfaring», «2-4 års relevant erfaring», «minimum 5 år med erfaring»,
# «3+ years of experience», «at least 2 years' experience»
YEARS_PATTERNS = [
    r"(\d{1,2})\s*(?:[-–]\s*\d{1,2}\s*)?\+?\s*års?\s+(?:\w+\s+){0,3}erfaring",
    r"(\d{1,2})\s*(?:[-–]\s*\d{1,2}\s*)?\+?\s*år\s+med\s+(?:\w+\s+){0,2}erfaring",
    r"erfaring\s+(?:på|fra)\s+(?:minst|minimum|over)\s+(\d{1,2})\s*år",
    r"(?:minst|minimum)\s+(\d{1,2})\s*år",
    r"(\d{1,2})\s*(?:[-–]\s*\d{1,2}\s*)?\+?\s*years?'?\s+(?:of\s+)?(?:\w+\s+){0,3}experience",
    r"(?:at least|minimum(?: of)?)\s+(\d{1,2})\s*years?",
]

# Krever mye erfaring uten å oppgi tall
DEMANDING = [
    "flere års erfaring", "lang erfaring", "solid erfaring", "omfattende erfaring",
    "bred erfaring", "betydelig erfaring", "dokumentert erfaring",
    "several years of experience", "extensive experience",
    "proven experience", "solid experience", "strong experience",
]
# «Erfaren» i selve tittelen betyr nesten alltid at de vil ha erfaring.
# (I annonseteksten kan det like gjerne stå «du får jobbe med erfarne kolleger».)
DEMANDING_TITLE = ["erfaren", "experienced"]

# Tegn på at nyutdannede passer
JUNIOR_OK = [
    "nyutdannet", "nyutdannede", "graduate", "trainee", "junior", "ferdigutdannet",
    "ingen krav til erfaring", "erfaring er ikke et krav", "erfaring er ikke påkrevd",
    "erfaring er en fordel", "erfaring er ønskelig", "erfaring er et pluss",
    "relevant erfaring er en fordel", "no experience required", "entry level", "entry-level",
    "recent graduate", "newly graduated", "first job", "første jobb",
]

MAX_PLAUSIBLE_YEARS = 10   # «vi har 25 års erfaring» handler om firmaet, ikke kravet


@dataclass
class Experience:
    years: int | None
    demanding: bool
    junior_ok: bool
    note: str


def analyze(text: str, title: str = "") -> Experience:
    text = (text or "").lower()
    title = (title or "").lower()

    found = []
    for pattern in YEARS_PATTERNS:
        for match in re.finditer(pattern, text):
            years = int(match.group(1))
            if 1 <= years <= MAX_PLAUSIBLE_YEARS:
                found.append(years)
    years = min(found) if found else None   # «2–4 år» eller flere krav → det laveste teller

    demanding = any(p in text for p in DEMANDING) or any(p in title for p in DEMANDING_TITLE)
    junior_ok = any(p in f"{title} {text}" for p in JUNIOR_OK)

    if junior_ok and (years is None or years <= 1):
        note = "Passer nyutdannede"
    elif years is not None:
        note = f"Krever {years}+ års erfaring"
    elif demanding:
        note = "Krever mye erfaring"
    else:
        note = "Ingen erfaringskrav nevnt"
    return Experience(years, demanding, junior_ok, note)
