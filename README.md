# Knowledge Structure, Exit Mode, and Sanctions Amplification

Does a multinational's knowledge structure determine *how* it exits a hostile market — and do sanctions sharpen that sorting?

This project studies how Western firms left Russia after the February 2022 invasion, using the Yale CELI tracker as the backbone of the analysis. The central research question is whether the transferability of a subsidiary's productive assets helps explain *how* the parent exits. Transferable assets can preserve value under new ownership and therefore increase the price a buyer is willing to pay. By contrast, value that depends on employees, relationships, and firm-specific routines may be difficult for a buyer to retain after ownership changes. The model therefore predicts that subsidiaries associated with more transferable intellectual property should be easier to sell, whereas subsidiaries that rely more heavily on non-transferable human capital may have fewer viable sale opportunities and may instead close, suspend operations, or otherwise exit without an arm's-length sale. The analysis also asks whether sanctions and home-country institutions alter this relationship. These are hypotheses to be tested, not assumptions that the current evidence has already established.

## The three questions and their specifications

1. **Q1 — Exit mode** (`scripts/10_selection_exit_mode.py`): Is a firm's knowledge structure associated with completing a sale rather than exiting without a sale? The code estimates a Heckman-style two-stage model on the **full population** of matched foreign parents (all Yale grades A–F, not only firms that exited). The first-stage probit models completion of a clean exit. The second-stage probit models sale versus non-sale exit and includes the inverse Mills ratio as a control function. Consumer-facing (B2C) NACE status is the proposed exclusion restriction: the design assumes that public pressure affects whether a firm exits but does not directly affect whether it can find a buyer. That assumption is contestable and requires validation. State seizures (Danone, Carlsberg, Fortum, and Uniper) are treated as a third outcome because they are not voluntary choices between sale and non-sale exit.
2. **Q2 — Sanctions amplification** (`scripts/11_sanctions_amplification.py`): a pooled **PatInt × SancExp interaction** (replacing the earlier split-sample R² comparison, which did not survive the rebuild — see "What changed") plus a **cause-specific competing-risks Cox** (statsmodels PHReg, episode-split counting-process data) with *time-varying* sector exposure built from the staggered 2022 EU package rollout.
3. **Q3 — Institutional moderators** (`scripts/12_institutional_moderators.py`): cross-level PatInt × institution interactions (coalition membership, WGI rule of law, legal origin) with home-country fixed effects — levels are absorbed, only the interactions are identified. Mundlak correlated-random-effects probit as robustness. Wild cluster bootstrap (home country, ~35 clusters) throughout.

The legacy cross-sectional specifications are retained in `scripts/09_run_regressions.py` (restricted to the original Grade A/B frame) for comparability.

## Headline empirical patterns (current build)

- Among Grade A exits with patent data (n=362): selling rises monotonically across patent-stock terciles (28% → 36% → 49%); patent percentile is positive in the mode probit (β ≈ 0.49, p ≈ 0.045; wild-cluster-bootstrap p ≈ 0.07 on the LPM analog). Labor intensity is negative but imprecise.
- In the cause-specific hazard model, higher patent intensity is associated with a lower estimated hazard of exit without a sale (log hazard coefficient ≈ −1.16, p < 0.001). Its estimated association with the sale hazard is not statistically distinguishable from zero. This pattern is consistent with the transferability mechanism, but it does not establish that mechanism because patent stock may also proxy for parent size, sector, profitability, or asset composition.
- The IMR (λ) is statistically indistinguishable from zero: little evidence that selection into exit biases the naive mode regression.
- The estimated PatInt × sanctions interaction is close to zero with the current sector-level exposure measure. More precise firm-level exposure data are needed to test the moderation hypothesis credibly.

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

## How the theoretical concepts are measured

The model distinguishes transferable codified assets from value embodied in people and routines. The available variables are imperfect proxies for those concepts and therefore enter separately (the symmetric composite α is retained only for legacy analysis):

```
pat_pctile          percentile rank of the parent's patent stock; a proxy for codified knowledge, not a direct measure of IP owned by the Russian subsidiary
lab_pctile          percentile rank of subsidiary employees/assets; a proxy for labor intensity, not a direct measure of tacit or firm-specific knowledge
alpha, alpha_sq     legacy composite (script 09 only)
```

The current mapping is incomplete. Parent patent stock does not show which patents would transfer with the Russian legal entity, and employees per unit of assets does not directly measure whether employee knowledge is firm-specific or likely to leave after a sale. Planned improvements include measuring the parent's 2017–2021 patent stock and scaling it by parent size, identifying subsidiary-level IP ownership where possible, and constructing labor intensity from a consistent 2019–2021 accounting window.

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

## What changed in the redesign

- The sample now includes **non-exiters** (grades C/D/F), fixing the exiter-only conditioning.
- Seizures are a separate competing risk (classifier priority + manual overrides), no longer misclassified as sales/exits.
- The sanctions question is an **interaction/hazard design**, not a subsample R² ratio. Instructively, the old "4.4×" headline did not survive the rebuild: with the corrected action classification and the population-based percentiles, the sanctioned-sector R² ratio flips below 1 — the interaction coefficient (currently ≈ 0) is the defensible statistic.
- Grade A **and** B firms form the broad exiter sample; Grade A alone defines completed exits for the exit-mode analysis. This makes the estimand clear but also ties the outcome to Yale's editorial classification.

## Where the model and evidence do—and do not—match

The model predicts a higher probability of sale when more subsidiary value can be transferred to a buyer. The positive association between parent patent rank and sale, together with the lower estimated non-sale exit hazard, is consistent with that prediction. The evidence does not yet identify the model's mechanism. Patent data are measured at the parent rather than the Russian subsidiary, labor intensity is only a rough proxy for non-transferable human capital, and the data do not directly measure the buyer's valuation or the fraction of value that survives a transfer. The current sanctions interaction is close to zero, so the data do not support the stronger claim that sanctions amplify knowledge-based sorting. Institutional interactions are also imprecisely estimated. These null and uncertain results should remain part of the project's substantive interpretation.

## Major work required before strong causal claims

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
  formal_model.md                model of sale with imperfectly transferable assets

scripts/
  01..12 + estimation_utils.py   see Pipeline
```
