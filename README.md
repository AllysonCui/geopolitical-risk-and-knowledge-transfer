# Knowledge Structure, Exit Mode, and Sanctions Amplification

Does a multinational's knowledge structure determine *how* it exits a hostile market — and do sanctions sharpen that sorting?

This project studies the Western firms that withdrew from Russia after the February 2022 invasion, using the Yale CELI tracker as the backbone. All three empirical questions are now anchored in a single formal model — **exit as a fire-sale problem with inalienable human capital** (`docs/formal_model.md`) — and each specification is a comparative static of that model: codified knowledge (patents) is alienable and transfers with the legal entity, tacit knowledge embodied in employees is not, so IP-heavy firms **sell** while operationally embedded firms **walk away**, and sanctions steepen the sorting by raising transaction costs.

## The three questions and their specifications

1. **Q1 — Exit mode** (`scripts/10_selection_exit_mode.py`): Heckman-style two-stage on the **full population** of matched foreign parents (all Yale grades A–F, not just exiters): a selection probit for whether a firm completes a clean exit, then a mode probit (sell vs. walk away) with the inverse-Mills-ratio control function. Exclusion restriction: consumer-facing (B2C) NACE status — boycott pressure shifts *whether* to exit, not the mechanics of the asset transfer. State seizures (Danone, Carlsberg, Fortum, Uniper) are coded as a third competing risk and dropped from the sell/walk margin.
2. **Q2 — Sanctions amplification** (`scripts/11_sanctions_amplification.py`): a pooled **PatInt × SancExp interaction** (replacing the earlier split-sample R² comparison, which did not survive the rebuild — see "What changed") plus a **cause-specific competing-risks Cox** (statsmodels PHReg, episode-split counting-process data) with *time-varying* sector exposure built from the staggered 2022 EU package rollout.
3. **Q3 — Institutional moderators** (`scripts/12_institutional_moderators.py`): cross-level PatInt × institution interactions (coalition membership, WGI rule of law, legal origin) with home-country fixed effects — levels are absorbed, only the interactions are identified. Mundlak correlated-random-effects probit as robustness. Wild cluster bootstrap (home country, ~35 clusters) throughout.

The legacy cross-sectional specifications are retained in `scripts/09_run_regressions.py` (restricted to the original Grade A/B frame) for comparability.

## Headline empirical patterns (current build)

- Among Grade A exits with patent data (n=362): selling rises monotonically across patent-stock terciles (28% → 36% → 49%); patent percentile is positive in the mode probit (β ≈ 0.49, p ≈ 0.045; wild-cluster-bootstrap p ≈ 0.07 on the LPM analog). Labor intensity is negative but imprecise.
- In the cause-specific hazard, patent intensity strongly *reduces* the walk-away hazard (log HR ≈ −1.16, p < 0.001) with no significant effect on the sale hazard — IP-heavy firms don't abandon.
- The IMR (λ) is statistically indistinguishable from zero: little evidence that selection into exit biases the naive mode regression.
- The PatInt × sanctions interaction is currently a precise zero at sector-level exposure; firm-level exposure measures are the planned sharpening.

## Data sources

### 1. Yale CELI Tracker (backbone)

- **What**: 1,589 firms tracked across 11 snapshots (Dec 2022 – May 2025), graded A–F on withdrawal compliance.
- **Where**: Public CSV snapshots in `data/raw/yale/` (e.g. `250521.csv`).
- **Provides**: firm name, home country, industry, Yale grade, action text; and — new — **exit timing** (first snapshot at Grade A) used by the hazard model.
- **Concern**: Grades are subjective editorial judgments, not verified outcomes. Timing is coarse: 323 firms were already Grade A at the first snapshot (left-censored). Exit-mode coding relies on a regex classifier over action text plus manual seizure overrides; the planned hand-validation against the KSE Institute "LeaveRussia" database and Bloomberg/Refinitiv M&A records has **not** been done yet.

### 2. Bureau van Dijk Orbis (subsidiary financials)

