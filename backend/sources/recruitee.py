"""Karrieresider på Recruitee (f.eks. Variant og Kantega).

Alle Recruitee-sider har et åpent API på <karriereside>/api/offers/ som gir
stillingene som JSON. Karrieresider på Recruitee har ofte lenker som
<side>/o/<stillingsnavn>.
"""
import requests

from utils import html_to_text, to_iso_date


def extent_from_code(code: str | None) -> str | None:
    """Recruitee-koder som 'fulltime_permanent' → 'Heltid'."""
    code = (code or "").lower()
    if "fulltime" in code:
        return "Heltid"
    if "parttime" in code:
        return "Deltid"
    if "intern" in code or "trainee" in code:
        return "Internship"
    return None


def location_text(offer: dict) -> str:
    if offer.get("location"):
        return offer["location"]
    cities = [loc.get("city") for loc in offer.get("locations") or [] if loc.get("city")]
    return ", ".join(cities) or offer.get("city") or ""


def to_job(offer: dict, company: str) -> dict:
    return {
        "id": f"recruitee:{offer.get('id') or offer.get('careers_url')}",
        "title": offer.get("title") or "",
        "company": company,
        "location": location_text(offer),
        "description": html_to_text((offer.get("description") or "") + (offer.get("requirements") or "")),
        "apply_url": offer.get("careers_url") or "",
        "published": to_iso_date(offer.get("published_at")),
        "deadline": None,
        "extent": extent_from_code(offer.get("employment_type_code")),
        "source": company,
    }


def fetch(config: dict) -> list[dict]:
    jobs = []
    for company in config.get("companies", []):
        if company.get("source") != "recruitee":
            continue
        url = company["url"].rstrip("/") + "/api/offers/"
        try:   # ett selskap som feiler skal ikke stoppe de andre
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            jobs += [to_job(o, company["name"]) for o in response.json().get("offers", [])]
        except Exception as error:
            print(f"  ! {company['name']}: {error}")
    return jobs
