"""Jobbvarsler fra en egen Gmail-innboks (FINN, LinkedIn, The Hub, Indeed …).

Slik virker det:
  1. Dere setter opp vanlige jobbvarsler på FINN, LinkedIn osv. til Gmail-kontoen.
  2. Hver natt logger skriptet inn med IMAP (app-passord) og leser e-postene
     fra de siste dagene, uten å markere dem som lest.
  3. Vi leter etter lenker til stillinger i e-postene og lager én stilling per lenke.

Krever secrets GMAIL_ADDRESS og GMAIL_APP_PASSWORD. Uten dem hoppes kilden over.
E-post gir sjelden full annonsetekst, så disse stillingene har kort beskrivelse.
"""
import email
from email.message import Message
import imaplib
import os
import re
from datetime import date, timedelta
from email.header import decode_header, make_header
from html.parser import HTMLParser
from urllib.parse import unquote

# Hvilke lenker som er stillinger, og hvordan vi lager en ren lenke uten sporing.
# (navn, regex som finner ID-en, mal for ren lenke)
JOB_LINKS = [
    ("FINN", r"finn\.no/(?:job/[\w/]*?ad(?:\.html\?finnkode=|/))?(\d{8,10})\b", "https://www.finn.no/job/ad/{}"),
    ("LinkedIn", r"linkedin\.com/(?:comm/)?jobs/view/(\d+)", "https://www.linkedin.com/jobs/view/{}"),
    ("The Hub", r"thehub\.io/jobs/([0-9a-f]{20,})", "https://thehub.io/jobs/{}"),
    ("Indeed", r"indeed\.com/\S*?[?&]jk=([0-9a-f]+)", "https://no.indeed.com/viewjob?jk={}"),
]

# Lenketekster som ikke er stillingstitler
GENERIC_TEXT = {"se stillingen", "se annonsen", "view job", "apply", "søk", "les mer",
                "see more jobs", "se alle", "vis alle", "se flere stillinger", ""}


def match_job_link(href: str) -> tuple[str, str, str] | None:
    """Gir (kilde, id, ren_lenke) hvis lenken peker til en stilling."""
    # Sporingslenker har ofte den ekte lenken URL-kodet inni seg, så vi dekoder to ganger
    decoded = unquote(unquote(href))
    for name, pattern, template in JOB_LINKS:
        match = re.search(pattern, decoded)
        if match:
            return name, match.group(1), template.format(match.group(1))
    return None


class JobLinkParser(HTMLParser):
    """Går gjennom HTML-en i én e-post og samler stillingslenker med tekst rundt."""

    def __init__(self):
        super().__init__()
        self.jobs: dict[str, dict] = {}   # ren_lenke -> stilling
        self.current: dict | None = None  # lenken vi står inni akkurat nå
        self.last_job: dict | None = None # forrige stilling, for å fange tekst etter lenken

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        found = match_job_link(dict(attrs).get("href") or "")
        if found:
            source, job_id, url = found
            job = self.jobs.setdefault(url, {"source": source, "id": job_id, "url": url,
                                             "texts": [], "context": []})
            self.current = job

    def handle_endtag(self, tag):
        if tag == "a" and self.current:
            self.last_job = self.current
            self.current = None

    def handle_data(self, data):
        text = " ".join(data.split())
        if not text:
            return
        if self.current:
            self.current["texts"].append(text)
        elif self.last_job and len(self.last_job["context"]) < 2 and len(text) < 120:
            # Teksten rett etter tittelen er som regel "Firma · Sted"
            self.last_job["context"].append(text)


def jobs_from_html(html_body: str) -> list[dict]:
    parser = JobLinkParser()
    parser.feed(html_body)
    jobs = []
    for job in parser.jobs.values():
        # Velg den beste lenketeksten som tittel
        candidates = [t for t in job["texts"] if t.lower() not in GENERIC_TEXT and len(t) < 150]
        if not candidates:
            continue
        title = max(candidates, key=len)
        context = [c for c in job["context"] if c != title]
        company = context[0].split(" · ")[0] if context else ""
        jobs.append({
            "id": f"email:{job['source']}:{job['id']}",
            "title": title,
            "company": company,
            "location": "",            # ukjent – varslene er allerede filtrert på sted
            "description": " · ".join(context),
            "apply_url": job["url"],
            "published": "",
            "deadline": None,
            "extent": None,
            "source": job["source"],
        })
    return jobs


def html_parts(message: Message) -> list[str]:
    parts = []
    for part in message.walk():
        if part.get_content_type() == "text/html":
            payload = part.get_payload(decode=True) or b""
            parts.append(payload.decode(part.get_content_charset() or "utf-8", errors="replace"))
    return parts


def fetch(config: dict) -> list[dict]:
    address = os.environ.get("GMAIL_ADDRESS", "").strip()
    password = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")
    if not address or not password:
        print("  (GMAIL_ADDRESS/GMAIL_APP_PASSWORD ikke satt – hopper over e-post)")
        return []

    days_back = config.get("email_alerts", {}).get("days_back", 14)
    since = (date.today() - timedelta(days=days_back)).strftime("%d-%b-%Y")

    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(address, password)
    imap.select("INBOX", readonly=True)    # readonly: endrer ingenting i innboksen
    _, data = imap.search(None, "SINCE", since)

    jobs = []
    for num in data[0].split():
        _, msg_data = imap.fetch(num, "(BODY.PEEK[])")
        message = email.message_from_bytes(msg_data[0][1])
        subject = str(make_header(decode_header(message.get("Subject", ""))))
        for body in html_parts(message):
            for job in jobs_from_html(body):
                job["description"] = job["description"] or f"Fra e-postvarsel: {subject}"
                jobs.append(job)
    imap.logout()
    return jobs
