# Corporate exit in a distorted market for control

## 1. Purpose

The model explains why a foreign parent can want to leave a market yet remain
the legal owner of its subsidiary for an extended period. The central friction
is that a completed sale requires both a qualified buyer and permission to
transfer control. The parent cannot produce either condition on demand.

While it waits, the parent pays the cost of maintaining the unresolved
subsidiary. It can instead close the operation, but closure is costly and
irreversible. Geopolitical policies affect the process by changing buyer
availability, permitted transaction value, and approval delay.

This framework is intended to discipline measurement and counterfactual
analysis. It is not yet structurally estimated with the current repository.

## 2. State and payoffs

Consider parent company $i$ at time $t$. It has announced an intention to leave
but still controls a Russian subsidiary.

| Symbol | Meaning |
|---|---|
| $k_i$ | Codified assets and other capabilities that can remain valuable under new ownership |
| $h_i$ | Dependence on employees, parent services, and continuing operations |
| $x_{it}$ | Time-varying conditions, including approval status, sanctions, demand, and operating restrictions |
| $V_i(x_{it})$ | Value of the subsidiary before transaction deductions |
| $\theta(k_i,x_{it})$ | Share of value a buyer can preserve after control changes |
| $\tau(x_{it})$ | Mandatory discount, transaction tax, compliance cost, and bargaining deduction |
| $S_i(x_{it})=\theta(k_i,x_{it})V_i(x_{it})-\tau(x_{it})$ | Net value of a completed transaction |
| $c(h_i,x_{it})$ | Cost per period of maintaining the unresolved subsidiary |
| $\mu(x_{it})$ | Rate at which an eligible buyer becomes available |
| $q(x_{it})$ | Rate at which a feasible transaction receives approval |
| $\lambda(x_{it})$ | Effective completion rate generated jointly by buyer availability and approval |
| $w_i$ | Cost of closing without a sale |

It is useful to distinguish buyer availability from approval conceptually even
when the data identify only their combined effect. In a simple sequential
process, buyers arrive at rate $\mu$ and approval arrives at rate $q$ after a
buyer is found. A reduced-form version summarizes both delays with the
effective rate $\lambda$.

Codified assets and operating dependence do different jobs. Codified assets
can increase $\theta$, because a buyer can retain patents, licenses, physical
assets, or documented processes. Operating dependence can increase $c$,
because payroll, maintenance, local contracts, and parent-provided services
continue or deteriorate during suspension. They are not opposite ends of one
index.

## 3. Constant-condition benchmark

Suppose $S$, $c$, and $\lambda$ remain constant. If the parent commits to wait
until completion, the value of waiting is

$$
rW=-c+\lambda(S-W),
\qquad
W=\frac{\lambda S-c}{r+\lambda}.
$$

Closing produces payoff $-w$. The parent closes immediately when

$$
W<-w
\quad\Longleftrightarrow\quad
c>\lambda(S+w)+rw.
$$

This equation displays the model's basic economics:

- Higher transferable value $S$ makes waiting more attractive.
- Faster buyer-and-approval completion $\lambda$ makes waiting more attractive.
- Higher carrying cost $c$ makes closure more attractive.
- A more costly closure $w$ makes waiting more attractive.

The benchmark does not create a duration decision: with constant conditions,
the parent either closes immediately or waits indefinitely. The full model
therefore allows conditions to evolve.

## 4. Dynamic stopping problem

Let $J_i(x)$ denote the value of an unresolved subsidiary in state $x$. The
parent chooses between closing now and continuing to wait:

$$
\max\left\{
-w_i-J_i(x),\;
-c(h_i,x)+\mathcal{L}J_i(x)
+\lambda(x)\left[S_i(x)-J_i(x)\right]
-rJ_i(x)
\right\}=0.
$$

$\mathcal{L}$ describes how the state changes while the parent waits. For
example, approval may become more likely after documents are filed, subsidiary
value may deteriorate during suspension, or carrying costs may rise as
temporary arrangements expire.

The parent waits when $J_i(x)>-w_i$ and closes when $J_i(x)=-w_i$. A completed
sale occurs only if the firm is still waiting when a buyer-and-approval
opportunity arrives.

Between two tracker observations separated by $\Delta$, the same problem has
the approximate discrete form

$$
J_{it}=\max\left\{
-w_i,\;
-c_{it}\Delta+e^{-r\Delta}
\left[(1-\lambda_{it}\Delta)E_tJ_{i,t+1}
+\lambda_{it}\Delta S_{it}\right]
\right\}.
$$

This form maps naturally to monthly or quarterly subsidiary data.

## 5. Policy distortions

The model separates three policy channels.

### Buyer restriction

