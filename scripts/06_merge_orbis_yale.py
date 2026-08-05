"""
Fuzzy-match Orbis GUO names to Yale CELI tracker firm names.

Links 6,400+ Orbis Russian subsidiaries to ~1,048 Grade A/B exiters
via fuzzy string matching on parent company names.

For parents with multiple Russian subsidiaries, aggregates by summing
total assets and using the largest subsidiary's employee intensity.

Input:
  data/analysis/orbis_subsidiaries.csv
  data/analysis/firms_exiters.csv

Output:
  data/analysis/merged_orbis_yale.csv — one row per Yale exiter with
    aggregated subsidiary financials and α proxy components
"""

import csv
import math
from pathlib import Path

try:
    from rapidfuzz import fuzz, process
except ImportError:
    raise SystemExit("rapidfuzz not installed: pip install rapidfuzz")

DATA_DIR = Path(__file__).parent.parent / "data" / "analysis"

ORBIS_FILE = DATA_DIR / "orbis_subsidiaries.csv"
YALE_FILE = DATA_DIR / "firms_exiters.csv"
OUT_FILE = DATA_DIR / "merged_orbis_yale.csv"

MATCH_THRESHOLD = 70

# Manual overrides for known short/ambiguous names
MANUAL_MATCHES = {
    "IKEA": "INTER IKEA HOLDING BV",
    "BMW": "BAYERISCHE MOTOREN WERKE AKTIENGESELLSCHAFT",
    "Renault": "RENAULT SA",
    "H&M": "H & M HENNES & MAURITZ AB",
    "VW": "VOLKSWAGEN AG",
    "Volkswagen": "VOLKSWAGEN AG",
    "LG": "LG ELECTRONICS INC.",
    "BP": "BP PLC",
    "SAP": "SAP SE",
    "ABB": "ABB LTD",
    "DSM": "KONINKLIJKE DSM NV",
    "BASF": "BASF SE",
    "3M": "3M COMPANY",
    "P&G": "PROCTER & GAMBLE COMPANY",
    "Procter & Gamble": "PROCTER & GAMBLE COMPANY",
    "J&J": "JOHNSON & JOHNSON",
    "PwC": "PRICEWATERHOUSECOOPERS INTERNATIONAL LIMITED",
    "EY": "ERNST & YOUNG GLOBAL LIMITED",
    "KPMG": "KPMG INTERNATIONAL LIMITED",
    "Deloitte": "DELOITTE TOUCHE TOHMATSU LIMITED",
    "McKinsey": "MCKINSEY & COMPANY INC",
    "BCG": "THE BOSTON CONSULTING GROUP INC",
}


def normalize_name(name):
    """Normalize company name for matching."""
    name = name.upper().strip()
    # Remove common suffixes
    for suffix in [
        " PLC", " LTD", " LIMITED", " INC", " INC.", " INCORPORATED",
        " CORP", " CORP.", " CORPORATION", " CO", " CO.",
        " AG", " SE", " SA", " SPA", " GMBH", " BV", " NV",
        " OYJ", " AB", " ASA", " A/S", " KG", " LLC", " LP",
        " GROUP", " HOLDINGS", " HOLDING", " INTERNATIONAL",
        " & CO", " AND CO",
    ]:
        if name.endswith(suffix):
            name = name[: -len(suffix)].strip()
    # Remove punctuation
    name = name.replace(",", "").replace(".", "").replace("-", " ")
    # Collapse whitespace
    name = " ".join(name.split())
    return name


