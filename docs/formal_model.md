# A waiting model of corporate exit completion

## 1. Economic question

A parent company has announced that it intends to leave Russia, but its exit
is not yet complete. The parent can continue to hold the subsidiary while it
waits for a suitable buyer and any required approvals. Alternatively, it can
close the operation without completing a sale. A completed sale is not treated
as an action that the parent can choose at any moment; it becomes possible
only when a qualified buyer and the necessary permissions are available.

The model asks when the parent continues to wait and when it stops waiting.

## 2. Economic objects

| Symbol | Meaning |
|---|---|
| $k$ | Importance of patents and other codified assets |
| $h$ | Dependence on employees and continuing operations |
| $\theta(k)$ | Share of subsidiary value that a buyer can preserve, with $\theta'(k)>0$ |
| $V_t$ | Subsidiary value at time $t$ before transaction costs |
| $\tau_t$ | Transaction costs, mandatory discounts, taxes, and other deductions |
| $S_t=\theta(k)V_t-\tau_t$ | Net value received if a qualified buyer completes a transaction at time $t$ |
| $c_t=c(h,x_t)$ | Cost per period of maintaining the unresolved subsidiary, with $c_h>0$ |
| $\lambda_t=\lambda(x_t)$ | Rate at which a qualified buyer and required permissions become available |
| $w$ | Cost of closing the operation without a sale |
| $x_t$ | Conditions that evolve over time, such as approval status, sanctions, operating restrictions, and demand |

The two knowledge concepts have different functions. Codified assets increase
the value preserved in a future transaction through $\theta(k)$. Dependence
on employees and continuing operations raises the cost of remaining unresolved
through $c(h,x_t)$. This separation avoids treating patents and labor intensity
as opposite ends of a single index.

## 3. Constant-condition benchmark

Suppose for the moment that $S$, $c$, and $\lambda$ never change. If the
company commits to waiting until a buyer arrives, the value of waiting is

$$
rW=-c+\lambda(S-W),
\qquad
W=\frac{\lambda S-c}{r+\lambda}.
$$

The company closes immediately when waiting is worth less than paying the
closure cost:

$$
W<-w
\quad\Longleftrightarrow\quad
c>\lambda(S+w)+rw.
$$

This benchmark is useful because it displays the economic forces clearly, but
it is not yet a model of *when* to stop waiting. Under constant conditions the
company either closes immediately or waits indefinitely. A genuine stopping
decision requires conditions to change over time.

## 4. Dynamic stopping problem

Let $x_t$ summarize the conditions facing the subsidiary. These conditions
may change because costs accumulate, subsidiary value deteriorates, sanctions
change the buyer pool, or government approval becomes more or less likely.
Let $J(x)$ denote the value of an unresolved subsidiary in state $x$.

The continuous-time stopping problem is

$$
\max\left\{
-w-J(x),\;
-c(h,x)+\mathcal{L}J(x)
+\lambda(x)\big[\theta(k)V(x)-\tau(x)-J(x)\big]
-rJ(x)
\right\}=0.
$$

The first expression is the value of closing now. The second is the value of
continuing to wait: the parent pays the current carrying cost, conditions may
change according to $\mathcal{L}$, and a completed transaction occurs at rate
$\lambda(x)$. The parent closes when $J(x)=-w$ and waits when $J(x)>-w$.

For readers who prefer a discrete interpretation, consider the interval
between two Yale tracker snapshots. If the company waits during period $t$,
its approximate value is

$$
-c_t\Delta
+e^{-r\Delta}\left[
(1-\lambda_t\Delta)E_t J(x_{t+1})
+\lambda_t\Delta S_t
\right].
$$

At each snapshot, the parent compares this continuation value with $-w$. This
form makes clear why a company may wait at one date and close later: costs,
value, buyer availability, or approval conditions can change between dates.

## 5. Testable predictions

### Prediction 1: codified assets delay closure

An increase in $k$ raises $\theta(k)$ and therefore raises the value of a
future completed transaction. Holding other quantities fixed, it expands the
set of conditions under which the parent continues to wait. The rate of
closure without a sale should therefore decline with $k$.

