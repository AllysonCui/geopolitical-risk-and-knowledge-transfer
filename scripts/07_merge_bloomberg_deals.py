"""
Match Bloomberg M&A deal sellers to Yale CELI tracker firms.

Filters post-invasion deals, fuzzy-matches seller names to the Yale
firm list, and extracts sale prices for Y_i construction.

Input:
  data/bloomberg_ma_deals.csv
  data/collected/firms_exiters.csv

Output:
  data/collected/exit_deals_matched.csv — one row per matched deal
"""

import csv
import re
from pathlib import Path

try:
    from rapidfuzz import fuzz, process
except ImportError:
    raise SystemExit("rapidfuzz not installed: pip install rapidfuzz")

DATA_DIR = Path(__file__).parent.parent / "data"
BLOOMBERG_FILE = DATA_DIR / "bloomberg_ma_deals.csv"
YALE_FILE = DATA_DIR / "collected" / "firms_exiters.csv"
OUT_FILE = DATA_DIR / "collected" / "exit_deals_matched.csv"

INVASION_DATE = "2022/02/24"
MATCH_THRESHOLD = 72


def normalize_seller(name):
    """Normalize seller name for matching."""
    name = name.upper().strip()
    for suffix in [
        " PLC", " LTD", " LIMITED", " INC", " INC.", " INCORPORATED",
        " CORP", " CORP.", " CORPORATION", " CO", " CO.",
        " AG", " SE", " SA", " SPA", " GMBH", " BV", " NV",
        " OYJ", " AB", " ASA", " A/S", " LLC", " LP",
        "/THE", " THE",
    ]:
        if name.endswith(suffix):
            name = name[: -len(suffix)].strip()
    name = name.replace(",", "").replace(".", "").replace("-", " ")
    return " ".join(name.split())


def main():
    # Load Yale exiters
    yale_firms = []
    with open(YALE_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            yale_firms.append(row)

    yale_names = [r["name"] for r in yale_firms]
    yale_norm_map = {normalize_seller(n): n for n in yale_names}
    yale_norm_list = list(yale_norm_map.keys())

    # Load Bloomberg deals
    deals = []
    with open(BLOOMBERG_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            deals.append(row)

    print(f"Total Bloomberg deals: {len(deals)}")

    # Filter post-invasion
    post_invasion = [d for d in deals if d.get("Announce Date", "") >= INVASION_DATE]
    print(f"Post-invasion deals (≥{INVASION_DATE}): {len(post_invasion)}")

    # Filter M&A only (exclude pure INV)
    ma_deals = [d for d in post_invasion if d.get("Deal Type", "").strip() == "M&A"]
    print(f"M&A deals only: {len(ma_deals)}")

    # Match sellers to Yale firms
    matched_deals = []
    unmatched_sellers = set()

    for deal in post_invasion:
        sellers_raw = deal.get("Seller Name", "")
        if not sellers_raw.strip():
            continue

        # A deal can have multiple sellers separated by comma
        sellers = [s.strip() for s in sellers_raw.split(",")]

        best_match = None
        best_score = 0
        best_seller = ""

        for seller in sellers:
            sn = normalize_seller(seller)
            if not sn:
                continue

            # Exact match
            if sn in yale_norm_map:
                best_match = yale_norm_map[sn]
                best_score = 100
                best_seller = seller
                break

            # Fuzzy match
            result_set = process.extractOne(
                sn, yale_norm_list, scorer=fuzz.token_set_ratio
            )
            result_partial = process.extractOne(
                sn, yale_norm_list, scorer=fuzz.partial_ratio
            )

            for result in [result_set, result_partial]:
                if result and result[1] > best_score:
                    best_score = result[1]
                    best_match = yale_norm_map[result[0]]
                    best_seller = seller

        threshold = 90 if len(normalize_seller(best_seller)) <= 5 else MATCH_THRESHOLD

        if best_match and best_score >= threshold:
            # Parse deal value
            val_str = deal.get("Announced Total Value (mil.)", "").strip()
            deal_value = None
            if val_str and val_str != "N/A":
                try:
                    deal_value = float(val_str)
                except ValueError:
                    pass

            matched_deals.append({
                "yale_name": best_match,
                "seller_name_bloomberg": best_seller,
                "match_score": best_score,
                "target_name": deal.get("Target Name", "").strip(),
                "acquirer_name": deal.get("Acquirer Name", "").strip(),
                "announce_date": deal.get("Announce Date", "").strip(),
                "deal_value_mn_usd": deal_value if deal_value else "",
                "deal_type": deal.get("Deal Type", "").strip(),
                "deal_status": deal.get("Deal Status", "").strip(),
                "payment_type": deal.get("Payment Type", "").strip(),
                "tv_ebitda": deal.get("TV/EBITDA", "").strip(),
            })
        else:
            for s in sellers:
                unmatched_sellers.add(s.strip())

    print(f"\nMatched deals: {len(matched_deals)}")
    unique_firms = set(d["yale_name"] for d in matched_deals)
    print(f"Unique Yale firms with deals: {len(unique_firms)}")

    with_value = [d for d in matched_deals if d["deal_value_mn_usd"]]
    print(f"Deals with disclosed value: {len(with_value)}")

    # Status distribution
    statuses = {}
    for d in matched_deals:
        s = d["deal_status"]
        statuses[s] = statuses.get(s, 0) + 1
    print(f"Deal status distribution: {statuses}")

    # Write output
    fields = list(matched_deals[0].keys()) if matched_deals else []
    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(matched_deals)

    print(f"\nOutput: {len(matched_deals)} deals → {OUT_FILE}")

    if unmatched_sellers:
        print(f"\nUnmatched sellers (sample of 15):")
        for s in sorted(unmatched_sellers)[:15]:
            print(f"  {s}")


if __name__ == "__main__":
    main()
