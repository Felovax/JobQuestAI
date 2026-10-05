"""NAV stillingsfeed (https://navikt.github.io/pam-stilling-feed/).

Feeden er en strøm av endringer i alle stillingsannonser, side for side.
Vi henter token, blar gjennom sidene, plukker ut aktive stillinger på
riktige steder og henter detaljene for dem.
"""
import os
import re
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import requests

from utils import html_to_text, to_iso_date

BASE_URL = "https://pam-stilling-feed.nav.no"


# ── Del 1: Token ─────────────────────────────────────────────
def get_token() -> str:
    """Henter NAVs offentlige token (eller egen token fra secret NAV_TOKEN)."""
    own = os.environ.get("NAV_TOKEN", "").strip()
    if own:
        return own

    response = requests.get(f"{BASE_URL}/api/publicToken", timeout=20)
    response.raise_for_status()

    # Svaret er vanlig tekst med tokenen inni, så vi plukker den ut
    match = re.search(r"eyJ[\w-]+\.[\w-]+\.[\w-]+", response.text)
    if not match:
        raise RuntimeError("Fant ingen token i svaret fra NAV")
    return match.group(0)


# ── Del 2: Hente én side fra feeden ──────────────────────────
def fetch_page(token: str, path: str, since: str | None = None) -> dict:
    """Henter én side fra feeden. 'since' = bare endringer etter denne datoen."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    if since:
        headers["If-Modified-Since"] = since

    response = requests.get(f"{BASE_URL}{path}", headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


# ── Del 3: Bla gjennom alle sidene ───────────────────────────
def iter_feed_items(token: str, days_back: int = 45, max_pages: int = 400):
    """Går gjennom feeden side for side og gir én stilling om gangen."""
    # Startpunkt: for 'days_back' dager siden, i formatet NAV krever
    start = datetime.now(timezone.utc) - timedelta(days=days_back)
    since = format_datetime(start, usegmt=True)

    path = "/api/v1/feed"
    for _ in range(max_pages):
        # Startdatoen sendes bare med på første side
        first_page = path == "/api/v1/feed"
        page = fetch_page(token, path, since if first_page else None)

        for item in page.get("items", []):
            yield item

        next_url = page.get("next_url")
        if not next_url:   # siste side nådd
            break
        path = next_url


def is_relevant(item: dict, locations: set[str]) -> bool:
    """True hvis stillingen er aktiv og ligger på et sted vi følger."""
    entry = item.get("_feed_entry", {})
    status = entry.get("status", "")
    municipal = entry.get("municipal", "")
    return status == "ACTIVE" and municipal.upper() in locations


# ── Del 4: Hente detaljer for én stilling ────────────────────
def fetch_details(token: str, item: dict) -> dict | None:
    """Henter hele annonsen. Returnerer None hvis den ikke finnes lenger."""
    response = requests.get(
        f"{BASE_URL}{item['url']}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        timeout=30,
    )
    if response.status_code != 200:
        return None
    body = response.json()
    # Annonsen ligger under "ad_content" (eller "json" i eldre svar)
    return body.get("ad_content") or body.get("json") or None


# ── Del 5: Gjøre om til felles format ────────────────────────
def to_job(ad: dict, uuid: str) -> dict:
    location = (ad.get("workLocations") or [{}])[0]
    return {
        "id": f"nav:{uuid}",
        "title": ad.get("title") or "",
        "company": (ad.get("employer") or {}).get("name") or "",
        "location": location.get("city") or (location.get("municipal") or "").title(),
        "description": html_to_text(ad.get("description")),
        # Søknadslenke hvis den finnes, ellers annonsen på arbeidsplassen.no
        "apply_url": ad.get("applicationUrl")
        or f"https://arbeidsplassen.nav.no/stillinger/stilling/{uuid}",
        "published": to_iso_date(ad.get("published")),
        "deadline": ad.get("applicationDue"),
        "extent": ad.get("extent"),
        "source": "NAV",
    }


def fetch(config: dict) -> list[dict]:
    """Setter sammen del 1–5."""
    filters = config["filters"]
    locations = {loc.upper() for loc in filters["locations"]}
    title_words = [w.lower() for w in filters["fields"] + filters["boost_keywords"]]
    days_back = config.get("nav", {}).get("days_back", 45)

    token = get_token()

    # Samme annonse kan dukke opp mange ganger i feeden (én gang per endring).
    # Vi tar vare på den nyeste versjonen per annonse.
    latest: dict[str, dict] = {}
    for item in iter_feed_items(token, days_back=days_back):
        uuid = item.get("_feed_entry", {}).get("uuid") or item.get("id")
        latest[uuid] = item

    jobs = []
    for uuid, item in latest.items():
        if not is_relevant(item, locations):
            continue
        # Grovsortering på tittel FØR vi henter detaljer – sparer tusenvis av kall
        title = item.get("_feed_entry", {}).get("title", "").lower()
        if not any(word in title for word in title_words):
            continue
        ad = fetch_details(token, item)
        if ad:
            jobs.append(to_job(ad, uuid))
    return jobs
