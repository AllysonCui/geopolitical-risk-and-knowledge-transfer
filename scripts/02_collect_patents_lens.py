"""
Collect patent counts per company from Lens.org public API.

Uses the firms_exiters.csv produced by 01_parse_yale_tracker.py.
Queries Lens.org for each parent company's patent portfolio size
(a key input to the proprietary-intensity component of α).

Setup:
  1. Register at https://www.lens.org/ (free account)
  2. Go to Profile > Subscriptions > API & Bulk Data > create a token
  3. Set the token as an environment variable:
       export LENS_API_TOKEN="your-token-here"
  OR pass it as a command-line argument:
       python3 02_collect_patents_lens.py --token YOUR_TOKEN

Output:
  data/raw/lens/patents_by_firm.csv — one row per firm with patent counts
"""

import csv
import json
import os
import time
import argparse
from pathlib import Path

try:
    import requests
except ImportError:
    raise SystemExit("requests not installed: pip install requests")

# Load .env file from project root if it exists
ENV_FILE = Path(__file__).parent.parent / ".env"
if ENV_FILE.exists():
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                val = val.strip().strip("'\"")
                os.environ.setdefault(key.strip(), val)

LENS_API_URL = "https://api.lens.org/patent/search"
IN_FILE = Path(__file__).parent.parent / "data" / "analysis" / "firms_exiters.csv"
OUT_FILE = Path(__file__).parent.parent / "data" / "raw" / "lens" / "patents_by_firm.csv"

# Rate limit: Lens.org free tier allows ~10 req/min → sleep 7s between requests
REQUEST_DELAY_SEC = 7


def get_patent_count(company_name: str, token: str) -> dict:
    """
    Query Lens.org for patents assigned to `company_name`.
    Returns a dict with total patent count and family count.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "x-lens-token": token,
        "Content-Type": "application/json",
    }
    # Search both applicant and owner fields; use phrase match for precision
    payload = {
        "query": {
            "bool": {
                "should": [
                    {"match_phrase": {"applicant.name": company_name}},
                    {"match_phrase": {"owner.name": company_name}},
                ]
            }
        },
        "size": 1,
        "include": ["lens_id"],
    }

    try:
        resp = requests.post(LENS_API_URL, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            total_patents = data.get("total", 0)
            return {
                "patents_total": total_patents,
                "api_status": "ok",
            }
        elif resp.status_code == 429:
            return {"patents_total": None, "api_status": "rate_limited"}
        else:
            detail = ""
            try:
                detail = resp.text[:200]
            except Exception:
                pass
            return {"patents_total": None, "api_status": f"http_{resp.status_code}", "detail": detail}
    except requests.RequestException as e:
        return {"patents_total": None, "api_status": f"error:{e}"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", default=os.environ.get("LENS_API_TOKEN", ""))
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Process only first N firms (for testing)"
    )
    args = parser.parse_args()

    if not args.token:
        raise SystemExit(
            "No Lens API token found.\n"
            "Set LENS_API_TOKEN env var or pass --token YOUR_TOKEN\n"
            "Get a free token at https://www.lens.org/ (Profile > API & Bulk Data)"
        )

    # Quick auth test before processing all firms
    print(f"Token loaded (first 8 chars): {args.token[:8]}...")
    print("Testing API connection with a sample query...")
    test = get_patent_count("Apple", args.token)
    if test["api_status"] != "ok":
        detail = test.get("detail", "")
        raise SystemExit(
            f"API test failed: {test['api_status']}\n"
            f"Response: {detail}\n"
            "Check that your token is for the Patent Search API (not Scholarly).\n"
            "Get a patent API token at: https://www.lens.org/lens/user/subscriptions"
        )
    print(f"  API test OK — Apple has {test['patents_total']} patents\n")

    firms = []
    with open(IN_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            firms.append(row)

    if args.limit:
        firms = firms[: args.limit]

    print(f"Querying patents for {len(firms)} firms...")

    out_fields = ["name", "country", "industry", "grade_latest", "patents_total", "api_status"]
    results = []

    for i, firm in enumerate(firms):
        name = firm["name"]
        print(f"  [{i+1}/{len(firms)}] {name}", end=" ... ", flush=True)
        result = get_patent_count(name, args.token)

        if result["api_status"] == "rate_limited":
            print("rate limited — waiting 60s")
            time.sleep(60)
            result = get_patent_count(name, args.token)

        results.append(
            {
                "name": name,
                "country": firm["country"],
                "industry": firm["industry"],
                "grade_latest": firm["grade_latest"],
                "patents_total": result["patents_total"],
                "api_status": result["api_status"],
            }
        )
        detail = result.get("detail", "")
        print(f"{result['api_status']} | patents={result['patents_total']}")
        if detail and result["api_status"] != "ok":
            print(f"    → {detail}")

        if i < len(firms) - 1:
            time.sleep(REQUEST_DELAY_SEC)

    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(results)

    ok = sum(1 for r in results if r["api_status"] == "ok")
    print(f"\nDone. {ok}/{len(results)} successful → {OUT_FILE}")
    print("NOTE: Patent counts are at the PARENT company level.")
    print("      Scale by subsidiary assets (from Orbis) to get proprietary intensity.")


if __name__ == "__main__":
    main()
