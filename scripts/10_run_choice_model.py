"""
Discrete-choice analysis: exit as a portfolio of real options.

THEORY
------
A multinational holding a Russian subsidiary after Feb 2022 chooses among
three terminal actions, each with a payoff:

  V_sell     = salvage price - transaction costs - exit tax
               (requires a BUYER: exists only if the operation has
                appropriable value a local acquirer can run without the
                parent -- codified IP, brands, plants)
  V_walk     = 0 salvage + write-off, but immediate severance
               (optimal when value is tacit -- embedded in people who
                leave -- so there is nothing a buyer would pay for)
  V_dissolve = liquidation of the legal entity
               (optimal for asset shells: no workforce, no going concern)

Adding iid extreme-value shocks to each payoff yields a multinomial logit
over exit modes (McFadden 1974) -- the estimation below is the reduced
form of that model.

Comparative statics tested:
  H1 (market formation): P(deal exists) increases in patent intensity
  H2 (mode sorting):     P(sell | exit) increases in patents relative to
                         employee intensity; walk-away increases in
                         employee intensity
  H3 (shell liquidation): P(dissolve) decreases in employee intensity
                         and subsidiary size
  H4 (sanctions):        sanctions shrink the buyer set and raise holding
                         costs, amplifying the sorting

Output:
  data/analysis/choice_model_results.txt
"""

import csv
from pathlib import Path

import numpy as np
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import Logit, MNLogit

DATA_DIR = Path(__file__).parent.parent / "data"
IN_FILE = DATA_DIR / "analysis" / "regression_sample.csv"
DEALS_FILE = DATA_DIR / "collected" / "exit_deals_matched.csv"
OUT_FILE = DATA_DIR / "analysis" / "choice_model_results.txt"


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
        model = sm.OLS(y, sm.add_constant(X)).fit(cov_type="HC1")
        results.append(f"\n  {label}: N={int(model.nobs)}, R²={model.rsquared:.4f}")
        results.append(f"  {'Variable':<20} {'Coef':>10}      {'Robust SE':>10} {'P>|t|':>8}")
        results.append(f"  {'-'*60}")
        for name, coef, se, p in zip(["const"] + var_names, model.params, model.bse, model.pvalues):
            results.append(f"  {name:<20} {fmt_coef(coef, p):>14} {se:>10.4f} {p:>8.4f}")
        return model
    except Exception as e:
        results.append(f"  {label} failed: {e}")
        return None


def run_logit(y, X, var_names, label, results):
    try:
        model = Logit(y, sm.add_constant(X)).fit(disp=0, maxiter=200)
        results.append(f"\n  {label}: N={model.nobs:.0f}, Pseudo-R²={model.prsquared:.4f}")
        results.append(f"  {'Variable':<20} {'Coef':>10}      {'Std Err':>10} {'P>|z|':>8}")
        results.append(f"  {'-'*60}")
        for name, coef, se, p in zip(["const"] + var_names, model.params, model.bse, model.pvalues):
            results.append(f"  {name:<20} {fmt_coef(coef, p):>14} {se:>10.4f} {p:>8.4f}")
        return model
    except Exception as e:
        results.append(f"  {label} failed: {e}")
        return None


