"""Main pipeline: fetch from all primary sources -> dedupe -> validate links -> enrich -> data.json
Run: python pipeline/fetch.py
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sources import reliefweb, grantsgov, sedia, ungm, unpp, donor_pages  # noqa: E402
from validate import validate  # noqa: E402
from enrich import enrich  # noqa: E402

OUT = Path(__file__).parent.parent / "data" / "data.json"

SOURCES = [
    ("Grants.gov (USAID/BHA, US federal)", grantsgov),
    ("EU Funding & Tenders Portal", sedia),
    ("UNGM (UN system tenders)", ungm),
    ("UN Partner Portal (CFEIs)", unpp),
    ("Donor pages (Gates/ADB/World Bank)", donor_pages),
    ("ReliefWeb (humanitarian appeals)", reliefweb),
]


def normalize_date(s):
    """Best-effort to ISO YYYY-MM-DD; returns None if unparseable. Never invents."""
    if not s:
        return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%d %b %Y", "%b %d, %Y", "%d-%b-%Y"):
        try:
            return datetime.strptime(s[:len(datetime.now().strftime(fmt))], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", s)
    return m.group(1) if m else None


def dedupe(opps):
    seen, out = set(), []
    for o in opps:
        key = re.sub(r"\W+", "", o["title"].lower())[:80]
        if key in seen:
            continue
        seen.add(key)
        out.append(o)
    return out


def main():
    all_opps = []
    stats = {}
    for label, mod in SOURCES:
        print(f"=== Fetching: {label}")
        items = mod.fetch()
        stats[label] = len(items)
        all_opps.extend(items)

    print(f"\nFetched total: {len(all_opps)}")
    all_opps = dedupe(all_opps)
    print(f"After dedupe: {len(all_opps)}")

    all_opps = validate(all_opps)
    all_opps = enrich(all_opps)

    today = datetime.now(timezone.utc).date()
    final = []
    for o in all_opps:
        o["deadline"] = normalize_date(o.get("deadline"))
        if o["deadline"]:
            try:
                dl = datetime.strptime(o["deadline"], "%Y-%m-%d").date()
                if dl < today:
                    continue  # expired — drop
                o["days_left"] = (dl - today).days
            except ValueError:
                o["deadline"], o["days_left"] = None, None
        else:
            o["days_left"] = None  # honestly unknown — dashboard shows "Not specified"
        o["url"] = o.pop("final_url", o["url"])
        o.pop("body", None)  # keep data.json lean
        final.append(o)

    # Sort: known deadlines ascending first, unknown last (by published desc)
    final.sort(key=lambda x: (x["days_left"] is None, x["days_left"] or 0))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_stats": stats,
        "count": len(final),
        "opportunities": final,
    }, indent=2, ensure_ascii=False))
    print(f"\nWrote {len(final)} opportunities -> {OUT}")


if __name__ == "__main__":
    main()
