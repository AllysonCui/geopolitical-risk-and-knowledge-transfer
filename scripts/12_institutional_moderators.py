"""
Q3 — Do home-country institutions moderate exit mode conditional on
knowledge type?

Cross-level interaction on the exit-mode sample (Grade A, sold vs
walked), with home-country fixed effects:

  Pr(Sell_i) = Φ(β₁ PatPct_i + β₂ PatPct_i × Coalition_c(i)
                 + β₃ PatPct_i × RuleOfLaw_c(i)
                 + β₄ PatPct_i × CommonLaw_c(i) + X_i'β + μ_c(i))

With country FE μ_c the LEVELS of country institutions are absorbed —
only the interactions are identified, which is exactly what the question
asks. Model predictions (docs/formal_model.md, Prediction 3):
  * Coalition membership raises transaction costs τ of a sale (permissible-
    buyer restrictions, exit-tax exposure) → coalition × PatPct < 0 on
    selling relative to the no-coalition benchmark for high-transferability
    firms, OR steeper sorting — the two institutional channels have
    opposite signs, which is the testable contrast.
  * Stakeholder-pressure institutions raise the reputational cost w of
    walking away → interactions > 0 on selling.

Estimation: LPM with country FE (primary — probit with ~35 country dummies
suffers incidental-parameter bias); Mundlak correlated-random-effects
probit as robustness (country means of firm covariates + institution
levels instead of FE). Wild cluster bootstrap (home country) on all
interaction terms.

Note: home-country institutions are hand-entered scaffold values —
see data/raw/institutions/README.md — verify before reporting.

Input:  data/analysis/regression_sample.csv
        (institutions already merged in by script 08)
Output: data/analysis/results_12_institutional_moderators.txt
"""

import numpy as np

from estimation_utils import (DATA_DIR, load_sample, safe_float, complete_rows,
                              dummies, ols_report, probit_report,
                              wild_cluster_bootstrap_p)

OUT_FILE = DATA_DIR / "results_12_institutional_moderators.txt"


