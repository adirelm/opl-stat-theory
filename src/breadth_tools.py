#!/usr/bin/env python3
"""
Course-tools breadth coverage. The instructions require using as many course
concepts as relevant; these exercise the ones without a natural home in H1-H4,
each anchored to the story (not a heap of tests):

  1. PAIRED test (Wilcoxon signed-rank): opener (attempt 1) vs final (attempt 3).
  2. F-test / ANOVA + Kruskal-Wallis omnibus + post-hoc: Dots across equipment.
  3. INDEPENDENCE chi^2 + Cramer's V + standardized residuals: Tested x made-weight.
  4. SEQUENTIAL Wald test (SPRT) + stopping time: sequential cut detection.
  5. POWER + Type I/II tradeoff for the cut test.
  6. ALL FOUR multiple-comparison corrections on the H2 seven-limit family.
  7. MP / UMP (Neyman-Pearson) framing of the one-sided allometry test.
"""
import json
import numpy as np
import pandas as pd
from scipy import stats as sp

import config, data, prep, stats_utils as su


def paired_attempts(df, lift="Squat", seed=config.SEED):
    a1, a3 = f"{lift}1Kg", f"{lift}3Kg"
    d = df[(df[a1] > 0) & (df[a3] > 0)]               # both attempts successful
    s = d.sample(min(100_000, len(d)), random_state=seed)
    x1, x3 = s[a1].to_numpy(), s[a3].to_numpy()
    W, p = sp.wilcoxon(x3, x1)                        # paired signed-rank, H0: no difference
    return {"lift": lift, "n_pairs": int(len(s)),
            "median_attempt1": round(float(np.median(x1)), 1),
            "median_attempt3": round(float(np.median(x3)), 1),
            "median_diff_kg": round(float(np.median(x3 - x1)), 1),
            "wilcoxon_p": float(p)}


def anova_equipment(df, seed=config.SEED):
    d = df[(df.Event == "SBD") & (df.TotalKg > 0) & df.Sex.isin(["M", "F"])].copy()
    d["Dots"] = pd.to_numeric(d["Dots"], errors="coerce")
    pl = prep.dedup_per_lifter(d.dropna(subset=["Dots"]), keep="random")
    cats = ["Raw", "Single-ply", "Multi-ply", "Wraps"]
    cats = [c for c in cats if (pl.Equipment == c).sum() > 100]
    groups = [pl.loc[pl.Equipment == c, "Dots"].to_numpy() for c in cats]
    F, pF = sp.f_oneway(*groups)
    H, pH = sp.kruskal(*groups)
    # post-hoc pairwise Mann-Whitney with Bonferroni (Dunn-style)
    labels, raw = [], []
    for i in range(len(cats)):
        for j in range(i + 1, len(cats)):
            U, pu = sp.mannwhitneyu(groups[i], groups[j])
            labels.append(f"{cats[i]} vs {cats[j]}"); raw.append(pu)
    p_adj, _ = su.correct_pvalues(raw, method="bonferroni")
    return {"groups": cats, "n_per_group": {c: int(len(g)) for c, g in zip(cats, groups)},
            "median_dots": {c: round(float(np.median(g)), 1) for c, g in zip(cats, groups)},
            "anova_F": round(float(F), 1), "anova_p": float(pF),
            "kruskal_H": round(float(H), 1), "kruskal_p": float(pH),
            "posthoc_bonferroni": {labels[k]: {"p_raw": float(raw[k]), "p_bonf": float(p_adj[k])}
                                   for k in range(len(labels))}}


