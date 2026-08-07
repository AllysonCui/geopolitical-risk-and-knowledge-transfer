# Corporate Exit from Russia: Current Data and Draft Status

## What this repository currently does

This repository is an early empirical draft about foreign companies that
reduced, suspended, or ended operations in Russia after the February 2022
invasion of Ukraine. It follows companies across repeated Yale CELI tracker
files and combines those records with Russian subsidiary accounts, parent
patent counts, selected transaction records, sanctions dates, and home-country
information.

The research proposal describes the study in its ideal form: a subsidiary-level
analysis of how buyer scarcity, transaction restrictions, approval delays, and
the cost of maintaining an unresolved business affect the completion of exit.
The current repository cannot yet estimate that full model. Its purpose is to
establish the descriptive facts, test provisional measures, and identify the
data that must be added.

## The practical question

An announcement that a company intends to leave is not the same as a completed
exit. After announcing, a company may:

- Continue operating while seeking a solution.
- Suspend activity but retain legal ownership.
- Complete a sale to a new owner.
- Close or liquidate the Russian operation.
- Lose control through state intervention.

The current draft asks how long companies remain unresolved and whether their
assets and operating structure are associated with the outcome eventually
reported.

## What is observed now

### Yale CELI tracker

The repository contains 11 Yale snapshots from December 2022 through May 2025.
Each snapshot provides a company name, home country, industry, Yale grade, and
a short description of the company's reported actions.

The new snapshot-level file contains 17,258 company-date observations. A
conservative text classifier assigns one of five provisional states:

1. Still operating.
2. Exit announced but unresolved.
3. Sale reported as completed.
4. Closure reported as completed.
5. State-imposed loss of control.

Generic language such as “plans to leave” is not treated as a completed sale.
The file also contains an ambiguity flag. There are currently 5,367 ambiguous
company-date observations, so the state labels should be treated as a review
queue rather than verified legal outcomes.

### Orbis subsidiary data

The current Orbis files contain 6,405 Russian subsidiaries associated with
foreign parents. Available fields include total assets, employees, NACE sector,
incorporation date, ownership names, and active or inactive status.

Important omissions include PP&E, intangible assets, monthly payroll,
profitability, and a historical record of changes in legal ownership. The next
Orbis export should add those fields and retain consistent pre-invasion dates.

### Patent data

The Lens.org file contains parent-company patent counts. It largely covers
companies that announced an exit and counts lifetime patents. It therefore
does not provide the full population needed for the proposed duration analysis.

The next pull should cover every matched parent and count patents granted in a
pre-invasion window such as 2017-2021. Parent patent stock remains only a rough
proxy because it does not show which patents were owned by or licensed to the
Russian subsidiary.

### Transactions

The Bloomberg file contains 790 reported transactions involving Russian
targets and foreign sellers, of which 165 have been matched to the company
sample. Announcement dates improve timing for some sales. Transaction values
are available for too few observations to support a reliable valuation model.

### Sanctions and institutions

The repository maps the timing of 2022 EU sanctions packages to broad economic
sectors. This is a coarse measure: it does not identify the exact restriction
facing a seller, buyer, product, or transaction. Home-country coalition status,
rule of law, and legal origin are also present, but their estimated interactions
are imprecise and are not central to the revised proposal.

## What the current evidence suggests

The present results should be read as descriptive associations:

- Among 362 companies currently classified as completed exits with patent
  data, the reported sale share rises from 28% in the lowest patent tercile to
  49% in the highest tercile.
- In the current duration sample, moving from the bottom to the top of the
  parent patent ranking is associated with an approximately 69% lower rate of
  completing an exit without a sale.
- The estimated relationship between parent patent rank and the rate of
  completed sales is small relative to its uncertainty.
- Labor intensity is associated with an estimated 32% higher rate of non-sale
  completion, but this estimate is too imprecise for a firm conclusion.
