"""Direct donor pages — for donors without proper APIs (JICA, Gates Foundation, ADB, World Bank).
We parse listing pages conservatively: title + link only.
Deadlines are NOT guessed here; enrich.py extracts them from the linked page text when present.
"""
import re
import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (wash-funding-tracker)"}

WASH_TERMS = ("wash", "water", "sanitation", "hygiene", "drinking water")

SOURCES = [
    {
        "name": "Gates Foundation RFPs",
        "donor": "Bill & Melinda Gates Foundation",
        "url": "https://www.gatesfoundation.org/about/how-we-work/grant-opportunities",
        "link_pattern": r'href="(/about/how-we-work/grant-opportunities/[^"]+)"[^>]*>([^<]{10,200})<',
        "base": "https://www.gatesfoundation.org",
    },
    {
        "name": "ADB Opportunities",
        "donor": "Asian Development Bank",
        "url": "https://www.adb.org/projects/tenders",
        "link_pattern": r'href="(/projects/tenders/[^"]+)"[^>]*>([^<]{10,200})<',
        "base": "https://www.adb.org",
    },
    {
        "name": "World Bank Procurement",
        "donor": "World Bank",
        "url": "https://projects.worldbank.org/en/projects-operations/procurement?srce=both&sector_exact=Water%2C%20sanitation%20and%20waste%20management",
        "link_pattern": r'href="(https://projects\.worldbank\.org/en/projects-operations/procurement-detail/[^"]+)"[^>]*>([^<]{10,200})<',
        "base": "",
    },
]


def fetch():
    results = []
    for src in SOURCES:
        try:
            r = requests.get(src["url"], headers=HEADERS, timeout=40)
            if r.status_code != 200:
                print(f"[donor_pages] {src['name']} returned {r.status_code}")
                continue
            html = r.text
            for m in re.finditer(src["link_pattern"], html, re.IGNORECASE):
                link, title = m.group(1), re.sub(r"\s+", " ", m.group(2)).strip()
                # WASH relevance filter — skip Gates RFP listing page itself etc.
                if not any(t in title.lower() for t in WASH_TERMS):
                    continue
                results.append({
                    "source_system": src["name"],
                    "title": title,
                    "donor": src["donor"],
                    "countries": [],
                    "body": "",
                    "published": "",
                    "deadline": None,
                    "url": (src["base"] + link) if link.startswith("/") else link,
                })
        except Exception as e:
            print(f"[donor_pages] {src['name']} error: {e}")
    return results