- **What**: 6,405 Russian subsidiaries of Western multinationals, with financial data.
- **Where**: Two XLSX exports in `data/raw/orbis/` per the query spec in `scripts/03_orbis_query_spec.md`.
- **Provides**: total assets, employee count, NACE code, GUO name/country, incorporation date, active/inactive status.
- **Concern**: No PP&E column, so **asset tangibility — the key sellability confounder — cannot be controlled yet**; no parent-level financials, so patent stock cannot be scaled by parent size. Both are now REQUIRED ADDITIONS in the 03 spec for the next export.

### 3. Bloomberg M&A Deals (exit valuations + sale timing)

- **What**: 790 M&A deals involving Russian targets and Western sellers.
- **Provides**: deal value, status, announce date — the announce date now provides sharp event timing for completed sales in the hazard model.
- **Concern**: Only ~18 firms have a computable exit-payoff ratio; binary/mode outcomes remain primary.

### 4. Lens.org Patent Data (IP intensity)

- **What**: Patent portfolio size per parent firm, `data/raw/lens/patents_by_firm.csv`.
- **Concern (important)**: the existing CSV covers **Grade A/B exiters only** and counts **lifetime** patents. Script 02 has been updated to (a) query the full 1,589-firm panel so patents can enter the selection stage, and (b) restrict to 2017–2021 granted patents (pre-determined vintage). **Re-run it (needs a Lens API token) to replace the file**; until then, the selection stage runs without patent intensity and the hazard risk set is effectively exiters.

### 5. EU Sanctions Package Data

- **What**: 9 EU sanctions packages adopted in 2022 with adoption dates (`data/raw/eu_sanctions/eu_sanctions_2022.csv`), mapped to NACE 2-digit sectors in script 08.
- **Provides**: `sanctions_exposure` (count of packages hitting the sector) and `sanction_hit_dates` (adoption dates — the time-varying exposure profile for the hazard).
- **Concern**: Sector-level and 2022-only. The design calls for firm-level exposure via CN/HS product codes from the EU Official Journal annexes (Eurostat RAMON correspondences), dual-use Annex I flags, and OFAC/Castellum counterparty exposure — not yet collected. Packages 9–14 are unmapped.

### 6. Home-country institutions (new)

- **What**: `data/raw/institutions/home_country_institutions.csv` — sanctions-coalition membership (Decree 430-r "unfriendly countries" list), WGI Rule of Law estimate, LLSV legal origin.
- **Provenance**: verified against sources on 2026-08-06 — the coalition dummy against the Decree 430-r list (zero changes from the initial coding), WGI from the official DataBank `RL.EST` export (via a vendored public mirror), legal origin per LLSV with one correction (UAE → french civil law). **One deviation**: the WGI column is the **2022 vintage** — the 2021 release was unreachable through this environment's network policy; adjacent-year estimates are highly correlated, but swap in 2021 when available (see `data/raw/institutions/README.md`). ESG-disclosure mandates (Carrots & Sticks) not yet collected.

## Knowledge-structure measures

The model treats **codifiability** as the driver, so the components enter separately (the symmetric composite α is legacy):

```
pat_pctile          percentile rank of parent patent stock (global; within-sector variant pat_pctile_sector)
lab_pctile          percentile rank of subsidiary employees/assets (global; within-sector variant)
alpha, alpha_sq     legacy composite (script 09 only)
```

Planned repairs that need new data: patent stock at the GUO with 2017–2021 vintage scaled by parent employees/assets (Lens re-pull + Orbis parent columns); labor intensity numerator and denominator from the same 2019–2021 window.

## Pipeline

```
01_parse_yale_tracker.py       Yale CSVs --> firms_exit_panel.csv (all grades, exit timing, seizure coding)
02_collect_patents_lens.py     full panel --> patents_by_firm.csv  (needs API token; 2017-21 grant window)
03_orbis_query_spec.md         (instructions for manual Orbis download, not a script)
05_parse_orbis_export.py       orbis_export_part*.xlsx --> orbis_subsidiaries.csv
06_merge_orbis_yale.py         orbis_subsidiaries + FULL panel --> merged_orbis_yale.csv (1,394 firms, A-F)
07_merge_bloomberg_deals.py    bloomberg_ma_deals + firms_exiters --> exit_deals_matched.csv
08_build_analysis_dataset.py   all raw + intermediate --> regression_sample.csv (population incl. stayers)
09_run_regressions.py          legacy cross-sectional specs (A/B frame) --> regression_results.txt
10_selection_exit_mode.py      Q1: Heckman two-stage --> results_10_selection_exit_mode.txt
11_sanctions_amplification.py  Q2: interaction + competing-risks Cox --> results_11_sanctions_amplification.txt
12_institutional_moderators.py Q3: country-FE interactions --> results_12_institutional_moderators.txt
```

