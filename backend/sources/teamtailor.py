"""Karrieresider på Teamtailor. Alle har en offentlig RSS-feed på <url>/jobs.rss.

Mange norske selskaper bruker Teamtailor, så dette er den enkleste måten å
følge enkeltselskaper på: legg dem til i config.yaml med source: teamtailor.
"""
import xml.etree.ElementTree as ET

import requests

from utils import html_to_text, to_iso_date


def local(tag: str) -> str:
    """'{https://teamtailor.com/locations}city' -> 'city'. Lar oss ignorere XML-navnerom."""
    return tag.rsplit("}", 1)[-1]


def find_text(element: ET.Element, name: str) -> str:
    """Finner første under-element med dette navnet (på alle nivåer) og returnerer teksten."""
    for child in element.iter():
        if local(child.tag) == name and child.text:
            return child.text.strip()
    return ""


def parse_rss(xml_text: str, company: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    jobs = []
    for item in root.iter("item"):
        cities = [c.text.strip() for c in item.iter() if local(c.tag) == "city" and c.text]
        link = find_text(item, "link")
        jobs.append({
            "id": f"teamtailor:{find_text(item, 'guid') or link}",
            "title": find_text(item, "title"),
            "company": company,
            "location": ", ".join(dict.fromkeys(cities)),  # fjerner like byer, beholder rekkefølgen
            "description": html_to_text(find_text(item, "description")),
            "apply_url": link,
            "published": to_iso_date(find_text(item, "pubDate")),
            "deadline": None,
            "extent": None,
            "source": company,
        })
    return jobs


def fetch(config: dict) -> list[dict]:
    jobs = []
    for company in config.get("companies", []):
        if company.get("source") != "teamtailor":
            continue
        url = company["url"].rstrip("/") + "/jobs.rss"
        try:   # ett selskap som feiler skal ikke stoppe de andre
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            jobs += parse_rss(response.text, company["name"])
        except Exception as error:
            print(f"  ! {company['name']}: {error}")
    return jobs
