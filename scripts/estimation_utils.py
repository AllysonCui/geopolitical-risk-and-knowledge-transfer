"""
Shared helpers for the model-based estimation scripts (10, 11, 12).

Provides: sample loading, design-matrix construction, and a wild cluster
bootstrap for settings with few clusters (~35-40 home countries), where
analytic cluster-robust standard errors are unreliable.
"""

import csv
from pathlib import Path

import numpy as np

DATA_DIR = Path(__file__).parent.parent / "data" / "analysis"
SAMPLE_FILE = DATA_DIR / "regression_sample.csv"


def safe_float(val):
    if val is None or str(val).strip() == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def load_sample():
    with open(SAMPLE_FILE, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def col(rows, key, default=None):
    """Extract a float column; None where missing."""
    out = []
    for r in rows:
        v = safe_float(r.get(key))
        out.append(v if v is not None else default)
    return out


def complete_rows(rows, float_keys, str_keys=()):
    """Rows with non-missing values for every listed key."""
    keep = []
    for r in rows:
        if any(safe_float(r.get(k)) is None for k in float_keys):
            continue
        if any(not (r.get(k) or "").strip() for k in str_keys):
            continue
        keep.append(r)
    return keep


def dummies(values, drop_first=True, min_count=1, other_label="OTHER"):
    """Categorical → (matrix, labels). Small cells pooled into OTHER."""
    from collections import Counter
    counts = Counter(values)
    mapped = [v if counts[v] >= min_count else other_label for v in values]
    levels = sorted(set(mapped))
    if drop_first:
        levels_used = levels[1:]
    else:
        levels_used = levels
    mat = np.zeros((len(mapped), len(levels_used)))
    for i, v in enumerate(mapped):
        if v in levels_used:
            mat[i, levels_used.index(v)] = 1.0
    return mat, levels_used


def fmt_coef(coef, pval):
    sig = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.1 else ""
    return f"{coef:>10.4f}{sig}"


def ols_report(y, X, var_names, label, results, cov_type="HC1"):
    import statsmodels.api as sm
    model = sm.OLS(y, sm.add_constant(X)).fit(cov_type=cov_type)
    results.append(f"\n  {label}: N={int(model.nobs)}, R²={model.rsquared:.4f}")
    results.append(f"  {'Variable':<26} {'Coef':>10}      {'Rob. SE':>10} {'t':>8} {'P>|t|':>8}")
    results.append(f"  {'-' * 72}")
    names = ["const"] + var_names
    for name, coef, se, t, p in zip(names, model.params, model.bse, model.tvalues, model.pvalues):
        results.append(f"  {name:<26} {fmt_coef(coef, p):>14} {se:>10.4f} {t:>8.3f} {p:>8.4f}")
    return model


def probit_report(y, X, var_names, label, results, maxiter=200):
    import statsmodels.api as sm
    try:
        model = sm.Probit(y, sm.add_constant(X)).fit(disp=0, maxiter=maxiter)
    except np.linalg.LinAlgError:
        # Singular Hessian under Newton (quasi-separation); BFGS is slower
        # but does not invert the Hessian at every step.
        model = sm.Probit(y, sm.add_constant(X)).fit(disp=0, maxiter=maxiter,
                                                     method="bfgs")
    results.append(f"\n  {label}: N={model.nobs:.0f}, Pseudo-R²={model.prsquared:.4f}, Log-L={model.llf:.1f}")
    results.append(f"  {'Variable':<26} {'Coef':>10}      {'Std Err':>10} {'z':>8} {'P>|z|':>8}   {'AME':>10}")
    results.append(f"  {'-' * 84}")
    names = ["const"] + var_names
    try:
        mfx = list(model.get_margeff(at="overall").margeff)
    except Exception:
        mfx = [None] * len(var_names)
    for i, (name, coef, se, z, p) in enumerate(
            zip(names, model.params, model.bse, model.tvalues, model.pvalues)):
        m = ""
        if i > 0 and i - 1 < len(mfx) and mfx[i - 1] is not None:
            m = f"{mfx[i - 1]:>10.4f}"
        results.append(f"  {name:<26} {fmt_coef(coef, p):>14} {se:>10.4f} {z:>8.3f} {p:>8.4f}   {m}")
    return model


def wild_cluster_bootstrap_p(y, X, clusters, coef_idx, n_boot=999, seed=42):
    """
    Wild cluster bootstrap-t p-value (Rademacher weights, null imposed)
    for one coefficient of a linear model — Cameron, Gelbach & Miller
    (2008). Used because ~35-40 home-country clusters is too few for
    analytic cluster-robust inference.

    y: (n,), X: (n,k) WITHOUT constant (added here), clusters: (n,) labels,
    coef_idx: index into X columns (0-based, constant excluded).
    Returns (beta_hat, boot_p).
    """
    rng = np.random.default_rng(seed)
    n = len(y)
    Xc = np.column_stack([np.ones(n), X])
    j = coef_idx + 1  # account for constant

    cluster_labels = np.asarray(clusters)
    uniq = np.unique(cluster_labels)
    cluster_masks = [cluster_labels == c for c in uniq]

    def cluster_se(resid, Xmat, XtXinv):
        meat = np.zeros((Xmat.shape[1], Xmat.shape[1]))
        for m in cluster_masks:
            s = Xmat[m].T @ resid[m]
            meat += np.outer(s, s)
        V = XtXinv @ meat @ XtXinv
        return np.sqrt(np.diag(V))

    XtXinv = np.linalg.pinv(Xc.T @ Xc)
    beta = XtXinv @ (Xc.T @ y)
    resid = y - Xc @ beta
    se = cluster_se(resid, Xc, XtXinv)
    t_obs = beta[j] / se[j] if se[j] > 0 else 0.0

    # Restricted model (null: beta_j = 0)
    Xr = np.delete(Xc, j, axis=1)
    XtXinv_r = np.linalg.pinv(Xr.T @ Xr)
    beta_r = XtXinv_r @ (Xr.T @ y)
    fit_r = Xr @ beta_r
    resid_r = y - fit_r

    t_boot = np.empty(n_boot)
    for b in range(n_boot):
        w = rng.choice([-1.0, 1.0], size=len(uniq))
        e_b = resid_r.copy()
        for wi, m in zip(w, cluster_masks):
            e_b[m] *= wi
        y_b = fit_r + e_b
        beta_b = XtXinv @ (Xc.T @ y_b)
        resid_b = y_b - Xc @ beta_b
        se_b = cluster_se(resid_b, Xc, XtXinv)
        t_boot[b] = beta_b[j] / se_b[j] if se_b[j] > 0 else 0.0

    p = (np.sum(np.abs(t_boot) >= abs(t_obs)) + 1) / (n_boot + 1)
    return beta[j], p
