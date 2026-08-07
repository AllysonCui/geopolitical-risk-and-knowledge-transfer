"""
Q2 — Do sanctions alter the association between knowledge structure and exit mode?

Replaces the subsample R² comparison (the old "4.4x" claim) with the two
designs the model actually implies:

  (a) Pooled interaction on the exit-mode margin:
        Pr(Sell | exit) = Φ(β₁ PatPct + β₂ SancExp + β₃ PatPct × SancExp + X'β)
      Sanctions may raise transaction costs and lower sale probabilities.
      Their interaction with patent intensity is theoretically ambiguous:
      higher transaction costs can make transferable value more important,
      while the loss of capable buyers can reduce the value of technology
      assets. The data must distinguish these channels.

  (b) Cause-specific competing-risks Cox (sale and exit without sale as competing
      events) with TIME-VARYING sanction exposure, using the staggered
      2022 EU package rollout:
        h_sell(t) = h₀(t) exp(β₁ PatPct + β₂ SancExp(t) + β₃ PatPct×SancExp(t) + X'β)
      Estimated with statsmodels PHReg on an episode-split (counting
      process) dataset: each firm's time at risk is split at the adoption
      dates of the packages hitting its NACE sector, so identification
      comes from WHEN a sector became exposed, conditional on sector
      composition — not from a cross-sectional sanctions dummy.

Timing notes (be honest about coarseness):
  * Event dates: Bloomberg announce date for completed sales, else the
    first Yale snapshot at Grade A. 323 firms already Grade A at the first
    snapshot (Dec 2022) are left-censored — their events pile up at t=11,
    creating heavy ties (Breslow approximation used).
  * Sanction exposure covers the 2022 EU packages 1-8 mapped to NACE
    sectors. Packages 9-14 (Dec 2022-2024) are not yet mapped — the
    time-varying profile is right-truncated at Oct 2022.

Input:  data/analysis/regression_sample.csv
Output: data/analysis/results_11_sanctions_amplification.txt
"""

import numpy as np

from estimation_utils import (DATA_DIR, load_sample, safe_float, complete_rows,
                              dummies, ols_report, probit_report,
                              wild_cluster_bootstrap_p)

OUT_FILE = DATA_DIR / "results_11_sanctions_amplification.txt"

END_MONTH = 40  # censoring horizon: May 2025 snapshot, months since 2022-02 (+1 shift)


def month_of(iso_date):
    y, m = int(iso_date[:4]), int(iso_date[5:7])
    return (y - 2022) * 12 + (m - 2)


