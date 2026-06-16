"""
Scrape SEC EDGAR for Russia-related impairment/write-down disclosures.

For each US-headquartered firm in the exiter sample:
  1. Queries the EDGAR EFTS API to find 10-K/20-F filings mentioning the
     company + Russia + impairment.
  2. For each unique filing found, uses the EDGAR submissions API
     (data.sec.gov) to get the primary document filename, then fetches
     and scans ALL qualifying filings (FY2022, FY2023, FY2024).
  3. Extracts dollar amounts from Russia + impairment/write-down context
     windows and writes to exit_payoffs_collected.csv.

Run this script LOCALLY — SEC.gov is blocked from cloud sandboxes.

Usage:
  python3 04_collect_exit_payoffs.py [--limit N] [--workers W]
  --limit N    First N firms only (testing)
  --workers W  Parallel threads (default 3; keep ≤ 5 for SEC rate limits)
"""

import csv
import re
import sys
import time
import argparse
from collections import defaultdict
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
SUBMISSIONS_API = "https://data.sec.gov/submissions/CIK{cik}.json"
EDGAR_ARCHIVES = "https://www.sec.gov/Archives/edgar/data"
EDGAR_SEARCH_UI = (
    "https://www.sec.gov/edgar/search/#/q={query}"
    "&dateRange=custom&category=custom"
    "&startdt=2022-01-01&enddt=2024-12-31&forms=10-K%2C20-F"
)

HEADERS = {"User-Agent": "Academic Research cuijiaxin0216@gmail.com"}

US_COUNTRIES = {"United States", "US", "USA"}

# Only these form types contain Russia write-down disclosures
TARGET_FORMS = {"10-K", "20-F"}

# Date range for relevant filings (covers FY2021 10-K filed early 2022 through FY2023)
START_DATE = "2022-01-01"
END_DATE   = "2024-12-31"

# ── Regex patterns ─────────────────────────────────────────────────────────

# Pattern 1: Russia mention → impairment keyword → dollar amount (forward window)
FORWARD_RE = re.compile(
    r"Russia[n]?.{0,500}?"
    r"(?:impairment|write[- ]?(?:down|off)|charge|loss|exit costs?|divestiture).{0,300}?"
    r"\$([\d,]+(?:\.\d+)?)\s*(million|billion|thousand)",
    re.IGNORECASE | re.DOTALL,
)

# Pattern 2: Dollar amount → Russia or impairment keyword (backward window)
BACKWARD_RE = re.compile(
    r"\$([\d,]+(?:\.\d+)?)\s*(million|billion|thousand).{0,300}?"
    r"(?:Russia[n]?|impairment|write[- ]?(?:down|off))",
    re.IGNORECASE | re.DOTALL,
)


def to_usd_mn(amount_str: str, unit: str) -> float:
    value = float(amount_str.replace(",", ""))
    u = unit.lower()
    if u == "billion":
        return value * 1_000
    if u == "thousand":
        return value / 1_000
    return value


def edgar_search_url(name: str) -> str:
    return EDGAR_SEARCH_UI.format(query=quote(f"{name} Russia impairment write"))


# ── EDGAR API helpers ──────────────────────────────────────────────────────

