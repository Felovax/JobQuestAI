"""Jobbnorge – åpent API, sterkt på offentlig sektor, universiteter og kommuner.

Ett kall gir alle åpne stillinger i Norge (ingen sider å bla i).
"""
import requests

from utils import html_to_text, to_iso_date

API_URL = "https://publicapi.jobbnorge.no/v3/jobs?language=1"


def location_text(job: dict) -> str:
    """Samler sted fra 'locations'-listen, primærsted først."""
    locs = job.get("locations") or []
    locs = sorted(locs, key=lambda l: not l.get("isPrimary"))
    parts = []
    for loc in locs:
        for key in ("area", "municipality"):
            if loc.get(key) and loc[key] not in parts:
                parts.append(loc[key])
    return ", ".join(parts)


def to_job(job: dict) -> dict:
    return {
        "id": f"jobbnorge:{job.get('id')}",
        "title": job.get("title") or "",
        "company": job.get("employer") or "",
        "location": location_text(job),
        "description": html_to_text(job.get("summary")),
        "apply_url": job.get("link") or "",
        "published": to_iso_date(job.get("publicationDate")),
        "deadline": job.get("deadline"),
        "extent": job.get("jobScope"),
        "source": "Jobbnorge",
    }


def fetch(config: dict) -> list[dict]:
    response = requests.get(API_URL, timeout=60, headers={"Accept": "application/json"})
    response.raise_for_status()
    return [to_job(job) for job in response.json()]
