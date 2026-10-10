"""Slår sammen samme stilling fra flere kilder.

To stillinger regnes som like hvis firma og tittel er like etter normalisering
(små bokstaver, uten tegnsetting og uten 'AS'/'ASA'). Vi beholder versjonen med
mest tekst, og tar vare på lenkene fra alle kildene.
"""
import re

from utils import normalize


def company_key(company: str) -> str:
    return re.sub(r"\b(as|asa|sa|ab|norge|norway)\b", "", normalize(company)).strip()


def key(job: dict) -> str:
    company = company_key(job["company"])
    if not company:   # uten firma kan vi ikke sammenligne trygt – bruk lenken
        return job["apply_url"]
    return f"{company}|{normalize(job['title'])}"


def merge(jobs: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for job in jobs:
        groups.setdefault(key(job), []).append(job)

    merged = []
    for group in groups.values():
        best = max(group, key=lambda j: len(j["description"]))   # mest innhold vinner
        links = []
        for job in group:
            if job["apply_url"] and job["apply_url"] not in [l["url"] for l in links]:
                links.append({"source": job["source"], "url": job["apply_url"]})
        merged.append({
            **best,
            "score": max(j.get("score", 0) for j in group),
            "published": min((j["published"] for j in group if j["published"]), default=""),
            "deadline": next((j["deadline"] for j in group if j["deadline"]), None),
            "deadline_date": next((j["deadline_date"] for j in group if j.get("deadline_date")), ""),
            "sources": list(dict.fromkeys(j["source"] for j in group)),
            "links": links,
        })
    return merged