def independence_cut_tested(df):
    d = df[(df.BodyweightKg > 0) & (df.Sex == "M") & config.is_h2_federation(df)].copy()
    d["year"] = pd.to_datetime(d["Date"], errors="coerce").dt.year
    d = d[d["year"] >= 2014]

    def lab(bw):
        for L in config.IPF_MEN_CLASSES:
            if L - 1 < bw <= L: return "below"
            if L < bw <= L + 1: return "above"
        return None
    d["cut"] = d["BodyweightKg"].map(lab)
    c = d.dropna(subset=["cut"]).copy()
    c["tested"] = np.where(c["Tested"] == "Yes", "tested", "untested")
    tab = pd.crosstab(c["tested"], c["cut"])
    chi2, p, dof, exp = sp.chi2_contingency(tab)
    n = tab.values.sum(); k = min(tab.shape) - 1
    cramers_v = float(np.sqrt(chi2 / (n * k)))
    std_resid = (tab.values - exp) / np.sqrt(exp)
    return {"table_tested_x_cut": {r: tab.loc[r].to_dict() for r in tab.index},
            "chi2": round(float(chi2), 1), "dof": int(dof), "p": float(p),
            "cramers_v": round(cramers_v, 3),
            "standardized_residuals": {tab.index[i]: {tab.columns[j]: round(float(std_resid[i, j]), 1)
                                       for j in range(tab.shape[1])} for i in range(tab.shape[0])}}


def sprt_cut(df, p0=0.5, p1=0.6, alpha=0.05, beta=0.10, seed=config.SEED):
    """Wald SPRT of the just-below/above cut indicator: H0 p=p0 vs H1 p=p1."""
    d = df[(df.BodyweightKg > 0) & (df.Sex == "M") & config.is_h2_federation(df)].copy()
    d["year"] = pd.to_datetime(d["Date"], errors="coerce").dt.year
    d = d[d["year"] >= 2014]

    def lab(bw):
        for L in config.IPF_MEN_CLASSES:
            if L - 1 < bw <= L: return 1
            if L < bw <= L + 1: return 0
        return np.nan
    obs = d["BodyweightKg"].map(lab).dropna().astype(int).to_numpy()
    obs = np.random.default_rng(seed).permutation(obs)
    A = np.log((1 - beta) / alpha); B = np.log(beta / (1 - alpha))     # decision boundaries
    s1, s0 = np.log(p1 / p0), np.log((1 - p1) / (1 - p0))
    llr = 0.0; decision = "no decision"; stop = len(obs)
    for i, x in enumerate(obs, 1):
        llr += s1 if x else s0
        if llr >= A: decision, stop = "accept H1 (bunching)", i; break
        if llr <= B: decision, stop = "accept H0 (no bunching)", i; break
    p_hat = float(obs.mean())
    # Wald approx expected sample size under H1
    num = (1 - beta) * A + beta * B
    den = p1 * s1 + (1 - p1) * s0
    asn_h1 = float(num / den)
    return {"p0": p0, "p1": p1, "alpha": alpha, "beta": beta,
            "boundary_A": round(A, 3), "boundary_B": round(B, 3),
            "observed_p_below": round(p_hat, 3),
            "decision": decision, "stopping_time": int(stop),
            "expected_n_under_H1_approx": round(asn_h1, 1), "total_available": int(len(obs))}


def power_analysis(p0=0.5, p_eff=0.6, alpha=0.05):
    """One-sided power to detect p>p0 (the cut signal) vs n, and a-priori n for 0.90.
    Demonstrates the Type I (alpha) / Type II (beta) tradeoff: power = 1 - beta."""
    z_a = sp.norm.ppf(1 - alpha)
    def power(n):
        crit = p0 + z_a * np.sqrt(p0 * (1 - p0) / n)
        return float(sp.norm.sf((crit - p_eff) / np.sqrt(p_eff * (1 - p_eff) / n)))
    curve = {n: round(power(n), 3) for n in (20, 50, 100, 200, 500)}
    n90 = next(n for n in range(5, 2000) if power(n) >= 0.90)
    # alpha-beta tradeoff at fixed n=100 (lower alpha -> lower power -> higher beta)
    ab = {}
    for a in (0.01, 0.05, 0.10):
        za = sp.norm.ppf(1 - a); crit = p0 + za * np.sqrt(p0 * (1 - p0) / 100)
        pw = float(sp.norm.sf((crit - p_eff) / np.sqrt(p_eff * (1 - p_eff) / 100)))
        ab[a] = {"type_I_alpha": a, "power_1_minus_beta": round(pw, 3), "type_II_beta": round(1 - pw, 3)}
    return {"effect_p": p_eff, "power_vs_n": curve, "n_for_power_0.90": int(n90),
            "alpha_beta_tradeoff_at_n100": ab}


