"""
Run the main regression specifications and robustness checks.

Main specification:
  Y_i = β₀ + β₁α_i + β₂α_i² + X_i'γ + μ_j + ε_i

Where Y_i is tested with multiple dependent variables:
  (1) Binary: sold=1 vs suspended=0 (probit/logit, full sample)
  (2) Ordinal: exit completeness (sold > nationalized > suspended > other)
  (3) Continuous: sale_price / book_value (small subsample with deal data)

α = employee intensity (employees / total assets), percentile-ranked

Controls X_i: ln(assets), years_in_russia, n_subsidiaries
Fixed effects μ_j: NACE 2-digit sector
Instrument Z: sanctions_exposure (number of EU packages hitting sector)

Input:
  data/analysis/regression_sample.csv

Output:
  data/analysis/regression_results.txt
"""

import csv
import math
from pathlib import Path

try:
    import numpy as np
    from scipy import stats as scipy_stats
except ImportError:
    raise SystemExit("numpy/scipy not installed: pip install numpy scipy")

try:
    import statsmodels.api as sm
    from statsmodels.discrete.discrete_model import Logit
except ImportError:
    raise SystemExit("statsmodels not installed: pip install statsmodels")

DATA_DIR = Path(__file__).parent.parent / "data" / "analysis"
IN_FILE = DATA_DIR / "regression_sample.csv"
OUT_FILE = DATA_DIR / "regression_results.txt"


