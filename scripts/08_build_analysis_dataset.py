"""
Build the final regression-ready dataset by combining all data sources.

Merges: Yale exit panel + Orbis subsidiary financials + Bloomberg deals
        + EU sanctions timing instrument

Constructs:
  Y_i  = sale_price / pre_exit_book_value (for firms with deal data)
  α    = employee_intensity proxy (employees / total_assets)
  X_i  = controls (ln_assets, years_in_russia, revenue)
  μ_j  = NACE 2-digit sector (for fixed effects)
  Z    = sanctions_exposure (instrument based on EU package timing)

Input:
  data/collected/merged_orbis_yale.csv
  data/collected/exit_deals_matched.csv
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
DEALS_FILE = COLLECTED / "exit_deals_matched.csv"
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


def main():
    # Load merged Orbis-Yale data
    orbis_yale = {}
    with open(MERGED_ORBIS, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            orbis_yale[row["name"]] = row

    # Load Bloomberg deals (take best deal per firm — highest value completed deal)
    deals_by_firm = {}
    with open(DEALS_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            firm = row["yale_name"]
            val = safe_float(row.get("deal_value_mn_usd"))
            status = row.get("deal_status", "")

            if firm not in deals_by_firm:
                deals_by_firm[firm] = []
            deals_by_firm[firm].append(row)

    # Load full panel for grade info
    panel = {}
    with open(PANEL_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            panel[row["name"]] = row

    print(f"Orbis-Yale merged: {len(orbis_yale)} firms")
    print(f"Firms with Bloomberg deals: {len(deals_by_firm)}")
    print(f"Full panel: {len(panel)} firms")

    # Build regression dataset
    reg_rows = []
    for name, oy in orbis_yale.items():
        if not oy.get("guo_matched"):
            continue

        # Core identifiers
        grade = oy.get("grade_latest", "")
        industry = oy.get("industry", "")
        country = oy.get("country", "")
        nace_sector = oy.get("nace_sector", "")

        # α proxy: employee intensity
        emp_intensity = safe_float(oy.get("emp_intensity"))

        # Controls
        ln_assets = safe_float(oy.get("ln_assets"))
        years_russia = safe_float(oy.get("years_in_russia"))
        sum_assets = safe_float(oy.get("sum_assets_th_usd"))
        equity = safe_float(oy.get("pre_inv_equity_th_usd"))

        # Y_i: exit payoff ratio
        deal_value_mn = None
        deal_status = ""
        has_deal = 0

        if name in deals_by_firm:
            firm_deals = deals_by_firm[name]
            # Prefer completed deal with highest value
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

        # Compute Y_i = deal_value / book_value
        # Deal value is in millions, equity is in thousands
        y_i = None
        if deal_value_mn is not None and equity and equity > 0:
            y_i = (deal_value_mn * 1000) / equity  # both now in thousands

        # Instrument: sanctions exposure
        sanctions_exp = compute_sanctions_exposure(nace_sector)

        # Action type from panel
        panel_row = panel.get(name, {})
        action_type = panel_row.get("action_type", oy.get("action_type", ""))

        reg_rows.append({
            "name": name,
            "country": country,
            "industry": industry,
            "grade": grade,
            "action_type": action_type,
            "nace_sector": nace_sector,
            "alpha_emp_intensity": f"{emp_intensity:.6f}" if emp_intensity else "",
            "alpha_sq": f"{emp_intensity**2:.6f}" if emp_intensity else "",
            "y_exit_payoff": f"{y_i:.4f}" if y_i else "",
            "deal_value_mn_usd": f"{deal_value_mn:.2f}" if deal_value_mn else "",
            "deal_status": deal_status,
            "has_deal": has_deal,
            "pre_inv_equity_th_usd": f"{equity:.2f}" if equity else "",
            "sum_assets_th_usd": f"{sum_assets:.2f}" if sum_assets else "",
            "ln_assets": f"{ln_assets:.4f}" if ln_assets else "",
            "years_in_russia": int(years_russia) if years_russia else "",
            "employees_total": oy.get("employees_total", ""),
            "n_subsidiaries": oy.get("n_subsidiaries", ""),
            "sanctions_exposure": sanctions_exp,
            "guo_matched": oy.get("guo_matched", ""),
        })

    # Write regression sample
    fields = list(reg_rows[0].keys())
    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(reg_rows)

    # Compute and write summary statistics
    n_total = len(reg_rows)
    n_alpha = sum(1 for r in reg_rows if r["alpha_emp_intensity"])
    n_yi = sum(1 for r in reg_rows if r["y_exit_payoff"])
    n_controls = sum(1 for r in reg_rows if r["ln_assets"] and r["years_in_russia"])
    n_full = sum(1 for r in reg_rows if r["alpha_emp_intensity"] and r["y_exit_payoff"] and r["ln_assets"])

    alphas = [float(r["alpha_emp_intensity"]) for r in reg_rows if r["alpha_emp_intensity"]]
    yis = [float(r["y_exit_payoff"]) for r in reg_rows if r["y_exit_payoff"]]

    stats = []
    stats.append("=" * 60)
    stats.append("REGRESSION SAMPLE SUMMARY STATISTICS")
    stats.append("=" * 60)
    stats.append(f"\nSample sizes:")
    stats.append(f"  Total firms (matched Orbis-Yale): {n_total}")
    stats.append(f"  With α (employee intensity): {n_alpha}")
    stats.append(f"  With Y_i (exit payoff ratio): {n_yi}")
    stats.append(f"  With all controls: {n_controls}")
    stats.append(f"  FULL SPECIFICATION (α + Y_i + controls): {n_full}")

    if alphas:
        alphas_sorted = sorted(alphas)
        stats.append(f"\nα (employee intensity) distribution:")
        stats.append(f"  Mean: {sum(alphas)/len(alphas):.6f}")
        stats.append(f"  Median: {alphas_sorted[len(alphas)//2]:.6f}")
        stats.append(f"  P10: {alphas_sorted[len(alphas)//10]:.6f}")
        stats.append(f"  P90: {alphas_sorted[9*len(alphas)//10]:.6f}")
        stats.append(f"  Min: {min(alphas):.6f}")
        stats.append(f"  Max: {max(alphas):.6f}")

    if yis:
        yis_sorted = sorted(yis)
        stats.append(f"\nY_i (exit payoff ratio) distribution:")
        stats.append(f"  Mean: {sum(yis)/len(yis):.4f}")
        stats.append(f"  Median: {yis_sorted[len(yis)//2]:.4f}")
        stats.append(f"  Min: {min(yis):.4f}")
        stats.append(f"  Max: {max(yis):.4f}")

    # Grade distribution in sample
    grades = {}
    for r in reg_rows:
        g = r["grade"]
        grades[g] = grades.get(g, 0) + 1
    stats.append(f"\nGrade distribution:")
    for g in ["A", "B"]:
        stats.append(f"  Grade {g}: {grades.get(g, 0)}")

    # Sanctions exposure distribution
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
