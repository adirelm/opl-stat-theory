#!/usr/bin/env python3
"""
H3 -- allometric scaling of strength: Total ~ Bodyweight^b, and is b the same for
men and women? Reference: isometric square-cube law predicts b = 2/3 (strength ~
muscle cross-section ~ volume^(2/3) ~ bodyweight^(2/3)).

Layers:
  1. DESCRIPTIVE (all SBD rows, plain OLS) -- matches the preliminary deck
     (b ~= 0.72 men / 0.49 women, R^2).
  2. FORMAL: log-log OLS on ONE ROW PER LIFTER (random seeded meet -> independence)
     with HC3 heteroskedasticity-robust SE; Wald test of b vs 2/3 (and vs 1); a
     pooled Sex x log(BW) interaction model to test the sex difference formally;
     Pearson/Spearman with Fisher-transform CIs.
  3. DIAGNOSIS of the low women's b (range restriction / leverage).
Effect sizes (b and its CI) lead; multiple-testing correction across the Wald tests.
"""
import json
import numpy as np

import config, data, prep, stats_utils as su

ISO = 2.0 / 3.0                                  # isometric reference exponent


def _fisher_ci(r, n, z=su.Z95):
    """Fisher z-transform CI for a correlation r."""
    zr = np.arctanh(r); se = 1.0 / np.sqrt(n - 3)
    return float(np.tanh(zr - z * se)), float(np.tanh(zr + z * se))


