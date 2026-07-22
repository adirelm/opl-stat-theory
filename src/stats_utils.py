#!/usr/bin/env python3
"""
Statistical helpers shared by the hypotheses, written around the project's
non-negotiables: lead with effect size + CI (not p), calibrate boundary/mixture
LRTs with a parametric bootstrap (Wilks fails there), and correct for multiple
testing. Heavy deps (statsmodels) are imported lazily so the core runs on
numpy/scipy alone.
"""
import numpy as np

Z95 = 1.959963984540054              # standard normal 0.975 quantile


# ---------- effect sizes + CIs ----------
def proportion_ci(k, n, z=Z95):
    """Proportion with a normal-approx CI (n is huge here, so the CI is very tight)."""
    p = k / n
    half = z * np.sqrt(p * (1 - p) / n)
    return p, p - half, p + half


def log_ratio_ci(below, above, z=Z95):
    """log(below/above) with its delta-method 95% half-width. Returns (lr, half, ratio)."""
    lr = np.log(below / above)
    half = z * np.sqrt(1.0 / below + 1.0 / above)
    return lr, half, np.exp(lr)


def ols_loglog(x, y, z=Z95):
    """Plain OLS slope on (x, y) with R^2 and a naive (homoskedastic) slope CI.

    This is the DESCRIPTIVE estimate (matches the preliminary deck). The formal
    H3 version uses HC3-robust SE on one row per lifter -- see ols_robust().
    """
    x = np.asarray(x, float); y = np.asarray(y, float)
    b, a = np.polyfit(x, y, 1)
    yhat = a + b * x
    ssres = np.sum((y - yhat) ** 2)
    sstot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ssres / sstot
    sxx = np.sum((x - x.mean()) ** 2)
    se_b = np.sqrt(ssres / (len(x) - 2) / sxx)
    return {"b": b, "a": a, "r2": r2, "se_b": se_b, "ci_b": z * se_b, "n": len(x)}


def ols_robust(x, y, groups=None, add_const=True):
    """OLS slope with HC3 robust SE, or cluster-robust SE if `groups` is given.

    Returns dict with slope b, its SE and CI. Used by the FORMAL H3 test to
    respect pseudo-replication (same lifter recurs).
    """
    import statsmodels.api as sm                          # lazy: heavy import
    X = sm.add_constant(x) if add_const else np.asarray(x, float)
    model = sm.OLS(np.asarray(y, float), X)
    if groups is not None:
        res = model.fit(cov_type="cluster", cov_kwds={"groups": np.asarray(groups)})
    else:
        res = model.fit(cov_type="HC3")
    b = res.params[-1]; se = res.bse[-1]
    return {"b": b, "se_b": se, "ci_lo": b - Z95 * se, "ci_hi": b + Z95 * se,
            "n": len(y)}


def wald_test(estimate, se, null_value=0.0):
    """Two-sided Wald test of H0: parameter == null_value. Returns (z, p)."""
    from scipy import stats as sp                          # lazy
    z = (estimate - null_value) / se
    p = 2 * sp.norm.sf(abs(z))
    return z, p


# ---------- multiple testing ----------
def correct_pvalues(pvals, method="holm"):
    """Adjust p-values. method in {bonferroni, holm, sidak, fdr_bh}."""
    from statsmodels.stats.multitest import multipletests  # lazy
    reject, p_adj, *_ = multipletests(pvals, method=method)
    return p_adj, reject


# ---------- parametric bootstrap engine ----------
def parametric_bootstrap(simulate, statistic, B=2000, seed=7):
    """Generic parametric bootstrap.

    simulate(rng) -> a synthetic dataset drawn UNDER H0.
    statistic(data) -> the test statistic for that dataset.
    Returns the array {T*_1..T*_B} = the empirical null distribution.
    Use it to calibrate boundary/mixture LRTs where Wilks' chi^2 is invalid.
    """
    rng = np.random.default_rng(seed)
    return np.array([statistic(simulate(rng)) for _ in range(B)])


def bootstrap_pvalue(t_obs, null_stats):
    """Right-tail bootstrap p-value: fraction of null draws >= the observed stat."""
    null_stats = np.asarray(null_stats)
    return (np.sum(null_stats >= t_obs) + 1) / (len(null_stats) + 1)
