"""Karrieresider på EasyCruit / Visma Recruit (f.eks. Eviny).

EasyCruit har en åpen XML-liste på
https://<firma>.easycruit.com/export/xml/vacancy/list.xml
"""
import xml.etree.ElementTree as ET

import requests

from utils import html_to_text, to_iso_date


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def first_text(element: ET.Element, *names: str) -> str:
    """Første under-element (på alle nivåer) med et av navnene, som ren tekst."""
    wanted = {n.lower() for n in names}
    for child in element.iter():
        if child is not element and local(child.tag).lower() in wanted:
            text = " ".join(t.strip() for t in child.itertext() if t.strip())
            if text:
                return text
    return ""


def parse_xml(xml_text: str, company: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    jobs = []
    for vacancy in root.iter():
        if local(vacancy.tag).lower() != "vacancy":
            continue
        url = first_text(vacancy, "VacancyURL", "ApplicationURL")
        jobs.append({
            "id": f"easycruit:{vacancy.get('id') or url}",
            "title": first_text(vacancy, "Title"),
            "company": first_text(vacancy, "AlternativeCompanyName") or company,
            "location": first_text(vacancy, "Location"),
            "description": html_to_text(first_text(vacancy, "Description", "TitleHeading")),
            "apply_url": url,
            "published": to_iso_date(vacancy.get("date_start") or first_text(vacancy, "Published")),
            "deadline": first_text(vacancy, "ApplicationDeadline") or None,
            "extent": None,
            "source": company,
        })
    return [j for j in jobs if j["title"]]


def fetch(config: dict) -> list[dict]:
    jobs = []
    for company in config.get("companies", []):
        if company.get("source") != "easycruit":
            continue
        url = company["url"].rstrip("/") + "/export/xml/vacancy/list.xml"
        try:   # ett selskap som feiler skal ikke stoppe de andre
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            jobs += parse_xml(response.text, company["name"])
        except Exception as error:
            print(f"  ! {company['name']}: {error}")
    return jobs
