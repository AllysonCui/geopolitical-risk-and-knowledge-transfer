"""
Run main regression specifications and robustness checks.

Main specification:
  Y_i = β₀ + β₁α_i + β₂α_i² + X_i'γ + μ_j + ε_i

Dependent variables tested:
  (1) Binary: Grade A (clean exit) vs Grade B (partial)
  (2) Binary: sold=1 vs not sold=0
  (3) Ordinal: sold=3, nationalized=2, suspended=1, other=0
  (4) 2SLS IV with sanctions instrument
  (5) Binary: Any subsidiary formally dissolved (Orbis inactive flag)
  (6) Binary: Grade A AND sold (cleanest exit with value recovery)
  (7) Binary: Suspended operations (stuck in the middle)

α = composite replicability index (emp_intensity - patent_intensity),
    already percentile-ranked to [0,1] by script 08

Controls X_i: ln(assets), years_in_russia, ln(n_subsidiaries)
Fixed effects μ_j: industry (Yale classification)
Instrument Z: sanctions_exposure

Robustness:
  R1: Employee intensity only as α
  R2: Patent intensity only as α
  R3: Separate α components (non-composite)
  R4: Excluding financial sector

Output:
  data/analysis/regression_results.txt
  data/analysis/regression_tables.csv
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
    from statsmodels.discrete.discrete_model import Logit, Probit
except ImportError:
    raise SystemExit("statsmodels not installed: pip install statsmodels")

DATA_DIR = Path(__file__).parent.parent / "data" / "analysis"
IN_FILE = DATA_DIR / "regression_sample.csv"
OUT_FILE = DATA_DIR / "regression_results.txt"
TABLE_FILE = DATA_DIR / "regression_tables.csv"


def load_data():
    with open(IN_FILE, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def safe_float(val):
    if not val or val.strip() == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def fmt_coef(coef, pval):
    sig = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.1 else ""
    return f"{coef:>10.4f}{sig}"


def run_ols(y, X, var_names, label, results):
    try:
        model = sm.OLS(y, sm.add_constant(X)).fit(cov_type='HC1')
        results.append(f"\n  {label}: N={int(model.nobs)}, R²={model.rsquared:.4f}, Adj-R²={model.rsquared_adj:.4f}")
        results.append(f"  F-stat: {model.fvalue:.3f} (p={model.f_pvalue:.4f})")
        results.append(f"  {'Variable':<20} {'Coef':>10}      {'Robust SE':>10} {'t':>8} {'P>|t|':>8}")
        results.append(f"  {'-'*65}")
        names = ["const"] + var_names
        for name, coef, se, t, p in zip(names, model.params, model.bse, model.tvalues, model.pvalues):
            results.append(f"  {name:<20} {fmt_coef(coef, p):>14} {se:>10.4f} {t:>8.3f} {p:>8.4f}")
        return model
    except Exception as e:
        results.append(f"  {label} failed: {e}")
        return None


def run_logit(y, X, var_names, label, results):
    try:
        model = Logit(y, sm.add_constant(X)).fit(disp=0, maxiter=100)
        results.append(f"\n  {label}: N={model.nobs:.0f}, Pseudo-R²={model.prsquared:.4f}, Log-L={model.llf:.1f}")
        results.append(f"  {'Variable':<20} {'Coef':>10}      {'Std Err':>10} {'z':>8} {'P>|z|':>8}   {'Marg Eff':>10}")
        results.append(f"  {'-'*75}")
        names = ["const"] + var_names
        # Marginal effects at means
        try:
            mfx = model.get_margeff(at='mean')
            mfx_vals = list(mfx.margeff)
        except:
            mfx_vals = [None] * len(var_names)

        for i, (name, coef, se, z, p) in enumerate(zip(names, model.params, model.bse, model.tvalues, model.pvalues)):
            mfx_str = ""
            if i > 0 and i-1 < len(mfx_vals) and mfx_vals[i-1] is not None:
                mfx_str = f"{mfx_vals[i-1]:>10.4f}"
            results.append(f"  {name:<20} {fmt_coef(coef, p):>14} {se:>10.4f} {z:>8.3f} {p:>8.4f}   {mfx_str}")
        return model
    except Exception as e:
        results.append(f"  {label} failed: {e}")
        return None


def main():
    rows = load_data()
    results = []
    table_rows = []

    results.append("=" * 75)
    results.append("REGRESSION RESULTS")
    results.append("Bimodal Knowledge Transfer Under Geopolitical Risk")
    results.append("Y_i = β₀ + β₁α_i + β₂α_i² + X_i'γ + μ_j + ε_i")
    results.append("=" * 75)

    # ── Prepare sample ────────────────────────────────────────────────────
    sample = []
    for r in rows:
        alpha = safe_float(r.get("alpha"))
        ln_a = safe_float(r.get("ln_assets"))
        yrs = safe_float(r.get("years_in_russia"))
        if alpha is not None and ln_a is not None and yrs is not None:
            sample.append(r)

    results.append(f"\nSample: N = {len(sample)} firms with α + controls")
    results.append(f"  Grade A (clean exit): {sum(1 for r in sample if r['grade']=='A')}")
    results.append(f"  Grade B (partial): {sum(1 for r in sample if r['grade']=='B')}")
    results.append(f"  Action sold: {sum(1 for r in sample if r['action_type']=='sold')}")
    results.append(f"  Action suspended: {sum(1 for r in sample if r['action_type']=='suspended')}")
    results.append(f"  Action other: {sum(1 for r in sample if r['action_type']=='other')}")

    # Variables
    alpha = np.array([float(r["alpha"]) for r in sample])
    alpha_sq = alpha ** 2
    ln_assets = np.array([float(r["ln_assets"]) for r in sample])
    years_russia = np.array([float(r["years_in_russia"]) for r in sample])
    n_subs = np.array([float(r["n_subsidiaries"]) if r["n_subsidiaries"] else 1 for r in sample])
    ln_subs = np.log1p(n_subs)
    sanctions = np.array([float(r["sanctions_exposure"]) for r in sample])

    # Industry dummies (Yale classification — better coverage than NACE)
    industries = [r.get("industry", "Other") for r in sample]
    unique_ind = sorted(set(industries))
    ind_dummies = np.zeros((len(sample), max(0, len(unique_ind) - 1)))
    for i, ind in enumerate(industries):
        idx = unique_ind.index(ind)
        if idx > 0:
            ind_dummies[i, idx - 1] = 1

    X_base = np.column_stack([alpha, alpha_sq, ln_assets, years_russia, ln_subs])
    var_names_base = ["alpha", "alpha_sq", "ln_assets", "years_russia", "ln_n_subs"]

    X_fe = np.column_stack([X_base, ind_dummies])
    var_names_fe = var_names_base + [f"ind_{s[:8]}" for s in unique_ind[1:]]

    # ── SPECIFICATION 1: P(Grade A) — clean exit vs partial ───────────────
    results.append("\n" + "━" * 75)
    results.append("SPECIFICATION 1: P(Clean Exit) — Grade A=1 vs Grade B=0")
    results.append("━" * 75)

    y_grade = np.array([1.0 if r["grade"] == "A" else 0.0 for r in sample])
    results.append(f"  Y=1: {int(y_grade.sum())}  |  Y=0: {int(len(y_grade) - y_grade.sum())}")

    m1a = run_logit(y_grade, X_base, var_names_base, "Model 1a: Logit (no FE)", results)
    m1b = run_logit(y_grade, X_fe, var_names_fe[:len(var_names_base)+2], "Model 1b: Logit (industry FE)", results)
    m1c = run_ols(y_grade, X_base, var_names_base, "Model 1c: LPM (no FE)", results)
    m1d = run_ols(y_grade, X_fe, var_names_fe, "Model 1d: LPM (industry FE)", results)

    # ── SPECIFICATION 2: P(Sold) — sold vs not sold ───────────────────────
    results.append("\n" + "━" * 75)
    results.append("SPECIFICATION 2: P(Sold) — sold=1 vs not=0")
    results.append("━" * 75)

    y_sold = np.array([1.0 if r["action_type"] == "sold" else 0.0 for r in sample])
    results.append(f"  Y=1: {int(y_sold.sum())}  |  Y=0: {int(len(y_sold) - y_sold.sum())}")

    m2a = run_logit(y_sold, X_base, var_names_base, "Model 2a: Logit (no FE)", results)
    m2b = run_ols(y_sold, X_base, var_names_base, "Model 2b: LPM (no FE)", results)
    m2c = run_ols(y_sold, X_fe, var_names_fe, "Model 2c: LPM (industry FE)", results)

    # ── SPECIFICATION 3: Exit completeness (ordinal) ──────────────────────
    results.append("\n" + "━" * 75)
    results.append("SPECIFICATION 3: Exit Completeness (ordinal)")
    results.append("━" * 75)

    score_map = {"sold": 3, "nationalized": 2, "suspended": 1, "other": 0}
    y_ord = np.array([score_map.get(r["action_type"], 0) for r in sample], dtype=float)

    m3a = run_ols(y_ord, X_base, var_names_base, "Model 3a: OLS (no FE)", results)
    m3b = run_ols(y_ord, X_fe, var_names_fe, "Model 3b: OLS (industry FE)", results)

    # ── SPECIFICATION 4: 2SLS IV ──────────────────────────────────────────
    results.append("\n" + "━" * 75)
    results.append("SPECIFICATION 4: 2SLS IV — sanctions instruments for α")
    results.append("━" * 75)

    X_iv_exog = np.column_stack([ln_assets, years_russia, ln_subs])
    X_first = np.column_stack([sanctions, ln_assets, years_russia, ln_subs])

    try:
        first = sm.OLS(alpha, sm.add_constant(X_first)).fit()
        results.append(f"\n  First stage: α = f(sanctions_exposure, controls)")
        results.append(f"  F-stat: {first.fvalue:.3f}, R²: {first.rsquared:.4f}")
        fs_names = ["const", "sanctions_exp", "ln_assets", "years_russia", "ln_n_subs"]
        results.append(f"  {'Variable':<20} {'Coef':>10}      {'Std Err':>10} {'t':>8} {'P>|t|':>8}")
        results.append(f"  {'-'*65}")
        for name, coef, se, t, p in zip(fs_names, first.params, first.bse, first.tvalues, first.pvalues):
            results.append(f"  {name:<20} {fmt_coef(coef, p):>14} {se:>10.4f} {t:>8.3f} {p:>8.4f}")

        f_excl = first.tvalues[1]**2
        results.append(f"\n  Excluded instrument F: {f_excl:.2f} {'(PASS: F>10)' if f_excl > 10 else '(WEAK: F<10)'}")

        alpha_hat = first.fittedvalues
        X_2sls = np.column_stack([alpha_hat, alpha_hat**2, ln_assets, years_russia, ln_subs])
        second = sm.OLS(y_grade, sm.add_constant(X_2sls)).fit()
        results.append(f"\n  Second stage: P(Grade A) = f(α_hat, α_hat², controls)")
        ss_names = ["const", "alpha_hat", "alpha_hat_sq", "ln_assets", "years_russia", "ln_n_subs"]
        results.append(f"  {'Variable':<20} {'Coef':>10}      {'Std Err':>10} {'t':>8} {'P>|t|':>8}")
        results.append(f"  {'-'*65}")
        for name, coef, se, t, p in zip(ss_names, second.params, second.bse, second.tvalues, second.pvalues):
            results.append(f"  {name:<20} {fmt_coef(coef, p):>14} {se:>10.4f} {t:>8.3f} {p:>8.4f}")
    except Exception as e:
        results.append(f"  IV failed: {e}")

    # ── SPECIFICATION 5: P(Any subsidiary formally dissolved) ──────────
    results.append("\n" + "━" * 75)
    results.append("SPECIFICATION 5: P(Subsidiary Dissolved) — any sub inactive=1 vs 0")
    results.append("━" * 75)

    y_sub_inact = np.array([float(r.get("y_sub_inactive", 0)) for r in sample])
    results.append(f"  Y=1: {int(y_sub_inact.sum())}  |  Y=0: {int(len(y_sub_inact) - y_sub_inact.sum())}")

    m5a = run_logit(y_sub_inact, X_base, var_names_base, "Model 5a: Logit (no FE)", results)
    m5b = run_ols(y_sub_inact, X_base, var_names_base, "Model 5b: LPM (no FE)", results)
    m5c = run_ols(y_sub_inact, X_fe, var_names_fe, "Model 5c: LPM (industry FE)", results)

    # ── SPECIFICATION 6: P(Grade A + Sold) — cleanest exit ───────────
    results.append("\n" + "━" * 75)
    results.append("SPECIFICATION 6: P(Grade A + Sold) — clean exit WITH sale=1 vs 0")
    results.append("━" * 75)

    y_a_sold = np.array([float(r.get("y_grade_a_sold", 0)) for r in sample])
    results.append(f"  Y=1: {int(y_a_sold.sum())}  |  Y=0: {int(len(y_a_sold) - y_a_sold.sum())}")

    m6a = run_logit(y_a_sold, X_base, var_names_base, "Model 6a: Logit (no FE)", results)
    m6b = run_ols(y_a_sold, X_base, var_names_base, "Model 6b: LPM (no FE)", results)
    m6c = run_ols(y_a_sold, X_fe, var_names_fe, "Model 6c: LPM (industry FE)", results)

    # ── SPECIFICATION 7: P(Suspended) — stuck in the middle ──────────
    results.append("\n" + "━" * 75)
    results.append("SPECIFICATION 7: P(Suspended) — operations suspended=1 vs 0")
    results.append("━" * 75)

    y_susp = np.array([float(r.get("y_suspended", 0)) for r in sample])
    results.append(f"  Y=1: {int(y_susp.sum())}  |  Y=0: {int(len(y_susp) - y_susp.sum())}")

    m7a = run_logit(y_susp, X_base, var_names_base, "Model 7a: Logit (no FE)", results)
    m7b = run_ols(y_susp, X_base, var_names_base, "Model 7b: LPM (no FE)", results)
    m7c = run_ols(y_susp, X_fe, var_names_fe, "Model 7c: LPM (industry FE)", results)

    # ── ROBUSTNESS CHECKS ─────────────────────────────────────────────────
    results.append("\n" + "━" * 75)
    results.append("ROBUSTNESS CHECKS")
    results.append("━" * 75)

    # R1: Employee intensity only
    results.append("\n  R1: α = employee intensity only (no patent component)")
    emp_pctile = np.array([float(r["alpha_emp_pctile"]) if r.get("alpha_emp_pctile") else 0.5
                           for r in sample])
    X_r1 = np.column_stack([emp_pctile, emp_pctile**2, ln_assets, years_russia, ln_subs])
    run_ols(y_grade, X_r1, ["emp_pctile", "emp_pctile_sq", "ln_assets", "years_russia", "ln_n_subs"],
            "R1: LPM P(Grade A)", results)

    # R2: Patent intensity only
    results.append("\n  R2: α = patent intensity only (no employee component)")
    pat_pctile = np.array([float(r["alpha_pat_pctile"]) if r.get("alpha_pat_pctile") else 0.5
                           for r in sample])
    X_r2 = np.column_stack([pat_pctile, pat_pctile**2, ln_assets, years_russia, ln_subs])
    run_ols(y_grade, X_r2, ["pat_pctile", "pat_pctile_sq", "ln_assets", "years_russia", "ln_n_subs"],
            "R2: LPM P(Grade A)", results)

    # R3: Both components separately
    results.append("\n  R3: Both α components entered separately")
    X_r3 = np.column_stack([emp_pctile, emp_pctile**2, pat_pctile, pat_pctile**2,
                             ln_assets, years_russia, ln_subs])
    run_ols(y_grade, X_r3,
            ["emp_pctile", "emp_pctile_sq", "pat_pctile", "pat_pctile_sq",
             "ln_assets", "years_russia", "ln_n_subs"],
            "R3: LPM P(Grade A)", results)

    # R4: Excluding financial sector
    results.append("\n  R4: Excluding financial sector")
    non_fin = [i for i, r in enumerate(sample) if r.get("industry", "") != "Financials"]
    if len(non_fin) > 50:
        X_r4 = X_base[non_fin]
        y_r4 = y_grade[non_fin]
        results.append(f"  Sample: {len(non_fin)} firms (excl. {len(sample)-len(non_fin)} financials)")
        run_ols(y_r4, X_r4, var_names_base, "R4: LPM P(Grade A)", results)

    # R5: Linear α only (no quadratic — test if U-shape matters)
    results.append("\n  R5: Linear α only (no quadratic term)")
    X_r5 = np.column_stack([alpha, ln_assets, years_russia, ln_subs])
    run_ols(y_grade, X_r5, ["alpha", "ln_assets", "years_russia", "ln_n_subs"],
            "R5: LPM P(Grade A)", results)

    # ── KEY HYPOTHESIS TESTS ──────────────────────────────────────────────
    results.append("\n" + "=" * 75)
    results.append("KEY HYPOTHESIS TESTS")
    results.append("=" * 75)
    results.append("\nH0: β₂ = 0 (no U-shape)  vs  H1: β₂ ≠ 0 (bimodal optimality)")

    for label, model in [("Spec 1a (Logit, Grade A)", m1a),
                         ("Spec 1c (LPM, Grade A)", m1c),
                         ("Spec 2a (Logit, Sold)", m2a),
                         ("Spec 3a (OLS, Ordinal)", m3a),
                         ("Spec 5a (Logit, Sub Dissolved)", m5a),
                         ("Spec 6a (Logit, A+Sold)", m6a),
                         ("Spec 7a (Logit, Suspended)", m7a)]:
        if model:
            try:
                b2 = model.params[2]
                p2 = model.pvalues[2]
                sig = "***" if p2 < 0.01 else "**" if p2 < 0.05 else "*" if p2 < 0.1 else "n.s."
                results.append(f"  {label}: β₂ = {b2:.4f}, p = {p2:.4f} [{sig}]")
            except:
                pass

    results.append("\nH0: β₁ = 0 (α has no linear effect)")
    for label, model in [("Spec 1a (Logit, Grade A)", m1a),
                         ("Spec 1c (LPM, Grade A)", m1c)]:
        if model:
            try:
                b1 = model.params[1]
                p1 = model.pvalues[1]
                sig = "***" if p1 < 0.01 else "**" if p1 < 0.05 else "*" if p1 < 0.1 else "n.s."
                results.append(f"  {label}: β₁ = {b1:.4f}, p = {p1:.4f} [{sig}]")
            except:
                pass

    # ── TURNING POINT ─────────────────────────────────────────────────────
    if m1c and m1c.params[2] != 0:
        turning = -m1c.params[1] / (2 * m1c.params[2])
        results.append(f"\n  Implied turning point (LPM Grade A): α* = {turning:.4f}")
        if 0 < turning < 1:
            results.append(f"  → Interior minimum at α = {turning:.2f} (within [0,1] range)")
        else:
            results.append(f"  → Outside [0,1] range — no interior U-shape")

    results_text = "\n".join(results)
    print(results_text)

    with open(OUT_FILE, "w") as f:
        f.write(results_text)

    print(f"\n\nResults saved to: {OUT_FILE}")


if __name__ == "__main__":
    main()
