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
  3. EVT / GEV: fit a Generalized Extreme Value distribution to equal-size block
     maxima of recent per-lifter totals; the shape xi<0 implies a BOUNDED upper tail
     (a population strength ceiling). Cite Einmahl & Magnus. (scipy genextreme uses c = -xi.)
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
    n_ge = int(np.sum(np.array(null) >= T))
    p = (n_ge + 1) / (B + 1)
    return {"lrt": round(float(T), 1), "boot_p": round(float(p), 4),
            "boot_p_is_upper_bound": (n_ge == 0),       # hit the (0+1)/(B+1) Monte-Carlo floor
            "boot_B": B,
            "aic_1comp": round(float(aic[1]), 1), "aic_2comp": round(float(aic[2]), 1),
            "bic_1comp": round(float(bic[1]), 1), "bic_2comp": round(float(bic[2]), 1),
            "best_k_by_bic": 2 if bic[2] < bic[1] else 1}


def residual_normality(sbd, seed=config.SEED):
    """Normality of the H3 log-log regression residuals (men). At n in the millions
    a formal test rejects any trivial deviation, so we report skew/kurtosis, the
    test's n-dependence, and rely on the CLT for the slope."""
    men = sbd[sbd.Sex == "M"]
    x, y = np.log(men.BodyweightKg.to_numpy()), np.log(men.TotalKg.to_numpy())
    b, a = np.polyfit(x, y, 1); r = y - (a + b * x); r = (r - r.mean()) / r.std()
    rng = np.random.default_rng(seed)
    small = [float(sp.normaltest(rng.choice(r, 300, replace=False)).pvalue) for _ in range(50)]
    # the three normality tests the course names, on one n=300 subsample: they need not
    # agree, and here they do not -- KS is the least powerful against this skew.
    sub = rng.choice(r, 300, replace=False)
    sw_W, sw_p = sp.shapiro(sub)
    ks_D, ks_p = sp.kstest(sub, "norm")
    ad = sp.anderson(sub, dist="norm")
    return {"n": int(len(r)), "skew": round(float(sp.skew(r)), 3),
            "excess_kurtosis": round(float(sp.kurtosis(r)), 3),
            "dagostino_p_full": float(sp.normaltest(r).pvalue),
            "dagostino_p_median_at_n300": round(float(np.median(small)), 3),
            "at_n300": {"shapiro_W": round(float(sw_W), 3), "shapiro_p": float(sw_p),
                        "ks_D": round(float(ks_D), 3), "ks_p": round(float(ks_p), 3),
                        "anderson_A2": round(float(ad.statistic), 2),
                        "anderson_crit_5pct": round(float(ad.critical_values[2]), 2)},
            "note": "residuals are left-skewed with a heavy lower tail, so they are not "
                    "normal even at moderate n; this does not threaten the slope, whose "
                    "sampling distribution is normal by the CLT at this n, and we report "
                    "HC3-robust SEs and lead with effect size"}


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
    # point-biserial: the course's conversion of an independent-samples t into a 0-1
    # effect size (its significance is exactly the t's).
    r_pb = float(tstat / np.sqrt(tstat ** 2 + len(tested) + len(untested) - 2))
    tested_ctrl = {"n_tested": int(len(tested)), "n_untested": int(len(untested)),
                   "point_biserial_r": round(r_pb, 3),
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

    def _gev_xi(b):
        """GEV shape with MOMENT-MATCHED starting values.

        scipy's default start makes the ML search diverge on a sizeable share of
        bootstrap resamples (harmless for the point estimate, but it inflates the
        percentile CI with |xi| values of order 1-4 that are pure optimizer noise).
        Seeding from the Gumbel moment match (sigma = s*sqrt(6)/pi, mu = mean - gamma*sigma)
        makes every fit converge and leaves the point estimate unchanged.
        """
        s = np.std(b) * np.sqrt(6) / np.pi
        return sp.genextreme.fit(b, 0.0, loc=np.mean(b) - 0.5772 * s, scale=s)

    c, loc, scale = _gev_xi(blocks)
    xi = -c                                              # scipy c = -xi (EVT convention)
    # bootstrap CI for xi: a point estimate alone cannot declare a ceiling
    bxi, n_diverged = [], 0
    for _ in range(300):
        bs = rng.choice(blocks, size=len(blocks), replace=True)
        try:
            xb = -_gev_xi(bs)[0]
            if abs(xb) > 1.0:                            # ML for a GEV shape this far out is
                n_diverged += 1                          # a failed search, not an estimate
                continue
            bxi.append(xb)
        except Exception:
            n_diverged += 1
    xi_lo, xi_hi = (float(np.percentile(bxi, 2.5)), float(np.percentile(bxi, 97.5))) if bxi else (np.nan, np.nan)
    bounded = xi_hi < 0
    evt = {"n_blocks": int(nb), "block_size": m, "scipy_c": round(float(c), 3),
           "xi": round(float(xi), 3), "xi_ci": [round(xi_lo, 3), round(xi_hi, 3)],
           "boot_n_kept": len(bxi), "boot_n_diverged": n_diverged,
           "tail": "bounded (ceiling)" if bounded else "ceiling unsupported (xi CI spans 0)",
           "implied_upper_endpoint_kg": (round(float(loc + scale / c), 0) if (c > 0 and bounded) else None),
           "cite": "Einmahl & Magnus (2008)"}

    # 4. time-trend (median Dots per year, Spearman)
    sbd["year"] = pd.to_datetime(sbd["Date"], errors="coerce").dt.year
    med = sbd.dropna(subset=["year", "Dots"]).groupby("year")["Dots"].median()
    med = med[(med.index >= 2000) & (med.index <= 2024)]
    rho, prho = sp.spearmanr(med.index, med.values)
    # a year-by-year series is NOT an independent sample: detrend and test the residual
    # autocorrelation, so the Spearman p is reported as descriptive rather than inferential.
    y = med.values.astype(float); x = np.arange(len(y), dtype=float)
    resid = y - np.polyval(np.polyfit(x, y, 1), x)
    acf1 = float(np.corrcoef(resid[:-1], resid[1:])[0, 1])
    from statsmodels.stats.diagnostic import acorr_ljungbox      # lazy: heavy import
    lb_p = float(acorr_ljungbox(resid, lags=[1], return_df=True)["lb_pvalue"].iloc[0])
    trend = {"years": [int(med.index.min()), int(med.index.max())],
             "spearman_rho": round(float(rho), 3), "spearman_p": float(prho),
             "resid_acf_lag1": round(acf1, 2), "ljung_box_p_lag1": round(lb_p, 4),
             "note": "annual medians are serially dependent, so rho is descriptive only",
             "direction": "rising" if rho > 0 else "falling"}

    normality = residual_normality(sbd)

    res = {"distribution_structure": struct, "tested_vs_untested": tested_ctrl,
           "evt_gev": evt, "time_trend": trend, "residual_normality": normality}

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
    nm = normality
    print(f"\n5. residual normality (H3 men): skew={nm['skew']}, excess-kurtosis={nm['excess_kurtosis']}; "
          f"D'Agostino p at n=300 ~{nm['dagostino_p_median_at_n300']} vs full ~{nm['dagostino_p_full']:.1e} "
          f"(genuinely non-normal; slope relies on the CLT + HC3-robust SE)")

    if save:
        config.RESULTS.mkdir(exist_ok=True)
        (config.RESULTS / "h5_supporting.json").write_text(json.dumps(res, indent=2))
        print(f"\nsaved -> {config.RESULTS / 'h5_supporting.json'}")
    return res


if __name__ == "__main__":
    run()
