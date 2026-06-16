"""
Scrape SEC EDGAR for Russia-related impairment/write-down disclosures.

For each US-headquartered firm in the exiter sample:
  1. Queries the EDGAR full-text search API (EFTS) to find 10-K/20-F filings
     that mention the company name + Russia + impairment/write-down.
  2. For each filing found, fetches the filing index to identify the main
     document, then downloads and scans it for dollar amounts near
     Russia-related impairment language.
  3. Writes extracted amounts to exit_payoffs_collected.csv.

Run this script LOCALLY (not in the cloud sandbox) because SEC.gov requires
direct internet access.

Usage:
  python3 04_collect_exit_payoffs.py [--limit N] [--workers W]

  --limit N    Process only first N firms (for testing; default: all)
  --workers W  Parallel workers (default: 3; stay ≤ 5 to respect SEC rate limits)

SEC rate limit: max 10 requests/second. The script sleeps between batches.
"""

import csv
import json
import re
import sys
import time
import argparse
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote

try:
    import requests
except ImportError:
    sys.exit("pip install requests")

# ── Paths ──────────────────────────────────────────────────────────────────

BASE = Path(__file__).parent.parent
IN_FILE = BASE / "data" / "collected" / "firms_exiters.csv"
OUT_FILE = BASE / "data" / "collected" / "exit_payoffs_collected.csv"
URL_FILE = BASE / "data" / "collected" / "edgar_search_urls.txt"

# ── Constants ──────────────────────────────────────────────────────────────

EFTS_API = "https://efts.sec.gov/LATEST/search-index"
EDGAR_ARCHIVES = "https://www.sec.gov/Archives/edgar/data"
EDGAR_SEARCH_UI = "https://www.sec.gov/edgar/search/#/q={query}&dateRange=custom&category=custom&startdt=2022-01-01&enddt=2024-12-31&forms=10-K%2C20-F"

HEADERS = {
    "User-Agent": "Academic Research cuijiaxin0216@gmail.com",
    "Accept-Encoding": "gzip, deflate",
}

US_COUNTRIES = {"United States", "US", "USA"}

# Regex to find dollar amounts within a 500-char window of Russia mentions
RUSSIA_WINDOW_RE = re.compile(
    r"(?:Russia[n]?|Ukrainian?)[^\n]{0,400}"
    r"(?:impairment|write[- ]?(?:down|off)|charge|loss|exit|divest)[^\n]{0,200}"
    r"\$\s*([\d,]+(?:\.\d+)?)\s*(million|billion|thousand)",
    re.IGNORECASE | re.DOTALL,
)
AMOUNT_NEAR_RUSSIA_RE = re.compile(
    r"\$\s*([\d,]+(?:\.\d+)?)\s*(million|billion|thousand)[^\n]{0,300}"
    r"(?:Russia[n]?|impairment|write[- ]?(?:down|off))",
    re.IGNORECASE | re.DOTALL,
)


def to_usd_mn(amount_str: str, unit: str) -> float:
    """Convert extracted amount string + unit to USD millions."""
    value = float(amount_str.replace(",", ""))
    unit = unit.lower()
    if unit == "billion":
        return value * 1_000
    elif unit == "thousand":
        return value / 1_000
    return value  # already millions


def edgar_search_url_ui(company_name: str) -> str:
    """Generate the EDGAR search UI URL (human-readable, opens in browser)."""
    q = f"{company_name} Russia impairment write"
    return EDGAR_SEARCH_UI.format(query=quote(q))


