"""Karrieresider på SmartRecruiters – åpent Posting API.

Dokumentasjon: https://developers.smartrecruiters.com/docs/posting-api
"""
import requests

from utils import html_to_text, to_iso_date

API = "https://api.smartrecruiters.com/v1/companies/{id}/postings"


def to_job(posting: dict, company_id: str, company_name: str, description: str = "") -> dict:
    location = posting.get("location") or {}
    return {
        "id": f"smartrecruiters:{posting.get('id')}",
        "title": posting.get("name") or "",
        "company": (posting.get("company") or {}).get("name") or company_name,
        "location": location.get("city") or "",
        "description": description,
        "apply_url": f"https://jobs.smartrecruiters.com/{company_id}/{posting.get('id')}",
        "published": to_iso_date(posting.get("releasedDate")),
        "deadline": None,
        "extent": (posting.get("typeOfEmployment") or {}).get("label"),
        "source": company_name,
    }


def fetch_description(posting: dict) -> str:
    """Henter annonseteksten fra detalj-lenken ('ref')."""
    if not posting.get("ref"):
        return ""
    response = requests.get(posting["ref"], timeout=30)
    if response.status_code != 200:
        return ""
    sections = (response.json().get("jobAd") or {}).get("sections") or {}
    parts = [(sections.get(key) or {}).get("text") or ""
             for key in ("jobDescription", "qualifications", "additionalInformation")]
    return html_to_text("\n".join(parts))


def fetch(config: dict) -> list[dict]:
    jobs = []
    for company in config.get("companies", []):
        if company.get("source") != "smartrecruiters":
            continue
        offset = 0
        while True:
            response = requests.get(
                API.format(id=company["id"]),
                params={"limit": 100, "offset": offset},
                timeout=30,
            )
            response.raise_for_status()
            body = response.json()
            postings = body.get("content") or []
            for posting in postings:
                # Store selskaper har stillinger i mange land – vi tar bare Norge,
                # og henter beskrivelse (ekstra kall) kun for dem
                country = ((posting.get("location") or {}).get("country") or "").lower()
                if country not in ("no", "nor", "norway", "norge"):
                    continue
                jobs.append(to_job(posting, company["id"], company["name"], fetch_description(posting)))
            offset += len(postings)
            if not postings or offset >= body.get("totalFound", 0):
                break
    return jobs
