# Formal Model

## 1. Entry choice

A firm chooses one of three ways to serve a foreign market before a political
rupture:

- $m=W$: a wholly owned local operation.
- $m=J$: a joint venture with an unrelated local partner.
- $m=C$: a contract with a local distributor, licensee, or franchisee.

Let $\pi_m$ denote the present value of operating profit under mode $m$ when
political relations remain stable. Let $K_m$ denote the firm's capital exposed
in the host country. This includes equity, physical assets, receivables,
guarantees, and contract-specific investments. A contractual arrangement can
therefore have positive exposure even when the firm owns no local subsidiary.

The firm assigns probability $p$ to a political rupture. Its entry problem is

\[
    m^* = \arg\max_m \left\{\pi_m - I_m - pL_m\right\},
\]

where $I_m$ is the normal cost of establishing the arrangement and $L_m$ is
the expected loss if a rupture occurs.

This equation states the basic tradeoff. Ownership may raise normal operating
profit by improving control over production and knowledge. It may also place
more capital under host-country jurisdiction.

## 2. Resolution after a rupture

For an equity operation, the parent owns an asset with pre-rupture book value
$K_m$. While ownership remains unresolved, the parent pays $c_m$ per unit of
time. This amount includes payroll, security, legal work, compliance, and other
costs required to maintain or dispose of the operation.

A permitted sale is completed at rate $\lambda_m$ and pays the parent $P_m$,
net of transaction taxes, required discounts, and direct selling costs. State
seizure or another forced loss of control occurs at rate $\sigma_m$ and leaves
the parent with $S_m$. Usually $S_m<P_m$. Let $V_m$ be the value of the
unresolved operation immediately after the rupture. Then

\[
    rV_m = -c_m
      + \lambda_m(P_m-V_m)
      + \sigma_m(S_m-V_m),
\]

so

\[
    V_m =
    \frac{\lambda_mP_m+\sigma_mS_m-c_m}
         {r+\lambda_m+\sigma_m}.
\]

The expected exit loss is

\[
    L_m = K_m - V_m.
\]

This definition places the three observed components in one measure. A larger
write-down raises the loss. A longer delay raises the present value of holding
costs. A larger recovery payment lowers the loss.

For a contractual arrangement, $K_C$ consists of receivables, guarantees,
inventory, and contract-specific investments rather than subsidiary equity.
The arrangement can end through notice, non-renewal, or breach. The same value
equation applies if $\lambda_C$ is interpreted as the rate at which the
contract is legally and commercially resolved, $P_C$ as net recovery at
resolution, and $\sigma_C$ as the rate of uncompensated termination or
appropriation.

## 3. Comparative results

The value of an unresolved operation changes as follows:

\[
    \frac{\partial V_m}{\partial c_m}<0,
    \qquad
    \frac{\partial V_m}{\partial P_m}>0,
    \qquad
    \frac{\partial V_m}{\partial \lambda_m}
    = \frac{P_m-V_m}{r+\lambda_m+\sigma_m}.
\]

When a permitted sale is better than continued waiting, $P_m>V_m$, a higher
sale-completion rate reduces expected loss. A higher forced-loss rate reduces
value when $S_m<V_m$.

The model does not impose a fixed ranking between wholly owned operations and
joint ventures. A local partner may improve access to buyers and government
approval, raising $\lambda_J$. The partner may also create bargaining disputes
or block a transfer, lowering $\lambda_J$. The ranking must be estimated.

Contractual entry has lower expected loss than wholly owned entry when

\[
    K_C-V_C < K_W-V_W.
\]

Lower local capital exposure makes this inequality more likely, but it does
not guarantee it. A distributor may fail to pay receivables, a license may be
used without compensation, or the foreign firm may remain liable under a
guarantee.

## 4. Empirical implications

The model identifies three separate comparisons:

1. **Capital at risk.** Entry modes with more host-country assets should have
   larger losses unless they also obtain larger recoveries.
2. **Time to resolution.** Entry mode affects the rate at which a sale,
   termination, or other legal resolution occurs.
3. **Recovery.** Entry mode affects the fraction of pre-rupture exposure that
   the parent receives after taxes, discounts, and settlement costs.

The primary empirical analysis should estimate each outcome separately. A
summary exit-cost measure can then be constructed as

\[
    \text{Exit Cost}_i
    = K_i-R_i+\int_0^{T_i}e^{-rt}c_i(t)\,dt+F_i,
\]

where $R_i$ is realized recovery, $T_i$ is time to resolution, and $F_i$
contains direct legal and transaction costs.

## 5. Selection into entry mode

The common rupture does not make entry mode random. Firms chose ownership,
joint ventures, and contracts before 2022 based on regulation, asset type,
market size, knowledge-transfer concerns, and their own capabilities. These
same factors can affect exit cost.

The baseline estimates are therefore conditional comparisons. The empirical
design should include detailed pre-rupture controls and industry effects. A
secondary analysis can compare Russian operations belonging to the same parent
when that parent used more than one mode. A causal interpretation requires an
additional source of pre-rupture variation in entry mode whose effect on exit
cost operates only through entry mode. The current data do not provide such
variation.

## 6. Link to measurement

The model and current data do not yet align in three places:

- The model requires entry mode immediately before the rupture. Current Orbis
  ownership can reflect later changes.
- The model requires the full population of foreign operations. Bloomberg
  observes reported transactions, not firms that closed, waited, or used only
  contracts.
- The model requires net recovery and holding costs. Bloomberg reports some
  transaction values but no write-downs or continuing costs.

These are data requirements for the main study. They are not variables that
should be inferred from missing observations.
