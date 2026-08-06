# Exit as a fire-sale problem with inalienable human capital

A single formal model anchors all three empirical specifications; each
sub-question (Q1–Q3) is a comparative static of one cutoff. The framing is a
divestment version of the Shleifer–Vishny (1992) fire-sale model combined
with Hart–Moore (1994) inalienability of human capital. *(Citation caveat:
verify the exact references before submission — Shleifer & Vishny, "Liquidation
Values and Debt Capacity: A Market Equilibrium Approach," J. Finance 1992;
Hart & Moore, "A Theory of Debt Based on the Inalienability of Human
Capital," QJE 1994.)*

## Setup

A parent forced to exit a hostile market chooses between **selling** the
subsidiary or **abandoning** it. Salvage value is negligible (S = 0, imposed
throughout) and abandonment incurs wind-down cost $w$. A buyer pays

$$P = V \cdot \theta(k, h) - \tau$$

| Object | Meaning |
|--------|---------|
| $V$ | going-concern value of the subsidiary |
| $k$ | codified-knowledge intensity (patents, documented processes) |
| $h$ | tacit/human-capital intensity (knowledge embodied in employees) |
| $\theta(k,h) \in [0,1]$ | fraction of value surviving the transfer: $\partial\theta/\partial k > 0$, $\partial\theta/\partial h < 0$ |
| $\tau$ | transaction cost of the sale |
| $w$ | wind-down cost of walking away |

**Core assumption.** Codified knowledge is *alienable* and transfers with the
legal entity; tacit knowledge embodied in employees is *inalienable* —
workers can quit, and their firm-specific complementarities with the
departing parent are destroyed. Hence $\theta$ rises in $k$ and falls in $h$.

The model is parameterized directly by $(k, h)$ — there is no composite
index. The project's earlier symmetric composite α is retired (it survives
only in the legacy script 09): the decomposition showed the patent component
does the work in the exit-mode margin, which is what $\theta(k,h)$ with
asymmetric partials predicts, and the empirical proxies (`pat_pctile`,
`lab_pctile`) enter scripts 10–12 separately, exactly as the model is
written.

## The cutoff

The firm sells iff $V\theta(k,h) - \tau > -w$, i.e. iff

$$\theta(k, h) \;>\; \theta^* \equiv \frac{\tau - w}{V}.$$

Everything in the paper is a movement of $\theta(k,h)$ or of $\theta^*$.
(The empirically relevant case is $\tau > w$ — a majority of completed exits
walk away, so the sale threshold binds.)

**Heterogeneity.** Firms differ in the private value of retaining the
subsidiary, $V_i$, which is distributed according to a continuous log-concave
distribution $F(\cdot)$. This heterogeneity implies that the deterministic
cutoff translates into a probabilistic sell/no-sell decision, yielding the
binary-choice specification estimated in the empirical analysis. Concretely,
firm $i$ sells iff $V_i > V^*(k,h;\tau,w) \equiv (\tau - w)/\theta(k,h)$, so

$$\Pr(\text{sell}) = 1 - F\!\left(V^*(k,h;\tau,w)\right),$$

and the probit in `scripts/10_selection_exit_mode.py` is the model's
likelihood, not an approximation bolted on afterwards.

## Predictions

**Prediction 1 (exit mode — slope of θ).**
$V^*_k = -(\tau-w)\,\theta_k/\theta^2 < 0$ and $V^*_h > 0$, so
$\partial\Pr(\text{sell})/\partial k > 0$ and
$\partial\Pr(\text{sell})/\partial h < 0$: patent-intensive firms sell,
labor-intensive firms walk away. Unambiguous — no distributional condition
needed.
→ `scripts/10_selection_exit_mode.py` (Heckman-style two-stage on the full
population; B2C exclusion restriction: boycott pressure moves *whether* to
exit, not the mechanics of the asset transfer).

**Prediction 2 (sanctions raise θ\*).** Sanctions raise $\tau$ (shrunken
buyer pool, licensing requirements, exit-tax discounts), so $\theta^*$ rises
and sales fall — a level effect, unambiguous. The *steepening* claim is a
cross-partial and is derivable rather than asserted:

$$\frac{\partial^2 \Pr(\text{sell})}{\partial \tau\,\partial k}
= -f'(V^*)\,V^*_\tau V^*_k \;-\; f(V^*)\,V^*_{k\tau},
\qquad V^*_\tau > 0,\; V^*_k < 0,\; V^*_{k\tau} = -\theta_k/\theta^2 < 0.$$

The second term is positive always; the first has the sign of $f'(V^*)$, so
the interaction is positive whenever the marginal firm sits at or below the
mode of $F$, and log-concavity bounds how negative the first term can be
beyond it. If instead sanctions destroy $V$ itself for technology assets
(the buyer-pool channel), the interaction flips sign. Both channels are
signed by the model; the data decide.
→ `scripts/11_sanctions_amplification.py` (pooled PatInt × SancExp
interaction — not a subsample R² comparison — plus a cause-specific
competing-risks Cox with time-varying exposure from the staggered 2022 EU
package rollout).

**Prediction 3 (home institutions move θ\* in opposite directions).**
Coalition alignment raises $\tau$ (buyer restrictions, exit-tax exposure):
$\theta^*\uparrow$, less selling. Stakeholder-pressure institutions raise
$w$ (reputational and legal cost of walking away): $\theta^*\downarrow$,
more selling. One cutoff, two opposite-signed shifts — that is the testable
contrast.
→ `scripts/12_institutional_moderators.py` (country fixed effects absorb
institution levels; only the $k \times$ institution interactions are
identified — exactly what the question asks).

## Mapping model objects to data

| Model object | Empirical proxy | Source |
|--------------|-----------------|--------|
| $k$ — codified-knowledge intensity | parent patent-stock percentile (`pat_pctile`, within-sector variant available) | Lens.org |
| $h$ — tacit/human-capital intensity | subsidiary employees/assets percentile (`lab_pctile`) | Orbis |
| $\tau$ shifters | EU package exposure of the NACE sector, time-varying | EU package dates + NACE map |
| $\tau$ and $w$ shifters (home institutions) | coalition status, rule of law, legal origin | Decree 430-r list, WGI (DataBank RL.EST), LLSV |
| seizure (involuntary transfer, outside the choice set) | `exit_mode = seized` — third competing risk, dropped from the sell/walk margin | Yale action text + manual overrides |

## Measurement rules implied by the model

1. $k$ should be measured at the **global ultimate owner** over a
   **pre-invasion window (2017–2021 grants)** and scaled by parent size —
   the codified knowledge at stake is the parent's, and vintage must be
   pre-determined. (Current build: lifetime stock, unscaled; see README.)
2. The $h$ numerator and denominator should come from the **same 2019–2021
   window** of the Russian subsidiary's accounts.
3. Asset tangibility (PP&E/assets) is the obvious confounder for
   "sellability" and belongs in $X_i$ (pending Orbis re-export; see
   `scripts/03_orbis_query_spec.md`).
4. Because $k$ and $h$ enter as ranks, coefficients are reported as
   **marginal effects at percentiles**. The quadratic-in-α specification
   survives only in the legacy script 09, with the linear model as a nested
   restriction.
