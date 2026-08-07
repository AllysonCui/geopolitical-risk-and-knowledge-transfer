# Knowledge Structure and the Completion of Corporate Exit from Russia

## The question in plain language

After Russia invaded Ukraine in February 2022, many foreign companies said
that they would reduce, suspend, or end their Russian operations. An
announcement did not necessarily produce a completed exit. Some companies
found a buyer, some closed their local operations, some remained in an
unresolved state for months or years, and a small number lost control through
state intervention.

This project asks:

> Why do some foreign companies complete their departure from Russia while
> others remain unresolved, and does the type of knowledge on which the
> Russian business depends help explain the difference?

The proposed mechanism is straightforward. A company can wait for a suitable
buyer, but waiting is costly. Patents, licenses, and documented processes may
preserve value for a future buyer, making continued waiting more attractive.
Businesses that depend heavily on employees and day-to-day operations may be
more expensive to hold in suspension because payroll and other operating costs
continue. These arguments generate predictions about how long companies wait
and which outcome eventually occurs. They do not assume that patents cause a
sale or that employee-intensive companies inevitably close.

## The outcomes

The repeated Yale CELI tracker files allow the project to follow changes in a
company's reported position between December 2022 and May 2025. The proposed
analysis uses five states:

1. **Still operating:** the company has not announced a full departure.
2. **Exit announced but unresolved:** the company has reduced or suspended
   activity or announced an intention to leave, but the available record does
   not show a completed sale or closure.
3. **Sale completed:** control of the Russian operation is reported to have
   transferred to a buyer.
4. **Closure completed:** the Russian operation is reported to have closed or
   been liquidated without a sale.
5. **State-imposed loss of control:** the Russian state seized or placed the
   operation under temporary administration. This is kept separate because it
   is not a voluntary corporate decision.

These labels describe what the current Yale text and Bloomberg records appear
to show. They are not yet a legal verification of ownership. Ambiguous cases
should remain unresolved rather than being forced into a completed outcome.

## The model

A company with an unresolved exit pays a carrying cost while it waits. A
suitable buyer may arrive. The value of waiting depends on four quantities:

- The value a buyer could preserve after taking control.
- The cost of completing the transaction.
- The cost of keeping the subsidiary in an unresolved state.
- The expected time until an eligible buyer and any required approvals become
  available.

The model allows these conditions to change over time. For example, payroll
costs may continue, the subsidiary's value may deteriorate, sanctions may
reduce the buyer pool, and Russian approval requirements may delay a
transaction. At each date, the parent compares the value of continuing to
wait with the cost of closing the operation. This creates a genuine decision
about when to stop waiting.

The complete mathematical skeleton and its assumptions are in
`docs/formal_model.md`.

## Predictions to take to the data

The revised model makes three primary predictions:

1. **Transferable assets and closure.** If patents and other codified assets
   preserve the value of a future transaction, companies with more of these
   assets should be slower to close without a sale.
2. **Human-capital dependence and closure.** If employee-intensive operations
   are more expensive to hold during suspension, they should close sooner,
   all else equal.
3. **Buyer availability and sale timing.** Sanctions, mandatory discounts, and
   approval requirements may delay completed sales by reducing the number of
   eligible buyers or lowering acceptable transaction values.

The present results are consistent with the first prediction: higher parent
patent rank is associated with a lower rate of closure or another completed
exit without a sale. Patent rank is not detectably associated with the rate
of completed sales. Labor intensity has the predicted positive association
with non-sale completion, but the estimate is imprecise. These are preliminary
associations, not causal estimates.

## How the concepts are measured

| Concept | Current measure | Important limitation |
|---|---|---|
| Transferable codified assets | Parent patent-stock percentile | Does not identify patents owned by or licensed to the Russian subsidiary |
| Cost of maintaining operations | Subsidiary employees divided by total assets | Labor intensity is not a direct measure of payroll during suspension |
| Exit status and timing | Changes across Yale tracker snapshots and action descriptions | Announcements may not establish legal completion; the first snapshot already contains many completed cases |
| Completed sale | Yale action text supplemented by Bloomberg deal records | Many transaction values and exact completion dates are missing |
| Sanctions pressure | Number and timing of EU packages covering the firm's sector | Sector exposure is broad and ends with the mapped 2022 packages |