def load_data():
    rows = []
    with open(IN_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def safe_float(val):
    if not val or val.strip() == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def winsorize(arr, pct=1):
    lower = np.percentile(arr, pct)
    upper = np.percentile(arr, 100 - pct)
    return np.clip(arr, lower, upper)


def percentile_rank(arr):
    from scipy.stats import rankdata
    ranks = rankdata(arr)
    return (ranks - 1) / (len(ranks) - 1)


def main():
    rows = load_data()
    results = []
    results.append("=" * 70)
    results.append("REGRESSION RESULTS: Bimodal Knowledge Transfer Under Geopolitical Risk")
    results.append("=" * 70)

    # ──────────────────────────────────────────────────────────────────────
    # Prepare variables
    # ──────────────────────────────────────────────────────────────────────

    # Filter to firms with α and controls
    sample = []
    for r in rows:
        alpha = safe_float(r.get("alpha"))
        ln_a = safe_float(r.get("ln_assets"))
        yrs = safe_float(r.get("years_in_russia"))
        if alpha is not None and ln_a is not None and yrs is not None:
            sample.append(r)

    n_both = sum(1 for r in sample if safe_float(r.get("alpha_pat_pctile")) is not None)
    results.append(f"\nSample with α + controls: N = {len(sample)}")
    results.append(f"  With both α components (emp + patent): {n_both}")
    results.append(f"  With employee intensity only: {len(sample) - n_both}")

    # α is already percentile-ranked in script 08
    alpha_pctile = np.array([float(r["alpha"]) for r in sample])
    alpha_sq = alpha_pctile ** 2

    # Controls
    ln_assets = np.array([float(r["ln_assets"]) for r in sample])
    years_russia = np.array([float(r["years_in_russia"]) for r in sample])
    n_subs = np.array([float(r["n_subsidiaries"]) if r["n_subsidiaries"] else 1
                       for r in sample])
    sanctions = np.array([float(r["sanctions_exposure"]) for r in sample])

    # Sector fixed effects (NACE 2-digit)
    sectors = [r.get("nace_sector", "00") for r in sample]
    unique_sectors = sorted(set(sectors))
    # Create dummies (drop first for identification)
    sector_dummies = np.zeros((len(sample), max(0, len(unique_sectors) - 1)))
    for i, s in enumerate(sectors):
        idx = unique_sectors.index(s)
        if idx > 0:
            sector_dummies[i, idx - 1] = 1

    # ──────────────────────────────────────────────────────────────────────
    # SPECIFICATION 1: Binary Y — sold (1) vs not sold (0)
    # ──────────────────────────────────────────────────────────────────────

    results.append("\n" + "─" * 70)
    results.append("SPECIFICATION 1: Logit — P(sold) = f(α, α², controls, sector FE)")
    results.append("─" * 70)

    y_sold = np.array([1.0 if r.get("action_type") == "sold" else 0.0
                       for r in sample])

    results.append(f"  Y=1 (sold): {int(y_sold.sum())}  |  Y=0 (not sold): {int(len(y_sold) - y_sold.sum())}")

    # Build X matrix
    X_base = np.column_stack([
        alpha_pctile,
        alpha_sq,
        ln_assets,
        years_russia,
        np.log1p(n_subs),
    ])
    X_with_const = sm.add_constant(X_base)

    var_names_base = ["const", "alpha", "alpha_sq", "ln_assets", "years_russia", "ln_n_subs"]

    # Without sector FE first
    try:
        model1 = Logit(y_sold, X_with_const).fit(disp=0)
        results.append(f"\n  Model 1a (no sector FE): N={model1.nobs:.0f}, Pseudo-R²={model1.prsquared:.4f}")
        results.append(f"  {'Variable':<15} {'Coef':>10} {'Std Err':>10} {'z':>8} {'P>|z|':>8}")
        results.append(f"  {'-'*55}")
        for name, coef, se, z, p in zip(
            var_names_base, model1.params, model1.bse, model1.tvalues, model1.pvalues
        ):
            sig = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
            results.append(f"  {name:<15} {coef:>10.4f} {se:>10.4f} {z:>8.3f} {p:>8.4f} {sig}")
    except Exception as e:
        results.append(f"  Model 1a failed: {e}")

    # With sector FE
    if sector_dummies.shape[1] > 0:
        X_fe = np.column_stack([X_base, sector_dummies])
        X_fe_const = sm.add_constant(X_fe)
        try:
            model1b = Logit(y_sold, X_fe_const).fit(disp=0, maxiter=100)
            results.append(f"\n  Model 1b (with sector FE): N={model1b.nobs:.0f}, Pseudo-R²={model1b.prsquared:.4f}")
            results.append(f"  {'Variable':<15} {'Coef':>10} {'Std Err':>10} {'z':>8} {'P>|z|':>8}")
            results.append(f"  {'-'*55}")
            fe_names = var_names_base + [f"sector_{s}" for s in unique_sectors[1:]]
            for name, coef, se, z, p in zip(
                fe_names[:6], model1b.params[:6], model1b.bse[:6],
                model1b.tvalues[:6], model1b.pvalues[:6]
            ):
                sig = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
                results.append(f"  {name:<15} {coef:>10.4f} {se:>10.4f} {z:>8.3f} {p:>8.4f} {sig}")
            results.append(f"  [+ {sector_dummies.shape[1]} sector dummies]")
        except Exception as e:
            results.append(f"  Model 1b failed: {e}")

    # ──────────────────────────────────────────────────────────────────────
    # SPECIFICATION 2: OLS — Y = exit ordinal score
    # ──────────────────────────────────────────────────────────────────────

    results.append("\n" + "─" * 70)
    results.append("SPECIFICATION 2: OLS — Exit completeness = f(α, α², controls)")
    results.append("─" * 70)

    # Score: sold=3, nationalized=2, suspended=1, other=0
    score_map = {"sold": 3, "nationalized": 2, "suspended": 1, "other": 0}
    y_ordinal = np.array([score_map.get(r.get("action_type", ""), 0) for r in sample],
                         dtype=float)

    results.append(f"  Score distribution: sold(3)={int((y_ordinal==3).sum())}, "
                   f"nat(2)={int((y_ordinal==2).sum())}, "
                   f"susp(1)={int((y_ordinal==1).sum())}, "
                   f"other(0)={int((y_ordinal==0).sum())}")

    try:
        model2 = sm.OLS(y_ordinal, X_with_const).fit()
        results.append(f"\n  Model 2 (OLS): N={int(model2.nobs)}, R²={model2.rsquared:.4f}, Adj-R²={model2.rsquared_adj:.4f}")
        results.append(f"  F-stat: {model2.fvalue:.3f} (p={model2.f_pvalue:.4f})")
        results.append(f"  {'Variable':<15} {'Coef':>10} {'Std Err':>10} {'t':>8} {'P>|t|':>8}")
        results.append(f"  {'-'*55}")
        for name, coef, se, t, p in zip(
            var_names_base, model2.params, model2.bse, model2.tvalues, model2.pvalues
        ):
            sig = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
            results.append(f"  {name:<15} {coef:>10.4f} {se:>10.4f} {t:>8.3f} {p:>8.4f} {sig}")
    except Exception as e:
        results.append(f"  Model 2 failed: {e}")

    # ──────────────────────────────────────────────────────────────────────
    # SPECIFICATION 3: OLS — Y = sale_price / book_value (subsample)
    # ──────────────────────────────────────────────────────────────────────

    results.append("\n" + "─" * 70)
    results.append("SPECIFICATION 3: OLS — Exit payoff ratio = f(α, α², controls)")
    results.append("  [Subsample with disclosed deal values]")
    results.append("─" * 70)

    sub3 = [(i, r) for i, r in enumerate(sample) if safe_float(r.get("y_exit_payoff"))]
    results.append(f"  Subsample N = {len(sub3)}")

    if len(sub3) >= 5:
        idx3 = [i for i, _ in sub3]
        y3 = np.array([float(r["y_exit_payoff"]) for _, r in sub3])
        X3 = X_with_const[idx3]

        # Winsorize Y
        y3_wins = winsorize(y3, pct=5)

        try:
            model3 = sm.OLS(y3_wins, X3).fit()
            results.append(f"\n  Model 3 (OLS): N={int(model3.nobs)}, R²={model3.rsquared:.4f}")
            results.append(f"  {'Variable':<15} {'Coef':>10} {'Std Err':>10} {'t':>8} {'P>|t|':>8}")
            results.append(f"  {'-'*55}")
            for name, coef, se, t, p in zip(
                var_names_base, model3.params, model3.bse, model3.tvalues, model3.pvalues
            ):
                sig = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
                results.append(f"  {name:<15} {coef:>10.4f} {se:>10.4f} {t:>8.3f} {p:>8.4f} {sig}")
        except Exception as e:
            results.append(f"  Model 3 failed: {e}")
    else:
        results.append("  Insufficient observations for regression")

    # ──────────────────────────────────────────────────────────────────────
    # SPECIFICATION 4: IV — 2SLS with sanctions exposure as instrument
    # ──────────────────────────────────────────────────────────────────────

    results.append("\n" + "─" * 70)
    results.append("SPECIFICATION 4: 2SLS IV — sanctions_exposure instruments for α")
    results.append("─" * 70)

    # First stage: α = π₀ + π₁Z + X'δ + ν
    X_iv = np.column_stack([sanctions, ln_assets, years_russia, np.log1p(n_subs)])
    X_iv_const = sm.add_constant(X_iv)

    try:
        first_stage = sm.OLS(alpha_pctile, X_iv_const).fit()
        results.append(f"\n  First stage: α = f(sanctions_exposure, controls)")
        results.append(f"  F-stat: {first_stage.fvalue:.3f} (p={first_stage.f_pvalue:.4f})")
        results.append(f"  R²: {first_stage.rsquared:.4f}")
        iv_names = ["const", "sanctions_exp", "ln_assets", "years_russia", "ln_n_subs"]
        results.append(f"  {'Variable':<15} {'Coef':>10} {'Std Err':>10} {'t':>8} {'P>|t|':>8}")
        results.append(f"  {'-'*55}")
        for name, coef, se, t, p in zip(
            iv_names, first_stage.params, first_stage.bse,
            first_stage.tvalues, first_stage.pvalues
        ):
            sig = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
            results.append(f"  {name:<15} {coef:>10.4f} {se:>10.4f} {t:>8.3f} {p:>8.4f} {sig}")

        # Weak instrument test
        f_stat_iv = first_stage.fvalue
        results.append(f"\n  Weak instrument test: F = {f_stat_iv:.2f} {'(PASS: F>10)' if f_stat_iv > 10 else '(WEAK: F<10)'}")

        # Second stage
        alpha_hat = first_stage.fittedvalues
        alpha_hat_sq = alpha_hat ** 2
        X_2sls = np.column_stack([alpha_hat, alpha_hat_sq, ln_assets, years_russia, np.log1p(n_subs)])
        X_2sls_const = sm.add_constant(X_2sls)

        second_stage = sm.OLS(y_ordinal, X_2sls_const).fit()
        results.append(f"\n  Second stage: Y_ordinal = f(α_hat, α_hat², controls)")
        results.append(f"  R²: {second_stage.rsquared:.4f}")
        ss_names = ["const", "alpha_hat", "alpha_hat_sq", "ln_assets", "years_russia", "ln_n_subs"]
        results.append(f"  {'Variable':<15} {'Coef':>10} {'Std Err':>10} {'t':>8} {'P>|t|':>8}")
        results.append(f"  {'-'*55}")
        for name, coef, se, t, p in zip(
            ss_names, second_stage.params, second_stage.bse,
            second_stage.tvalues, second_stage.pvalues
        ):
            sig = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
            results.append(f"  {name:<15} {coef:>10.4f} {se:>10.4f} {t:>8.3f} {p:>8.4f} {sig}")
    except Exception as e:
        results.append(f"  IV estimation failed: {e}")

    # ──────────────────────────────────────────────────────────────────────
    # Key hypothesis test: β₂ ≠ 0 (U-shape / bimodality)
    # ──────────────────────────────────────────────────────────────────────

    results.append("\n" + "=" * 70)
    results.append("KEY HYPOTHESIS TEST: β₂ (alpha_sq) ≠ 0")
    results.append("  H0: No U-shape (β₂ = 0)")
    results.append("  H1: Bimodal optimality (β₂ ≠ 0)")
    results.append("=" * 70)

    try:
        results.append(f"\n  Spec 1 (Logit, sold): β₂ = {model1.params[2]:.4f}, p = {model1.pvalues[2]:.4f}")
    except:
        pass
    try:
        results.append(f"  Spec 2 (OLS, ordinal): β₂ = {model2.params[2]:.4f}, p = {model2.pvalues[2]:.4f}")
    except:
        pass

    # Print results
    results_text = "\n".join(results)
    print(results_text)

    with open(OUT_FILE, "w") as f:
        f.write(results_text)

    print(f"\n\nResults saved to: {OUT_FILE}")


if __name__ == "__main__":
    main()