def main():
    rows = load_sample()
    results = []
    results.append("=" * 78)
    results.append("Q3: HOME-COUNTRY INSTITUTIONS AND EXIT MODE")
    results.append("Cross-level interactions with country fixed effects")
    results.append("=" * 78)

    need = ["pat_pctile", "lab_pctile", "ln_assets", "years_in_russia",
            "sanctions_coalition", "wgi_rule_of_law"]
    ex = [r for r in complete_rows(rows, need, str_keys=("legal_origin",))
          if r["exit_mode"] in ("sold", "walked")]

    pat = np.array([float(r["pat_pctile"]) for r in ex])
    lab = np.array([float(r["lab_pctile"]) for r in ex])
    ln_a = np.array([float(r["ln_assets"]) for r in ex])
    yrs = np.array([float(r["years_in_russia"]) for r in ex])
    ln_subs = np.log1p(np.array([safe_float(r["n_subsidiaries"]) or 1 for r in ex]))
    sold = np.array([1.0 if r["exit_mode"] == "sold" else 0.0 for r in ex])
    countries = np.array([r["country"] for r in ex])

    coalition = np.array([float(r["sanctions_coalition"]) for r in ex])
    wgi = np.array([float(r["wgi_rule_of_law"]) for r in ex])
    common_law = np.array([1.0 if r["legal_origin"] == "english" else 0.0 for r in ex])

    ind_mat, ind_labels = dummies([r["industry"] or "Other" for r in ex], min_count=15)
    ind_names = [f"ind_{s[:12]}" for s in ind_labels]
    # Country FE: pool countries with <5 exiters into OTHER
    c_mat, c_labels = dummies(countries.tolist(), min_count=5)
    c_names = [f"cty_{s[:10]}" for s in c_labels]

    n_countries = len(set(countries.tolist()))
    results.append(f"\nExit-mode sample: {len(ex)} Grade A exits "
                   f"(sold {int(sold.sum())} / walked {int(len(ex) - sold.sum())})")
    results.append(f"  Home countries: {n_countries} "
                   f"({len(c_labels)} FE cells after pooling <5-firm countries)")
    results.append(f"  Non-coalition firms: {int((coalition == 0).sum())} | "
                   f"Common-law: {int(common_law.sum())} | "
                   f"WGI range: [{wgi.min():.1f}, {wgi.max():.1f}]")

    # ── Primary: LPM with country FE + interactions ──────────────────────
    results.append("\n" + "─" * 78)
    results.append("Spec 1: LPM, country FE — institution LEVELS absorbed by FE;")
    results.append("        only PatPct × institution interactions identified")
    results.append("─" * 78)

    X_fe = np.column_stack([pat, pat * coalition, pat * wgi, pat * common_law,
                            lab, ln_a, yrs, ln_subs, ind_mat, c_mat])
    v_fe = ["pat_pctile", "pat_x_coalition", "pat_x_wgi", "pat_x_commonlaw",
            "lab_pctile", "ln_assets", "years_russia", "ln_n_subs"] + ind_names + c_names
    ols_report(sold, X_fe, v_fe, "1: LPM country FE + interactions (HC1)", results)

    results.append("\n  Wild cluster bootstrap (home country, 999 reps):")
    for key in ("pat_x_coalition", "pat_x_wgi", "pat_x_commonlaw"):
        beta, p = wild_cluster_bootstrap_p(sold, X_fe, countries, v_fe.index(key))
        results.append(f"    {key:<16}: β={beta:+.4f}, WCB p={p:.4f}")

    # ── Robustness: Mundlak correlated-random-effects probit ─────────────
    results.append("\n" + "─" * 78)
    results.append("Spec 2: Mundlak CRE probit — country means of firm covariates +")
    results.append("        institution levels, instead of country FE")
    results.append("─" * 78)

    # Country means of firm-level covariates (Mundlak device)
    def country_means(x):
        out = np.empty_like(x)
        for c in set(countries.tolist()):
            m = countries == c
            out[m] = x[m].mean()
        return out

    pat_bar = country_means(pat)
    lab_bar = country_means(lab)
    lna_bar = country_means(ln_a)

    X_cre = np.column_stack([pat, pat * coalition, pat * wgi, pat * common_law,
                             coalition, wgi, common_law,
                             lab, ln_a, yrs, ln_subs,
                             pat_bar, lab_bar, lna_bar, ind_mat])
    v_cre = ["pat_pctile", "pat_x_coalition", "pat_x_wgi", "pat_x_commonlaw",
             "coalition", "wgi_rule_of_law", "common_law",
             "lab_pctile", "ln_assets", "years_russia", "ln_n_subs",
             "pat_bar_c", "lab_bar_c", "ln_assets_bar_c"] + ind_names
    probit_report(sold, X_cre, v_cre, "2: Mundlak CRE probit", results)

    # ── Descriptive: sale rates by institution cell ──────────────────────
    results.append("\n" + "─" * 78)
    results.append("Descriptive: sale rate by institutions × patent-intensity half")
    results.append("─" * 78)
    hi_pat = pat >= np.median(pat)
    for label, mask in (("Coalition", coalition == 1), ("Non-coalition", coalition == 0),
                        ("Common law", common_law == 1), ("Civil law", common_law == 0)):
        for pl, pm in (("high-pat", hi_pat), ("low-pat", ~hi_pat)):
            m = mask & pm
            if m.sum() >= 5:
                results.append(f"  {label:<14} {pl:<9}: sold {sold[m].mean():.0%} (n={int(m.sum())})")

    results.append("\n" + "=" * 78)
    results.append("LIMITATIONS")
    results.append("=" * 78)
    results.append("""
  * Institution values are a hand-entered scaffold (see
    data/raw/institutions/README.md) — verify WGI 2021, the Decree 430-r
    coalition list, and legal-origin codings before reporting.
  * Nearly all exiters have coalition home countries, so pat_x_coalition
    leans on few firms; the WCB p-value is the honest one.
  * The stakeholder-pressure channel is proxied by legal origin; the
    sharper measure (ESG-disclosure mandates in force by 2021, Carrots &
    Sticks) is not yet collected.
  * No selection correction here; combining the country-FE interaction
    design with the stage-1 IMR from script 10 is a next step.""")

    text = "\n".join(results)
    print(text)
    with open(OUT_FILE, "w") as f:
        f.write(text)
    print(f"\nSaved: {OUT_FILE}")


if __name__ == "__main__":
    main()
