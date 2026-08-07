# A model of subsidiary sale when some assets are difficult to transfer

The model explains when a parent company that must leave a host country can
sell its subsidiary rather than exit without a sale. Its central idea is
that a buyer will pay more when a larger share of the subsidiary's value can
be retained after ownership changes. The framework combines the fire-sale
logic of Shleifer and Vishny (1992), in which forced sales can occur at
discounted prices, with Hart and Moore's (1994) insight that human capital
cannot be owned or transferred in the same way as physical or legal assets.
The model organizes the three empirical questions, but it does not establish
that the available variables measure its theoretical concepts accurately.

## Setup

A parent that must exit chooses between **selling** the subsidiary and
**exiting without an arm's-length sale**. The second category may include
closure, suspension, or abandonment; it excludes state seizure, which is not
a voluntary exit choice. For tractability, the model normalizes the salvage
value of a non-sale exit to zero and denotes its wind-down cost by $w$. A
buyer pays

$$P = V \cdot \theta(k, h) - \tau$$

| Object | Meaning |
|--------|---------|
| $V$ | going-concern value of the subsidiary |
| $k$ | codified-knowledge intensity (patents, documented processes) |
| $h$ | tacit/human-capital intensity (knowledge embodied in employees) |
| $\theta(k,h) \in [0,1]$ | fraction of value surviving the transfer: $\partial\theta/\partial k > 0$, $\partial\theta/\partial h < 0$ |
| $\tau$ | transaction cost of the sale |
| $w$ | cost of closing or otherwise exiting without a sale |

**Core assumption.** Codified assets such as patents, licenses, and documented
processes can in principle be conveyed by contract. Knowledge embodied in
employees, relationships, and firm-specific routines is less reliably
transferable because employees may leave and organizational complementarities
may weaken after the parent departs. A buyer can therefore capture a larger
share of going-concern value when transferable assets are more important and
a smaller share when value depends more heavily on non-transferable human
capital. Formally, $\theta$ rises in $k$ and falls in $h$. This assumption
concerns assets owned or used by the subsidiary; parent-level patent counts
are only an empirical proxy for that concept.

The model is parameterized directly by $(k, h)$ rather than by a composite
index. The project's earlier symmetric composite α is retained only in legacy
script 09. In the current sample, the patent component is more strongly
associated with exit mode than the labor component. This pattern motivates
separate regressors, but it does not validate either proxy or prove the
model's transferability mechanism.

## The cutoff

The firm sells iff $V\theta(k,h) - \tau > -w$, i.e. iff

$$\theta(k, h) \;>\; \theta^* \equiv \frac{\tau - w}{V}.$$

Everything in the paper is a movement of $\theta(k,h)$ or of $\theta^*$.
(The analysis focuses on the case $\tau > w$, in which completing a sale
requires enough transferable value to compensate for transaction costs.)

**Heterogeneity.** Firms differ in the private value of retaining the
subsidiary, $V_i$, which is distributed according to a continuous log-concave
distribution $F(\cdot)$. This heterogeneity implies that the deterministic
cutoff translates into a probabilistic sell/no-sell decision, yielding the
binary-choice specification estimated in the empirical analysis. Concretely,
firm $i$ sells iff $V_i > V^*(k,h;\tau,w) \equiv (\tau - w)/\theta(k,h)$, so

$$\Pr(\text{sell}) = 1 - F\!\left(V^*(k,h;\tau,w)\right),$$

This expression motivates a binary-response model. A probit additionally
requires a distributional assumption about the latent error; it is therefore
an empirical implementation of the model rather than a likelihood uniquely
implied by the economic framework.

## Predictions

**Prediction 1 (exit mode — slope of θ).**
$V^*_k = -(\tau-w)\,\theta_k/\theta^2 < 0$ and $V^*_h > 0$, so
$\partial\Pr(\text{sell})/\partial k > 0$ and
$\partial\Pr(\text{sell})/\partial h < 0$. In words, transferable assets
increase the expected value of a sale. When geopolitical frictions reduce
buyers' willingness to pay, subsidiaries whose value depends primarily on
transferable assets should remain more likely to attract buyers. Subsidiaries
whose value relies heavily on employees and firm-specific routines should be
more likely to lack a viable sale opportunity and therefore exit without an
arm's-length sale. These signs are unambiguous within the model; testing them
requires credible measures of $k$ and $h$.
→ `scripts/10_selection_exit_mode.py` (Heckman-style two-stage on the full
population; B2C exclusion restriction: boycott pressure moves *whether* to
exit, not the mechanics of the asset transfer).

**Prediction 2 (sanctions may raise the sale threshold).** Licensing rules,
exit taxes, mandatory discounts, and a smaller pool of eligible buyers can
raise $\tau$. Holding other quantities fixed, this raises $\theta^*$ and
reduces the probability of sale. Whether sanctions strengthen the association
between transferable assets and sale is a separate interaction effect:

$$\frac{\partial^2 \Pr(\text{sell})}{\partial \tau\,\partial k}
= -f'(V^*)\,V^*_\tau V^*_k \;-\; f(V^*)\,V^*_{k\tau},
\qquad V^*_\tau > 0,\; V^*_k < 0,\; V^*_{k\tau} = -\theta_k/\theta^2 < 0.$$

The second term is positive, whereas the first depends on the location of the
marginal firm in the value distribution. Moreover, sanctions may reduce $V$
especially sharply for technology assets by eliminating capable buyers. That
channel can reverse the sign. The model therefore does not deliver an
unconditional prediction for the interaction; the empirical estimate must
distinguish these competing mechanisms.
→ `scripts/11_sanctions_amplification.py` (pooled PatInt × SancExp
interaction — not a subsample R² comparison — plus a cause-specific
competing-risks Cox with time-varying exposure from the staggered 2022 EU
package rollout).

**Prediction 3 (home institutions move θ\* in opposite directions).**
Coalition alignment raises $\tau$ (buyer restrictions, exit-tax exposure):
$\theta^*\uparrow$, less selling. Stakeholder-pressure institutions raise
$w$ (reputational and legal cost of walking away): $\theta^*\downarrow$,
more selling. These mechanisms imply opposite movements in the cutoff.
→ `scripts/12_institutional_moderators.py` (country fixed effects absorb
institution levels, so the specification estimates only the $k \times$
institution interactions).

## Mapping model objects to data

| Model object | Empirical proxy | Source |
|--------------|-----------------|--------|
| $k$ — transferable codified assets | parent patent-stock percentile (`pat_pctile`, within-sector variant available); an indirect proxy that does not identify patents owned by the Russian subsidiary | Lens.org |
| $h$ — non-transferable human capital | subsidiary employees/assets percentile (`lab_pctile`); a labor-intensity proxy that does not directly measure tacitness, specificity, or employee retention | Orbis |
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
4. Because $k$ and $h$ enter as ranks, substantive results should be reported
   as predicted probabilities or average marginal effects across meaningful
   percentile changes, not interpreted as effects of one additional patent or
   employee.
5. A persuasive test also requires direct validation of the exit-mode coding,
   evidence for the B2C exclusion restriction, and controls for parent size,
   profitability, and subsidiary asset composition. Until those additions are
   made, the estimates are best described as conditional associations.
