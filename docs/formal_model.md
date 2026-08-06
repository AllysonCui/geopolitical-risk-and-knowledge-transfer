# Exit as a fire-sale problem with inalienable human capital

A single formal model anchors all three empirical specifications; each
sub-question (Q1–Q3) is a comparative static of the model. The framing is a
divestment version of the Shleifer–Vishny (1992) fire-sale model combined
with Hart–Moore (1994) inalienability of human capital. *(Citation caveat:
verify the exact references before submission — Shleifer & Vishny, "Liquidation
Values and Debt Capacity: A Market Equilibrium Approach," J. Finance 1992;
Hart & Moore, "A Theory of Debt Based on the Inalienability of Human
Capital," QJE 1994.)*

## Setup

A parent forced to exit a hostile market chooses between **selling** the
subsidiary at price $P$ or **abandoning** it at salvage value $S \approx 0$
minus wind-down costs $w$. The buyer's willingness to pay is

$$P = V \cdot \theta(\alpha) - \tau$$

| Object | Meaning |
|--------|---------|
| $V$ | going-concern value of the subsidiary |
| $\theta(\alpha) \in [0,1]$ | fraction of value that survives the transfer |
| $\tau$ | transaction cost of the sale |
| $S - w$ | payoff to walking away (salvage minus wind-down cost) |

**Core assumption.** Codified knowledge (patents, documented processes) is
*alienable* and transfers with the legal entity; tacit knowledge embodied in
employees is *inalienable* — workers can quit, and their firm-specific
complementarities with the departing parent are destroyed. Hence $\theta$ is
**increasing in codified-knowledge intensity** and **decreasing in
tacit/human-capital intensity**.

The firm sells iff

$$V \cdot \theta(\alpha) - \tau \;>\; S - w.$$

Note the recasting of the project's original $\alpha$: it is now a
**codifiability** parameter, not a symmetric two-factor index. This makes the
earlier decomposition finding — patent percentile does all the work in the
exit-mode margin, employee percentile does little — a *feature* of the model
rather than an anomaly: the sale margin prices what transfers, and what
transfers is the codified component.

## Predictions and the specification each one pins down

**Prediction 1 (exit mode).** Pr(sell | exit) is increasing in patent
intensity and decreasing in labor intensity.
→ Tested in `scripts/10_selection_exit_mode.py`: Heckman-style two-stage on
the full population of foreign subsidiaries (selection into exit, then mode),
with a consumer-facing (B2C) exclusion restriction — boycott pressure moves
*whether* to exit, not the mechanics of the asset transfer.

**Prediction 2 (sanctions amplification).** Sanctions raise $\tau$ (shrunken
buyer pool, licensing requirements, exit-tax discounts). A higher $\tau$
raises the $\theta$ threshold a sale must clear, so the sorting on
codifiability **steepens**: the effect is an interaction ($\beta_3 > 0$ on
PatInt × SancExp), *not* a subsample R² comparison. If the buyer-pool channel
dominates for technology firms specifically, $\beta_3 < 0$; the model signs
both channels and the data decide.
→ Tested in `scripts/11_sanctions_amplification.py`: pooled interaction plus
a cause-specific competing-risks Cox with time-varying sector exposure built
from the staggered 2022 EU package rollout — identification from *when* a
sector became exposed, conditional on sector effects.

**Prediction 3 (home institutions).** Home institutions shift both sides of
the inequality:
* Sanctions-coalition alignment raises $\tau$ (restricts permissible buyers,
  exit-tax exposure) → dampens selling for given $\theta$;
* Stakeholder-pressure institutions (rule of law, disclosure regimes,
  common-law investor scrutiny) raise the reputational/legal cost of walking
  away — a larger $w$ → favors selling.

The two institutional channels therefore predict **opposite-signed
interactions** with codifiability, which is the testable contrast.
→ Tested in `scripts/12_institutional_moderators.py`: country fixed effects
absorb institution levels; only the PatInt × institution interactions are
identified — exactly what the question asks.

## Mapping model objects to data

| Model object | Empirical proxy | Source |
|--------------|-----------------|--------|
| codified-knowledge intensity (raises $\theta$) | parent patent-stock percentile (`pat_pctile`, within-sector variant available) | Lens.org |
| tacit/human-capital intensity (lowers $\theta$) | subsidiary employees/assets percentile (`lab_pctile`) | Orbis |
| $\tau$ shifters | EU package exposure of the NACE sector, time-varying | EU package dates + NACE map |
| $S - w$ shifters | home-country coalition status, rule of law, legal origin | Decree 430-r list, WGI 2021, LLSV |
| seizure (involuntary transfer, outside the choice set) | `exit_mode = seized` — third competing risk, dropped from the sell/walk margin | Yale action text + manual overrides |

## Measurement rules implied by the model

1. Patent stock should be measured at the **global ultimate owner** over a
   **pre-invasion window (2017–2021 grants)** and scaled by parent size —
   the codified knowledge at stake is the parent's, and vintage must be
   pre-determined. (Current build: lifetime stock, unscaled; see README.)
2. Labor intensity numerator and denominator should come from the **same
   2019–2021 window** of the Russian subsidiary's accounts.
3. Asset tangibility (PP&E/assets) is the obvious confounder for
   "sellability" and belongs in $X_i$ (pending Orbis re-export; see
   `scripts/03_orbis_query_spec.md`).
4. Because the sale threshold is a function of ranks, coefficients are
   reported as **marginal effects at percentiles**; the quadratic-in-α
   specification is retained in the legacy script with the linear model as a
   nested restriction.
