#!/usr/bin/env python3
"""
Supporting analyses (paper, not the mid-deck). Each serves the "limits of strength"
side of the story and exercises additional course tools.

  1. Distribution structure: is the strength distribution a latent 2-component
     MIXTURE, or just sex? Mixture-LRT (1 vs 2 Gaussian components) with a
     PARAMETRIC BOOTSTRAP null (Wilks fails for the number-of-components test).
     Run on Dots (already sex/bodyweight-normalized) vs raw Total.
  2. Tested vs untested: a two-independent-samples comparison of Dots
     (Mann-Whitney U, nonparametric + Welch t), with a rank-biserial effect size.
  3. EVT / GEV: fit a Generalized Extreme Value distribution to annual maxima of
     Total; the shape xi<0 implies a BOUNDED upper tail (a population strength
     ceiling). Cite Einmahl & Magnus. (scipy genextreme uses c = -xi.)
  4. Time-trend: median Dots per year, Spearman trend.
"""
import json
import numpy as np
import pandas as pd
from scipy import stats as sp
from sklearn.mixture import GaussianMixture

import config, data, prep


def _gmm(x, k, seed):
    return GaussianMixture(k, random_state=seed, n_init=8, reg_covar=1e-6).fit(x)


def mixture_lrt(x, B=150, seed=config.SEED):
    """1 vs 2 Gaussian components: AIC/BIC model selection + a parametric-bootstrap
    LRT (the #-components test is on the boundary -> Wilks chi^2 invalid). n_init=8
    keeps the 2-comp fit from getting stuck below the 1-comp fit (nested -> LRT>=0)."""
    x = np.asarray(x, float).reshape(-1, 1); n = len(x)
    g1, g2 = _gmm(x, 1, seed), _gmm(x, 2, seed)
    T = max(0.0, 2 * (g2.score(x) - g1.score(x)) * n)        # nested: clamp optimizer noise
    aic = {1: g1.aic(x), 2: g2.aic(x)}; bic = {1: g1.bic(x), 2: g2.bic(x)}
    rng = np.random.default_rng(seed); null = []
    mu, sd = g1.means_[0, 0], np.sqrt(g1.covariances_[0, 0, 0])
    for _ in range(B):
        xb = rng.normal(mu, sd, n).reshape(-1, 1)
        null.append(max(0.0, 2 * (_gmm(xb, 2, seed).score(xb) - _gmm(xb, 1, seed).score(xb)) * n))
    p = (np.sum(np.array(null) >= T) + 1) / (B + 1)
    return {"lrt": round(float(T), 1), "boot_p": round(float(p), 4),
            "aic_1comp": round(float(aic[1]), 1), "aic_2comp": round(float(aic[2]), 1),
            "bic_1comp": round(float(bic[1]), 1), "bic_2comp": round(float(bic[2]), 1),
            "best_k_by_bic": 2 if bic[2] < bic[1] else 1}