Steps 02, 05, 06, 07 can run in any order after 01. Step 08 requires all prior outputs; 09–12 require 08. Scripts 10–12 share `scripts/estimation_utils.py` (wild cluster bootstrap, probit/OLS reporting).

### Dependencies

```
pip install openpyxl rapidfuzz numpy scipy statsmodels
```

## What changed in the model-based redesign (and what it overturned)

- The sample now includes **non-exiters** (grades C/D/F), fixing the exiter-only conditioning.
- Seizures are a separate competing risk (classifier priority + manual overrides), no longer misclassified as sales/exits.
- The sanctions question is an **interaction/hazard design**, not a subsample R² ratio. Instructively, the old "4.4×" headline did not survive the rebuild: with the corrected action classification and the population-based percentiles, the sanctioned-sector R² ratio flips below 1 — the interaction coefficient (currently ≈ 0) is the defensible statistic.
- Grade A **and** B firms are the exiter sample; Grade A alone defines completed exits for the mode margin.

## Not yet implemented (needs data access)

1. **Lens re-pull** for the full panel with the 2017–2021 grant window (API token required) — unblocks patents in the selection stage and stayers in the hazard risk set.
2. **Orbis re-export** with PP&E/intangibles and parent-level financials (tangibility control; parent-scaled patent intensity; 2019–2021 window alignment).
3. **Exit-mode hand-validation** against KSE LeaveRussia and Bloomberg/Refinitiv transaction records.
4. **Firm-level sanction exposure** (EU OJ annexes → CN → CPA → NACE via Eurostat RAMON; dual-use Annex I; OFAC/Castellum) and mapping of packages 9–14.
5. **Survey-based public pressure** (Eurobarometer 2022 / Pew) for the B2C × pressure exclusion restriction; currently B2C alone identifies (the B2C × non-coalition cell is near-empty).
6. **ESG-disclosure mandates** (Carrots & Sticks) for the stakeholder-pressure channel.
7. **FIML heckprobit** (Stata/R) to replace the two-step control-function approximation.
8. Swap the WGI Rule of Law column from the 2022 vintage to 2021 once the WGI download is reachable (values verified otherwise; see `data/raw/institutions/README.md`).

## Fuzzy matching

The Orbis-to-Yale merge uses `rapidfuzz` token-set/partial ratios with a threshold of 70 (90 for names ≤ 5 characters) plus 21 manual overrides. Match rate: 1,394 of 1,589 panel firms (88%). The Bloomberg-to-Yale merge uses the same approach on seller names.

## File structure

```
data/
  raw/
    yale/                        11 Yale CELI tracker snapshots
    orbis/                       Orbis subsidiary exports (xlsx)
    bloomberg/                   Bloomberg M&A export
    lens/                        patents_by_firm.csv (exiters-only, lifetime — re-pull pending)
    eu_sanctions/                9 packages with adoption dates
    institutions/                home-country institutions (+ verification README)
  analysis/
    firms_exit_panel.csv         1,589 firms, all grades, exit timing
    firms_exiters.csv            1,048 Grade A+B firms
    orbis_subsidiaries.csv       6,405 Russian subsidiaries
    merged_orbis_yale.csv        1,394 matched firms (all grades)
    exit_deals_matched.csv       matched M&A deals
    regression_sample.csv        1,394-row analysis dataset
    regression_results.txt       legacy specs (09)
    results_10_*.txt             Q1 selection model
    results_11_*.txt             Q2 interaction + hazard
    results_12_*.txt             Q3 institutions
    sample_stats.txt             summary statistics

docs/
  formal_model.md                the fire-sale / inalienable-human-capital model

scripts/
  01..12 + estimation_utils.py   see Pipeline
```
