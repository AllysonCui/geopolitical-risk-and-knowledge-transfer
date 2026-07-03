"""
Parse Orbis XLSX exports into a clean subsidiary-level panel.

Reads the two Orbis export files (split due to export size limits),
extracts financial variables, and computes derived measures for the
α proxy and controls.

Input:
  data/orbis_export_part1.xlsx
  data/orbis_export_part2.xlsx

Output:
  data/collected/orbis_subsidiaries.csv — one row per subsidiary with
    financials, GUO info, and derived variables
"""

import csv
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
OUT_DIR = DATA_DIR / "collected"
OUT_DIR.mkdir(exist_ok=True)

ORBIS_FILES = [
    DATA_DIR / "orbis_export_part1.xlsx",
    DATA_DIR / "orbis_export_part2.xlsx",
]

YEARS = ["2023", "2022", "2021", "2020", "2019", "2018"]


def parse_xlsx_manual(path):
    """Parse Orbis xlsx by reading XML directly (avoids openpyxl version issues)."""
    zf = zipfile.ZipFile(path)
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

    ss_tree = ET.parse(zf.open("xl/sharedStrings.xml"))
    strings = []
    for si in ss_tree.findall(".//s:si", ns):
        t = si.find(".//s:t", ns)
        strings.append(t.text if t is not None else "")

    def get_val(cell):
        t = cell.get("t", "")
        v = cell.find("s:v", ns)
        if v is None:
            return ""
        if t == "s":
            idx = int(v.text)
            return strings[idx] if idx < len(strings) else ""
        return v.text

    def col_letters_to_idx(letters):
        idx = 0
        for ch in letters:
            idx = idx * 26 + (ord(ch) - ord("A") + 1)
        return idx - 1

    tree = ET.parse(zf.open("xl/worksheets/sheet2.xml"))
    all_rows = tree.findall(".//s:row", ns)

    header_cells = all_rows[0].findall("s:c", ns)
    headers = {}
    header_list = []
    for c in header_cells:
        ref = c.get("r", "")
        col = re.match(r"([A-Z]+)", ref).group(1)
        idx = col_letters_to_idx(col)
        name = get_val(c)
        headers[idx] = name
        header_list.append((idx, name))

    rows_out = []
    for row in all_rows[1:]:
        cells = row.findall("s:c", ns)
        record = {}
        for c in cells:
            ref = c.get("r", "")
            col = re.match(r"([A-Z]+)", ref).group(1)
            idx = col_letters_to_idx(col)
            if idx in headers:
                record[headers[idx]] = get_val(c)
        rows_out.append(record)

    return rows_out


def safe_float(val):
    if not val or val == "n.a." or val.strip() == "":
        return None
    try:
        return float(val.replace(",", ""))
    except (ValueError, AttributeError):
        return None


def parse_incorporation_date(val):
    """Convert Orbis date value to year. May be Excel serial or plain year."""
    if not val or val == "n.a.":
        return None
    try:
        num = float(val)
        if num > 2100:
            # Excel serial date (days since 1899-12-30)
            from datetime import datetime, timedelta
            base = datetime(1899, 12, 30)
            dt = base + timedelta(days=int(num))
            return dt.year
        elif 1900 <= num <= 2025:
            return int(num)
        else:
            return None
    except (ValueError, TypeError):
        return None


def best_year_value(record, base_field):
    """Return the most recent non-null value across years 2023→2018."""
    for year in YEARS:
        val = safe_float(record.get(f"{base_field} {year}"))
        if val is not None:
            return val, year
    val = safe_float(record.get(f"{base_field} Last avail. yr"))
    if val is not None:
        return val, "last"
    return None, None