def query_efts(company_name: str, session: requests.Session) -> list[dict]:
    """
    Query EFTS API for 10-K/20-F filings mentioning company + Russia + impairment.
    Returns list of {entity_name, form_type, file_date, cik, accession_no}.
    """
    params = {
        "q": f'"{company_name}" Russia impairment',
        "forms": "10-K,20-F",
        "dateRange": "custom",
        "startdt": "2022-01-01",
        "enddt": "2024-12-31",
        "_source": "entity_name,file_date,form_type,period_of_report,entity_id,file_num",
        "hits.hits._source": True,
        "hits.hits.total": True,
    }

    try:
        resp = session.get(EFTS_API, params=params, timeout=20)
        if resp.status_code == 429:
            time.sleep(10)
            resp = session.get(EFTS_API, params=params, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as e:
        return [{"error": str(e)}]

    data = resp.json()
    hits = data.get("hits", {}).get("hits", [])
    results = []
    for h in hits:
        src = h.get("_source", {})
        # CIK is in entity_id field; accession from _id (format: cik:accession)
        raw_id = h.get("_id", "")
        parts = raw_id.split(":")
        cik = src.get("entity_id", parts[0] if parts else "")
        accession = parts[1].replace("-", "") if len(parts) > 1 else ""
        results.append(
            {
                "entity_name": src.get("entity_name", ""),
                "form_type": src.get("form_type", ""),
                "file_date": src.get("file_date", ""),
                "period_of_report": src.get("period_of_report", ""),
                "cik": cik,
                "accession": accession,
            }
        )
    return results


def get_filing_document_url(cik: str, accession: str, session: requests.Session) -> str | None:
    """
    Fetch the filing index page and return the URL of the main 10-K/20-F document.
    Accession format: 18-digit string (no dashes) e.g. '0001234567890123456'
    """
    # EDGAR index URL format: /Archives/edgar/data/{cik}/{accession_dashes}/
    if not cik or not accession:
        return None

    # Format accession with dashes: XXXXXXXXXX-YY-ZZZZZZ
    acc_dashed = f"{accession[:10]}-{accession[10:12]}-{accession[12:]}"
    index_url = f"{EDGAR_ARCHIVES}/{cik}/{acc_dashed}/{acc_dashed}-index.htm"

    try:
        resp = session.get(index_url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException:
        return None

    # Find the primary document link — look for 10-K or 20-F type
    doc_re = re.compile(
        r'href="(/Archives/edgar/data/[^"]+\.htm[l]?)"[^>]*>\s*(?:[^<]*)'
        r'</a>[^<]*<[^>]+>(?:10-K|20-F|Annual Report)',
        re.IGNORECASE,
    )
    match = doc_re.search(resp.text)
    if match:
        return "https://www.sec.gov" + match.group(1)

    # Fallback: find any .htm file that isn't the index
    htm_re = re.compile(
        r'href="(/Archives/edgar/data/' + re.escape(cik) + r'/[^"]+\.htm[l]?)"',
        re.IGNORECASE,
    )
    matches = [m.group(1) for m in htm_re.finditer(resp.text)
               if "index" not in m.group(1).lower()]
    if matches:
        return "https://www.sec.gov" + matches[0]

    return None


def extract_russia_amounts(filing_url: str, session: requests.Session) -> list[dict]:
    """
    Download a 10-K/20-F document and extract all dollar amounts
    within context windows that mention Russia + impairment/write-down.
    Returns list of {amount_usd_mn, context, filing_url}.
    """
    try:
        resp = session.get(filing_url, timeout=30)
        resp.raise_for_status()
        text = resp.text
        # Strip HTML tags for cleaner text
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
    except requests.RequestException:
        return []

    found = []
    for pattern in (RUSSIA_WINDOW_RE, AMOUNT_NEAR_RUSSIA_RE):
        for m in pattern.finditer(text):
            amount_str, unit = m.group(1), m.group(2)
            amount_mn = to_usd_mn(amount_str, unit)
            # Skip implausibly large (>$500bn) or tiny (<$0.1mn) values
            if 0.1 <= amount_mn <= 500_000:
                context = m.group(0)[:300].replace("\n", " ")
                found.append(
                    {
                        "amount_usd_mn": round(amount_mn, 2),
                        "context": context,
                        "filing_url": filing_url,
                    }
                )

    # Deduplicate by amount
    seen = set()
    unique = []
    for f in found:
        key = f["amount_usd_mn"]
        if key not in seen:
            seen.add(key)
            unique.append(f)

    return unique


def process_firm(firm: dict, session: requests.Session) -> dict:
    """Full pipeline for one firm: EFTS search → filing → extract amounts."""
    name = firm["name"]
    country = firm.get("country", "")
    industry = firm.get("industry", "")
    grade = firm.get("grade_latest", "")
    action_type = firm.get("action_type", "")

    base = {
        "name": name,
        "country": country,
        "industry": industry,
        "grade_latest": grade,
        "action_type": action_type,
        "edgar_search_url": edgar_search_url_ui(name),
        "filings_found": 0,
        "writedown_usd_mn": "",
        "sale_price_usd_mn": "",
        "filing_date": "",
        "filing_form": "",
        "filing_url": "",
        "extracted_amounts": "",
        "status": "",
    }

    filings = query_efts(name, session)
    time.sleep(0.15)  # ~7 req/sec, well under SEC's 10 req/sec limit

    if filings and "error" in filings[0]:
        base["status"] = f"efts_error:{filings[0]['error']}"
        return base

    if not filings:
        base["status"] = "no_filings_found"
        return base

    base["filings_found"] = len(filings)
    filing = filings[0]  # use most recent
    base["filing_date"] = filing.get("file_date", "")
    base["filing_form"] = filing.get("form_type", "")

    doc_url = get_filing_document_url(filing["cik"], filing["accession"], session)
    time.sleep(0.15)

    if not doc_url:
        base["status"] = "filing_index_failed"
        base["filing_url"] = (
            f"{EDGAR_ARCHIVES}/{filing['cik']}/{filing['accession'][:10]}-"
            f"{filing['accession'][10:12]}-{filing['accession'][12:]}"
        )
        return base

    base["filing_url"] = doc_url
    amounts = extract_russia_amounts(doc_url, session)
    time.sleep(0.2)

    if amounts:
        # Report the largest amount as the primary writedown estimate
        largest = max(amounts, key=lambda x: x["amount_usd_mn"])
        base["writedown_usd_mn"] = largest["amount_usd_mn"]
        base["extracted_amounts"] = " | ".join(
            f"${a['amount_usd_mn']}mn" for a in amounts[:5]
        )
        base["status"] = "extracted"
    else:
        base["status"] = "filing_fetched_no_amounts"

    return base


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()

    # Load firms — all grades (not just A+B) to avoid missing partial exits
    firms = []
    with open(IN_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("country", "").strip() in US_COUNTRIES:
                firms.append(row)

    if args.limit:
        firms = firms[: args.limit]

    print(f"Processing {len(firms)} US-headquartered firms from exiter sample...")

    # ── Write search URLs file (fixed format) ──────────────────────────────
    with open(URL_FILE, "w", encoding="utf-8") as f:
        f.write("# SEC EDGAR Search URLs (open in browser to review results)\n\n")
        for firm in firms:
            f.write(f"{firm['name']}\n{edgar_search_url_ui(firm['name'])}\n\n")
    print(f"Search URLs → {URL_FILE}")

    # ── Scrape filings ──────────────────────────────────────────────────────
    out_fields = [
        "name", "country", "industry", "grade_latest", "action_type",
        "filings_found", "filing_date", "filing_form",
        "writedown_usd_mn", "sale_price_usd_mn",  # sale_price filled manually
        "extracted_amounts", "filing_url", "edgar_search_url", "status",
    ]

    results = []
    session = requests.Session()
    session.headers.update(HEADERS)

    def worker(firm):
        return process_firm(firm, session)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(worker, f): f["name"] for f in firms}
        done = 0
        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
            except Exception as e:
                result = {"name": name, "status": f"exception:{e}"}
            results.append(result)
            done += 1
            status = result.get("status", "")
            amt = result.get("writedown_usd_mn", "")
            print(f"  [{done}/{len(firms)}] {name[:45]:<45} | {status} | ${amt}mn")

    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
        writer.writeheader()
        results.sort(key=lambda r: r.get("name", ""))
        writer.writerows(results)

    # ── Summary ─────────────────────────────────────────────────────────────
    extracted = [r for r in results if r.get("status") == "extracted"]
    no_filing = [r for r in results if r.get("status") == "no_filings_found"]
    print(f"\nResults:")
    print(f"  Amounts extracted : {len(extracted)}")
    print(f"  No filings found  : {len(no_filing)}")
    print(f"  Other statuses    : {len(results) - len(extracted) - len(no_filing)}")
    print(f"\nOutput → {OUT_FILE}")
    print("\nNext: fill in sale_price_usd_mn manually for 'sold' firms,")
    print("      and cross-check extracted amounts against annual report tables.")


if __name__ == "__main__":
    main()
