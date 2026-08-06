"""
Build the final regression-ready dataset by combining all data sources.

Merges: Yale exit panel (ALL grades A–F) + Orbis subsidiary financials
        + Bloomberg deals + Lens.org patent counts + EU sanctions packages
        + home-country institutions (coalition / rule of law / legal origin)

The sample is now the full matched population of foreign parents with
Russian subsidiaries — not just Grade A/B exiters — so that
10_selection_exit_mode.py can estimate the exit decision (selection) and
the exit mode (sell vs. walk away) as separate stages.

Constructs:
  Knowledge structure (theory: codified knowledge is alienable and
  transfers with the legal entity; tacit knowledge embodied in employees
  is inalienable — see docs/formal_model.md):
    pat_pctile         parent patent stock, percentile rank (global)
    pat_pctile_sector  same, ranked within Yale industry sector
    lab_pctile         subsidiary employee intensity, percentile rank
    lab_pctile_sector  same, within sector
    alpha, alpha_sq    legacy composite (kept for the legacy script 09)

  Outcomes:
    exiter        1 if Yale Grade A or B
    clean_exit    1 if Grade A
    exit_mode     sold / seized / walked (Grade A firms; seized is a
                  separate competing risk, per the fire-sale model)
    event_date    Bloomberg deal announce date if a completed deal exists,
                  else first snapshot date at Grade A (coarse)

  Instruments / moderators:
    b2c                  consumer-facing NACE division (exclusion-restriction
                         component: boycott pressure shifts WHETHER to exit,
                         not the mechanics of the asset transfer)
    sanctions_coalition  home state on Russia's "unfriendly countries" list
    wgi_rule_of_law      WGI Rule of Law 2021
    legal_origin         LLSV legal-origin family
    sanctions_exposure   count of 2022 EU packages hitting the NACE sector
    sanction_hit_dates   semicolon list of package adoption dates for the
                         firm's sector (feeds the time-varying hazard in 11)

Input:
  data/analysis/merged_orbis_yale.csv
  data/analysis/exit_deals_matched.csv
  data/raw/lens/patents_by_firm.csv
  data/raw/eu_sanctions/eu_sanctions_2022.csv
  data/raw/institutions/home_country_institutions.csv
  data/analysis/firms_exit_panel.csv

Output:
  data/analysis/regression_sample.csv — final regression dataset
  data/analysis/sample_stats.txt — summary statistics
"""

import csv
import math
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
ANALYSIS_DIR = DATA_DIR / "analysis"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

MERGED_ORBIS = ANALYSIS_DIR / "merged_orbis_yale.csv"
ORBIS_SUBS = ANALYSIS_DIR / "orbis_subsidiaries.csv"
DEALS_FILE = ANALYSIS_DIR / "exit_deals_matched.csv"
PATENTS_FILE = RAW_DIR / "lens" / "patents_by_firm.csv"
SANCTIONS_FILE = RAW_DIR / "eu_sanctions" / "eu_sanctions_2022.csv"
INSTITUTIONS_FILE = RAW_DIR / "institutions" / "home_country_institutions.csv"
PANEL_FILE = ANALYSIS_DIR / "firms_exit_panel.csv"

OUT_FILE = ANALYSIS_DIR / "regression_sample.csv"
STATS_FILE = ANALYSIS_DIR / "sample_stats.txt"

# Sectors targeted by each package (NACE 2-digit prefixes). Package adoption
# dates come from eu_sanctions_2022.csv, not a hard-coded table.
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

# Consumer-facing NACE divisions (B2C): retail and vehicle sale,
# accommodation and food service, gambling, sports/amusement, personal
# services. Wholesale (46) is deliberately excluded — it is B2B.
B2C_NACE_DIVISIONS = {"45", "47", "55", "56", "92", "93", "96"}


def safe_float(val):
    if not val or val == "n.a." or val.strip() == "":
        return None
    try:
        return float(val.replace(",", ""))
    except (ValueError, AttributeError):
        return None


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


def parse_date(val):
    """'2022/8/12' or '2022-08-12' → 'YYYY-MM-DD' or None."""
    if not val:
        return None
    val = val.strip().replace("/", "-")
    parts = val.split("-")
    if len(parts) != 3:
        return None
    try:
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        return f"{y:04d}-{m:02d}-{d:02d}"
    except ValueError:
        return None


def months_since_invasion(iso_date):
    """Months elapsed from 2022-02 to iso_date (YYYY-MM-DD)."""
    if not iso_date:
        return None
    y, m = int(iso_date[:4]), int(iso_date[5:7])
    return (y - 2022) * 12 + (m - 2)