def process_record(record):
    """Extract and compute variables for one subsidiary."""
    name = (record.get("Company name Latin alphabet") or "").strip()
    if not name:
        return None

    guo_name = (record.get("GUO - Name") or "").strip()
    guo_country = (record.get("GUO - Country ISO code") or "").strip()
    guo_direct_pct = safe_float(record.get("GUO - Direct %"))
    guo_total_pct = safe_float(record.get("GUO - Total %"))

    inactive = (record.get("Inactive") or "").strip()
    nace = (record.get("NACE Rev. 2, core code (4 digits)") or "").strip()
    incorp_year = parse_incorporation_date(record.get("Date of incorporation"))

    total_assets, ta_year = best_year_value(record, "Total assets th USD")
    shareholders_funds, sf_year = best_year_value(record, "Shareholders funds th USD")
    revenue, rev_year = best_year_value(record, "Operating revenue (Turnover) th USD")
    employees_val = safe_float(record.get("Number of employees Last avail. yr"))
    costs_employees, ce_year = best_year_value(record, "Costs of employees th USD")
    other_op_items, oo_year = best_year_value(record, "Other operating items th USD")

    # Pre-invasion values (2021 preferred, then 2020)
    ta_2021 = safe_float(record.get("Total assets th USD 2021"))
    ta_2020 = safe_float(record.get("Total assets th USD 2020"))
    sf_2021 = safe_float(record.get("Shareholders funds th USD 2021"))
    sf_2020 = safe_float(record.get("Shareholders funds th USD 2020"))
    pre_inv_assets = ta_2021 if ta_2021 is not None else ta_2020
    pre_inv_equity = sf_2021 if sf_2021 is not None else sf_2020

    # Employee intensity proxy for α (operational delegation)
    emp_intensity = None
    if employees_val and pre_inv_assets and pre_inv_assets > 0:
        emp_intensity = employees_val / pre_inv_assets

    # Years in Russia
    years_in_russia = None
    if incorp_year and incorp_year < 2022:
        years_in_russia = 2022 - incorp_year

    # Log assets
    import math
    ln_assets = None
    if pre_inv_assets and pre_inv_assets > 0:
        ln_assets = math.log(pre_inv_assets)

    return {
        "subsidiary_name": name,
        "inactive": inactive,
        "nace_code": nace,
        "nace_sector": nace[:2] if len(nace) >= 2 else "",
        "guo_name": guo_name,
        "guo_country": guo_country,
        "guo_direct_pct": guo_direct_pct,
        "guo_total_pct": guo_total_pct,
        "incorp_year": incorp_year,
        "years_in_russia": years_in_russia,
        "total_assets_th_usd": total_assets,
        "total_assets_year": ta_year,
        "pre_inv_assets_th_usd": pre_inv_assets,
        "pre_inv_equity_th_usd": pre_inv_equity,
        "shareholders_funds_th_usd": shareholders_funds,
        "revenue_th_usd": revenue,
        "employees": employees_val,
        "costs_employees_th_usd": costs_employees,
        "emp_intensity": emp_intensity,
        "ln_assets": ln_assets,
    }


def main():
    all_records = []
    for fpath in ORBIS_FILES:
        if not fpath.exists():
            print(f"WARNING: {fpath} not found, skipping")
            continue
        print(f"Parsing {fpath.name}...")
        rows = parse_xlsx_manual(fpath)
        print(f"  {len(rows)} rows read")
        all_records.extend(rows)

    print(f"\nTotal raw records: {len(all_records)}")

    processed = []
    for rec in all_records:
        out = process_record(rec)
        if out:
            processed.append(out)

    print(f"Processed records: {len(processed)}")

    # Filter to Western GUOs only
    western_countries = {
        "US", "GB", "DE", "FR", "JP", "CH", "FI", "NL", "IT", "SE",
        "DK", "AT", "ES", "NO", "CA", "BE", "IE", "LU", "CY", "VG",
        "BM", "KY", "JE", "GG", "LI", "MC", "AU", "NZ", "KR", "SG",
    }
    western = [r for r in processed if r["guo_country"] in western_countries]
    print(f"Western GUO subsidiaries: {len(western)}")

    # Stats
    has_assets = sum(1 for r in western if r["pre_inv_assets_th_usd"] is not None)
    has_equity = sum(1 for r in western if r["pre_inv_equity_th_usd"] is not None)
    has_emp = sum(1 for r in western if r["employees"] is not None)
    has_intensity = sum(1 for r in western if r["emp_intensity"] is not None)
    has_incorp = sum(1 for r in western if r["years_in_russia"] is not None)

    print(f"\nCoverage (Western GUO only):")
    print(f"  Pre-invasion assets: {has_assets}/{len(western)} ({100*has_assets/len(western):.0f}%)")
    print(f"  Pre-invasion equity: {has_equity}/{len(western)} ({100*has_equity/len(western):.0f}%)")
    print(f"  Employees: {has_emp}/{len(western)} ({100*has_emp/len(western):.0f}%)")
    print(f"  Employee intensity: {has_intensity}/{len(western)} ({100*has_intensity/len(western):.0f}%)")
    print(f"  Years in Russia: {has_incorp}/{len(western)} ({100*has_incorp/len(western):.0f}%)")

    # Write output
    out_path = OUT_DIR / "orbis_subsidiaries.csv"
    fields = list(processed[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(western)

    print(f"\nOutput: {len(western)} subsidiaries → {out_path}")


if __name__ == "__main__":
    main()