### Prediction 2: human-capital dependence accelerates closure

An increase in $h$ raises the cost of maintaining an unresolved operation.
Holding other quantities fixed, it makes the stopping condition more likely
to bind. The rate of closure without a sale should therefore rise with $h$.

### Prediction 3: sale timing depends primarily on buyer and approval availability

Among subsidiaries that remain unresolved, the instantaneous rate of a
completed transaction is $\lambda(x)$. Sanctions may reduce this rate by
shrinking the eligible buyer pool. Russian approval requirements may also
delay completion. Mandatory discounts and transaction taxes instead reduce
$S_t$ and may cause the parent to keep waiting or close.

The model does **not** require the sale-completion rate to be unrelated to
$k$. That restriction holds only if codified assets affect the value of
waiting but do not attract buyers, speed approval, or change bid acceptance.
The current estimate for $k$ in the sale-completion equation is imprecise and
should not be interpreted as proof of no relationship.

### Prediction 4: cumulative sale probability can rise without a higher sale rate

Even if $k$ does not change $\lambda$, a subsidiary with more codified assets
may remain unresolved longer because it is less likely to close. Its
cumulative probability of eventually finding a buyer can therefore increase
without an increase in the transaction rate at any particular instant.

## 6. Mapping the model to the Yale snapshots

The current data skeleton treats each company at each snapshot as being in one
of the following states:

| State | Interpretation |
|---|---|
| Still operating | No full exit announcement is visible in the current record |
| Exit announced but unresolved | Reduction, suspension, or announced departure without a verified completed outcome |
| Sale completed | Available text or transaction data report a completed transfer to a buyer |
| Closure completed | Available text reports closure or liquidation without a sale |
| State-imposed loss of control | Seizure or temporary administration |

The main empirical sample begins when a company first enters the unresolved
state. The analysis then follows it until sale, closure, state intervention,
or the final snapshot. Companies still operating are also needed to study the
earlier decision to announce an exit, but that is a separate transition.

## 7. Empirical skeleton

The first implementation should estimate four easily explained quantities:

1. Expected months from an exit announcement to any completed outcome.
2. Probability of remaining unresolved after 6, 12, and 24 months.
3. Probability that the next observed outcome is a completed sale.
4. Probability that the next observed outcome is a completed closure.

The statistical model may use transition-specific duration regressions, but
the paper should describe results as waiting times and predicted
probabilities. Technical estimator names belong in the methods appendix.

Primary explanatory variables:

- Parent patent rank as a provisional proxy for $k$.
- Subsidiary employees/assets as a provisional proxy for $h$.
- Assets, age, subsidiary count, sector, and home country as controls.
- Time-varying sector sanctions as a provisional shifter of $\lambda_t$ or
  $S_t$.

## 8. What the current evidence says

In the existing selected duration sample, moving from the bottom to the top of
the parent patent ranking is associated with an approximately 69% lower rate
of completing an exit without a sale (p < 0.001). Its estimated relationship
with the rate of completed sales is small relative to its uncertainty
(p = 0.54). Moving across the labor-intensity ranking is associated with an
estimated 32% higher rate of non-sale completion, but that estimate is also
imprecise (p = 0.30).

These estimates are consistent with Predictions 1 and 2, but they are not a
test of the full model because patent data are currently missing for much of
the population and the outcome categories rely on announcement text.

## 9. Main limitations

1. Yale grades are editorial assessments rather than legal ownership records.
2. Several distinct actions may appear within the same Yale grade.
3. Many companies were already recorded as completed exits in the first
   available snapshot, so their waiting times are not observed from the start.
4. Parent patent stock is not the same as IP transferred with a Russian
   subsidiary.
5. Employees/assets does not directly measure payroll or the cost of
   maintaining a suspended operation.
6. The full panel needs pre-invasion patent coverage before the duration
   results can be interpreted as population relationships.
7. The processes governing $V_t$, $c_t$, and $\lambda_t$ remain to be
   parameterized. The present document is a theoretical and empirical
   skeleton, not a completed structural estimation.
