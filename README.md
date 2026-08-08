# Foreign-Market Entry Mode and Exit after Political Rupture

## Research question

Foreign firms can operate in a country through a wholly owned subsidiary, a
joint venture, or a contract with a local distributor, licensee, or franchisee.
This project asks which arrangement creates the lowest cost when political
relations deteriorate and the firm tries to leave.

The main outcomes are:

1. The accounting loss caused by exit.
2. The time from the political rupture to legal and operational resolution.
3. The share of the firm's pre-rupture investment that it recovers.

Russia after 24 February 2022 is the first application. The event affected
foreign firms using different arrangements at the same time. It therefore
provides a common shock, but it does not make firms' earlier entry-mode choices
random.

## Current status

This branch is a research-design draft. It contains a formal model, a proposal,
a conservative entry-mode review file, and an initial description of Bloomberg
transactions. The current data do not support a final comparison of exit cost
across the three entry modes.

The main data limitations are:

- The Orbis export is not a 2021 historical ownership file. Current ownership
  can reflect transactions that occurred after the invasion.
- The Yale descriptions record public actions after the invasion. They were not
  collected to measure the firm's pre-invasion entry mode.
- The Bloomberg file contains reported transactions. Firms that did not try to
  sell are not represented.
- Distributor, license, and franchise relationships are generally absent from
  Orbis and Bloomberg.
- Bloomberg reports transaction values in several currencies. It does not
  report accounting write-downs, and most transaction values are undisclosed.

Absence from Orbis is therefore coded as unclassified, not as contractual
entry. An undisclosed transaction value is treated as missing, not as zero
recovery.

## Data currently used

### Bloomberg transactions

`data/raw/bloomberg/bloomberg_data_russia.csv` contains 1,392 transaction
records. The baseline script selects 158 transactions announced on or after 24
February 2022 that have a non-Russian seller and either a Russian target or an
explicit reference to Russian assets.

The file provides announcement dates, completion or termination dates,
transaction status, the percentage interest offered, transaction values when
disclosed, and the reported currency.

### Orbis subsidiaries

The processed Orbis file contains 6,405 Russian subsidiaries linked to foreign
parents. It includes parent names, direct and total ownership percentages,
pre-2022 assets and equity when available, industry, and employment.

Only strict normalized name matches are used in the new review file. Fuzzy
matches are excluded because several short or generic firm names produce false
matches.

### Yale company descriptions

The Yale files contain 1,589 companies and repeated descriptions of their
reported actions in Russia. The new script uses a description only when it
explicitly mentions a joint venture, distributor, license, or franchise.
Every resulting entry-mode label remains marked for manual review.

## Preliminary transaction result

The Bloomberg sample contains 145 transactions with a usable percentage
interest. It separates them by the interest offered in the transaction:

| Interest offered | Transactions | Completed | Median days from 24 February 2022 to completion | Value disclosed |
|---|---:|---:|---:|---:|
| At least 95 percent | 114 | 57 (50.0%) | 476 | 25 (21.9%) |
| More than 0 and less than 95 percent | 31 | 22 (71.0%) | 532.5 | 8 (25.8%) |

The difference in completion rates is 21.0 percentage points. A two-sided
exact test gives a p-value of 0.043. The shared-interest transactions were more
likely to be recorded as completed, but they did not complete sooner.

This is not an estimate of the effect of entry mode. The percentage offered is
measured after the rupture, the sample is limited to reported transactions, and
the full-interest group includes asset sales as well as sales of subsidiaries.
The result is included to document what the new Bloomberg file can support
before historical entry modes are collected.

## Files added for this study

```text
docs/formal_model.md
    Formal model of entry choice and expected loss after a rupture.

proposal_management_science.txt
    Proposal based on the ideal data rather than the current incomplete files.

scripts/13_entry_mode_baseline.py
    Builds the review file and the Bloomberg transaction baseline.

data/analysis/entry_mode_review_queue.csv
    One row per Yale firm with provisional evidence and a manual-review flag.

data/analysis/bloomberg_post_rupture_transactions.csv
    Clean transaction sample used for the preliminary comparison.

data/analysis/results_13_entry_mode_baseline.txt
    Plain-text baseline results and limitations.
```

## Reproduction

The new baseline uses only the Python standard library:

```bash
python3 scripts/13_entry_mode_baseline.py
```

The earlier scripts and data remain in the branch as source material. Their
patent and knowledge-transfer results answer a different question and are not
evidence for the entry-mode study.

## Data required for the main study

1. Historical ownership immediately before the invasion, including all direct
   and indirect shareholders and voting stakes.
2. A verified list of pre-invasion distributor, license, and franchise
   agreements.
3. Russian registry records showing the date on which legal ownership changed
   or the entity was liquidated.
4. Firm disclosures that identify write-downs, impairment charges, sale
   proceeds, retained claims, and guarantees related to Russia.
5. Transaction values converted at the exchange rate on the relevant date.
6. Pre-invasion assets, revenue, employment, and profitability for each Russian
   operation.

The first empirical objective is a verified firm-by-entry-mode file. Outcome
comparisons should not be treated as entry-mode estimates until that file is
complete.
