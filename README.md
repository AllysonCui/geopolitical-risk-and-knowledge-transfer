# Hostage Capital: Exit Choices Under Geopolitical Coercion

The assets a multinational can salvage in a geopolitical crisis are the same assets a hostile state can hold hostage. This project studies the 1,048 Western firms that withdrew from Russia after the February 2022 invasion (Yale CELI tracker backbone) and models exit as a discrete choice among three real options.

## Theory

A firm holding a Russian subsidiary after the invasion chooses the maximum of three payoffs:

- **V_sell** — salvage price minus transaction costs, exit levy, and mandated discount. Requires a buyer, and a buyer exists only for *appropriable* assets (codified IP, brands, plants) that survive the parent's departure.
- **V_walk** — zero salvage plus a write-off, but immediate and unilateral. Optimal when value is *tacit* — embedded in people who leave with the firm.
- **V_dissolve** — liquidate the legal entity. Optimal for *asset shells* with no going concern.

Adding iid extreme-value shocks yields a multinomial logit over exit modes (McFadden). The coercion mechanism: only the sell option runs through a state-controlled gate (approval commission, escalating exit levy from ~10% to ~35%, mandated discount from ~50% to ~60%, seizures of Danone and Carlsberg mid-negotiation). The state cannot tax a walk-away; it can and did tax the sale.

## Findings (H1-H4)

1. **Market formation.** P(a matched M&A deal exists) rises steeply in patent intensity (logit 2.19, p < 0.001) and is flat in employee intensity. Across patent quintiles, P(deal) goes 6% to 19%.
2. **The hostage gradient.** Across the same quintiles, P(clean exit, Grade A) *falls* 78% to 42% (patent percentile -0.36, p < 0.0001). The knowledge that creates a buyer also blocks the door. Conditional on committed exit, composite alpha confirms mode sorting: replicable operations walk away, IP-heavy operations sell (alpha = -0.20, p = 0.087).
3. **Shell liquidation.** Subsidiary dissolution is driven by low employee intensity (logit -6.94, p < 0.0001) and small size (p = 0.0007): an 11-to-1 dissolution gradient across employee-intensity terciles (8.5% vs 0.8%).
4. **Sanctions amplification.** The knowledge gradient on clean exit is 4.4x stronger in sanctioned sectors (R-squared 12.5% vs 2.2%).

## Estimation

Multinomial logit over {sold, suspended, ambiguous} as the RUM reduced form, plus per-hypothesis LPM/logit with HC1 robust errors. Controls: ln(assets), years_in_russia, ln(n_subsidiaries); industry fixed effects in robustness. Main script: `scripts/10_run_choice_model.py`; the earlier single-index specification is preserved in `scripts/09_run_regressions.py`.

## Data sources

### 1. Yale CELI Tracker (backbone)

- **What**: 1,589 firms tracked across 12 snapshots (Dec 2022 - May 2025), graded A-F on withdrawal compliance.
- **Where**: Public CSV snapshots in `data/` (e.g. `250521.csv`).
- **Provides**: firm name, home country, industry, Yale grade, action type (sold/suspended/other).
- **Concern**: Grades are subjective editorial judgments, not verified outcomes. Action text is inconsistent across snapshots (same firm may say "exited" in one and "sold operations" in another). We take the latest snapshot as ground truth.

### 2. Bureau van Dijk Orbis (subsidiary financials)

- **What**: 6,405 Russian subsidiaries of Western multinationals, with financial data.
- **Where**: Downloaded as two XLSX files (`data/orbis_export_part1.xlsx`, `data/orbis_export_part2.xlsx`) per the query spec in `scripts/03_orbis_query_spec.md`.
- **Provides**: total assets, employee count, employee costs, shareholders' equity, NACE sector code, GUO (global ultimate owner) name and country, incorporation date, active/inactive status.
- **Concern**: The Orbis export had limited column coverage initially — personnel costs and total costs were missing for many firms, so we use employees/total_assets as the employee-intensity proxy instead of the originally specified personnel_costs/total_costs. Multi-year data (2018-2023) was requested but coverage is uneven; the parser cascades through years to find the most recent available. Currency conversion from RUB to USD uses Orbis's internal period-average exchange rates, which may distort values during the 2022 ruble crash.

### 3. Bloomberg M&A Deals (exit valuations)

- **What**: 790 M&A deals involving Russian targets and Western sellers.
- **Where**: Exported from Bloomberg `MA <GO>` to `data/bloomberg_ma_deals.csv`.
- **Provides**: deal value, TV/EBITDA, payment type, deal status, seller/acquirer/target names.
- **Concern**: Only 38 of 178 post-invasion deals have disclosed sale values. The rest are "N/A." This means Y_i (exit payoff ratio = sale price / pre-exit book value) is available for only ~16 firms in the regression sample. The project has therefore pivoted from continuous Y_i to binary dependent variables (Grade A, Sold, Subsidiary dissolved). An expanded Bloomberg pull with write-down/impairment data would restore the continuous Y_i for 200+ additional firms.

### 4. Lens.org Patent Data (IP intensity)

- **What**: Patent portfolio size for each of the 1,048 parent firms.
- **Where**: Collected via `scripts/02_collect_patents_lens.py` using the Lens.org scholarly API; saved to `data/collected/patents_by_firm.csv`.
- **Provides**: total patent count per parent company, used as the numerator for the proprietary-intensity component of alpha.
- **Concern**: Lens.org's free API has aggressive rate limits (7 seconds between requests). Coverage is imperfect — some firms return zero patents due to name mismatches (e.g., "3M" matches noise). Patent counts are a stock measure (lifetime patents), not a flow measure (recent R&D activity), so a firm with legacy patents but no current R&D scores high on IP intensity.