def run(save=True):
    df = data.load()
    sbd = df[(df.Event == "SBD") & (df.TotalKg > 0) & (df.BodyweightKg > 0)
             & df.Sex.isin(["M", "F"])].copy()
    sbd["Dots"] = pd.to_numeric(sbd["Dots"], errors="coerce")
    pl = prep.dedup_per_lifter(sbd.dropna(subset=["Dots"]), keep="random")
    rng = np.random.default_rng(config.SEED)

    # 1. distribution structure (sample for the mixture fit)
    samp = pl.sample(min(30000, len(pl)), random_state=config.SEED)
    struct = {"dots_normalized": mixture_lrt(samp["Dots"].to_numpy()),
              "raw_total": mixture_lrt(samp["TotalKg"].to_numpy())}

    # 2. tested vs untested (two independent samples)
    tested = pl.loc[pl["Tested"] == "Yes", "Dots"].to_numpy()
    untested = pl.loc[pl["Tested"] != "Yes", "Dots"].to_numpy()
    U, pU = sp.mannwhitneyu(tested, untested, alternative="two-sided")
    tstat, pt = sp.ttest_ind(tested, untested, equal_var=False)
    rbc = 2 * U / (len(tested) * len(untested)) - 1      # rank-biserial (tested - untested)
    tested_ctrl = {"n_tested": int(len(tested)), "n_untested": int(len(untested)),
                   "median_tested": round(float(np.median(tested)), 1),
                   "median_untested": round(float(np.median(untested)), 1),
                   "mannwhitney_p": float(pU), "welch_t": round(float(tstat), 1), "welch_p": float(pt),
                   "rank_biserial": round(float(rbc), 3)}

    # 3. EVT / GEV with IID EQUAL-SIZE blocks (annual maxima of a growing sport are
    # non-stationary -> invalid). Recent stationary window (2015+), one Total per
    # lifter, randomly partitioned into equal blocks; xi<0 => bounded => ceiling.
    men = sbd[sbd.Sex == "M"].copy()
    men["year"] = pd.to_datetime(men["Date"], errors="coerce").dt.year
    men_pl = prep.dedup_per_lifter(men[men["year"] >= 2015].dropna(subset=["TotalKg"]), keep="random")
    vals = men_pl["TotalKg"].to_numpy(); vals = rng.permutation(vals)
    m = 250; nb = len(vals) // m
    blocks = vals[:nb * m].reshape(nb, m).max(axis=1)
    c, loc, scale = sp.genextreme.fit(blocks)
    xi = -c                                              # scipy c = -xi (EVT convention)
    # bootstrap CI for xi: a point estimate alone cannot declare a ceiling
    bxi = []
    for _ in range(300):
        bs = rng.choice(blocks, size=len(blocks), replace=True)
        try:
            bxi.append(-sp.genextreme.fit(bs)[0])
        except Exception:
            pass
    xi_lo, xi_hi = (float(np.percentile(bxi, 2.5)), float(np.percentile(bxi, 97.5))) if bxi else (np.nan, np.nan)
    bounded = xi_hi < 0
    evt = {"n_blocks": int(nb), "block_size": m, "scipy_c": round(float(c), 3),
           "xi": round(float(xi), 3), "xi_ci": [round(xi_lo, 3), round(xi_hi, 3)],
           "tail": "bounded (ceiling)" if bounded else "light / near-Gumbel (xi CI includes 0)",
           "implied_upper_endpoint_kg": (round(float(loc + scale / c), 0) if (c > 0 and bounded) else None),
           "cite": "Einmahl & Magnus (2008)"}

    # 4. time-trend (median Dots per year, Spearman)
    sbd["year"] = pd.to_datetime(sbd["Date"], errors="coerce").dt.year
    med = sbd.dropna(subset=["year", "Dots"]).groupby("year")["Dots"].median()
    med = med[(med.index >= 2000) & (med.index <= 2024)]
    rho, prho = sp.spearmanr(med.index, med.values)
    trend = {"years": [int(med.index.min()), int(med.index.max())],
             "spearman_rho": round(float(rho), 3), "spearman_p": float(prho),
             "direction": "rising" if rho > 0 else "falling"}

    res = {"distribution_structure": struct, "tested_vs_untested": tested_ctrl,
           "evt_gev": evt, "time_trend": trend}

    print("==== Supporting analyses ====")
    print("1. distribution structure (1 vs 2 components; bootstrap LRT + BIC):")
    for k, v in struct.items():
        print(f"   {k:<16} LRT={v['lrt']} boot_p={v['boot_p']}  BIC 1c={v['bic_1comp']} 2c={v['bic_2comp']} "
              f"-> best k={v['best_k_by_bic']}")
    t = tested_ctrl
    print(f"\n2. tested vs untested Dots (Mann-Whitney): med {t['median_tested']} vs {t['median_untested']}, "
          f"U-p={t['mannwhitney_p']:.2e}, rank-biserial={t['rank_biserial']} "
          f"(n {t['n_tested']:,}/{t['n_untested']:,})")
    print(f"\n3. EVT/GEV ({evt['n_blocks']} iid blocks of {evt['block_size']}): xi={evt['xi']} "
          f"CI{evt['xi_ci']} -> {evt['tail']}"
          + (f"; implied ceiling ~{evt['implied_upper_endpoint_kg']} kg" if evt['implied_upper_endpoint_kg'] else ""))
    print(f"\n4. time-trend (median Dots {trend['years'][0]}-{trend['years'][1]}): "
          f"Spearman rho={trend['spearman_rho']} (p={trend['spearman_p']:.2e}), {trend['direction']}")

    if save:
        config.RESULTS.mkdir(exist_ok=True)
        (config.RESULTS / "h5_supporting.json").write_text(json.dumps(res, indent=2))
        print(f"\nsaved -> {config.RESULTS / 'h5_supporting.json'}")
    return res


if __name__ == "__main__":
    run()
