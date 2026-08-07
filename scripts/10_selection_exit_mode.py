"""
Q1 — Is knowledge structure associated with sale rather than exit without a sale?

Heckman-style two-stage estimation on the FULL population of matched
foreign parents with Russian subsidiaries (all Yale grades A–F), fixing
the selection problem induced by conditioning on exiters:

  Stage 1 (selection, full population):
      Pr(CleanExit_i = 1) = Φ(γ₁ LabPct_i + γ₂ Z_i + X_i'γ)
  Stage 2 (mode, completed exits only, seized dropped):
      Pr(Sell_i = 1 | CleanExit) = Φ(β₁ PatPct_i + β₂ LabPct_i + X_i'β + ρ λ_i)

λ_i is the inverse Mills ratio from stage 1 (control-function
approximation of the FIML heckprobit, which statsmodels does not
provide — see the LIMITATIONS note at the bottom of the output).

DATA CONSTRAINTS THAT SHAPE THE SPECIFICATION:
  * The Lens.org patent pull (script 02) covered only Grade A/B exiters,
    so PatPct is unobserved for the C/D/F stayers and CANNOT enter the
    selection stage yet. Stage 1 therefore uses labor intensity, the
    exclusion restriction, and controls; patent intensity enters stage 2.
    Script 02 now queries the full panel — re-run it to lift this.
  * The intended exclusion restriction was B2C × home-country public
    pressure. In the current sample every B2C firm has a coalition home
    country (the B2C × non-coalition cell is empty), so the interaction
    has no identifying variation and is dropped: Z = B2C alone, with
    coalition membership included as a stage-1 control. Boycott-pressure
    logic: consumer-facing status shifts WHETHER a firm exits, not the
    mechanics of how an asset transfers.

Model predictions (docs/formal_model.md):
  Prediction 1: β(PatPct) > 0 if parent patent intensity is a useful proxy
                for transferable value that a buyer can retain;
                β(LabPct) < 0 if labor intensity captures value tied to
                employees and routines that may not survive a change in
                ownership. These are tests of associations implied by the
                model, not direct estimates of knowledge transferability.

Inference: default probit SEs; wild cluster bootstrap (home country,
Rademacher, null-imposed, 999 reps) on the LPM analog for the two key
stage-2 coefficients.

Input:  data/analysis/regression_sample.csv
Output: data/analysis/results_10_selection_exit_mode.txt
"""

import numpy as np
from scipy import stats as spstats

from estimation_utils import (DATA_DIR, load_sample, safe_float, complete_rows,
                              dummies, probit_report, wild_cluster_bootstrap_p)

OUT_FILE = DATA_DIR / "results_10_selection_exit_mode.txt"