### 5. EU Sanctions Package Data (instrument)

- **What**: 9 EU sanctions packages adopted in 2022, mapped to NACE 2-digit sectors.
- **Where**: `data/collected/eu_sanctions_2022.csv` (manually constructed) + hard-coded mapping in `scripts/08_build_analysis_dataset.py`.
- **Provides**: sanctions_exposure = count of packages hitting the firm's NACE sector (0-8).
- **Concern**: The mapping is coarse — sector-level, not firm-level. 798 of 899 firms in the sample have zero sanctions exposure. Only 101 firms are in affected sectors, and only ~35 of those are Grade A, limiting statistical power in split-sample regressions. Firm-level sanctions data (from Bloomberg BSRP or OFAC/EU lists) would be a much sharper instrument.

## Alpha construction

Alpha measures how replicable a firm's Russian operations are:

```
alpha = rescale_to_01(
    percentile_rank(employees / total_assets)     -- high = labor-heavy, operational
  - percentile_rank(patents / total_assets)        -- high = IP-embedded
)
```

- High alpha (near 1): operational arm — many employees relative to assets, few patents. Knowledge is tacit, embedded in people and routines. Walking away is cheap because there is little proprietary value to extract.
- Low alpha (near 0): knowledge repository — asset-heavy, patent-rich. Walking away means abandoning recoverable IP, so these firms sell.

For firms missing patent data (no Lens.org match), alpha falls back to employee-intensity percentile only.

## Pipeline

Run scripts in numerical order. Each consumes the output of prior steps.

```
01_parse_yale_tracker.py       Yale CSVs --> firms_exit_panel.csv, firms_exiters.csv
02_collect_patents_lens.py     firms_exiters.csv --> patents_by_firm.csv  (needs API token)
03_orbis_query_spec.md         (instructions for manual Orbis download, not a script)
05_parse_orbis_export.py       orbis_export_part*.xlsx --> orbis_subsidiaries.csv
06_merge_orbis_yale.py         orbis_subsidiaries + firms_exiters --> merged_orbis_yale.csv
07_merge_bloomberg_deals.py    bloomberg_ma_deals + firms_exiters --> exit_deals_matched.csv
08_build_analysis_dataset.py   all collected data --> regression_sample.csv
09_run_regressions.py          regression_sample.csv --> regression_results.txt
10_run_choice_model.py         regression_sample.csv --> choice_model_results.txt  (MAIN)
```

Steps 02, 05, 06, 07 can run in any order as long as 01 has run first. Step 08 requires all prior outputs. Steps 09 and 10 require step 08.

### Dependencies

```
pip install openpyxl rapidfuzz numpy statsmodels
```

- `openpyxl`: parsing Orbis XLSX exports (step 05)
- `rapidfuzz`: fuzzy string matching for Orbis-Yale and Bloomberg-Yale merges (steps 06, 07)
- `numpy` + `statsmodels`: regression estimation (step 09)

## Fuzzy matching

The Orbis-to-Yale merge uses `rapidfuzz.fuzz.token_sort_ratio` with a threshold of 70 (90 for short names <= 5 characters). Twenty-one manual overrides handle known problem names (IKEA, BMW, H&M, etc.). Match rate: 899 of 1,048 exiters (86%). The Bloomberg-to-Yale merge uses the same approach on seller names.

## File structure

```
data/
  *.csv                          Yale CELI tracker snapshots (raw)
  bloomberg_ma_deals.csv         Bloomberg M&A export (raw)
  orbis_export_part1.xlsx        Orbis subsidiary export (raw)
  orbis_export_part2.xlsx
  collected/                     Intermediate processed data
    firms_exit_panel.csv           1,589 firms, all grades
    firms_exiters.csv              1,048 Grade A+B firms
    orbis_subsidiaries.csv         6,405 Russian subsidiaries
    merged_orbis_yale.csv          899 matched firm-level records
    exit_deals_matched.csv         165 matched M&A deals
    patents_by_firm.csv            1,048 firms with patent counts
    eu_sanctions_2022.csv          9 sanctions packages
  analysis/                      Final outputs
    regression_sample.csv          899-row regression-ready dataset
    regression_results.txt         Single-index specification output (script 09)
    choice_model_results.txt       Discrete-choice model output (script 10, main)
    sample_stats.txt               Summary statistics

scripts/
  01_parse_yale_tracker.py
  02_collect_patents_lens.py
  03_orbis_query_spec.md
  05_parse_orbis_export.py
  06_merge_orbis_yale.py
  07_merge_bloomberg_deals.py
  08_build_analysis_dataset.py
  09_run_regressions.py
  10_run_choice_model.py
```

## Known limitations

1. **Alpha is a proxy, not a direct measure.** The ideal alpha would use personnel_costs/total_costs (operational delegation). The Orbis export lacked consistent cost breakdowns, so we substitute employees/total_assets. These are correlated but not identical.
2. **Y_i is mostly binary.** Only 16 firms have a continuous exit payoff ratio. The analysis therefore uses P(Grade A) and P(Sold) as dependent variables rather than the originally intended sale_price/book_value.
3. **Sanctions instrument is coarse.** Sector-level mapping leaves 89% of firms with zero sanctions exposure. Firm-level sanctions data would improve identification.
4. **Cross-sectional design.** The data supports panel structure (multi-year Orbis financials, multiple Yale snapshots), but the current regressions are cross-sectional. A difference-in-differences or event-study design would strengthen causal claims.
5. **No parent-level controls.** R&D/revenue, geographic diversification, and Russia revenue share are not yet integrated. These are standard controls in the divestiture literature and would address omitted-variable concerns.
