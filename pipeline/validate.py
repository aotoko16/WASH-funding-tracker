"""Link validation — every opportunity URL is checked before it reaches the dashboard.
Dead links are dropped. This is non-negotiable: a funding tracker with broken links is worse than none.
"""
import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (wash-funding-tracker link checker)"}


def validate(opportunities):
    valid = []
    for opp in opportunities:
        url = opp.get("url")
        if not url or not url.startswith("http"):
            print(f"[validate] DROP (no url): {opp.get('title','')[:60]}")
            continue
        try:
            r = requests.head(url, headers=HEADERS, timeout=15, allow_redirects=True)
            # Some servers reject HEAD; retry with GET
            if r.status_code in (403, 405, 501):
                r = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True, stream=True)
                r.close()
            if r.status_code < 400:
                opp["final_url"] = r.url  # post-redirect canonical URL
                valid.append(opp)
            else:
                print(f"[validate] DROP ({r.status_code}): {url}")
        except Exception as e:
            print(f"[validate] DROP (error {type(e).__name__}): {url}")
    print(f"[validate] {len(valid)}/{len(opportunities)} links alive")
    return valid