def main():
    # Load Yale exiters
    yale_firms = []
    with open(YALE_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            yale_firms.append(row)

    yale_names = [r["name"] for r in yale_firms]
    yale_normalized = {normalize_name(n): n for n in yale_names}

    # Load Orbis subsidiaries
    orbis_rows = []
    with open(ORBIS_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            orbis_rows.append(row)

    # Get unique GUO names
    guo_names = set()
    for r in orbis_rows:
        if r["guo_name"]:
            guo_names.add(r["guo_name"])

    print(f"Yale exiters: {len(yale_firms)}")
    print(f"Orbis subsidiaries: {len(orbis_rows)}")
    print(f"Unique GUO names: {len(guo_names)}")

    # Build lookup structures
    guo_normalized = {normalize_name(g): g for g in guo_names}
    guo_norm_list = list(guo_normalized.keys())
    guo_upper_map = {g.upper(): g for g in guo_names}

    matches = {}
    match_scores = {}
    no_match = []

    for yale_name in yale_names:
        # Check manual overrides first
        if yale_name in MANUAL_MATCHES:
            override = MANUAL_MATCHES[yale_name]
            if override.upper() in guo_upper_map:
                matches[yale_name] = guo_upper_map[override.upper()]
                match_scores[yale_name] = 100
                continue

        yn = normalize_name(yale_name)

        # Exact normalized match
        if yn in guo_normalized:
            matches[yale_name] = guo_normalized[yn]
            match_scores[yale_name] = 100
            continue

        # Combined fuzzy: take best of token_set_ratio and partial_ratio
        result_set = process.extractOne(
            yn, guo_norm_list, scorer=fuzz.token_set_ratio
        )
        result_partial = process.extractOne(
            yn, guo_norm_list, scorer=fuzz.partial_ratio
        )

        best = None
        best_score = 0

        if result_set and result_set[1] > best_score:
            best = result_set
            best_score = result_set[1]
        if result_partial and result_partial[1] > best_score:
            best = result_partial
            best_score = result_partial[1]

        # For short names (≤5 chars), require higher threshold
        threshold = MATCH_THRESHOLD
        if len(yn) <= 5:
            threshold = 90

        if best and best_score >= threshold:
            matches[yale_name] = guo_normalized[best[0]]
            match_scores[yale_name] = best_score
        else:
            no_match.append(yale_name)

    print(f"\nMatched: {len(matches)}/{len(yale_firms)} ({100*len(matches)/len(yale_firms):.0f}%)")
    print(f"Unmatched: {len(no_match)}")

    # Aggregate subsidiaries per matched GUO
    guo_to_subs = {}
    for r in orbis_rows:
        gn = r["guo_name"]
        if gn not in guo_to_subs:
            guo_to_subs[gn] = []
        guo_to_subs[gn].append(r)

    # Build output: one row per Yale exiter
    output_rows = []
    for yale_row in yale_firms:
        yale_name = yale_row["name"]
        guo_match = matches.get(yale_name)

        if not guo_match or guo_match not in guo_to_subs:
            output_rows.append({
                "name": yale_name,
                "country": yale_row["country"],
                "industry": yale_row["industry"],
                "grade_latest": yale_row["grade_latest"],
                "action_type": yale_row["action_type"],
                "guo_matched": "",
                "match_quality": "",
                "n_subsidiaries": 0,
                "sum_assets_th_usd": "",
                "largest_sub_assets": "",
                "pre_inv_equity_th_usd": "",
                "employees_total": "",
                "emp_intensity": "",
                "years_in_russia": "",
                "ln_assets": "",
                "nace_sector": "",
            })
            continue

        subs = guo_to_subs[guo_match]

        # Sum total assets across subsidiaries
        assets_list = []
        for s in subs:
            a = s.get("pre_inv_assets_th_usd")
            if a:
                try:
                    assets_list.append(float(a))
                except ValueError:
                    pass

        sum_assets = sum(assets_list) if assets_list else None

        # Use largest subsidiary for key metrics
        largest = max(subs, key=lambda s: float(s.get("pre_inv_assets_th_usd") or 0))

        equity = largest.get("pre_inv_equity_th_usd")
        emp_intensity = largest.get("emp_intensity")
        years_russia = largest.get("years_in_russia")
        nace = largest.get("nace_sector")

        # Total employees across all subs
        total_emp = 0
        for s in subs:
            e = s.get("employees")
            if e:
                try:
                    total_emp += float(e)
                except ValueError:
                    pass

        ln_a = None
        if sum_assets and sum_assets > 0:
            ln_a = math.log(sum_assets)

        # Match quality
        mq = match_scores.get(yale_name, 0)

        output_rows.append({
            "name": yale_name,
            "country": yale_row["country"],
            "industry": yale_row["industry"],
            "grade_latest": yale_row["grade_latest"],
            "action_type": yale_row["action_type"],
            "guo_matched": guo_match,
            "match_quality": mq,
            "n_subsidiaries": len(subs),
            "sum_assets_th_usd": f"{sum_assets:.2f}" if sum_assets else "",
            "largest_sub_assets": f"{max(assets_list):.2f}" if assets_list else "",
            "pre_inv_equity_th_usd": equity if equity else "",
            "employees_total": int(total_emp) if total_emp > 0 else "",
            "emp_intensity": emp_intensity if emp_intensity else "",
            "years_in_russia": years_russia if years_russia else "",
            "ln_assets": f"{ln_a:.4f}" if ln_a else "",
            "nace_sector": nace if nace else "",
        })

    # Write output
    fields = list(output_rows[0].keys())
    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)

    matched_with_data = sum(1 for r in output_rows if r["sum_assets_th_usd"])
    print(f"\nOutput: {len(output_rows)} rows → {OUT_FILE}")
    print(f"  Matched with financial data: {matched_with_data}")
    print(f"  With employee intensity: {sum(1 for r in output_rows if r['emp_intensity'])}")

    # Show some unmatched for debugging
    if no_match:
        print(f"\nSample unmatched firms (first 15):")
        for n in no_match[:15]:
            print(f"  {n}")


if __name__ == "__main__":
    main()