def main():
    rows = load_sample()
    results = []
    results.append("=" * 78)
    results.append("Q1: SELECTION-CORRECTED EXIT MODE — SALE vs EXIT WITHOUT SALE")
    results.append("Heckman-style two-stage (probit selection + IMR control function)")
    results.append("=" * 78)

    # Population: all grades, complete on stage-1 covariates (NOT patents —
    # patent data currently exists only for exiters; see header).
    need = ["lab_pctile", "ln_assets", "years_in_russia"]
    pop = complete_rows(rows, need)
    pop = [r for r in pop if r.get("exit_mode") != "seized"]

    lab = np.array([float(r["lab_pctile"]) for r in pop])
    ln_a = np.array([float(r["ln_assets"]) for r in pop])
    yrs = np.array([float(r["years_in_russia"]) for r in pop])
    nsub = np.array([safe_float(r["n_subsidiaries"]) or 1 for r in pop])
    ln_subs = np.log1p(nsub)
    b2c = np.array([float(r["b2c"]) for r in pop])
    coalition = np.array([safe_float(r["sanctions_coalition"]) or 0 for r in pop])

    clean_exit = np.array([float(r["clean_exit"]) for r in pop])
    exiter_ab = np.array([float(r["exiter"]) for r in pop])
    countries = [r["country"] for r in pop]
    ind_mat, ind_labels = dummies([r["industry"] or "Other" for r in pop], min_count=15)

    n_b2c_noncoal = int(((b2c == 1) & (coalition == 0)).sum())
    results.append(f"\nPopulation: {len(pop)} matched firms (all grades; seized dropped)")
    results.append(f"  Completed exits (Grade A): {int(clean_exit.sum())} | "
                   f"Exiters A/B: {int(exiter_ab.sum())} | "
                   f"Stayers C/D/F: {int(len(pop) - exiter_ab.sum())}")
    results.append(f"  B2C firms: {int(b2c.sum())} | Non-coalition home: "
                   f"{int((coalition == 0).sum())} | B2C × non-coalition cell: "
                   f"{n_b2c_noncoal} (interaction dropped — near-empty cell)")

    # ── Stage 1: selection probit on the full population ─────────────────
    results.append("\n" + "─" * 78)
    results.append("Stage 1: Pr(Clean exit = Grade A) — full population")
    results.append("  Exclusion restriction: B2C (consumer-facing NACE division)")
    results.append("─" * 78)

    X1 = np.column_stack([lab, b2c, coalition, ln_a, yrs, ln_subs, ind_mat])
    v1 = ["lab_pctile", "b2c", "coalition", "ln_assets", "years_russia",
          "ln_n_subs"] + [f"ind_{s[:12]}" for s in ind_labels]
    m1 = probit_report(clean_exit, X1, v1, "S1: Selection probit", results)

    names1 = ["const"] + v1
    iz = names1.index("b2c")
    results.append(f"\n  Instrument relevance: b2c z = {m1.tvalues[iz]:.3f} "
                   f"(p = {m1.pvalues[iz]:.4f})")

    xb = np.asarray(m1.fittedvalues)
    imr = spstats.norm.pdf(xb) / np.clip(spstats.norm.cdf(xb), 1e-12, None)

    # ── Stage 2: exit mode among completed exits ─────────────────────────
    results.append("\n" + "─" * 78)
    results.append("Stage 2: Pr(Sold | clean exit) — sale vs exit without sale")
    results.append("─" * 78)

    pat_all = np.array([safe_float(r["pat_pctile"]) if safe_float(r["pat_pctile"]) is not None
                        else np.nan for r in pop])
    sel = (clean_exit == 1) & ~np.isnan(pat_all)
    mode = np.array([1.0 if r["exit_mode"] == "sold" else 0.0 for r in pop])
    sold_s = mode[sel]
    pat_s = pat_all[sel]
    results.append(f"  Exiter sample (Grade A, patent data): {int(sel.sum())} | "
                   f"Sold: {int(sold_s.sum())} | Exit without sale: {int(sel.sum() - sold_s.sum())}")

    # Tercile pattern (descriptive)
    for a, nm in ((pat_s, "patent pctile"), (lab[sel], "labor pctile")):
        line = []
        for lo, hi, lbl in [(0, 1 / 3, "low"), (1 / 3, 2 / 3, "mid"), (2 / 3, 1.01, "high")]:
            m = (a >= lo) & (a < hi)
            if m.sum() > 0:
                line.append(f"{lbl}: sold {sold_s[m].mean():.0%} (n={int(m.sum())})")
        results.append(f"    {nm:14s} " + " | ".join(line))

    X2_base = np.column_stack([pat_s, lab[sel], ln_a[sel], yrs[sel],
                               ln_subs[sel], ind_mat[sel]])
    v2_base = ["pat_pctile", "lab_pctile", "ln_assets", "years_russia",
               "ln_n_subs"] + [f"ind_{s[:12]}" for s in ind_labels]

    probit_report(sold_s, X2_base, v2_base,
                  "S2a: Naive probit (no selection correction)", results)

    X2_heck = np.column_stack([X2_base, imr[sel]])
    v2_heck = v2_base + ["lambda_IMR"]
    m2_heck = probit_report(sold_s, X2_heck, v2_heck,
                            "S2b: Selection-corrected (IMR included)", results)

    lam_i = (["const"] + v2_heck).index("lambda_IMR")
    lam_c, lam_p = m2_heck.params[lam_i], m2_heck.pvalues[lam_i]
    results.append(f"\n  λ (IMR): coef={lam_c:.4f}, p={lam_p:.4f}")
    if lam_p > 0.10:
        results.append("  → λ is not statistically distinguishable from zero: little "
                       "evidence that selection into exit biases the naive mode probit.")
    else:
        results.append("  → λ significant: selection into exit matters; prefer S2b.")

    # ── Wild cluster bootstrap on the LPM analog ─────────────────────────
    results.append("\n" + "─" * 78)
    results.append("Wild cluster bootstrap (home country, Rademacher, 999 reps)")
    results.append("  LPM analog of S2b; few-cluster-robust p-values for key terms")
    results.append("─" * 78)
    cl = np.array(countries)[sel]
    results.append(f"  Clusters: {len(set(cl.tolist()))} home countries")
    for key in ("pat_pctile", "lab_pctile"):
        idx = v2_heck.index(key)
        beta, p = wild_cluster_bootstrap_p(sold_s, X2_heck, cl, idx)
        results.append(f"  {key:<12}: β={beta:+.4f}, wild-cluster-bootstrap p={p:.4f}")

    # ── Robustness: A+B exiter definition in stage 1 ─────────────────────
    results.append("\n" + "─" * 78)
    results.append("Robustness: selection = Grade A OR B (announced exit)")
    results.append("─" * 78)
    m1b = probit_report(exiter_ab, X1, v1, "S1': Selection probit, exit = A/B", results)
    xb_b = np.asarray(m1b.fittedvalues)
    imr_b = spstats.norm.pdf(xb_b) / np.clip(spstats.norm.cdf(xb_b), 1e-12, None)
    X2_hb = np.column_stack([X2_base, imr_b[sel]])
    probit_report(sold_s, X2_hb, v2_heck, "S2': Mode probit with A/B-based IMR", results)

    results.append("\n" + "=" * 78)
    results.append("LIMITATIONS")
    results.append("=" * 78)
    results.append("""
  * Two-step control function, not FIML bivariate probit ("heckprobit"):
    statsmodels has no bivariate-probit estimator; standard errors in S2b
    ignore first-stage estimation noise. For publication, re-estimate with
    Stata heckprobit or R GJRM and compare.
  * Patent intensity is missing for non-exiters (the Lens pull covered
    Grade A/B only), so it cannot yet enter the selection stage. Script 02
    now queries the full panel; re-run it and add pat_pctile to stage 1.
  * The B2C × home-country-pressure interaction has no variation in the
    current sample (no B2C firm from a non-coalition country), so Z = B2C
    alone. The survey-based pressure measure (Eurobarometer / Pew) is not
    yet collected.
  * Exit mode comes from the Yale action-text classifier plus manual
    seizure overrides — the KSE LeaveRussia / Bloomberg hand-validation
    described in the README has NOT yet been done.
  * PatPct is the percentile of the parent's lifetime patent stock, not
    the 2017-2021 granted stock scaled by parent size (needs the Lens
    re-pull in script 02 plus parent financials, see 03 spec).
  * Asset tangibility (PP&E/assets) — the obvious confounder for
    sellability — is absent from the current Orbis export (see 03 spec).""")

    text = "\n".join(results)
    print(text)
    with open(OUT_FILE, "w") as f:
        f.write(text)
    print(f"\nSaved: {OUT_FILE}")


if __name__ == "__main__":
    main()