def main():
    rows = load_sample()
    results = []
    results.append("=" * 78)
    results.append("Q2: SANCTIONS MODERATION — INTERACTION + COMPETING-RISKS HAZARD")
    results.append("=" * 78)

    # ── (a) Pooled interaction on the exit-mode margin ───────────────────
    need = ["pat_pctile", "lab_pctile", "ln_assets", "years_in_russia"]
    ex = [r for r in complete_rows(rows, need)
          if r["exit_mode"] in ("sold", "walked")]

    pat = np.array([float(r["pat_pctile"]) for r in ex])
    lab = np.array([float(r["lab_pctile"]) for r in ex])
    ln_a = np.array([float(r["ln_assets"]) for r in ex])
    yrs = np.array([float(r["years_in_russia"]) for r in ex])
    ln_subs = np.log1p(np.array([safe_float(r["n_subsidiaries"]) or 1 for r in ex]))
    sanc = np.array([float(r["sanctions_exposure"]) for r in ex])
    sold = np.array([1.0 if r["exit_mode"] == "sold" else 0.0 for r in ex])
    countries = np.array([r["country"] for r in ex])
    ind_mat, ind_labels = dummies([r["industry"] or "Other" for r in ex], min_count=15)
    ind_names = [f"ind_{s[:12]}" for s in ind_labels]

    results.append(f"\nExit-mode sample: {len(ex)} Grade A exits "
                   f"(sold {int(sold.sum())} / walked {int(len(ex) - sold.sum())})")
    results.append(f"  Sanctioned-sector firms: {int((sanc > 0).sum())}")

    results.append("\n" + "─" * 78)
    results.append("Spec A: Pr(Sold | exit) with PatPct × sanctions interaction")
    results.append("  (pooled interaction — supersedes the old split-sample R² ratio)")
    results.append("─" * 78)

    X_int = np.column_stack([pat, lab, sanc, pat * sanc, ln_a, yrs, ln_subs, ind_mat])
    v_int = ["pat_pctile", "lab_pctile", "sanctions_exp", "pat_x_sanctions",
             "ln_assets", "years_russia", "ln_n_subs"] + ind_names
    probit_report(sold, X_int, v_int, "A1: Probit with interaction", results)
    ols_report(sold, X_int, v_int, "A2: LPM with interaction (HC1)", results)

    beta, p = wild_cluster_bootstrap_p(sold, X_int, countries,
                                       v_int.index("pat_x_sanctions"))
    results.append(f"\n  Key term pat_x_sanctions: β={beta:+.4f}, "
                   f"wild-cluster-bootstrap (home country) p={p:.4f}")

    # Binary exposure variant (any 2022 package hits the sector)
    sanc_d = (sanc > 0).astype(float)
    X_d = np.column_stack([pat, lab, sanc_d, pat * sanc_d, ln_a, yrs, ln_subs, ind_mat])
    v_d = ["pat_pctile", "lab_pctile", "sanctioned(0/1)", "pat_x_sanctioned",
           "ln_assets", "years_russia", "ln_n_subs"] + ind_names
    probit_report(sold, X_d, v_d, "A3: Probit, binary sanctioned-sector", results)

    # ── (b) Cause-specific competing-risks hazard ────────────────────────
    results.append("\n" + "─" * 78)
    results.append("Spec B: Cause-specific Cox with time-varying sanction exposure")
    results.append("  Risk set: firms with patent data (announced exiters). Events:")
    results.append("  sale vs exit without sale (competing); Grade B and seized censored.")
    results.append("─" * 78)

    # Patent data only exists for exiters, so complete cases restrict the
    # risk set to (essentially) the Grade A/B firms: the hazard compares
    # timing of completed sale vs exit without sale among announced exiters, with
    # Grade B and seized firms censored. (A missingness-indicator variant
    # was degenerate — stayers never have events, so the indicator perfectly
    # predicts censoring.) Re-running the Lens pull for the full panel will
    # restore the stayers to the risk set.
    haz_rows = complete_rows(rows, ["pat_pctile", "lab_pctile", "ln_assets",
                                    "years_in_russia"])

    subjects = []
    for r in haz_rows:
        pv = float(r["pat_pctile"])
        mode = r["exit_mode"]
        ev_month = safe_float(r["event_month"])
        if mode == "sold" and ev_month is not None:
            stop, event = ev_month + 1, "sold"
        elif mode == "walked" and ev_month is not None:
            stop, event = ev_month + 1, "walked"
        else:
            stop, event = END_MONTH, ""      # censored: stayers, B, seized
        stop = max(stop, 1.0)
        hits = sorted({month_of(d) for d in r["sanction_hit_dates"].split(";") if d})
        subjects.append({
            "pat": pv,
            "lab": float(r["lab_pctile"]),
            "ln_a": float(r["ln_assets"]),
            "yrs": float(r["years_in_russia"]),
            "stop": stop, "event": event, "hits": hits,
            "industry": r["industry"] or "Other",
        })

    n_sold = sum(1 for s in subjects if s["event"] == "sold")
    n_walk = sum(1 for s in subjects if s["event"] == "walked")
    results.append(f"\n  Hazard risk set: {len(subjects)} firms with patent data "
                   f"(effectively announced exiters until the Lens re-pull) | "
                   f"sale events: {n_sold} | non-sale exit events: {n_walk} | "
                   f"censored: {len(subjects) - n_sold - n_walk}")

    # Episode-split (counting process) records
    def build_episodes(cause):
        start_l, stop_l, status_l, X_l = [], [], [], []
        ind_all, _ = dummies([s["industry"] for s in subjects], min_count=15)
        for i, s in enumerate(subjects):
            cuts = [0.0] + [float(h + 1) for h in s["hits"] if 0 < h + 1 < s["stop"]] + [s["stop"]]
            for a, b in zip(cuts[:-1], cuts[1:]):
                if b <= a:
                    continue
                expo = sum(1 for h in s["hits"] if h + 1 <= a)
                is_last = (b == s["stop"])
                status_l.append(1.0 if (is_last and s["event"] == cause) else 0.0)
                start_l.append(a)
                stop_l.append(b)
                X_l.append([s["pat"], s["lab"], float(expo),
                            s["pat"] * expo, s["ln_a"], s["yrs"]] + list(ind_all[i]))
        return (np.array(start_l), np.array(stop_l), np.array(status_l),
                np.array(X_l))

    import statsmodels.api as sm
    _, ind_labels_h = dummies([s["industry"] for s in subjects], min_count=15)
    v_haz = ["pat_pctile", "lab_pctile", "sanc_exposure(t)",
             "pat_x_sanc(t)", "ln_assets", "years_russia"] + \
            [f"ind_{s[:12]}" for s in ind_labels_h]

    for cause, label in (("sold", "SALE"), ("walked", "EXIT WITHOUT SALE")):
        entry, stop, status, Xh = build_episodes(cause)
        results.append(f"\n  Cause-specific hazard: {label} "
                       f"({int(status.sum())} events, {len(stop)} episodes)")
        try:
            mod = sm.PHReg(stop, Xh, status=status, entry=entry, ties="breslow")
            fit = mod.fit()
            results.append(f"  {'Variable':<26} {'log HR':>10} {'HR':>8} {'SE':>8} {'P>|z|':>8}")
            results.append(f"  {'-' * 66}")
            for name, coef, se, p_ in zip(v_haz, fit.params, fit.bse,
                                          np.asarray(fit.pvalues)):
                sig = "***" if p_ < 0.01 else "**" if p_ < 0.05 else "*" if p_ < 0.1 else ""
                results.append(f"  {name:<26} {coef:>10.4f}{sig:<3} {np.exp(coef):>8.3f} "
                               f"{se:>8.4f} {p_:>8.4f}")
        except Exception as e:
            results.append(f"  PHReg failed: {e}")

    results.append("\n" + "=" * 78)
    results.append("LIMITATIONS")
    results.append("=" * 78)
    results.append("""
  * Sector-level exposure (NACE 2-digit x package), not the firm-level
    CN/HS product-code mapping the design document calls for (EU Official
    Journal annexes → CN → CPA → NACE via Eurostat RAMON, dual-use
    Annex I flags, OFAC/Castellum counterparty exposure). Only 2022
    packages 1-8 are mapped; the staggered variation ends Oct 2022.
  * Event timing is coarse: 323 firms are left-censored at the first Yale
    snapshot (Dec 2022), producing heavy ties at t=11 (Breslow used).
    Bloomberg announce dates sharpen timing only for completed sales.
  * The hazard risk set is limited to firms with patent data — in the
    current build, announced exiters (A/B) — because the Lens pull
    covered exiters only. Stayers rejoin the risk set once script 02 is
    re-run over the full panel.""")

    text = "\n".join(results)
    print(text)
    with open(OUT_FILE, "w") as f:
        f.write(text)
    print(f"\nSaved: {OUT_FILE}")


if __name__ == "__main__":
    main()