Sanctions, financing restrictions, and counterparty rules can reduce $\mu$ by
removing eligible buyers or lenders. This increases expected waiting time and
can eventually make closure preferable.

### Approval delay

Host-government review can reduce $q$ or make approval conditional on buyer
identity, sector, or transaction terms. This creates a queue between agreement
and legal completion.

### Transaction-value reduction

Mandatory discounts, exit levies, taxes, and bargaining pressure raise $\tau$
and reduce $S$. They may lower the seller's recovery without changing the
physical productivity of the subsidiary.

These channels can produce similar observed delays but have different policy
implications. Better data are required to distinguish them.

## 6. Main predictions

### Transferable assets

An increase in $k$ raises the value of a future transaction when it increases
$\theta$. It should reduce the rate of closure while the parent waits. It may
also attract buyers and raise $\mu$, but that is a separate empirical channel.

### Operating dependence

An increase in $h$ raises closure when it increases the cost of maintaining an
unresolved operation. The preferred measure is payroll and other continuing
costs, not employees divided by assets.

### Buyer and approval restrictions

Lower $\mu$ or $q$ increases expected completion time. It can raise closure if
the expected delay makes waiting too costly.

### Mandatory discounts and levies

A larger $\tau$ reduces the value of completion. It can lengthen negotiations,
lead the parent to reject available transactions, or bring forward closure.

### Cumulative outcomes

A firm characteristic can increase the eventual probability of sale without
raising the completion rate at a particular instant. If the characteristic
reduces closure, the subsidiary remains available to match with a buyer for
longer.

## 7. Measurement in the ideal study

| Model object | Preferred evidence |
|---|---|
| $\mu$ | Dated buyer approaches, bids, buyer identity, buyer financing, and eligibility |
| $q$ | Application, approval, denial, and conditional-approval dates |
| $V$ | Pre-invasion subsidiary cash flow, assets, production, and comparable transaction values |
| $\theta$ | Assets and rights conveyed; buyer operating continuity; subsidiary patents and licenses; parent-service dependence |
| $\tau$ | Transaction price relative to valuation; mandatory discount; exit levy; taxes; professional fees |
| $c$ | Payroll, leases, maintenance, compliance expense, working capital, and asset deterioration during suspension |
| $w$ | Liquidation expense, severance, creditor losses, asset write-offs, and legal closure costs |
| Completion | Historical legal ownership and liquidation records, not announcement text alone |

The current repository measures only fragments of these objects. Parent patent
rank is a provisional proxy for $k$, and employees/assets is a provisional
proxy for $h$. Neither is a direct structural measure.

## 8. Moments for estimation

An estimated version of the model should match moments that identify distinct
mechanisms:

1. Time from exit announcement to buyer agreement.
2. Time from buyer agreement to government approval.
3. Time from approval to legal ownership transfer.
4. Share of firms unresolved after 6, 12, and 24 months.
5. Transaction price relative to independent valuation and pre-invasion value.
6. Closure and liquidation rates.
7. Employment, assets, production, and taxes before and after each outcome.
8. Differences in these moments across firms with varying asset transferability
   and continuing operating costs.

Separating agreement, approval, and legal completion is essential. A single
sale date cannot identify whether delay came from buyer scarcity or government
review.

## 9. Counterfactual decomposition

The quantitative contribution would compare the observed economy with
counterfactual environments that remove one distortion at a time while holding
the estimated firm characteristics fixed.

1. **No buyer restriction:** restore the pre-crisis eligible-buyer arrival
   process.
2. **No approval delay:** allow an otherwise valid transaction to complete
   immediately after agreement.
3. **No mandatory discount or exit levy:** remove the policy component of
   $\tau$.
4. **Lower carrying cost:** allow temporary suspension without continued
   payroll or selected compliance costs.
5. **Combined undistorted completion market:** remove all four distortions.

For each experiment, report changes in:

- Time to completed exit.
- Probability of sale, closure, unresolved ownership, and state intervention.
- Seller recovery and buyer surplus.
- Employment and production retained in Russia.
- Host-country tax payments.
- Productive and strategic assets transferred, idled, or destroyed.

The decomposition is more informative than asking whether sanctions simply
“increase” or “decrease” exit. Different rules can increase the desire to leave
while reducing the ability to complete departure.

## 10. What the current data can support

Repeated Yale snapshots can provisionally describe movement between reported
states. Orbis supplies selected subsidiary characteristics. Bloomberg provides
some transaction dates, and Lens.org provides incomplete parent patent counts.

These data can motivate the model and document selected correlations. They
cannot separately identify buyer arrival, approval delay, transaction-value
reductions, or carrying costs. The current duration estimates are also based on
an incomplete patent sample. Structural estimation and policy counterfactuals
must therefore wait for the ideal data described above.
