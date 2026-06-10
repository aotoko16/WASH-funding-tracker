"""EU Funding & Tenders Portal (SEDIA) — PRIMARY source for EU/ECHO/Horizon calls.
Public search API, apiKey=SEDIA (a public constant, not a secret).
Deadlines come as structured metadata = reliable.
"""
import json
import requests

API = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"

QUERIES = ["water sanitation hygiene", "WASH"]


def fetch():
    results = []
    seen = set()
    for q in QUERIES:
        params = {"apiKey": "SEDIA", "text": q, "pageSize": 25, "pageNumber": 1}
        # SEDIA expects a multipart/form-data style 'query' describing filters
        query_body = {
            "bool": {
                "must": [
                    {"terms": {"type": ["1", "2"]}},          # 1=tenders, 2=grants
                    {"terms": {"status": ["31094501", "31094502"]}},  # open / forthcoming
                ]
            }
        }
        try:
            r = requests.post(
                API,
                params=params,
                files={
                    "query": ("query.json", json.dumps(query_body), "application/json"),
                    "languages": ("lang.json", json.dumps(["en"]), "application/json"),
                },
                timeout=40,
            )
            r.raise_for_status()
            for item in r.json().get("results", []):
                meta = item.get("metadata", {})
                ident = item.get("reference") or meta.get("identifier", [""])[0]
                if ident in seen:
                    continue
                seen.add(ident)
                deadline_raw = (meta.get("deadlineDate") or [None])[0]
                title = (meta.get("title") or [item.get("summary", "")])[0]
                url = item.get("url") or (
                    f"https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/{ident.lower()}"
                    if ident else None
                )
                if not url:
                    continue
                results.append({
                    "source_system": "EU Funding & Tenders Portal",
                    "title": title,
                    "donor": "European Commission",
                    "countries": [],
                    "body": (item.get("content") or item.get("summary") or "")[:4000],
                    "published": (meta.get("startDate") or [""])[0],
                    "deadline": deadline_raw,  # structured field — trustworthy
                    "url": url,
                })
        except Exception as e:
            print(f"[sedia] error for '{q}': {e}")
    return results
