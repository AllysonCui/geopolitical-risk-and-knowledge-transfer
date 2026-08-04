# Hostage Capital: Exit Choices Under Geopolitical Coercion

An empirical study of the 1,048 Western multinationals that withdrew from Russia after the February 2022 invasion of Ukraine. The central finding: **the assets a firm can salvage in a geopolitical crisis are the same assets a hostile state can hold hostage.** Firms with sellable, codified knowledge (patents, brands, plants) attracted buyers — but were the least able to exit cleanly, because selling runs through a gate the state controls. Firms whose value lived in their people had nothing to sell — and walked away free.

---

## 1. The research question

When Russia invaded Ukraine, over a thousand Western firms faced the same decision at the same moment: what to do with their Russian operations. This is a rare natural experiment. Normally, firms divest at different times for different reasons, and it is hard to separate the firm's choice from its circumstances. Here, one political shock hit everyone simultaneously — so differences in *how* firms responded can be traced to differences in *what kind of firm they are*.

The question is not whether firms exit under geopolitical pressure (most announced they would). It is: **what determines the exit each firm can actually execute?** Some sold their Russian business. Some abandoned it and wrote it off. Some liquidated their legal entities. Some announced exits they never completed. We want to know what sorts firms into these outcomes.

## 2. The theory: exit as a choice among three options

Think of a firm holding a Russian subsidiary in March 2022 as holding a portfolio of three options. It will pick whichever has the highest payoff:

| Option | Payoff | When it's best |
|---|---|---|
| **Sell** | Salvage price − transaction costs − exit tax − mandated discount | Only works if a **buyer exists** — someone who can run the operation without the parent |
| **Walk away** | Zero salvage + a write-off, but immediate and needs nobody's permission | Best when the value is **tacit** — embedded in people who leave with the firm |
| **Dissolve** | Liquidate the legal entity; cheap and administrative | Best for **asset shells** — entities with no workforce, no going concern |

This is a standard *discrete choice* setup from microeconomics. If you add a random shock to each option's payoff (capturing everything we can't observe), the probability of each choice follows a **multinomial logit** — the workhorse model of McFadden's random-utility framework, the same tool used to model consumers choosing among products or commuters choosing travel modes. That is what we estimate.

### Why knowledge type determines the payoffs

The key economic idea is **appropriability** — can someone else capture the value of an asset?

- **Codified knowledge** (patents, licensed technology, brand rights, physical plants) survives the parent company's departure. A local buyer can keep running the factory or licensing the brand. So codified assets have a salvage price — but that also means abandoning them hands them to whoever takes over. Codified-knowledge firms *must* sell to recover anything.
- **Tacit knowledge** (consultant expertise, account relationships, organizational routines) leaves with the people. There is nothing a buyer can buy. So tacit-knowledge firms have nothing to sell — but also nothing to lose by walking away. Their exit is fast, clean, and unilateral.

### The coercion mechanism

Here is the twist that makes this a study of geopolitical *coercion* rather than ordinary divestiture: **only the sell option runs through a gate the state controls.** Every sale by an "unfriendly-country" owner required Russian government commission approval, an exit levy, and a mandated valuation discount. The state cannot tax a walk-away — there is no transaction to approve. It can and did tax the sale. And it escalated:

- **2022**: approval commission erected; ~50% mandatory discount becomes standard
- **March 2023**: exit levy of ~10% of deal value formalized
- **July 2023**: Danone's Russian business and Carlsberg's Baltika seized (placed under "external administration") — both firms were mid-negotiation to sell
- **October 2024**: levy raised to ~35%, discount deepened to ~60%

So the firms with the most salvageable value faced the most obstructed exit path — *hostage capital*. This also answers a broader question about state backlash: when the private sector acts collectively against a state's interests, the state reprices the options it controls.

## 3. Data sources

The study merges five datasets. Each row of the final analysis file is one firm.

### 3.1 Yale CELI tracker (the backbone — who exited, and how)

