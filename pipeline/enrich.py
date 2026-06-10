"""Claude enrichment — extracts structured fields from opportunity text.
HONESTY RULES (enforced by prompt + post-validation):
  - deadline: only if explicitly stated in the text; otherwise null. NEVER guessed.
  - All other fields: null when absent. The dashboard shows "Not specified" for nulls.
Runs only if ANTHROPIC_API_KEY is set; otherwise opportunities pass through unenriched.
"""
import json
import os
import re

import requests

API = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-20250514"

SYSTEM = """You extract structured data from funding opportunity texts for WASH programme staff at development organizations.
Return ONLY a JSON object, no markdown fences, with these keys:
- deadline: ISO date "YYYY-MM-DD" ONLY if a submission deadline is EXPLICITLY stated in the text. If not stated, null. NEVER infer or estimate.
- budget: string summarizing the funding amount/range if stated, else null.
- eligibility: one sentence on who can apply, if stated, else null.
- eligible_countries: array of country names explicitly listed, else [].
- requirements_summary: 2-3 sentences max summarizing key application requirements, else null.
- wash_relevance: "high" | "medium" | "low" — how directly this funds WASH work.
- un_eligible: true/false/null — can a UN agency apply or partner, based ONLY on the text.
If the text is too thin to judge a field, use null. Honesty over completeness."""


def enrich(opportunities):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print("[enrich] ANTHROPIC_API_KEY not set — skipping AI extraction")
        for o in opportunities:
            o.setdefault("wash_relevance", "medium")
        return opportunities

    headers = {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    for opp in opportunities:
        text = f"TITLE: {opp['title']}\nDONOR: {opp['donor']}\nBODY:\n{opp.get('body','')[:3500]}"
        try:
            r = requests.post(API, headers=headers, timeout=60, json={
                "model": MODEL,
                "max_tokens": 600,
                "system": SYSTEM,
                "messages": [{"role": "user", "content": text}],
            })
            r.raise_for_status()
            raw = r.json()["content"][0]["text"]
            raw = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
            data = json.loads(raw)

            # Structured deadlines from the source API always win over extracted ones
            if not opp.get("deadline") and data.get("deadline"):
                if re.match(r"^\d{4}-\d{2}-\d{2}$", str(data["deadline"])):
                    opp["deadline"] = data["deadline"]
            opp["budget"] = data.get("budget")
            opp["eligibility"] = data.get("eligibility")
            opp["eligible_countries"] = data.get("eligible_countries") or []
            opp["requirements_summary"] = data.get("requirements_summary")
            opp["wash_relevance"] = data.get("wash_relevance", "medium")
            opp["un_eligible"] = data.get("un_eligible")
        except Exception as e:
            print(f"[enrich] error on '{opp['title'][:50]}': {e}")
            opp.setdefault("wash_relevance", "medium")
    return opportunities
