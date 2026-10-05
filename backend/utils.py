"""Små hjelpefunksjoner som flere filer bruker."""
import html
import re
from datetime import datetime


def html_to_text(raw: str | None, max_len: int = 4000) -> str:
    """Gjør HTML om til ren, lesbar tekst."""
    if not raw:
        return ""
    text = re.sub(r"<(br|/p|/li|/h\d|/div)[^>]*>", "\n", raw, flags=re.I)  # linjeskift der HTML har blokker
    text = re.sub(r"<li[^>]*>", "• ", text, flags=re.I)                    # punktlister
    text = re.sub(r"<[^>]+>", "", text)                                     # fjern resten av taggene
    text = html.unescape(text)
    text = re.sub(r"[ \t\xa0]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    return text[:max_len]


def normalize(text: str | None) -> str:
    """Små bokstaver, bare bokstaver/tall og enkle mellomrom. Brukes til sammenligning."""
    text = (text or "").lower()
    text = re.sub(r"[^\wæøå]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def to_iso_date(value: str | None) -> str:
    """Gjør ulike datoformater om til '2026-10-05'. Returnerer '' hvis ukjent."""
    if not value:
        return ""
    value = value.strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d.%m.%Y", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    match = re.match(r"(\d{4}-\d{2}-\d{2})", value)  # f.eks. med tidssone på slutten
    return match.group(1) if match else ""