- **What**: Yale's School of Management tracked ~1,589 Western firms' responses to the invasion, grading each A (clean break) through F (business as usual), with a text description of each firm's action.
- **Files**: 12 snapshot CSVs in `data/` (e.g. `250521.csv` = May 21, 2025).
- **What we use**: the latest grade, the firm's home country and industry, and an action classification we parse from the text (sold / suspended / other). Our sample is the 1,048 Grade A and B firms — the committed exiters.
- **Concerns**: grades are editorial judgments, not audited outcomes. The action text is inconsistently worded across firms and snapshots.

### 3.2 Bureau van Dijk Orbis (what each firm owned in Russia)

- **What**: financial data on 6,405 Russian subsidiaries whose global ultimate owner is in a Western country: total assets, employees, employee costs, equity, sector code (NACE), incorporation date, and active/inactive status.
- **Files**: `data/orbis_export_part1.xlsx`, `part2.xlsx`, exported from the Orbis database per the spec in `scripts/03_orbis_query_spec.md`.
- **What we use**: employee intensity (employees / total assets) for the tacitness dimension; subsidiary size, age, and count as controls; the inactive flag to detect dissolved entities.
- **Concerns**: Russian financial filings lag; we cascade back from 2023 to the most recent available year. Ruble-to-dollar conversion during the 2022 crash may distort values. Personnel *costs* (the ideal tacitness measure) were too sparsely populated, so we use employee counts instead.

### 3.3 Lens.org patents (the codified-knowledge dimension)

- **What**: total patent count for each parent firm, collected via the free Lens.org API (`scripts/02_collect_patents_lens.py`).
- **File**: `data/collected/patents_by_firm.csv`.
- **What we use**: patent intensity = patents / Russian subsidiary assets, the appropriability dimension.
- **Concerns**: name-matching errors for short names; patent stock is a lifetime measure, so a firm with old patents but no current R&D still scores high.

### 3.4 Bloomberg deal exports (did a buyer show up, and at what price)

- **What**: two exports from the Bloomberg terminal — the original M&A screen (790 deals) and an asset-sale (AST) screen (290 deals) covering Russian targets sold by Western sellers.
- **Files**: `data/bloomberg_ma_deals.csv`, `data/bloomberg_ast_deals.csv`.
- **What we use**: after filtering to post-invasion deals and fuzzy-matching seller names to Yale firms, we get 204 matched deals across 130 firms, 40 with disclosed prices. This gives us the key outcome "a buyer materialized" and, where disclosed, the salvage price.
- **Concerns**: most deal values are undisclosed (Russian exit deals were often nominal — Renault sold for one ruble). The two exports overlap; we de-duplicate on (firm, target, date).

### 3.5 EU sanctions packages (the policy shock)

- **What**: the nine EU sanctions packages of 2022, mapped to the economic sectors (NACE codes) they targeted.
- **File**: `data/collected/eu_sanctions_2022.csv` plus a mapping table in `scripts/08_build_analysis_dataset.py`.
- **What we use**: `sanctions_exposure` = how many packages hit the firm's sector (0–8). About 101 of our 899 matched firms are in sanctioned sectors.
- **Concerns**: this is sector-level, not firm-level — a blunt measure that limits statistical power.

## 4. Variable construction

### The two knowledge dimensions