## Current evidence

- The merged dataset contains 1,394 matched foreign parents from the Yale and
  Orbis files.
- Among 362 companies currently classified as completed exits with patent
  data, the reported sale share rises from 28% in the lowest patent tercile to
  49% in the highest tercile.
- In the current duration analysis, moving from the bottom to the top of the
  parent patent ranking is associated with an approximately 69% lower rate of
  completing an exit without a sale (p < 0.001).
- The estimated relationship between patent rank and the rate of completed
  sales is small relative to its uncertainty (p = 0.54).
- Moving from the bottom to the top of the labor-intensity ranking is
  associated with an estimated 32% higher rate of completion without a sale,
  but the estimate is too imprecise to support a firm conclusion (p = 0.30).
- The current sanctions interaction is close to zero.

The duration estimates currently use only companies with patent data. Because
the existing patent file largely covers companies that announced an exit, the
risk set is selected. A full-panel pre-invasion patent measure is required
before these estimates can support the revised research question.

## Analysis plan

### Primary analysis

Follow each company from one Yale snapshot to the next and estimate how its
current state predicts the next observed transition:

- Still operating to exit announced.
- Exit announced but unresolved to completed sale.
- Exit announced but unresolved to completed closure.
- Exit announced but unresolved to state-imposed loss of control.

The main quantities of interest are the time spent unresolved and the
probability of each eventual outcome. Statistical details belong in the
methods section and scripts; the economic interpretation should be reported
in predicted probabilities and expected waiting times.

### Existing analyses retained for comparison

- `scripts/09_run_regressions.py`: earlier cross-sectional models.
- `scripts/10_selection_exit_mode.py`: earlier two-stage exit-mode model.
- `scripts/11_sanctions_amplification.py`: current duration estimates for
  completed sale and completed non-sale exit.
- `scripts/12_institutional_moderators.py`: exploratory home-country results.

These scripts are useful diagnostics, but scripts 10 and 11 do not yet
implement the revised state-transition model.

## Data sources

- **Yale CELI tracker:** repeated company grades and descriptions from
  December 2022 through May 2025.
- **Orbis:** Russian subsidiary assets, employees, sector, age, and ownership
  structure.
- **Lens.org:** parent patent portfolios. The current file must be replaced by
  a full-panel, pre-invasion pull.
- **Bloomberg M&A:** reported sales and transaction dates where available.
- **EU sanctions packages:** sector coverage and adoption dates.
- **Home-country institutions:** coalition membership, rule of law, and legal
  origin; currently exploratory rather than central.

## Work still required

1. Translate every Yale snapshot into the five states above, retaining an
   explicit `ambiguous` flag.
2. Re-pull 2017–2021 patents for the full population, including companies that
   never announced an exit.
3. Add PP&E/assets, intangible assets, profitability, and parent size to the
   Orbis export.
4. Check reported completed sales and closures against current ownership and
   liquidation records where available.
5. Replace the current selected duration analysis with a full-risk-set
   state-transition model.
6. Treat sanctions moderation and home-country interactions as secondary
   until their measurement and statistical power improve.

## Reproducing the current build

```text
01_parse_yale_tracker.py       combine Yale snapshots and construct timing
02_collect_patents_lens.py     collect pre-invasion patents for the full panel
03_orbis_query_spec.md         fields required for the next Orbis download
05_parse_orbis_export.py       combine and clean Orbis exports
06_merge_orbis_yale.py         match Russian subsidiaries to Yale companies
07_merge_bloomberg_deals.py    match reported transactions
08_build_analysis_dataset.py   construct the analysis file
09_run_regressions.py          run legacy cross-sectional checks
10_selection_exit_mode.py      run the earlier two-stage model
11_sanctions_amplification.py  run the current duration models
12_institutional_moderators.py run exploratory country interactions
```

Dependencies:

```bash
pip install openpyxl rapidfuzz numpy scipy statsmodels
```
