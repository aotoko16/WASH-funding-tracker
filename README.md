# WASH Funding Tracker

A daily-updated dashboard of WASH funding opportunities for WASH teams in East Asia & the Pacific.

## Why this is accurate

Three rules are hard-coded into the pipeline:

1. **Primary sources only.** Data comes directly from donor systems — Grants.gov (USAID/BHA), the EU Funding & Tenders Portal, UNGM, the UN Partner Portal, and donor pages (Gates, ADB, World Bank). ReliefWeb is a supplementary feed for humanitarian appeals, not the backbone.
2. **Every link is verified.** Before publication, every URL gets an HTTP check. Dead links are dropped, redirects are resolved to the final page.
3. **Deadlines are never invented.** A deadline appears only if the donor's system provides it as a structured field, or it is explicitly written in the opportunity text. Otherwise the dashboard says *"Deadline not stated — check the source page."*

## Setup (one time, ~10 minutes)

1. Create a GitHub repository and upload this entire folder.
2. **Settings → Pages** → Source: `main` branch, root → Save.
3. (Optional, recommended) **Settings → Secrets and variables → Actions → New repository secret**:
   - Name: `ANTHROPIC_API_KEY`
   - Value: your key from console.anthropic.com
   Without it the tracker still works, but eligibility/requirements summaries will be empty.
4. **Actions tab → Update funding data → Run workflow** to populate `data/data.json` for the first time.

After that it self-updates every morning at 05:00 Bangkok time.

## Run locally

```bash
pip install requests
ANTHROPIC_API_KEY=sk-... python pipeline/fetch.py
python -m http.server 8000   # open http://localhost:8000
```

## Architecture

```
GitHub Actions (daily, 05:00 ICT)
  └─ pipeline/fetch.py
       ├─ sources/grantsgov.py     ← Grants.gov search2 API (structured deadlines)
       ├─ sources/sedia.py         ← EU Funding & Tenders Portal (structured deadlines)
       ├─ sources/ungm.py          ← UNGM notices (structured deadlines)
       ├─ sources/unpp.py          ← UN Partner Portal CFEIs
       ├─ sources/donor_pages.py   ← Gates / ADB / World Bank listing pages
       ├─ sources/reliefweb.py     ← ReliefWeb appeals (supplementary)
       ├─ validate.py              ← HTTP-checks every URL, drops dead links
       └─ enrich.py                ← Claude extracts deadline/budget/eligibility (nulls when absent)
            └─ data/data.json      ← the only thing the dashboard reads
index.html                          ← static dashboard on GitHub Pages
```

## Adding a new source

Create `pipeline/sources/yourdonor.py` with a `fetch()` returning dicts with keys
`source_system, title, donor, countries, body, published, deadline, url`,
then add it to the `SOURCES` list in `fetch.py`. Validation and enrichment apply automatically.

## Known limitations

- UNPP's public endpoint is undocumented and may change; failures are logged, not fatal.
- Donor listing pages (Gates/ADB/WB) can change their HTML; the regex patterns in
  `donor_pages.py` may need occasional updates. The Actions log will show zero results
  from a source when that happens.
- Japan (MOFA/JICA) calls are mostly published as PDFs without feeds; track these
  manually for now.
