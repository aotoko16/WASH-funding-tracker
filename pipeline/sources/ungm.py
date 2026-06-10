"""UNGM (UN Global Marketplace) — PRIMARY source for UN system tenders/EOIs incl. UNICEF.
Public notice search endpoint (the same XHR the website uses).
Deadlines are structured = reliable.
"""
import requests

API = "https://www.ungm.org/Public/Notice/Search"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "wash-funding-tracker",
}


def fetch():
    results = []
    payload = {
        "PageIndex": 0,
        "PageSize": 30,
        "Title": "water sanitation",
        "Description": "",
        "Reference": "",
        "PublishedFrom": "",
        "PublishedTo": "",
        "DeadlineFrom": "",
        "DeadlineTo": "",
        "Countries": [],
        "Agencies": [],
        "UNSPSCs": [],
        "NoticeTypes": [],
        "SortField": "DatePublished",
        "SortAscending": False,
        "isActive": True,
        "NoticeSearchTotalLabelId": "noticeSearchTotal",
        "TypeOfCompetitions": [],
    }
    try:
        r = requests.post(API, json=payload, headers=HEADERS, timeout=40)
        r.raise_for_status()
        data = r.json()
        for n in data.get("noticeSearchDtos", data if isinstance(data, list) else []):
            notice_id = n.get("id") or n.get("Id")
            if not notice_id:
                continue
            results.append({
                "source_system": "UNGM",
                "title": n.get("title") or n.get("Title", ""),
                "donor": n.get("agency") or n.get("Agency", "UN System"),
                "countries": [n.get("country") or n.get("Country", "")],
                "body": (n.get("description") or n.get("Description") or "")[:4000],
                "published": n.get("publishedOn") or n.get("DatePublished", ""),
                "deadline": n.get("deadlineOn") or n.get("Deadline") or None,
                "url": f"https://www.ungm.org/Public/Notice/{notice_id}",
            })
    except Exception as e:
        print(f"[ungm] error: {e}")
    return results