def run(save=True):
    df = data.load()
    al = df[(df["Event"] == "SBD") & (df["TotalKg"] > 0) & (df["BodyweightKg"] > 0)
            & df["Sex"].isin(["M", "F"])][["Name", "Sex", "BodyweightKg", "TotalKg"]].dropna()

    # one row per lifter (random seeded meet) -> independence for the formal test
    pl = prep.dedup_per_lifter(al, keep="random")
    pl = pl.assign(logbw=np.log(pl["BodyweightKg"]), logtot=np.log(pl["TotalKg"]),
                   male=(pl["Sex"] == "M").astype(float))

    res = {"n_rows_sbd": int(len(al)), "n_per_lifter": int(len(pl)), "by_sex": {}}
    wald_ps = {}
    from scipy import stats as sp
    for sex, name in [("M", "men"), ("F", "women")]:
        g_all = al[al["Sex"] == sex]
        desc = su.ols_loglog(np.log(g_all["BodyweightKg"]), np.log(g_all["TotalKg"]))
        g = pl[pl["Sex"] == sex]
        x, y = g["logbw"].to_numpy(), g["logtot"].to_numpy()
        rob = su.ols_robust(x, y)                            # HC3 robust SE
        z23, p23 = su.wald_test(rob["b"], rob["se_b"], ISO)  # vs 2/3
        z1, p1 = su.wald_test(rob["b"], rob["se_b"], 1.0)    # vs 1 (anchor)
        r_p = float(np.corrcoef(x, y)[0, 1])
        r_s = float(sp.spearmanr(x, y).statistic)
        res["by_sex"][name] = {
            "descriptive_all_rows": {"b": round(desc["b"], 3), "r2": round(desc["r2"], 3),
                                     "n": desc["n"]},
            "formal_per_lifter": {"b": round(rob["b"], 3), "se": round(rob["se_b"], 4),
                                  "ci": [round(rob["ci_lo"], 3), round(rob["ci_hi"], 3)],
                                  "n": rob["n"]},
            "wald_vs_2/3": {"z": round(z23, 2), "p": p23},
            "wald_vs_1": {"z": round(z1, 2), "p": p1},
            "pearson_logbw_logtot": {"r": round(r_p, 3), "ci": [round(c, 3) for c in _fisher_ci(r_p, len(x))]},
            "spearman": round(r_s, 3),
            "logbw_sd": round(float(np.std(x)), 4),          # range-restriction diagnostic
            "bw_pctiles": {p: round(float(np.percentile(g["BodyweightKg"], p)), 1) for p in (5, 50, 95)},
        }
        wald_ps[f"{name}_vs_2/3"] = p23

    # ---- formal sex difference: pooled Sex x log(BW) interaction, HC3 ----
    import statsmodels.api as sm
    X = sm.add_constant(pl[["male", "logbw"]].copy())
    X["male_x_logbw"] = pl["male"].to_numpy() * pl["logbw"].to_numpy()
    fit = sm.OLS(pl["logtot"].to_numpy(), X).fit(cov_type="HC3")
    b_int = float(fit.params["male_x_logbw"]); se_int = float(fit.bse["male_x_logbw"])
    p_int = float(fit.pvalues["male_x_logbw"])
    res["sex_interaction"] = {
        "coef_male_x_logbw": round(b_int, 3), "se": round(se_int, 4), "p": p_int,
        "meaning": "men's slope minus women's slope; tests the sex difference in scaling"}
    wald_ps["sex_interaction"] = p_int

    # ---- diagnosis of the low women's b: is it range restriction? ----
    men_sd = res["by_sex"]["men"]["logbw_sd"]; wom_sd = res["by_sex"]["women"]["logbw_sd"]
    explains = wom_sd < 0.8 * men_sd
    res["women_b_diagnosis"] = {
        "men_logbw_sd": men_sd, "women_logbw_sd": wom_sd,
        "range_restriction_explains_low_b": bool(explains),
        "note": ("women have a much narrower log-bodyweight spread -> range restriction "
                 "plausibly lowers the estimated slope")
                if explains else
                ("women's log-bodyweight spread is essentially the same as men's, so range "
                 "restriction does NOT explain the lower b; the sex difference appears genuine "
                 "in this sample (mechanism left to the discussion)")}

    # ---- multiple-testing across the formal tests ----
    keys = list(wald_ps); ps = [wald_ps[k] for k in keys]
    p_holm, _ = su.correct_pvalues(ps, method="holm")
    res["multiple_testing"] = {k: {"p_raw": float(ps[i]), "p_holm": float(p_holm[i])}
                               for i, k in enumerate(keys)}

    # ---- report ----
    print("==== H3: allometric scaling (Total ~ Bodyweight^b) ====")
    print(f"SBD rows {len(al):,} -> {len(pl):,} unique lifters (formal unit); isometric ref b=2/3={ISO:.3f}")
    for name in ("men", "women"):
        s = res["by_sex"][name]
        f = s["formal_per_lifter"]; d = s["descriptive_all_rows"]
        print(f"\n{name}:")
        print(f"  descriptive (all rows): b={d['b']} (R2={d['r2']}, n={d['n']:,})")
        print(f"  formal (per-lifter, HC3): b={f['b']} +/- se {f['se']}  "
              f"CI[{f['ci'][0]:.3f}, {f['ci'][1]:.3f}]  n={f['n']:,}")
        print(f"  Wald vs 2/3: z={s['wald_vs_2/3']['z']}  p={s['wald_vs_2/3']['p']:.2e}")
        print(f"  logBW sd={s['logbw_sd']} (range restriction), BW p5/50/95={list(s['bw_pctiles'].values())}")
    si = res["sex_interaction"]
    print(f"\nsex interaction (men slope - women slope): {si['coef_male_x_logbw']:+.3f} "
          f"+/- {si['se']}  p={si['p']:.2e}")
    print("\nmultiple-testing (Holm):")
    for k, v in res["multiple_testing"].items():
        print(f"  {k:<18} p_raw={v['p_raw']:.2e}  p_holm={v['p_holm']:.2e}  "
              f"{'reject' if v['p_holm'] < config.ALPHA else 'ns'}")
    dg = res["women_b_diagnosis"]
    print(f"\ndiagnosis (women's low b): men logBW sd={dg['men_logbw_sd']} vs women {dg['women_logbw_sd']} "
          f"-> range restriction explains it? {dg['range_restriction_explains_low_b']}")
    print(f"  => {dg['note']}")
    print("\nNOTE: at this n almost everything is 'significant' -> we lead with the effect "
          "size (b and its CI) and the SEX GAP, not the p-values.")

    if save:
        config.RESULTS.mkdir(exist_ok=True)
        (config.RESULTS / "h3.json").write_text(json.dumps(res, indent=2))
        print(f"saved -> {config.RESULTS / 'h3.json'}")
    return res


if __name__ == "__main__":
    run()