def query_efts(name: str, session: requests.Session) -> list[dict]:
    """
    Query EFTS for filings mentioning company + Russia + impairment.
    Returns list of parsed hit dicts.

    The EFTS _id field is a document path:
      /Archives/edgar/data/{cik}/{accession18}/{filename}
    """
    params = {
        "q": f'"{name}" Russia impairment',
        "forms": "10-K,20-F",
        "dateRange": "custom",
        "startdt": START_DATE,
        "enddt": END_DATE,
    }
    try:
        resp = session.get(EFTS_API, params=params, timeout=20)
        if resp.status_code == 429:
            time.sleep(15)
            resp = session.get(EFTS_API, params=params, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as e:
        return [{"_error": str(e)}]

    hits = resp.json().get("hits", {}).get("hits", [])
    parsed = []
    for h in hits:
        src = h.get("_source", {})
        raw_id = h.get("_id", "")   # e.g. /Archives/edgar/data/868857/000141.../file.htm

        # Parse path components
        parts = raw_id.lstrip("/").split("/")
        # ['Archives','edgar','data',{cik},{acc18},{filename}]
        if len(parts) >= 5 and parts[0] == "Archives":
            cik       = parts[3]
            acc18     = parts[4]   # 18-digit accession, no dashes
            filename  = parts[5] if len(parts) > 5 else ""
        else:
            cik       = src.get("entity_id", "")
            acc18     = ""
            filename  = ""

        parsed.append({
            "entity_name":      src.get("entity_name", ""),
            "form_type":        src.get("form_type", ""),
            "file_date":        src.get("file_date", ""),
            "period_of_report": src.get("period_of_report", ""),
            "cik":              cik,
            "acc18":            acc18,
            "filename":         filename,
            "doc_url": f"https://www.sec.gov{raw_id}" if raw_id.startswith("/Archives") else "",
        })
    return parsed


def acc18_to_dashed(acc18: str) -> str:
    """'0001410578-24-002030' from '000141057824002030'"""
    return f"{acc18[:10]}-{acc18[10:12]}-{acc18[12:]}"


def get_submissions(cik: str, session: requests.Session) -> dict | None:
    """
    Fetch EDGAR submissions JSON for a CIK.
    Returns the 'filings.recent' dict with parallel arrays
    (accessionNumber, filingDate, form, primaryDocument, ...).
    """
    cik_padded = cik.zfill(10)
    url = SUBMISSIONS_API.format(cik=cik_padded)
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("filings", {}).get("recent", {})
    except requests.RequestException:
        return None


def get_primary_doc_url(cik: str, acc18: str, session: requests.Session) -> str | None:
    """
    Given CIK + 18-digit accession, return URL of the primary 10-K/20-F document
    by looking up the filing index page.
    """
    acc_dashed = acc18_to_dashed(acc18)
    index_url = f"{EDGAR_ARCHIVES}/{cik}/{acc_dashed}/{acc_dashed}-index.htm"
    try:
        resp = session.get(index_url, timeout=15)
        resp.raise_for_status()
        text = resp.text
    except requests.RequestException:
        return None

    # Look for the primary document: a .htm/.html link described as "Complete submission"
    # or the first non-index .htm in the filing
    primary_re = re.compile(
        r'href="(/Archives/edgar/data/' + re.escape(cik) + r'/'
        + re.escape(acc_dashed.replace("-", "")) + r'/([^"]+\.htm[l]?))"',
        re.IGNORECASE,
    )
    candidates = []
    for m in primary_re.finditer(text):
        path = m.group(1)
        fname = m.group(2).lower()
        # Skip obvious exhibits and index files
        if any(x in fname for x in ("ex", "index", "xbrl", "r1.", "r2.", "r3.")):
            continue
        candidates.append("https://www.sec.gov" + path)

    return candidates[0] if candidates else None


def get_all_filings_for_cik(
    cik: str, session: requests.Session
) -> list[dict]:
    """
    Use EDGAR submissions API to get all 10-K/20-F filings for a CIK
    in the target date range. Returns list of
    {form, filing_date, period, acc18, primary_doc_url}.
    """
    recent = get_submissions(cik, session)
    if not recent:
        return []

    forms     = recent.get("form", [])
    dates     = recent.get("filingDate", [])
    accessions= recent.get("accessionNumber", [])  # already dashed
    primary   = recent.get("primaryDocument", [])
    periods   = recent.get("reportDate", [])

    results = []
    for form, date, acc_dashed, doc, period in zip(forms, dates, accessions, primary, periods):
        if form not in TARGET_FORMS:
            continue
        if not (START_DATE <= date <= END_DATE):
            continue
        acc18 = acc_dashed.replace("-", "")
        doc_url = f"{EDGAR_ARCHIVES}/{cik}/{acc18}/{doc}" if doc else None
        results.append({
            "form":         form,
            "filing_date":  date,
            "period":       period,
            "acc18":        acc18,
            "primary_doc_url": doc_url,
        })

    return results


def extract_amounts(text: str, filing_url: str) -> list[dict]:
    """Find all Russia-impairment dollar amounts in cleaned filing text."""
    found = []
    seen_amounts = set()

    for pattern in (FORWARD_RE, BACKWARD_RE):
        for m in pattern.finditer(text):
            amt_mn = to_usd_mn(m.group(1), m.group(2))
            # Filter implausible values
            if not (0.1 <= amt_mn <= 500_000):
                continue
            key = round(amt_mn, 1)
            if key in seen_amounts:
                continue
            seen_amounts.add(key)
            context = re.sub(r"\s+", " ", m.group(0))[:400]
            found.append({
                "amount_usd_mn": round(amt_mn, 2),
                "context":       context,
                "filing_url":    filing_url,
            })

    return found


def fetch_and_extract(doc_url: str, session: requests.Session) -> list[dict]:
    """Download a filing document, strip HTML, and extract Russia amounts."""
    try:
        resp = session.get(doc_url, timeout=45)
        resp.raise_for_status()
        text = resp.text
    except requests.RequestException:
        return []

    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return extract_amounts(text, doc_url)


# ── Per-firm pipeline ──────────────────────────────────────────────────────

def process_firm(firm: dict, session: requests.Session) -> dict:
    name     = firm["name"]
    country  = firm.get("country", "")
    industry = firm.get("industry", "")
    grade    = firm.get("grade_latest", "")
    action   = firm.get("action_type", "")

    base = {
        "name":            name,
        "country":         country,
        "industry":        industry,
        "grade_latest":    grade,
        "action_type":     action,
        "edgar_search_url": edgar_search_url(name),
        "filings_searched":  0,
        "writedown_usd_mn":  "",
        "sale_price_usd_mn": "",   # filled manually
        "all_amounts_mn":    "",
        "filing_dates":      "",
        "filing_urls":       "",
        "status":            "",
    }

    # Step 1: EFTS search to discover CIK
    hits = query_efts(name, session)
    time.sleep(0.2)

    if hits and "_error" in hits[0]:
        base["status"] = f"efts_error:{hits[0]['_error']}"
        return base

    if not hits:
        base["status"] = "no_efts_results"
        return base

    # Collect unique CIKs from hits (usually just one)
    ciks = list({h["cik"] for h in hits if h.get("cik")})
    if not ciks:
        base["status"] = "no_cik_in_hits"
        return base

    cik = ciks[0]

    # Step 2: Get ALL 10-K/20-F filings for this CIK via submissions API
    filings = get_all_filings_for_cik(cik, session)
    time.sleep(0.2)

    if not filings:
        # Fallback: use filing URLs directly from EFTS hits
        filings_from_hits = []
        seen_acc = set()
        for h in hits:
            if h.get("acc18") and h["acc18"] not in seen_acc:
                seen_acc.add(h["acc18"])
                filings_from_hits.append({
                    "form":            h["form_type"],
                    "filing_date":     h["file_date"],
                    "period":          h.get("period_of_report", ""),
                    "acc18":           h["acc18"],
                    "primary_doc_url": None,  # will try index fallback
                })
        filings = filings_from_hits

    if not filings:
        base["status"] = "no_filings_found"
        return base

    base["filings_searched"] = len(filings)

    # Step 3: For each filing, fetch primary document and extract amounts
    all_amounts = []
    filing_dates = []
    filing_urls  = []

    for filing in filings:
        doc_url = filing.get("primary_doc_url")

        # If submissions API gave no URL, fall back to index-page lookup
        if not doc_url and filing.get("acc18"):
            doc_url = get_primary_doc_url(cik, filing["acc18"], session)
            time.sleep(0.15)

        # Last resort: use the raw document URL from the EFTS hit
        if not doc_url:
            matching_hits = [h for h in hits if h.get("acc18") == filing.get("acc18") and h.get("doc_url")]
            if matching_hits:
                doc_url = matching_hits[0]["doc_url"]

        if not doc_url:
            continue

        amounts = fetch_and_extract(doc_url, session)
        time.sleep(0.2)

        if amounts:
            all_amounts.extend(amounts)
            filing_dates.append(filing.get("filing_date", ""))
            filing_urls.append(doc_url)

    if all_amounts:
        # Primary estimate: largest amount (most likely to be total write-down)
        largest = max(all_amounts, key=lambda x: x["amount_usd_mn"])
        base["writedown_usd_mn"] = largest["amount_usd_mn"]
        base["all_amounts_mn"] = " | ".join(
            f"${a['amount_usd_mn']}mn ({a['filing_url'].split('/')[-1]})"
            for a in sorted(all_amounts, key=lambda x: -x["amount_usd_mn"])[:5]
        )
        base["filing_dates"] = " | ".join(dict.fromkeys(filing_dates))
        base["filing_urls"]  = " | ".join(dict.fromkeys(filing_urls))
        base["status"] = f"extracted:{len(all_amounts)}_amounts_from_{len(filings)}_filings"
    else:
        base["filing_dates"] = " | ".join(f.get("filing_date","") for f in filings)
        base["status"] = f"fetched_{len(filings)}_filings_no_amounts"

    return base


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()

    firms = []
    with open(IN_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("country", "").strip() in US_COUNTRIES:
                firms.append(row)

    if args.limit:
        firms = firms[: args.limit]

    print(f"Processing {len(firms)} US firms...")

    # Regenerate search URL file with correct format
    with open(URL_FILE, "w", encoding="utf-8") as f:
        f.write("# SEC EDGAR Search URLs (open in browser to review results)\n\n")
        for firm in firms:
            f.write(f"{firm['name']}\n{edgar_search_url(firm['name'])}\n\n")
    print(f"Search URLs → {URL_FILE}")

    out_fields = [
        "name", "country", "industry", "grade_latest", "action_type",
        "filings_searched", "filing_dates",
        "writedown_usd_mn", "sale_price_usd_mn",
        "all_amounts_mn", "filing_urls", "edgar_search_url", "status",
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
            amt = result.get("writedown_usd_mn", "")
            status = result.get("status", "")
            filings_n = result.get("filings_searched", 0)
            print(
                f"  [{done:>3}/{len(firms)}] {name[:50]:<50}"
                f" | filings={filings_n}"
                f" | {status}"
                f" | ${amt}mn"
            )

    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
        writer.writeheader()
        results.sort(key=lambda r: r.get("name", ""))
        writer.writerows(results)

    extracted = [r for r in results if "extracted" in r.get("status", "")]
    print(f"\nResults: {len(extracted)}/{len(results)} firms with extracted amounts → {OUT_FILE}")
    print("Fill in sale_price_usd_mn manually for 'sold' action_type firms.")


if __name__ == "__main__":
    main()
