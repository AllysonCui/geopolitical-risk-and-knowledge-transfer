"""
Build the final regression-ready dataset by combining all data sources.

Merges: Yale exit panel + Orbis subsidiary financials + Bloomberg deals
        + Lens.org patent counts + EU sanctions timing instrument

Constructs:
  Y_i  = sale_price / pre_exit_book_value (for firms with deal data)
  α    = composite replicability index:
         component 1: employee intensity (employees / total_assets) — high = operational
         component 2: proprietary intensity (patents / total_assets) — high = embedded IP
         α = percentile_rank(emp_intensity) - percentile_rank(patent_intensity)
         High α → easy to replicate (labor-heavy, low IP)
         Low α → hard to replicate (asset-heavy, high IP)
  X_i  = controls (ln_assets, years_in_russia, revenue)
  μ_j  = NACE 2-digit sector (for fixed effects)
  Z    = sanctions_exposure (instrument based on EU package timing)

Input:
  data/collected/merged_orbis_yale.csv
  data/collected/exit_deals_matched.csv
  data/collected/patents_by_firm.csv
  data/collected/eu_sanctions_2022.csv
  data/collected/firms_exit_panel.csv

Output:
  data/analysis/regression_sample.csv — final regression dataset
  data/analysis/sample_stats.txt — summary statistics
"""

import csv
import math
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
COLLECTED = DATA_DIR / "collected"
ANALYSIS_DIR = DATA_DIR / "analysis"
ANALYSIS_DIR.mkdir(exist_ok=True)

MERGED_ORBIS = COLLECTED / "merged_orbis_yale.csv"
ORBIS_SUBS = COLLECTED / "orbis_subsidiaries.csv"
DEALS_FILE = COLLECTED / "exit_deals_matched.csv"
PATENTS_FILE = COLLECTED / "patents_by_firm.csv"
SANCTIONS_FILE = COLLECTED / "eu_sanctions_2022.csv"
PANEL_FILE = COLLECTED / "firms_exit_panel.csv"

OUT_FILE = ANALYSIS_DIR / "regression_sample.csv"
STATS_FILE = ANALYSIS_DIR / "sample_stats.txt"

# Sanctions package dates for instrument construction
SANCTIONS_DATES = [
    ("2022-02-25", 1), ("2022-03-02", 2), ("2022-03-15", 3),
    ("2022-04-08", 4), ("2022-06-03", 5), ("2022-07-21", 6),
    ("2022-10-06", 7), ("2022-12-16", 8), ("2022-02-25", 9),
]

# Sectors targeted by each package (NACE 2-digit prefixes)
SANCTIONS_SECTOR_MAP = {
    "06": [1, 2, 3, 4, 5, 6, 7, 8],  # Oil/gas extraction
    "19": [1, 2, 3, 5, 6, 8],         # Refined petroleum
    "24": [4, 5, 6, 7, 8],            # Basic metals / steel
    "64": [1, 2, 3, 4, 5, 6, 7, 8],  # Financial services
    "65": [1, 2, 3, 4, 5, 6, 7, 8],  # Insurance
    "20": [5, 6, 7, 8],              # Chemicals
    "26": [4, 5, 6, 7, 8],           # Electronics
    "30": [5, 6, 7, 8],              # Transport equipment
    "61": [3, 4, 5, 6, 7, 8],        # Telecom
    "62": [5, 6, 7, 8],              # IT/software
    "35": [6, 7, 8],                 # Energy supply
    "49": [7, 8],                    # Land transport
    "50": [7, 8],                    # Water transport
}


def safe_float(val):
    if not val or val == "n.a." or val.strip() == "":
        return None
    try:
        return float(val.replace(",", ""))
    except (ValueError, AttributeError):
        return None


def compute_sanctions_exposure(nace_sector):
    """Count how many sanctions packages hit this sector (instrument Z)."""
    packages = SANCTIONS_SECTOR_MAP.get(nace_sector, [])
    return len(packages)


def percentile_rank_list(values):
    """Return percentile ranks (0-1) for a list, handling ties."""
    n = len(values)
    if n == 0:
        return []
    sorted_vals = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * n
    for rank, (orig_idx, _) in enumerate(sorted_vals):
        ranks[orig_idx] = rank / (n - 1) if n > 1 else 0.5
    return ranks


