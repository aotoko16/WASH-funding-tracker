"""ReliefWeb API — secondary aggregator, but useful for humanitarian funding appeals.
Docs: https://apidoc.reliefweb.int/
"""
import requests

API = "https://api.reliefweb.int/v1/reports"
APP = "wash-funding-tracker"


def fetch():
    """Fetch funding-related WASH reports. Returns list of raw opportunity dicts."""
    results = []
    payload = {
        "appname": APP,
        "query": {
            "value": '("call for proposals" OR "funding opportunity" OR "call for expressions of interest" OR "request for proposals") AND (WASH OR water OR sanitation OR hygiene)',
            "operator": "AND",
        },
        "fields": {
            "include": ["title", "date", "source", "country", "body", "url_alias", "origin"]
        },
        "limit": 30,
        "sort": ["date:desc"],
    }
    try:
        r = requests.post(API, json=payload, timeout=30)
        r.raise_for_status()
        for item in r.json().get("data", []):
            f = item.get("fields", {})
            url = f.get("origin") or (
                "https://reliefweb.int" + f["url_alias"] if f.get("url_alias") else None
            )
            if not url:
                continue
            results.append({
                "source_system": "ReliefWeb",
                "title": f.get("title", ""),
                "donor": ", ".join(s.get("name", "") for s in f.get("source", [])),
                "countries": [c.get("name", "") for c in f.get("country", [])],
                "body": (f.get("body") or "")[:4000],
                "published": (f.get("date") or {}).get("created", ""),
                "url": url,
                "deadline": None,  # extracted later by enrich.py — never invented
            })
    except Exception as e:
        print(f"[reliefweb] error: {e}")
    return results
