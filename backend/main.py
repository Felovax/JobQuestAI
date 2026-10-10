"""Kjører hele flyten: hent → filtrer → fjern duplikater → skriv jobs.json.

Kjør fra repo-roten:   python backend/main.py
"""
import json
import sys
import time
import traceback
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

import dedupe
import filters
from utils import parse_deadline
from sources import easycruit, email_alerts, jobbnorge, nav, recruitee, smartrecruiters, teamtailor

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "config.yaml"
OUTPUT_FILE = ROOT / "frontend" / "public" / "jobs.json"

SOURCES = [
    ("NAV", nav),
    ("Jobbnorge", jobbnorge),
    ("Teamtailor", teamtailor),
    ("SmartRecruiters", smartrecruiters),
    ("Recruitee", recruitee),
    ("EasyCruit", easycruit),
    ("E-postvarsler", email_alerts),
]


def main() -> None:
    # Skriv ut linje for linje, så loggen i GitHub Actions viser fremdriften underveis
    sys.stdout.reconfigure(line_buffering=True)
    config = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))

    all_jobs, status = [], []
    for name, module in SOURCES:
        started = time.time()
        print(f"Henter {name} …")
        # Én kilde som feiler skal ikke stoppe de andre
        try:
            jobs = module.fetch(config)
            all_jobs += jobs
            status.append({"name": name, "ok": True, "count": len(jobs)})
            print(f"  {len(jobs)} stillinger ({time.time() - started:.0f} s)")
        except Exception as error:
            traceback.print_exc()
            status.append({"name": name, "ok": False, "count": 0, "error": str(error)[:200]})

    # Fristen som ekte dato ("2026-10-20"), så nettsiden kan sortere og varsle.
    # Stillinger der fristen allerede har gått ut, tas ikke med.
    today = date.today().isoformat()
    for job in all_jobs:
        job["deadline_date"] = parse_deadline(job.get("deadline"))
    all_jobs = [j for j in all_jobs if not j["deadline_date"] or j["deadline_date"] >= today]

    kept = filters.apply(all_jobs, config["filters"])
    merged = dedupe.merge(kept)
    # Best score først, nyeste først ved lik score
    merged.sort(key=lambda j: (j["score"], j["published"]), reverse=True)

    print(f"Totalt {len(all_jobs)} hentet → {len(kept)} passer filtrene → {len(merged)} etter duplikatfjerning")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps({
        "updated": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "sources": status,
        "jobs": merged,
    }, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
