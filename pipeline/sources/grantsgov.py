"""Grants.gov search2 API — PRIMARY source for US federal funding (USAID, BHA, State, EPA...).
No authentication required. Deadlines are structured fields = reliable.
Docs: https://www.grants.gov/api/api-guide
"""
import requests

API = "https://api.grants.gov/v1/api/search2"

KEYWORDS = ["water sanitation hygiene", "WASH humanitarian", "safe drinking water international"]


def fetch():
    results = []
    seen = set()
    for kw in KEYWORDS:
        payload = {
            "keyword": kw,
            "oppStatuses": "posted|forecasted",
            "rows": 25,
        }
        try:
            r = requests.post(API, json=payload, timeout=30)
            r.raise_for_status()
            hits = r.json().get("data", {}).get("oppHits", []) or []
            for h in hits:
                opp_id = h.get("id") or h.get("number")
                if opp_id in seen:
                    continue
                seen.add(opp_id)
                results.append({
                    "source_system": "Grants.gov",
                    "title": h.get("title", ""),
                    "donor": h.get("agencyName") or h.get("agency", "US Federal"),
                    "countries": [],  # US fed grants rarely geo-coded in search; enrich.py fills from body
                    "body": "",
                    "published": h.get("openDate", ""),
                    # closeDate is a structured field from the donor itself = trustworthy
                    "deadline": h.get("closeDate") or None,
                    "url": f"https://www.grants.gov/search-results-detail/{h.get('id')}",
                    "opportunity_number": h.get("number", ""),
                })
        except Exception as e:
            print(f"[grants.gov] error for '{kw}': {e}")
    return results
