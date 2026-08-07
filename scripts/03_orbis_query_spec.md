# Orbis Download Specification
## Purpose
Download Russian subsidiary-level financial data to construct:
- α component (i): **operational delegation index** = local employee costs / total subsidiary costs
- α component (ii): denominator for **proprietary intensity** = subsidiary total assets
- **Controls**: subsidiary size, years in Russia

---

## Step-by-Step Instructions (Bureau van Dijk Orbis)

### 1. Access Orbis
Log in via your university library portal → Orbis (Bureau van Dijk).

### 2. Search Screen → Define the Universe

Set **ALL** of the following filters:

| Filter | Setting |
|--------|---------|
| Country of location | **Russia** |
| Entity type | Subsidiary / branch (exclude ultimate parents) |
| Shareholder country | Any of: US, UK, Germany, France, Japan, Switzerland, Finland, Netherlands, Italy, Sweden, Denmark, Austria, Spain, Norway, Canada, Belgium, Ireland |
| Shareholder ownership % | ≥ 25% (to ensure meaningful control link) |
| Year of incorporation | ≤ 2021 (established before invasion) |
| Status | Active **or** Inactive (include both — you need exited firms) |

### 3. Columns to Export

Click **"Columns to display"** → Add each of the following fields:

**Identifiers**
- Company name (local + translated)
- BvD ID number (unique key for merging)
- National ID (OGRN — Russian registration number)
- NACE Rev. 2 primary code + description

**Financials (request ALL available years: 2018–2023)**
- Total assets (USD thousands)
- Operating revenue / turnover (USD thousands)
- Number of employees
- Costs of employees / Personnel costs (USD thousands)
- Total costs / Operating expenses (USD thousands)
- P/L for period [net income] (USD thousands)
- Shareholders' funds / equity (USD thousands)
- **Tangible fixed assets / PP&E (USD thousands)** — REQUIRED ADDITION:
  asset tangibility (PP&E/assets) is the obvious confounder for
  "sellability" in the exit-mode regressions (scripts 10–12) and is
  missing from the current export
- **Intangible fixed assets (USD thousands)** — complement to the above

**Parent (GUO) financials — REQUIRED ADDITION for the repaired knowledge
measures (docs/formal_model.md):**
- GUO total assets (USD thousands), 2019–2021
- GUO number of employees, 2019–2021
- GUO consolidated operating revenue, 2019–2021

These scale the parent patent stock (patents per parent employee/assets,
full parent footprint — not the largest Russian subsidiary), and let the
labor-intensity numerator and denominator come from the same 2019–2021
window.

**Shareholder info**
- Ultimate owner name
- Ultimate owner BvD ID
- Ultimate owner country
- Direct ownership %
- Indirect ownership %

**Date fields**
- Date of incorporation
- Date of last accounts filed
- Last available year of accounts

### 4. Export Format

- Format: **Excel (.xlsx)** or **CSV**
- Character encoding: UTF-8
- Financial values: **USD** (standardised, not local currency)
- Select **"All found companies"** (not just first page)

### 5. Merge Key

The merge to the Yale tracker is on **ultimate owner name** (Orbis) ↔ **name** (Yale CSV).  
This match will be fuzzy — run `04_merge_orbis_yale.py` (to be written) using fuzzy string matching (e.g. `rapidfuzz` library) to link the ~1,590 Yale companies to their Orbis subsidiaries.

### 6. Derived Variables (computed after download)

Once you have the raw download:

```
# Operational delegation index (α proxy component i)
op_delegation = personnel_costs_rub / total_costs_rub

# Proprietary intensity denominator
asset_base = total_assets_usd  # used to scale parent patent stock

# Subsidiary age (years in Russia before 2022)
years_in_russia = 2022 - year_of_incorporation

# Subsidiary size (log)
ln_assets = log(total_assets_usd)
```

### 7. Data Volume Estimate

The Yale tracker has ~1,590 Western firms. Not all will have Orbis entries for Russian subsidiaries (some operate through distributors or agents with no local legal entity). Expect ~600–900 matches with usable financial data.

### 8. Known Issues

- **Currency**: Request USD-standardised values; Orbis converts from RUB using period-average exchange rates. Verify the exchange rate vintage used.
- **Missing years**: Some subsidiaries file accounts with a lag. If 2022 data is missing, use 2021 as the pre-invasion baseline for controls.
- **Multiple subsidiaries**: A parent (e.g. Siemens AG) may have multiple Russian subsidiaries. Sum assets across subsidiaries; use the largest for the delegation index.
- **Inactive entities**: Firms that liquidated will show "inactive" status. Include them — these are your exiters.
