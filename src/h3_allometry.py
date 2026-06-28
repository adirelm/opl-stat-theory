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


def _fp(p):
    """Format a p-value, flagging underflow honestly (Wald z can be huge here)."""
    return "<1e-300" if p == 0.0 else f"{p:.2e}"


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

    # ---- diagnosis of the low women's b: COMMON-SUPPORT refit ----
    # Comparing marginal logBW spread is not enough (restricting x mainly hurts
    # precision, not the slope). The real test: refit BOTH sexes on the OVERLAPPING
    # bodyweight range. If the sex gap in b persists on common support, it is not an
    # artifact of the sexes covering different weight ranges.
    bw_m = pl.loc[pl["male"] == 1, "BodyweightKg"]; bw_w = pl.loc[pl["male"] == 0, "BodyweightKg"]
    lo = float(max(bw_m.quantile(0.05), bw_w.quantile(0.05)))
    hi = float(min(bw_m.quantile(0.95), bw_w.quantile(0.95)))
    cs = pl[(pl["BodyweightKg"] >= lo) & (pl["BodyweightKg"] <= hi)]
    cs_b = {}
    for sex, name in [("M", "men"), ("F", "women")]:
        gg = cs[cs["Sex"] == sex]
        cs_b[name] = round(su.ols_loglog(gg["logbw"].to_numpy(), gg["logtot"].to_numpy())["b"], 3)
    gap_full = (res["by_sex"]["men"]["formal_per_lifter"]["b"]
                - res["by_sex"]["women"]["formal_per_lifter"]["b"])
    gap_cs = round(cs_b["men"] - cs_b["women"], 3)
    persists = gap_cs > 0.5 * gap_full
    res["women_b_diagnosis"] = {
        "common_support_kg": [round(lo, 1), round(hi, 1)],
        "b_common_support": cs_b,
        "sex_gap_full": round(gap_full, 3), "sex_gap_common_support": gap_cs,
        "men_logbw_sd": res["by_sex"]["men"]["logbw_sd"],
        "women_logbw_sd": res["by_sex"]["women"]["logbw_sd"],
        "range_restriction_explains_low_b": (not persists),
        "note": ("the sex gap in b PERSISTS on common bodyweight support -> it is NOT an "
                 "artifact of different weight ranges; the difference appears genuine "
                 "(mechanism left to the discussion)") if persists else
                ("the sex gap SHRINKS substantially on common support -> partly a "
                 "range/support effect")}
    res["notes"] = {"wald_vs_1": "secondary anchor only; NOT part of the Holm-corrected family"}

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
        print(f"  Wald vs 2/3: z={s['wald_vs_2/3']['z']}  p={_fp(s['wald_vs_2/3']['p'])}")
        print(f"  logBW sd={s['logbw_sd']} (range restriction), BW p5/50/95={list(s['bw_pctiles'].values())}")
    si = res["sex_interaction"]
    print(f"\nsex interaction (men slope - women slope): {si['coef_male_x_logbw']:+.3f} "
          f"+/- {si['se']}  p={_fp(si['p'])}")
    print("\nmultiple-testing (Holm; wald_vs_1 is a secondary anchor, excluded):")
    for k, v in res["multiple_testing"].items():
        print(f"  {k:<18} p_raw={_fp(v['p_raw'])}  p_holm={_fp(v['p_holm'])}  "
              f"{'reject' if v['p_holm'] < config.ALPHA else 'ns'}")
    dg = res["women_b_diagnosis"]
    print(f"\ndiagnosis (common-support refit on BW {dg['common_support_kg']} kg):")
    print(f"  b men={dg['b_common_support']['men']} vs women={dg['b_common_support']['women']}; "
          f"sex gap full={dg['sex_gap_full']} -> common-support={dg['sex_gap_common_support']}")
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