def main():
    with open(IN_FILE, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    sample = [r for r in rows
              if r["alpha_emp_pctile"] and r["alpha_pat_pctile"]
              and r["ln_assets"] and r["years_in_russia"]]

    emp = np.array([float(r["alpha_emp_pctile"]) for r in sample])
    pat = np.array([float(r["alpha_pat_pctile"]) for r in sample])
    ln_a = np.array([float(r["ln_assets"]) for r in sample])
    yrs = np.array([float(r["years_in_russia"]) for r in sample])
    n_subs = np.array([float(r["n_subsidiaries"]) if r["n_subsidiaries"] else 1 for r in sample])
    ln_subs = np.log1p(n_subs)
    sanc_exp = np.array([float(r["sanctions_exposure"]) for r in sample])
    sanctioned = (sanc_exp > 0).astype(float)

    grade_a = np.array([1.0 if r["grade"] == "A" else 0.0 for r in sample])
    sold = np.array([1.0 if r["action_type"] == "sold" else 0.0 for r in sample])
    diss = np.array([float(r["y_sub_inactive"]) for r in sample])
    has_deal = np.array([float(r["has_deal"]) for r in sample])
    # Choice: 0 = other/ambiguous, 1 = suspended (walk away), 2 = sold
    choice = np.array([2 if r["action_type"] == "sold"
                       else 1 if r["action_type"] == "suspended"
                       else 0 for r in sample])

    alpha = np.array([float(r["alpha"]) for r in sample])

    controls = [ln_a, yrs, ln_subs]
    ctrl_names = ["ln_assets", "years_russia", "ln_n_subs"]

    results = []
    results.append("=" * 78)
    results.append("EXIT AS A PORTFOLIO OF REAL OPTIONS: DISCRETE-CHOICE RESULTS")
    results.append("=" * 78)
    results.append(f"\nSample: {len(sample)} exiters with both α components + controls")
    results.append(f"  Sold: {int(sold.sum())}  Suspended: {int((choice == 1).sum())}  "
                   f"Other: {int((choice == 0).sum())}")
    results.append(f"  Grade A: {int(grade_a.sum())}  Sanctioned sectors: {int(sanctioned.sum())}")
    results.append(f"  Matched deals: {int(has_deal.sum())}  Subsidiary dissolved: {int(diss.sum())}")

    # 2x2 typology table
    results.append("\n" + "─" * 78)
    results.append("Knowledge-structure typology (median splits)")
    results.append("─" * 78)
    emp_med, pat_med = np.median(emp), np.median(pat)
    results.append(f"  {'Quadrant':<28} {'N':>4} {'Sold':>6} {'Susp':>6} {'GradeA':>7} {'Dissolved':>10} {'HasDeal':>8}")
    quads = [
        ("Tacit franchise  (E+ P-)", (emp >= emp_med) & (pat < pat_med)),
        ("Integrated ops   (E+ P+)", (emp >= emp_med) & (pat >= pat_med)),
        ("License fortress (E- P+)", (emp < emp_med) & (pat >= pat_med)),
        ("Asset shell      (E- P-)", (emp < emp_med) & (pat < pat_med)),
    ]
    for label, mask in quads:
        n = int(mask.sum())
        results.append(
            f"  {label:<28} {n:>4} {sold[mask].mean():>6.0%} "
            f"{(choice[mask] == 1).mean():>6.0%} {grade_a[mask].mean():>7.0%} "
            f"{diss[mask].mean():>10.1%} {has_deal[mask].mean():>8.0%}")

    # ═════════════════════════════════════════════════════════════════════
    # H1: MARKET FORMATION — a buyer exists only for appropriable knowledge
    # ═════════════════════════════════════════════════════════════════════
    results.append("\n\n" + "═" * 78)
    results.append("H1: MARKET FORMATION — P(matched M&A deal exists)")
    results.append("  Prediction: buyers pay for codified, appropriable knowledge (patents),")
    results.append("  not for tacit organizational knowledge that departs with employees.")
    results.append("═" * 78)

    X_h1 = np.column_stack([pat, emp] + controls)
    v_h1 = ["pat_pctile", "emp_pctile"] + ctrl_names
    run_ols(has_deal, X_h1, v_h1, "H1a: LPM P(has deal)", results)
    run_logit(has_deal, X_h1, v_h1, "H1b: Logit P(has deal)", results)

    # ═════════════════════════════════════════════════════════════════════
    # H2: MODE SORTING — sell vs walk away, conditional on committed exit
    # ═════════════════════════════════════════════════════════════════════
    results.append("\n\n" + "═" * 78)
    results.append("H2: MODE SORTING — P(Sold | Grade A) and the three-mode choice")
    results.append("═" * 78)

    ga = grade_a == 1
    X_h2 = np.column_stack([pat[ga], emp[ga]] + [c[ga] for c in controls])
    v_h2 = ["pat_pctile", "emp_pctile"] + ctrl_names
    run_ols(sold[ga], X_h2, v_h2, "H2a: LPM P(Sold|A), components", results)

    X_h2c = np.column_stack([alpha[ga]] + [c[ga] for c in controls])
    run_ols(sold[ga], X_h2c, ["alpha"] + ctrl_names,
            "H2b: LPM P(Sold|A), composite α", results)

    # Multinomial logit over the three modes (RUM reduced form)
    results.append("\n  H2c: Multinomial logit over {other, suspended, sold} (base=other)")
    X_mnl = sm.add_constant(np.column_stack([pat, emp] + controls))
    v_mnl = ["const", "pat_pctile", "emp_pctile"] + ctrl_names
    try:
        mnl = MNLogit(choice, X_mnl).fit(disp=0, maxiter=200)
        params, pvals = np.asarray(mnl.params), np.asarray(mnl.pvalues)
        for j, lab in enumerate(["suspended vs other", "sold vs other"]):
            results.append(f"\n    --- {lab} ---")
            for i, nm in enumerate(v_mnl):
                results.append(f"    {nm:<20} {fmt_coef(params[i, j], pvals[i, j]):>14} "
                               f"(p={pvals[i, j]:.4f})")
        results.append(f"\n    N={len(choice)}, Pseudo-R²={mnl.prsquared:.4f}")
    except Exception as e:
        results.append(f"    MNLogit failed: {e}")

    # ═════════════════════════════════════════════════════════════════════
    # H3: SHELL LIQUIDATION — dissolution is for entities with no going concern
    # ═════════════════════════════════════════════════════════════════════
    results.append("\n\n" + "═" * 78)
    results.append("H3: SHELL LIQUIDATION — P(subsidiary dissolved)")
    results.append("  Prediction: dissolution decreases in employee intensity (a workforce")
    results.append("  = a going concern worth transferring) and in subsidiary size.")
    results.append("═" * 78)

    X_h3 = np.column_stack([emp, pat] + controls)
    v_h3 = ["emp_pctile", "pat_pctile"] + ctrl_names
    run_ols(diss, X_h3, v_h3, "H3a: LPM P(dissolved)", results)
    run_logit(diss, X_h3, v_h3, "H3b: Logit P(dissolved)", results)

    # Dissolution rate by employee-intensity tercile
    results.append("\n  Dissolution rate by employee-intensity tercile:")
    terc = np.percentile(emp, [33.3, 66.7])
    for lo, hi, lab in [(-0.01, terc[0], "Low emp (shells)"),
                        (terc[0], terc[1], "Mid emp"),
                        (terc[1], 1.01, "High emp (going concerns)")]:
        m = (emp > lo) & (emp <= hi)
        results.append(f"    {lab:<26}: n={int(m.sum()):3d}, dissolved={diss[m].mean():.1%}")

    # ═════════════════════════════════════════════════════════════════════
    # H4: SANCTIONS — choice-set restriction and holding-cost shock
    # ═════════════════════════════════════════════════════════════════════
    results.append("\n\n" + "═" * 78)
    results.append("H4: SANCTIONS — amplification of the sorting")
    results.append("═" * 78)

    X_h4 = np.column_stack([alpha, alpha**2] + controls)
    v_h4 = ["alpha", "alpha_sq"] + ctrl_names
    s = sanctioned == 1
    run_ols(grade_a[s], np.column_stack([alpha[s], alpha[s]**2] + [c[s] for c in controls]),
            v_h4, "H4a: P(Grade A), sanctioned sectors", results)
    run_ols(grade_a[~s], np.column_stack([alpha[~s], alpha[~s]**2] + [c[~s] for c in controls]),
            v_h4, "H4b: P(Grade A), non-sanctioned", results)

    X_int = np.column_stack([pat, emp, sanctioned, pat * sanctioned, emp * sanctioned] + controls)
    v_int = ["pat_pctile", "emp_pctile", "sanctioned", "pat×sanc", "emp×sanc"] + ctrl_names
    run_ols(grade_a, X_int, v_int, "H4c: P(Grade A), component interactions", results)

    # ═════════════════════════════════════════════════════════════════════
    # DESCRIPTIVE: fire-sale prices over time (small N — descriptive only)
    # ═════════════════════════════════════════════════════════════════════
    results.append("\n\n" + "═" * 78)
    results.append("DESCRIPTIVE: deal values by months since invasion (N small)")
    results.append("═" * 78)
    from datetime import date
    INVASION = date(2022, 2, 24)
    vals = []
    with open(DEALS_FILE, encoding="utf-8") as f:
        for d in csv.DictReader(f):
            v = safe_float(d.get("deal_value_mn_usd", ""))
            dt = d.get("announce_date", "").strip()
            if v is None or v <= 0 or not dt:
                continue
            try:
                p = dt.split("/")
                months = (date(int(p[0]), int(p[1]), int(p[2])) - INVASION).days / 30.44
            except (ValueError, IndexError):
                continue
            if months >= 0:
                vals.append((months, v))
    for lo, hi, lab in [(0, 6, "0-6 months"), (6, 12, "6-12 months"),
                        (12, 24, "12-24 months"), (24, 48, "24-48 months")]:
        bucket = [v for m, v in vals if lo <= m < hi]
        if bucket:
            results.append(f"  {lab:<14}: n={len(bucket):2d}, "
                           f"median=${np.median(bucket):8.1f}mn, mean=${np.mean(bucket):8.1f}mn")
    results.append("  Note: composition effects dominate at this N; the exit-tax escalation")
    results.append("  (10% → 35%) and mandatory 50% discount (Dec 2022) bind on later deals.")

    text = "\n".join(results)
    print(text)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"\nSaved: {OUT_FILE}")


if __name__ == "__main__":
    main()
