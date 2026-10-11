import yaml
from pathlib import Path

import dedupe
import filters

FILTERS = yaml.safe_load((Path(__file__).parents[2] / "config.yaml").read_text(encoding="utf-8"))["filters"]


def job(**kw):
    base = {"id": "nav:1", "title": "Utvikler", "company": "Firma AS", "location": "Bergen",
            "description": "", "apply_url": "https://a", "published": "2026-10-01",
            "deadline": None, "extent": "Heltid", "source": "NAV"}
    return base | kw


def test_god_juniorjobb_scorer_hoyt():
    keep, score, _ = filters.check(job(title="Junior Python-utvikler",
                                       description="Vi søker nyutdannet med TypeScript og React"), FILTERS)
    assert keep and score >= 60


def test_feil_sted():
    assert not filters.check(job(location="Trondheim"), FILTERS)[0]


def test_deltid():
    assert not filters.check(job(extent="Deltid"), FILTERS)[0]


def test_senior_i_tittel():
    assert not filters.check(job(title="Senior utvikler"), FILTERS)[0]


def test_ikke_it():
    assert not filters.check(job(title="Sykepleier"), FILTERS)[0]


def test_it_ordgrense():
    assert filters.check(job(title="IT-konsulent"), FILTERS)[0]
    assert not filters.check(job(title="Kvalitetsrådgiver"), FILTERS)[0]


def test_epost_uten_sted_og_fagord_slipper_gjennom():
    assert filters.check(job(id="email:FINN:1", title="Rådgiver", location="", extent=None), FILTERS)[0]


def test_duplikater_slas_sammen():
    a = job(source="NAV", apply_url="https://nav", description="kort", score=50)
    b = job(id="tt:1", source="Stacc", company="Firma", title="utvikler!", apply_url="https://stacc",
            description="mye lengre tekst", score=60)
    merged = dedupe.merge([a, b])
    assert len(merged) == 1
    assert merged[0]["description"] == "mye lengre tekst"
    assert merged[0]["sources"] == ["NAV", "Stacc"]
    assert len(merged[0]["links"]) == 2


def test_frister_tolkes():
    from utils import parse_deadline
    assert parse_deadline("2026-10-20T00:00:00") == "2026-10-20"
    assert parse_deadline("01.11.2026") == "2026-11-01"
    assert parse_deadline("Frist 5.1.27") == "2027-01-05"
    assert parse_deadline("Snarest") == ""
    assert parse_deadline("Løpende") == ""
    assert parse_deadline(None) == ""


def test_erfaringsanalyse():
    from experience import analyze
    assert analyze("Du har minst 3 års erfaring med Java").years == 3
    assert analyze("Vi ser etter deg med 2-4 års relevant erfaring").years == 2
    assert analyze("You have 5+ years of professional experience").years == 5
    assert analyze("Vi har over 25 års erfaring som konsulentselskap").years is None
    assert analyze("Du har lang erfaring med skyplattformer").demanding
    assert analyze("Erfaring er en fordel, men ikke et krav").junior_ok
    assert analyze("Du får jobbe med erfarne kolleger").demanding is False
    assert analyze("Spennende stilling", "Erfaren utvikler").demanding


def test_erfaringskrav_filtrerer():
    krever = job(title="Python-utvikler", description="Du har minst 5 års erfaring")
    assert not filters.check(krever, FILTERS)[0]
    nyutdannet = job(title="Python-utvikler", description="Passer for nyutdannede. Minst 5 års erfaring er en fordel")
    assert filters.check(nyutdannet, FILTERS)[0]
    lang = job(title="Utvikler", description="Du har solid erfaring fra produksjon")
    assert not filters.check(lang, FILTERS)[0]
    litt = job(title="Utvikler", description="1-2 års erfaring")
    ingen = job(title="Utvikler", description="Spennende produkt")
    assert filters.check(litt, FILTERS)[1] < filters.check(ingen, FILTERS)[1]
