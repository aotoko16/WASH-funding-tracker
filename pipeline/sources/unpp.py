"""UN Partner Portal (UNPP) — PRIMARY source for CFEIs from UNICEF, UNHCR, WFP, UNFPA, WHO.
The public landing page exposes an open-opportunities JSON endpoint.
NOTE: endpoint may evolve; failures are non-fatal and logged.
"""
import requests

# The landing page at unpartnerportal.org/landing/opportunities/ is backed by an API.
CANDIDATE_ENDPOINTS = [
    "https://www.unpartnerportal.org/api/public/partnership-opportunities/?page_size=30&ordering=-published",
    "https://www.unpartnerportal.org/landing/api/opportunities/?limit=30",
]

HEADERS = {"User-Agent": "wash-funding-tracker"}

WASH_TERMS = ("wash", "water", "sanitation", "hygiene")


def fetch():
    results = []
    for endpoint in CANDIDATE_ENDPOINTS:
        try:
            r = requests.get(endpoint, headers=HEADERS, timeout=30)
            if r.status_code != 200:
                continue
            data = r.json()
            items = data.get("results", data if isinstance(data, list) else [])
            for it in items:
                title = it.get("title", "")
                blob = (title + " " + str(it.get("description", ""))).lower()
                if not any(t in blob for t in WASH_TERMS):
                    continue
                cfei_id = it.get("id")
                results.append({
                    "source_system": "UN Partner Portal",
                    "title": title,
                    "donor": it.get("agency", {}).get("name", "UN Agency") if isinstance(it.get("agency"), dict) else str(it.get("agency", "UN Agency")),
                    "countries": [c.get("name", "") for c in it.get("countries", []) if isinstance(c, dict)],
                    "body": str(it.get("description", ""))[:4000],
                    "published": it.get("published_timestamp", ""),
                    "deadline": it.get("deadline_date") or None,
                    "url": f"https://www.unpartnerportal.org/landing/opportunities/{cfei_id}" if cfei_id else "https://www.unpartnerportal.org/landing/opportunities/",
                })
            if results:
                break  # first working endpoint wins
        except Exception as e:
            print(f"[unpp] {endpoint} error: {e}")
    return results