def all_four_corrections():
    h2 = json.loads((config.RESULTS / "h2.json").read_text())
    fm = h2["formal_mccrary"]
    ps = [fm[str(L)]["p"] for L in config.IPF_MEN_CLASSES]
    out = {}
    for method in ("bonferroni", "holm", "sidak", "fdr_bh"):
        p_adj, rej = su.correct_pvalues(ps, method=method)
        out[method] = {"n_rejected": int(np.sum(rej)), "of": len(ps)}
    return {"family": "H2 seven class limits", "raw_p": ps, "corrections": out}


def ump_framing():
    h3 = json.loads((config.RESULTS / "h3.json").read_text())
    z = h3["by_sex"]["men"]["wald_vs_2/3"]["z"]
    one_sided_p = float(sp.norm.sf(z))               # H1: b > 2/3
    return {"test": "allometry men b > 2/3 (one-sided)", "z": z,
            "one_sided_p": one_sided_p,
            "note": ("a one-sided test of a single exponential-family parameter is UMP "
                     "(Neyman-Pearson); the GLRTs (H1, mixture) are the composite generalization")}


def run(save=True):
    df = data.load()
    res = {
        "paired_attempts": paired_attempts(df),
        "anova_equipment": anova_equipment(df),
        "independence_cut_tested": independence_cut_tested(df),
        "sprt_cut": sprt_cut(df),
        "power_analysis": power_analysis(),
        "all_four_corrections": all_four_corrections(),
        "ump_framing": ump_framing(),
    }

    pa = res["paired_attempts"]
    print("==== Breadth tools ====")
    print(f"1. PAIRED Wilcoxon (Squat opener vs final): med {pa['median_attempt1']} -> {pa['median_attempt3']} "
          f"(diff {pa['median_diff_kg']} kg), p={pa['wilcoxon_p']:.2e}  [n={pa['n_pairs']:,}]")
    av = res["anova_equipment"]
    print(f"2. ANOVA across equipment: F={av['anova_F']} (p={av['anova_p']:.2e}); "
          f"Kruskal-Wallis H={av['kruskal_H']} (p={av['kruskal_p']:.2e}); medians {av['median_dots']}")
    ind = res["independence_cut_tested"]
    print(f"3. INDEPENDENCE chi2 (tested x cut): chi2={ind['chi2']} (dof={ind['dof']}, p={ind['p']:.2e}), "
          f"Cramer's V={ind['cramers_v']}; std-resid={ind['standardized_residuals']}")
    sp_ = res["sprt_cut"]
    print(f"4. SPRT (cut p0={sp_['p0']} vs p1={sp_['p1']}): decision='{sp_['decision']}' at "
          f"stopping time N={sp_['stopping_time']} (boundaries A={sp_['boundary_A']}, B={sp_['boundary_B']}; "
          f"obs p_below={sp_['observed_p_below']}; theoretical E[N|H1]~{sp_['expected_n_under_H1_approx']})")
    pw = res["power_analysis"]
    print(f"5. POWER (detect p>{0.5}, effect {pw['effect_p']}): power vs n {pw['power_vs_n']}; "
          f"n for 0.90 = {pw['n_for_power_0.90']}; alpha-beta @n100: "
          + ", ".join(f"a={k}->power {v['power_1_minus_beta']}" for k, v in pw['alpha_beta_tradeoff_at_n100'].items()))
    c4 = res["all_four_corrections"]
    print(f"6. ALL-4 corrections on H2's 7 limits: "
          + ", ".join(f"{m}={d['n_rejected']}/{d['of']}" for m, d in c4["corrections"].items()))
    uf = res["ump_framing"]
    print(f"7. MP/UMP: one-sided allometry b>2/3 z={uf['z']} -> p={uf['one_sided_p']:.2e} (UMP for the exp. family)")

    if save:
        config.RESULTS.mkdir(exist_ok=True)
        (config.RESULTS / "breadth.json").write_text(json.dumps(res, indent=2))
        print(f"\nsaved -> {config.RESULTS / 'breadth.json'}")
    return res


if __name__ == "__main__":
    run()