def main():
    # Load merged Orbis-Yale data (full panel, all grades)
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

    # Load EU sanctions package adoption dates (source of truth for timing)
    package_dates = {}
    with open(SANCTIONS_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                package_dates[int(row["package"])] = parse_date(row["date_adopted"])
            except (ValueError, KeyError):
                continue

    # Load home-country institutions
    institutions = {}
    with open(INSTITUTIONS_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            institutions[row["country"]] = row

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
    print(f"Sanctions packages with dates: {sorted(package_dates)}")
    print(f"Institution rows: {len(institutions)} countries")

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

        # Y_i: exit payoff ratio + deal timing
        deal_value_mn = None
        deal_status = ""
        deal_announce_date = None
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
                deal_announce_date = parse_date(best_deal.get("announce_date"))
                has_deal = 1

        y_i = None
        if deal_value_mn is not None and equity and equity > 0:
            y_i = (deal_value_mn * 1000) / equity

        # Sanctions exposure: which packages hit this sector, and when
        pkgs = SANCTIONS_SECTOR_MAP.get(nace_sector, [])
        sanctions_exp = len(pkgs)
        hit_dates = sorted(d for d in (package_dates.get(p) for p in pkgs) if d)
        sanction_hit_dates = ";".join(hit_dates)

        panel_row = panel.get(name, {})
        action_type = panel_row.get("action_type", oy.get("action_type", ""))

        # Exit outcomes
        exiter = 1 if grade in ("A", "B") else 0
        clean_exit = 1 if grade == "A" else 0

        # Exit mode is defined for completed exits (Grade A). Seizure is a
        # third competing risk, not a chosen mode.
        exit_mode = ""
        if grade == "A":
            if action_type == "seized":
                exit_mode = "seized"
            elif action_type == "sold" or (has_deal and deal_status == "Completed"
                                           and deal_announce_date
                                           and deal_announce_date >= "2022-02-24"):
                exit_mode = "sold"
            else:
                exit_mode = "walked"
        elif action_type == "seized":
            exit_mode = "seized"

        # Event timing for the hazard model: prefer the Bloomberg deal
        # announce date for completed post-invasion sales; otherwise the
        # first snapshot at Grade A (coarse, and left-censored for firms
        # already at A in Dec 2022).
        first_a = oy.get("first_grade_a_date", "") or panel_row.get("first_grade_a_date", "")
        event_date = ""
        if exit_mode == "sold" and deal_announce_date and deal_announce_date >= "2022-02-24":
            event_date = deal_announce_date
        elif grade == "A" and first_a:
            event_date = first_a
        event_month = months_since_invasion(event_date) if event_date else None

        # B2C flag from NACE division of the largest subsidiary
        b2c = 1 if nace_sector in B2C_NACE_DIVISIONS else 0

        # Home-country institutions (WGI vintage: 2022 estimates — the 2021
        # release was unreachable through this environment's network policy;
        # see data/raw/institutions/README.md)
        inst = institutions.get(country, {})
        coalition = inst.get("sanctions_coalition", "")
        wgi = inst.get("wgi_rule_of_law_2022", "")
        legal_origin = inst.get("legal_origin", "")

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
            "exiter": exiter,
            "clean_exit": clean_exit,
            "exit_mode": exit_mode,
            "event_date": event_date,
            "event_month": event_month,
            "timing_left_censored": oy.get("timing_left_censored", ""),
            "nace_sector": nace_sector,
            "b2c": b2c,
            "sanctions_coalition": coalition,
            "wgi_rule_of_law": wgi,
            "legal_origin": legal_origin,
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
            "sanction_hit_dates": sanction_hit_dates,
            "guo_matched": guo_name,
            "y_sub_inactive": y_sub_inactive,
            "sub_inactivation_rate": sub_inactivation_rate,
            "y_grade_a_sold": y_grade_a_sold,
            "y_suspended": y_suspended,
        })

    # ── Knowledge-structure percentiles ──────────────────────────────────
    # Separate patent and labor percentiles (global and within Yale industry
    # sector). The theory treats codifiability — not a symmetric two-factor
    # index — as the driver, so the components enter regressions separately;
    # the legacy composite alpha is kept only for script 09.

    def assign_pctiles(idx_list, key, out_key):
        vals = [raw_rows[i][key] for i in idx_list]
        pcts = percentile_rank_list(vals)
        for j, i in enumerate(idx_list):
            raw_rows[i][out_key] = pcts[j]

    pat_idx = [i for i, r in enumerate(raw_rows) if r["patent_count"] is not None]
    lab_idx = [i for i, r in enumerate(raw_rows) if r["emp_intensity_raw"] is not None]
    # Global percentiles of the raw parent patent stock. NOTE: absent parent
    # assets/employees in the current Orbis export, the patent stock is not
    # scaled by parent size — ln_assets and sector ranks below are the
    # partial fix; see README "Not yet implemented".
    assign_pctiles(pat_idx, "patent_count", "pat_pctile")
    assign_pctiles(lab_idx, "emp_intensity_raw", "lab_pctile")

    # Within-sector percentiles (Yale industry), only for cells with n >= 8
    from collections import defaultdict as dd
    by_sector_pat = dd(list)
    by_sector_lab = dd(list)
    for i in pat_idx:
        by_sector_pat[raw_rows[i]["industry"]].append(i)
    for i in lab_idx:
        by_sector_lab[raw_rows[i]["industry"]].append(i)
    for sector, idxs in by_sector_pat.items():
        if len(idxs) >= 8:
            assign_pctiles(idxs, "patent_count", "pat_pctile_sector")
    for sector, idxs in by_sector_lab.items():
        if len(idxs) >= 8:
            assign_pctiles(idxs, "emp_intensity_raw", "lab_pctile_sector")

    # ── Legacy composite α (kept for 09_run_regressions.py) ──────────────
    both_idx = [i for i, r in enumerate(raw_rows)
                if r["emp_intensity_raw"] is not None and r["patent_intensity_raw"] is not None]
    emp_only_idx = [i for i, r in enumerate(raw_rows)
                    if r["emp_intensity_raw"] is not None and r["patent_intensity_raw"] is None]

    if both_idx:
        emp_vals = [raw_rows[i]["emp_intensity_raw"] for i in both_idx]
        emp_pctiles = percentile_rank_list(emp_vals)

        pat_vals = [raw_rows[i]["patent_intensity_raw"] for i in both_idx]
        pat_pctiles = percentile_rank_list(pat_vals)

        composites = [e - p for e, p in zip(emp_pctiles, pat_pctiles)]
        comp_min = min(composites)
        comp_max = max(composites)
        comp_range = comp_max - comp_min if comp_max > comp_min else 1

        for j, i in enumerate(both_idx):
            raw_rows[i]["alpha_composite"] = (composites[j] - comp_min) / comp_range
            raw_rows[i]["alpha_emp_pctile"] = emp_pctiles[j]
            raw_rows[i]["alpha_pat_pctile"] = pat_pctiles[j]

    if emp_only_idx:
        emp_vals = [raw_rows[i]["emp_intensity_raw"] for i in emp_only_idx]
        emp_pctiles = percentile_rank_list(emp_vals)
        for j, i in enumerate(emp_only_idx):
            raw_rows[i]["alpha_composite"] = emp_pctiles[j]
            raw_rows[i]["alpha_emp_pctile"] = emp_pctiles[j]
            raw_rows[i]["alpha_pat_pctile"] = None

    # Build final output rows
    def fmt(v, spec=".6f"):
        return format(v, spec) if v is not None else ""

    reg_rows = []
    for r in raw_rows:
        alpha = r.get("alpha_composite")
        reg_rows.append({
            "name": r["name"],
            "country": r["country"],
            "industry": r["industry"],
            "grade": r["grade"],
            "action_type": r["action_type"],
            "exiter": r["exiter"],
            "clean_exit": r["clean_exit"],
            "exit_mode": r["exit_mode"],
            "event_date": r["event_date"],
            "event_month": r["event_month"] if r["event_month"] is not None else "",
            "timing_left_censored": r["timing_left_censored"],
            "nace_sector": r["nace_sector"],
            "b2c": r["b2c"],
            "sanctions_coalition": r["sanctions_coalition"],
            "wgi_rule_of_law": r["wgi_rule_of_law"],
            "legal_origin": r["legal_origin"],
            "pat_pctile": fmt(r.get("pat_pctile")),
            "lab_pctile": fmt(r.get("lab_pctile")),
            "pat_pctile_sector": fmt(r.get("pat_pctile_sector")),
            "lab_pctile_sector": fmt(r.get("lab_pctile_sector")),
            "alpha": fmt(alpha),
            "alpha_sq": fmt(alpha ** 2) if alpha is not None else "",
            "alpha_emp_pctile": fmt(r.get("alpha_emp_pctile")),
            "alpha_pat_pctile": fmt(r.get("alpha_pat_pctile")),
            "emp_intensity_raw": fmt(r["emp_intensity_raw"]),
            "patent_count": r["patent_count"] if r["patent_count"] is not None else "",
            "patent_intensity_raw": fmt(r["patent_intensity_raw"]),
            "y_exit_payoff": fmt(r["y_exit_payoff"], ".4f") if r["y_exit_payoff"] else "",
            "deal_value_mn_usd": fmt(r["deal_value_mn_usd"], ".2f") if r["deal_value_mn_usd"] else "",
            "deal_status": r["deal_status"],
            "has_deal": r["has_deal"],
            "pre_inv_equity_th_usd": fmt(r["pre_inv_equity_th_usd"], ".2f") if r["pre_inv_equity_th_usd"] else "",
            "sum_assets_th_usd": fmt(r["sum_assets_th_usd"], ".2f") if r["sum_assets_th_usd"] else "",
            "ln_assets": fmt(r["ln_assets"], ".4f") if r["ln_assets"] else "",
            "years_in_russia": int(r["years_in_russia"]) if r["years_in_russia"] else "",
            "employees_total": r["employees_total"],
            "n_subsidiaries": r["n_subsidiaries"],
            "sanctions_exposure": r["sanctions_exposure"],
            "sanction_hit_dates": r["sanction_hit_dates"],
            "guo_matched": r["guo_matched"],
            "y_sub_inactive": r["y_sub_inactive"],
            "sub_inactivation_rate": fmt(r["sub_inactivation_rate"], ".4f") if r["sub_inactivation_rate"] is not None else "",
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
    n_exiters = sum(1 for r in reg_rows if r["exiter"] == 1)
    n_alpha = sum(1 for r in reg_rows if r["alpha"])
    n_pat = sum(1 for r in reg_rows if r["pat_pctile"])
    n_lab = sum(1 for r in reg_rows if r["lab_pctile"])
    n_yi = sum(1 for r in reg_rows if r["y_exit_payoff"])
    n_controls = sum(1 for r in reg_rows if r["ln_assets"] and r["years_in_russia"])
    n_event = sum(1 for r in reg_rows if r["event_date"])

    mode_counts = {}
    for r in reg_rows:
        if r["exit_mode"]:
            mode_counts[r["exit_mode"]] = mode_counts.get(r["exit_mode"], 0) + 1

    stats = []
    stats.append("=" * 60)
    stats.append("REGRESSION SAMPLE SUMMARY STATISTICS")
    stats.append("=" * 60)
    stats.append(f"\nSample sizes:")
    stats.append(f"  Total firms (matched Orbis-Yale, ALL grades): {n_total}")
    stats.append(f"  Exiters (Grade A/B): {n_exiters}")
    stats.append(f"  Non-exiters (C/D/F): {n_total - n_exiters}")
    stats.append(f"  With patent percentile: {n_pat}")
    stats.append(f"  With labor percentile: {n_lab}")
    stats.append(f"  With legacy α: {n_alpha}")
    stats.append(f"  With Y_i (exit payoff ratio): {n_yi}")
    stats.append(f"  With all controls: {n_controls}")
    stats.append(f"  With event date (hazard sample): {n_event}")

    stats.append(f"\nExit mode (Grade A firms; seized = competing risk):")
    for k in ("sold", "walked", "seized"):
        stats.append(f"  {k}: {mode_counts.get(k, 0)}")

    grades = {}
    for r in reg_rows:
        g = r["grade"]
        grades[g] = grades.get(g, 0) + 1
    stats.append(f"\nGrade distribution:")
    for g in ["A", "B", "C", "D", "F"]:
        stats.append(f"  Grade {g}: {grades.get(g, 0)}")

    n_b2c = sum(1 for r in reg_rows if r["b2c"] == 1)
    n_coal = sum(1 for r in reg_rows if r["sanctions_coalition"] == "1")
    n_noncoal = sum(1 for r in reg_rows if r["sanctions_coalition"] == "0")
    stats.append(f"\nInstruments / moderators:")
    stats.append(f"  B2C (consumer-facing NACE): {n_b2c}")
    stats.append(f"  Coalition home country: {n_coal} | Non-coalition: {n_noncoal} "
                 f"| Unmatched country: {n_total - n_coal - n_noncoal}")

    sanc = [r["sanctions_exposure"] for r in reg_rows]
    stats.append(f"\nSanctions exposure (2022 EU packages hitting sector):")
    stats.append(f"  0 packages: {sum(1 for s in sanc if s == 0)}")
    stats.append(f"  1-4 packages: {sum(1 for s in sanc if 1 <= s <= 4)}")
    stats.append(f"  5-8 packages: {sum(1 for s in sanc if 5 <= s <= 8)}")

    stats.append(f"\nOther Y variables:")
    stats.append(f"  Y = any subsidiary inactive: {sum(1 for r in reg_rows if r['y_sub_inactive'] == 1)}")
    stats.append(f"  Y = Grade A + Sold: {sum(1 for r in reg_rows if r['y_grade_a_sold'] == 1)}")
    stats.append(f"  Y = Suspended: {sum(1 for r in reg_rows if r['y_suspended'] == 1)}")

    stats_text = "\n".join(stats)
    print(stats_text)

    with open(STATS_FILE, "w") as f:
        f.write(stats_text)

    print(f"\n\nOutput files:")
    print(f"  Regression data: {OUT_FILE}")
    print(f"  Summary stats: {STATS_FILE}")


if __name__ == "__main__":
    main()
