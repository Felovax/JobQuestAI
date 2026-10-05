from unittest.mock import MagicMock, patch

from sources import email_alerts, jobbnorge, nav, teamtailor


def test_nav_is_relevant():
    locs = {"BERGEN", "OSLO"}
    assert nav.is_relevant({"_feed_entry": {"status": "ACTIVE", "municipal": "Bergen"}}, locs)
    assert not nav.is_relevant({"_feed_entry": {"status": "INACTIVE", "municipal": "BERGEN"}}, locs)
    assert not nav.is_relevant({"_feed_entry": {"status": "ACTIVE", "municipal": "BODØ"}}, locs)


def test_nav_fetch_hele_flyten():
    feed = {"next_url": None, "items": [
        {"url": "/api/v1/feedentry/a", "_feed_entry": {"uuid": "a", "status": "ACTIVE",
                                                       "municipal": "BERGEN", "title": "Junior utvikler"}},
        {"url": "/api/v1/feedentry/b", "_feed_entry": {"uuid": "b", "status": "ACTIVE",
                                                       "municipal": "BERGEN", "title": "Kokk"}},
    ]}
    detail = {"ad_content": {"title": "Junior utvikler", "employer": {"name": "Firma AS"},
                             "workLocations": [{"city": "Bergen"}], "description": "<p>Hei</p>",
                             "extent": "Heltid", "published": "2026-10-01T08:00:00Z"}}

    def fake_get(url, **kw):
        r = MagicMock(status_code=200)
        r.raise_for_status.return_value = None
        if url.endswith("publicToken"):
            r.text = "token: eyJa.eyJb.c-d"
        elif "feedentry" in url:
            r.json.return_value = detail
        else:
            r.json.return_value = feed
        return r

    config = {"filters": {"locations": ["Bergen"], "fields": ["utvikler"], "boost_keywords": []}}
    with patch("sources.nav.requests.get", side_effect=fake_get) as get:
        jobs = nav.fetch(config)
    assert len(jobs) == 1                       # kokken ble sortert bort før detaljkall
    assert jobs[0]["company"] == "Firma AS" and jobs[0]["description"] == "Hei"
    assert jobs[0]["published"] == "2026-10-01"
    assert sum("feedentry" in c.args[0] for c in get.call_args_list) == 1


def test_jobbnorge_to_job():
    j = jobbnorge.to_job({"id": 1, "title": "Rådgiver IT", "employer": "UiB", "jobScope": "Heltid",
                          "publicationDate": "11.09.2026", "deadline": "01.11.2026", "link": "https://x",
                          "summary": "<b>Om</b>", "locations": [{"area": "Bergen", "municipality": "Bergen",
                                                                "isPrimary": True}]})
    assert j["location"] == "Bergen" and j["published"] == "2026-09-11" and j["description"] == "Om"


RSS = """<?xml version="1.0"?>
<rss xmlns:tt="https://teamtailor.com/locations" version="2.0"><channel>
<item><title>Utvikler</title><link>https://jobs.stacc.com/jobs/1-utvikler</link>
<guid>1</guid><pubDate>Mon, 05 Oct 2026 08:00:00 +0200</pubDate>
<description>&lt;p&gt;Bli med&lt;/p&gt;</description>
<tt:locations><tt:location><tt:city>Bergen</tt:city></tt:location>
<tt:location><tt:city>Oslo</tt:city></tt:location></tt:locations></item>
</channel></rss>"""


def test_teamtailor_rss():
    jobs = teamtailor.parse_rss(RSS, "Stacc")
    assert jobs[0]["location"] == "Bergen, Oslo"
    assert jobs[0]["description"] == "Bli med" and jobs[0]["published"] == "2026-10-05"


def test_epost_lenker():
    html = """
    <a href="https://www.linkedin.com/comm/jobs/view/123456/?trackingId=abc"><img src="x"></a>
    <a href="https://www.linkedin.com/comm/jobs/view/123456/?trackingId=abc">Junior utvikler</a>
    <p>Bouvet · Bergen</p>
    <a href="https://click.finn.no/r?u=https%3A%2F%2Fwww.finn.no%2Fjob%2Fad%2F433221100">Systemutvikler</a>
    <a href="https://www.linkedin.com/jobs">See more jobs</a>
    """
    jobs = email_alerts.jobs_from_html(html)
    assert [j["apply_url"] for j in jobs] == ["https://www.linkedin.com/jobs/view/123456",
                                              "https://www.finn.no/job/ad/433221100"]
    assert jobs[0]["title"] == "Junior utvikler" and jobs[0]["company"] == "Bouvet"