For each firm we compute two percentile ranks (a firm's position from 0 to 1 among all sample firms):

- **emp_pctile** — rank on employees per dollar of subsidiary assets. High = labor-heavy, operational, tacit.
- **pat_pctile** — rank on parent patents per dollar of subsidiary assets. High = IP-dense, codified, appropriable.

We use percentile ranks rather than raw values because both distributions are extremely skewed (a few firms have thousands of patents; most have none). Ranks make firms comparable without letting outliers dominate.

### The composite index α

The earlier phase of the project combined the two into one **replicability index**: α = rescale(emp_pctile − pat_pctile) to [0,1]. High α = easy-to-replicate operational business; low α = hard-to-replicate IP-embedded business. The current phase mostly enters the two components separately — that is what lets us see that the two dimensions do *different work* (patents drive buyer arrival; employees drive walk-away and dissolution) — but α is retained for continuity and for the sanctions split.

### Outcomes

| Variable | Meaning |
|---|---|
| `grade == A` | Clean exit achieved (vs. Grade B partial withdrawal) |
| `action_type` | sold / suspended / other — the exit mode |
| `has_deal` | A matched Bloomberg deal exists — a buyer materialized |
| `y_sub_inactive` | At least one Russian subsidiary was dissolved |

### Controls

Subsidiary size (log total assets), years operating in Russia, and number of Russian subsidiaries — the standard suspects that could confound a knowledge-structure story (bigger, older, more entangled operations are harder to exit regardless of knowledge type).

## 5. Empirical strategy

Three estimators, all standard for binary/categorical outcomes:

- **Linear probability model (LPM)**: OLS with a 0/1 outcome. Coefficients read directly as percentage-point changes. We use robust (HC1) standard errors.
- **Logit**: the nonlinear cousin, better behaved near probabilities of 0 or 1. We report it alongside every LPM as a check.
- **Multinomial logit (MNLogit)**: for the three-way exit mode choice — the direct empirical counterpart of the random-utility model in Section 2.

Each hypothesis is a comparative static of the theory: a statement about which payoff rises when a knowledge dimension changes, and therefore which choice becomes more likely.

## 6. Findings

**H1 — Market formation.** P(a buyer materializes) rises steeply in patent intensity (logit 2.55, p < 0.0001) and is flat in employee intensity (p = 0.91). Across patent quintiles, the share of firms with a matched deal goes from 7% to 24%. Buyers pay for what survives the parent's departure.

**H2 — The hostage gradient.** Across the same patent quintiles, the share achieving a *clean exit* falls from 78% to 42% (patent percentile −0.36, p < 0.0001). Read together with H1: the firms whose assets attract buyers are the firms whose exits stall. The knowledge that creates the market blocks the door. Conditional on a committed exit, the composite index confirms the mode sorting — replicable operations walk away, IP-heavy operations sell (α = −0.20, p = 0.087).

**H3 — Shell liquidation.** Subsidiary dissolution is overwhelmingly a low-employment phenomenon (logit −6.94, p < 0.0001) and a small-entity phenomenon (p = 0.0007). The dissolution rate falls from 8.5% in the lowest employee-intensity tercile to 0.8% in the highest — an 11-to-1 gradient. A workforce constitutes a going concern: something to transfer, not something to liquidate.

**H4 — Sanctions amplification.** In EU-sanctioned sectors the knowledge gradient on clean exit is roughly 4x stronger (model R² of 12.5% vs 2.2% outside). Sanctions raise the cost of staying and shrink the legal buyer set, pushing firms harder toward whichever exit their knowledge structure permits.

**Descriptive — deal values over time.** With only 40 disclosed prices, no significant time trend is detectable, but the policy record (levy 10% → 35%, discount 50% → 60%) implies later sellers kept less. Testing this properly needs exit announcement dates (see roadmap).

## 7. What it means for firms

Three practical layers, generalizing beyond Russia:

1. **Audit.** For every at-risk jurisdiction, score each entity on appropriability (could a local buyer run it without us?) and embeddedness (does the value leave with our people?). That tells you today which exit you could actually execute.
2. **Structure.** Your position in the typology is a design choice. Holding IP offshore and licensing it in converts a hostage asset into a terminable contract. Pre-negotiated buyback options (as Renault and McDonald's improvised) convert ownership into an option before the state converts it into a hostage.
3. **Timing.** Because the state reprices the sale gate adversarially, the sell option decays. If your audit says "we would need to sell," the first months of a rupture are the only real window.

## 8. Reproducing the analysis

Run the scripts in order (each consumes prior outputs):

```
01_parse_yale_tracker.py       Yale CSVs --> firms_exit_panel.csv, firms_exiters.csv
02_collect_patents_lens.py     firms_exiters.csv --> patents_by_firm.csv  (needs API token)
03_orbis_query_spec.md         (manual Orbis download instructions, not a script)
05_parse_orbis_export.py       orbis_export_part*.xlsx --> orbis_subsidiaries.csv
06_merge_orbis_yale.py         orbis_subsidiaries + firms_exiters --> merged_orbis_yale.csv
07_merge_bloomberg_deals.py    bloomberg_ma_deals + bloomberg_ast_deals --> exit_deals_matched.csv
08_build_analysis_dataset.py   all collected data --> regression_sample.csv
09_run_regressions.py          regression_sample.csv --> regression_results.txt   (earlier single-index phase)
10_run_choice_model.py         regression_sample.csv --> choice_model_results.txt (main analysis)
```

Dependencies: `pip install openpyxl rapidfuzz numpy statsmodels`

The firm-name merges (Orbis→Yale, Bloomberg→Yale) use fuzzy string matching (`rapidfuzz`, threshold 70–72, with manual overrides for known problem names like IKEA and H&M). Orbis match rate: 899 of 1,048 exiters (86%); 709 have both knowledge components plus controls — that is the main estimation sample.

## 9. File structure

```
data/
  *.csv                          Yale CELI tracker snapshots (raw)
  bloomberg_ma_deals.csv         Bloomberg M&A/INV export (raw)
  bloomberg_ast_deals.csv        Bloomberg asset-sale (AST) export (raw)
  orbis_export_part1.xlsx        Orbis subsidiary export (raw)
  orbis_export_part2.xlsx
  collected/                     Intermediate processed data
    firms_exit_panel.csv           1,589 firms, all grades
    firms_exiters.csv              1,048 Grade A+B firms
    orbis_subsidiaries.csv         6,405 Russian subsidiaries
    merged_orbis_yale.csv          899 matched firm-level records
    exit_deals_matched.csv         204 matched post-invasion deals
    patents_by_firm.csv            1,048 firms with patent counts
    eu_sanctions_2022.csv          9 sanctions packages
  analysis/                      Final outputs
    regression_sample.csv          899-row regression-ready dataset
    choice_model_results.txt       Discrete-choice results (main)
    regression_results.txt         Earlier single-index results
    sample_stats.txt               Summary statistics

scripts/                         Pipeline (see Section 8)
```

## 10. Limitations and roadmap

1. **Payoffs are inferred from choices, not measured.** Only 40 deals have disclosed prices, and write-off amounts are absent entirely. *Next data*: Bloomberg income-statement pull of impairments/write-downs (FY2019–FY2024) for the ~500 listed parents — this converts the model from revealed-preference to measured-payoff.
2. **No timing dimension yet.** The option-decay claim (Layer 3) rests on the policy record, not firm-level evidence. *Next data*: exit announcement dates, enabling a duration model of time-to-exit against the escalating toll.
3. **Sanctions are sector-level.** 58 sanctioned-sector firms in the estimation sample is thin. Firm-level OFAC/EU designations would sharpen H4.
4. **Employee intensity proxies tacitness imperfectly.** Personnel costs / total costs (the delegation measure in the original design) was too sparse in Orbis; employee counts per asset dollar are the workable substitute.
5. **Cross-sectional identification.** Everything is correlational sorting after one shock. The simultaneity of the shock helps, but unobserved firm traits (e.g. risk culture) could correlate with both knowledge structure and exit behavior.

## 11. Related visualization

The full narrative with interactive figures is published as an artifact: *Hostage Capital: Exit Choices Under Geopolitical Coercion* — the 2×2 typology, the twin gradients (H1/H2), the dissolution gradient (H3), sanctions amplification (H4), the state's countermove timeline, and the three-layer decision framework.