def main():
    # Load merged Orbis-Yale data
    orbis_yale = {}
    with open(MERGED_ORBIS, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            orbis_yale[row["name"]] = row

    # Load patent data
    patents = {}
    with open(PATENTS_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["api_status"] == "ok":
                patents[row["name"]] = int(row["patents_total"])

    # Load Bloomberg deals
    deals_by_firm = {}
    with open(DEALS_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            firm = row["yale_name"]
            if firm not in deals_by_firm:
                deals_by_firm[firm] = []
            deals_by_firm[firm].append(row)

    # Load full panel for grade info
    panel = {}
    with open(PANEL_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            panel[row["name"]] = row

    # Load subsidiary-level data for inactivation rate
    from collections import defaultdict
    guo_total_subs = defaultdict(int)
    guo_inactive_subs = defaultdict(int)
    with open(ORBIS_SUBS, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            guo = row["guo_name"]
            guo_total_subs[guo] += 1
            if row.get("inactive") == "Yes":
                guo_inactive_subs[guo] += 1

    print(f"Orbis-Yale merged: {len(orbis_yale)} firms")
    print(f"Patent data: {len(patents)} firms")
    print(f"Firms with Bloomberg deals: {len(deals_by_firm)}")
    print(f"Full panel: {len(panel)} firms")
    print(f"Orbis subsidiaries (for inactivation): {sum(guo_total_subs.values())} subs across {len(guo_total_subs)} GUOs")

    # First pass: collect raw values for all matched firms
    raw_rows = []
    for name, oy in orbis_yale.items():
        if not oy.get("guo_matched"):
            continue

        grade = oy.get("grade_latest", "")
        industry = oy.get("industry", "")
        country = oy.get("country", "")
        nace_sector = oy.get("nace_sector", "")

        emp_intensity = safe_float(oy.get("emp_intensity"))
        ln_assets = safe_float(oy.get("ln_assets"))
        years_russia = safe_float(oy.get("years_in_russia"))
        sum_assets = safe_float(oy.get("sum_assets_th_usd"))
        equity = safe_float(oy.get("pre_inv_equity_th_usd"))

        # Patent intensity = patents / total_assets (in thousands)
        patent_count = patents.get(name, None)
        patent_intensity = None
        if patent_count is not None and sum_assets and sum_assets > 0:
            patent_intensity = patent_count / sum_assets

        # Y_i: exit payoff ratio
        deal_value_mn = None
        deal_status = ""
        has_deal = 0

        if name in deals_by_firm:
            firm_deals = deals_by_firm[name]
            completed = [d for d in firm_deals if d.get("deal_status") == "Completed"]
            candidates = completed if completed else firm_deals

            best_deal = None
            best_val = -1
            for d in candidates:
                v = safe_float(d.get("deal_value_mn_usd"))
                if v is not None and v > best_val:
                    best_val = v
                    best_deal = d
                elif best_deal is None:
                    best_deal = d

            if best_deal:
                deal_value_mn = safe_float(best_deal.get("deal_value_mn_usd"))
                deal_status = best_deal.get("deal_status", "")
                has_deal = 1

        y_i = None
        if deal_value_mn is not None and equity and equity > 0:
            y_i = (deal_value_mn * 1000) / equity

        sanctions_exp = compute_sanctions_exposure(nace_sector)

        panel_row = panel.get(name, {})
        action_type = panel_row.get("action_type", oy.get("action_type", ""))

        # New Y variables
        guo_name = oy.get("guo_matched", "")
        total_s = guo_total_subs.get(guo_name, 0)
        inactive_s = guo_inactive_subs.get(guo_name, 0)
        y_sub_inactive = 1 if inactive_s > 0 else 0
        sub_inactivation_rate = inactive_s / total_s if total_s > 0 else None
        y_grade_a_sold = 1 if grade == "A" and action_type == "sold" else 0
        y_suspended = 1 if action_type == "suspended" else 0

        raw_rows.append({
            "name": name,
            "country": country,
            "industry": industry,
            "grade": grade,
            "action_type": action_type,
            "nace_sector": nace_sector,
            "emp_intensity_raw": emp_intensity,
            "patent_count": patent_count,
            "patent_intensity_raw": patent_intensity,
            "y_exit_payoff": y_i,
            "deal_value_mn_usd": deal_value_mn,
            "deal_status": deal_status,
            "has_deal": has_deal,
            "pre_inv_equity_th_usd": equity,
            "sum_assets_th_usd": sum_assets,
            "ln_assets": ln_assets,
            "years_in_russia": years_russia,
            "employees_total": oy.get("employees_total", ""),
            "n_subsidiaries": oy.get("n_subsidiaries", ""),
            "sanctions_exposure": sanctions_exp,
            "guo_matched": oy.get("guo_matched", ""),
            "y_sub_inactive": y_sub_inactive,
            "sub_inactivation_rate": sub_inactivation_rate,
            "y_grade_a_sold": y_grade_a_sold,
            "y_suspended": y_suspended,
        })

    # Second pass: compute composite α using percentile ranks
    # Firms with both components get the composite; others get single-component
    both_idx = [i for i, r in enumerate(raw_rows)
                if r["emp_intensity_raw"] is not None and r["patent_intensity_raw"] is not None]
    emp_only_idx = [i for i, r in enumerate(raw_rows)
                    if r["emp_intensity_raw"] is not None and r["patent_intensity_raw"] is None]

    # Percentile rank employee intensity (higher = more operational/replaceable)
    if both_idx:
        emp_vals = [raw_rows[i]["emp_intensity_raw"] for i in both_idx]
        emp_pctiles = percentile_rank_list(emp_vals)

        pat_vals = [raw_rows[i]["patent_intensity_raw"] for i in both_idx]
        pat_pctiles = percentile_rank_list(pat_vals)

        # Composite: α = emp_pctile - patent_pctile, rescaled to [0,1]
        # High α = high employee intensity, low patent intensity → operational arm
        # Low α = low employee intensity, high patent intensity → knowledge repository
        composites = [e - p for e, p in zip(emp_pctiles, pat_pctiles)]
        comp_min = min(composites)
        comp_max = max(composites)
        comp_range = comp_max - comp_min if comp_max > comp_min else 1

        for j, i in enumerate(both_idx):
            raw_rows[i]["alpha_composite"] = (composites[j] - comp_min) / comp_range
            raw_rows[i]["alpha_emp_pctile"] = emp_pctiles[j]
            raw_rows[i]["alpha_pat_pctile"] = pat_pctiles[j]

    # For firms with only employee intensity, use emp percentile as α
    if emp_only_idx:
        emp_vals = [raw_rows[i]["emp_intensity_raw"] for i in emp_only_idx]
        emp_pctiles = percentile_rank_list(emp_vals)
        for j, i in enumerate(emp_only_idx):
            raw_rows[i]["alpha_composite"] = emp_pctiles[j]
            raw_rows[i]["alpha_emp_pctile"] = emp_pctiles[j]
            raw_rows[i]["alpha_pat_pctile"] = None

    # Build final output rows
    reg_rows = []
    for r in raw_rows:
        alpha = r.get("alpha_composite")
        reg_rows.append({
            "name": r["name"],
            "country": r["country"],
            "industry": r["industry"],
            "grade": r["grade"],
            "action_type": r["action_type"],
            "nace_sector": r["nace_sector"],
            "alpha": f"{alpha:.6f}" if alpha is not None else "",
            "alpha_sq": f"{alpha**2:.6f}" if alpha is not None else "",
            "alpha_emp_pctile": f"{r.get('alpha_emp_pctile', ''):.6f}" if r.get("alpha_emp_pctile") is not None else "",
            "alpha_pat_pctile": f"{r.get('alpha_pat_pctile', ''):.6f}" if r.get("alpha_pat_pctile") is not None else "",
            "emp_intensity_raw": f"{r['emp_intensity_raw']:.6f}" if r["emp_intensity_raw"] is not None else "",
            "patent_count": r["patent_count"] if r["patent_count"] is not None else "",
            "patent_intensity_raw": f"{r['patent_intensity_raw']:.6f}" if r["patent_intensity_raw"] is not None else "",
            "y_exit_payoff": f"{r['y_exit_payoff']:.4f}" if r["y_exit_payoff"] else "",
            "deal_value_mn_usd": f"{r['deal_value_mn_usd']:.2f}" if r["deal_value_mn_usd"] else "",
            "deal_status": r["deal_status"],
            "has_deal": r["has_deal"],
            "pre_inv_equity_th_usd": f"{r['pre_inv_equity_th_usd']:.2f}" if r["pre_inv_equity_th_usd"] else "",
            "sum_assets_th_usd": f"{r['sum_assets_th_usd']:.2f}" if r["sum_assets_th_usd"] else "",
            "ln_assets": f"{r['ln_assets']:.4f}" if r["ln_assets"] else "",
            "years_in_russia": int(r["years_in_russia"]) if r["years_in_russia"] else "",
            "employees_total": r["employees_total"],
            "n_subsidiaries": r["n_subsidiaries"],
            "sanctions_exposure": r["sanctions_exposure"],
            "guo_matched": r["guo_matched"],
            "y_sub_inactive": r["y_sub_inactive"],
            "sub_inactivation_rate": f"{r['sub_inactivation_rate']:.4f}" if r["sub_inactivation_rate"] is not None else "",
            "y_grade_a_sold": r["y_grade_a_sold"],
            "y_suspended": r["y_suspended"],
        })

    # Write regression sample
    fields = list(reg_rows[0].keys())
    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(reg_rows)

    # Summary statistics
    n_total = len(reg_rows)
    n_alpha = sum(1 for r in reg_rows if r["alpha"])
    n_alpha_both = len(both_idx)
    n_yi = sum(1 for r in reg_rows if r["y_exit_payoff"])
    n_controls = sum(1 for r in reg_rows if r["ln_assets"] and r["years_in_russia"])
    n_full = sum(1 for r in reg_rows if r["alpha"] and r["y_exit_payoff"] and r["ln_assets"])

    alphas = [float(r["alpha"]) for r in reg_rows if r["alpha"]]
    yis = [float(r["y_exit_payoff"]) for r in reg_rows if r["y_exit_payoff"]]

    stats = []
    stats.append("=" * 60)
    stats.append("REGRESSION SAMPLE SUMMARY STATISTICS")
    stats.append("=" * 60)
    stats.append(f"\nSample sizes:")
    stats.append(f"  Total firms (matched Orbis-Yale): {n_total}")
    stats.append(f"  With α (composite): {n_alpha}")
    stats.append(f"    - Both components (emp + patent): {n_alpha_both}")
    stats.append(f"    - Employee intensity only: {n_alpha - n_alpha_both}")
    stats.append(f"  With Y_i (exit payoff ratio): {n_yi}")
    stats.append(f"  With all controls: {n_controls}")
    stats.append(f"  FULL SPECIFICATION (α + Y_i + controls): {n_full}")

    if alphas:
        alphas_sorted = sorted(alphas)
        stats.append(f"\nα (composite replicability index) distribution:")
        stats.append(f"  Mean: {sum(alphas)/len(alphas):.4f}")
        stats.append(f"  Median: {alphas_sorted[len(alphas)//2]:.4f}")
        stats.append(f"  Std Dev: {(sum((a - sum(alphas)/len(alphas))**2 for a in alphas) / len(alphas))**0.5:.4f}")
        stats.append(f"  P10: {alphas_sorted[len(alphas)//10]:.4f}")
        stats.append(f"  P90: {alphas_sorted[9*len(alphas)//10]:.4f}")
        stats.append(f"  Min: {min(alphas):.4f}")
        stats.append(f"  Max: {max(alphas):.4f}")

    if yis:
        yis_sorted = sorted(yis)
        stats.append(f"\nY_i (exit payoff ratio) distribution:")
        stats.append(f"  Mean: {sum(yis)/len(yis):.4f}")
        stats.append(f"  Median: {yis_sorted[len(yis)//2]:.4f}")
        stats.append(f"  Min: {min(yis):.4f}")
        stats.append(f"  Max: {max(yis):.4f}")

    grades = {}
    for r in reg_rows:
        g = r["grade"]
        grades[g] = grades.get(g, 0) + 1
    stats.append(f"\nGrade distribution:")
    for g in ["A", "B"]:
        stats.append(f"  Grade {g}: {grades.get(g, 0)}")

    stats.append(f"\nNew Y variables:")
    stats.append(f"  Y = any subsidiary inactive: {sum(1 for r in reg_rows if r['y_sub_inactive'] == 1)}")
    stats.append(f"  Y = Grade A + Sold: {sum(1 for r in reg_rows if r['y_grade_a_sold'] == 1)}")
    stats.append(f"  Y = Suspended: {sum(1 for r in reg_rows if r['y_suspended'] == 1)}")

    sanc = [r["sanctions_exposure"] for r in reg_rows]
    stats.append(f"\nSanctions exposure (instrument Z):")
    stats.append(f"  0 packages: {sum(1 for s in sanc if s == 0)}")
    stats.append(f"  1-4 packages: {sum(1 for s in sanc if 1 <= s <= 4)}")
    stats.append(f"  5-8 packages: {sum(1 for s in sanc if 5 <= s <= 8)}")

    stats_text = "\n".join(stats)
    print(stats_text)

    with open(STATS_FILE, "w") as f:
        f.write(stats_text)

    print(f"\n\nOutput files:")
    print(f"  Regression data: {OUT_FILE}")
    print(f"  Summary stats: {STATS_FILE}")


if __name__ == "__main__":
    main()
