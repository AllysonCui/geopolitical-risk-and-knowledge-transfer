"""
Build a template for exit payoff data (dependent variable Y_i).

Since no single public API returns write-down and sale-price data,
this script does two things:

  1. Produces data/collected/exit_payoffs_template.csv — a pre-filled
     shell with all Grade-A exiters plus action-text classification,
     leaving the financial columns blank for manual/semi-manual fill.

  2. Prints per-firm search queries for SEC EDGAR full-text search
     (EFTS) to find 10-K/20-F filings mentioning Russia impairments.
     Each URL can be opened in a browser or fetched programmatically.

Financial columns to fill (manually from annual reports):
  - writedown_usd_mn     : Russia-related write-down / impairment reported (USD millions)
  - sale_price_usd_mn    : Proceeds from sale of Russian subsidiary (USD millions)
  - book_value_pre_usd_mn: Book value of Russian subsidiary before exit
  - exit_year            : Year the exit was finalised
  - exit_quarter         : Quarter (1-4)
  - data_source          : e.g. "10-K 2022", "press release", "KSE tracker"
  - notes                : Free text

Sources to check per firm:
  - US firms     : SEC EDGAR EFTS full-text search (automated below)
  - EU firms     : ESMA ESEF filings, company investor relations pages
  - KSE Institute: https://kse.ua/selfsanctions-kse-institute/
  - Refinitiv    : M&A deals database (if your institution has access)
"""

import csv
from pathlib import Path
from urllib.parse import quote

IN_FILE = Path(__file__).parent.parent / "data" / "collected" / "firms_exit_panel.csv"
OUT_TEMPLATE = Path(__file__).parent.parent / "data" / "collected" / "exit_payoffs_template.csv"
OUT_EDGAR_QUERIES = Path(__file__).parent.parent / "data" / "collected" / "edgar_search_urls.txt"

FINANCIAL_FIELDS = [
    "writedown_usd_mn",
    "sale_price_usd_mn",
    "book_value_pre_usd_mn",
    "exit_year",
    "exit_quarter",
    "data_source",
    "notes",
]

US_COUNTRIES = {"United States", "US", "USA"}

EDGAR_BASE = "https://efts.sec.gov/LATEST/search-index?q={query}&dateRange=custom&startdt=2022-01-01&enddt=2024-12-31&forms=10-K,20-F"


def edgar_url(company_name: str) -> str:
    query = quote(f'"{company_name}" Russia impairment write')
    return EDGAR_BASE.format(query=query)


def main():
    firms = []
    with open(IN_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            firms.append(row)

    # Focus on Grade A (full exit) + Grade B (suspended) as primary sample
    sample = [r for r in firms if r["grade_latest"] in ("A", "B")]
    print(f"Exit payoff template: {len(sample)} Grade A+B firms")

    # ── Write template CSV ──────────────────────────────────────────────────
    out_fields = (
        ["name", "country", "industry", "grade_latest", "action_type", "action_text"]
        + FINANCIAL_FIELDS
    )

    with open(OUT_TEMPLATE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        for firm in sample:
            row = {k: firm.get(k, "") for k in out_fields}
            for field in FINANCIAL_FIELDS:
                row[field] = ""   # blank — to be filled
            writer.writerow(row)

    print(f"Template written → {OUT_TEMPLATE}")

    # ── Write EDGAR search URLs for US-headquartered firms ──────────────────
    us_firms = [r for r in sample if r.get("country", "").strip() in US_COUNTRIES]
    print(f"Generating SEC EDGAR search URLs for {len(us_firms)} US firms...")

    with open(OUT_EDGAR_QUERIES, "w", encoding="utf-8") as f:
        f.write("# SEC EDGAR Full-Text Search URLs\n")
        f.write("# Search for Russia impairment/write-down mentions in 10-K and 20-F filings\n")
        f.write("# Open each URL in a browser, find the filing, check Note to Financial Statements\n\n")
        for firm in us_firms:
            name = firm["name"]
            url = edgar_url(name)
            f.write(f"{name}\n{url}\n\n")

    print(f"EDGAR URLs written → {OUT_EDGAR_QUERIES}")

    # ── Summary ─────────────────────────────────────────────────────────────
    sold_count = sum(1 for r in sample if r["action_type"] == "sold")
    wd_count = sum(1 for r in sample if r["action_type"] == "writedown_mentioned")
    nat_count = sum(1 for r in sample if r["action_type"] == "nationalized")
    susp_count = sum(1 for r in sample if r["action_type"] == "suspended")
    other_count = sum(1 for r in sample if r["action_type"] == "other")

    print(f"\nAction-type breakdown for Grade A+B sample:")
    print(f"  sold               : {sold_count}")
    print(f"  writedown_mentioned: {wd_count}")
    print(f"  nationalized       : {nat_count}")
    print(f"  suspended          : {susp_count}")
    print(f"  other              : {other_count}")
    print(f"\nPriority for manual data entry: 'sold' and 'writedown_mentioned' firms")
    print(f"(These are most likely to have quantifiable Y_i in annual reports)")


if __name__ == "__main__":
    main()