- The current relationship between sanctions exposure and patent intensity is
  close to zero.

These estimates do not show that patents cause a company to wait or that
employee intensity causes closure. The patent sample is selected, the outcome
labels are provisional, and important subsidiary characteristics are missing.

## How the revised proposal differs from the current code

The proposal treats geopolitical exit as a distorted market for corporate
control. A parent waits for an eligible buyer and any required approval while
paying the cost of maintaining the subsidiary. Sanctions and host-country rules
can reduce buyer availability, lower permitted transaction value, or delay
completion.

The existing scripts do not yet estimate that quantitative model. In
particular, they do not observe:

- The date a company applied for government approval.
- The date approval was granted or denied.
- The set of potential buyers.
- The monthly cost of maintaining the subsidiary.
- Legal ownership at every date.
- Intellectual property attached to each Russian subsidiary.

The formal model is therefore a research design and accounting framework, not
a description of the current estimator.

## Files produced by the current pipeline

```text
data/analysis/firm_snapshot_states.csv
    One row per company and Yale snapshot, with a provisional state and an
    ambiguity flag.

data/analysis/firms_exit_panel.csv
    One row per company, retaining the older grade and timing variables.

data/analysis/orbis_subsidiaries.csv
    Cleaned Russian subsidiary records.

data/analysis/merged_orbis_yale.csv
    Matched parent-level Yale-Orbis sample.

data/analysis/regression_sample.csv
    Current parent-level analysis file.

data/analysis/results_10_selection_exit_mode.txt
    Earlier two-stage analysis of exit completion and reported outcome.

data/analysis/results_11_sanctions_amplification.txt
    Current duration results for reported sales and non-sale completions.

data/analysis/results_12_institutional_moderators.txt
    Exploratory home-country interactions.
```

## Scripts

```text
01_parse_yale_tracker.py       combine Yale snapshots and assign provisional states
02_collect_patents_lens.py     collect patent counts; full-panel re-run required
03_orbis_query_spec.md         fields requested for the next Orbis export
05_parse_orbis_export.py       clean and combine Orbis files
06_merge_orbis_yale.py         match subsidiaries and parents to Yale companies
07_merge_bloomberg_deals.py    match reported transactions
08_build_analysis_dataset.py   construct the current parent-level dataset
09_run_regressions.py          retain earlier cross-sectional checks
10_selection_exit_mode.py      retain the earlier two-stage model
11_sanctions_amplification.py  estimate the current duration relationships
12_institutional_moderators.py explore home-country relationships
```

## Reproducing the current build

Install the Python dependencies:

```bash
pip install openpyxl rapidfuzz numpy scipy statsmodels
```

Run the scripts in numerical order. Scripts 02, 05, 06, and 07 can run after
script 01. Script 08 requires the preceding data outputs, and scripts 09-12
use the dataset produced by script 08.

## Highest-priority next steps

1. Fix the intended outlet and satisfy its formal eligibility requirements.
   An Academy of Management Collections proposal needs a selected article list;
   the cited AMP special-issue call requires a focal managerial implication
   previously published in an eligible AOM journal. Neither requirement is met
   by the current draft, and an article should not be invented merely to make
   the proposal appear compliant.
2. Manually review the ambiguous Yale company-date records and document the
   evidence supporting every completed outcome.
3. Obtain historical legal ownership and liquidation records for the Russian
   subsidiaries.
4. Collect pre-invasion patents for the full parent population.
5. Add PP&E, intangible assets, profitability, payroll or labor cost, and
   parent size.
6. Build transaction histories containing buyer identity, price, completion
   date, and approval information.
7. Replace the current selected duration regressions with a subsidiary-level
   model using the complete population at risk.

## Interpretation standard

Until those steps are completed, the repository supports a presentable
motivation and a transparent description of the current evidence. It does not
yet support causal claims about knowledge transfer, sanctions effectiveness,
government approval, or the welfare consequences of sale versus closure.
