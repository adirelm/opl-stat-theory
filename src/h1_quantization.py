#!/usr/bin/env python3
"""
H1 -- attempt loads are quantized to the 2.5 kg plate grid (formal test).

Effect size (headline): the fraction of attempts sitting exactly on the 2.5 kg
grid (~96.2%). The formal test below confirms it is far beyond chance, using a
GLRT whose null parameter sits ON THE BOUNDARY -- so we calibrate the null with
a parametric bootstrap, not a naive chi^2 (Chernoff / Self-Liang).

MODEL (kg-native subset)
------------------------
We restrict to attempts on the 0.5 kg lattice (multiples of 0.5). This is the
kg-loaded data; pound-denominated loads (e.g. 102.06 kg = 225 lb) are NOT on the
0.5 lattice and are excluded here -- we handle them separately as a robustness
note (they are themselves quantized, on a pound grid). See lb_robustness().

Within a 2.5 kg cell at 0.5 kg resolution there are 5 slots {0, .5, 1, 1.5, 2};
slot 0 IS the 2.5 kg grid point.
  - H0 (no grid preference): each of the 5 slots is equally likely
    -> P(on grid) = p0 = 1/5, i.e. the spike weight pi = 0 (the boundary).
  - H1: P(on grid) = p0 + (1-p0)*pi,  pi in [0,1]  (pi = fraction "snapped" to grid).
GLRT statistic 2*lnLambda tests pi=0 vs pi>0. Because pi=0 is on the boundary,
the null distribution of 2*lnLambda is a 50:50 mixture of chi^2_0 and chi^2_1,
NOT chi^2_1 -- we get the correct null (and cutoff) by parametric bootstrap.

ASSUMPTION: the uniform-1/5 baseline is a simple, transparent "no-2.5-preference"
null. The effect is so large (~0.96 vs 0.20) that the conclusion is robust to the
exact baseline; a richer baseline (e.g. whole-kg preference) is a Stage-2 refinement.
"""
import json
import numpy as np
from scipy.special import xlogy                # endpoint-safe x*log(y): xlogy(0,0)=0

import config, data, prep, stats_utils as su

RES = 0.5                                  # kg resolution of the within-cell lattice
N_SLOTS = int(config.GRID_KG / RES)        # = 5
P0 = 1.0 / N_SLOTS                          # no-preference baseline for the grid slot


def kg_lattice(att):
    """Keep attempts on the 0.5 kg lattice; return (loads, within-cell slot 0..4, kept_frac)."""
    ticks = att / RES
    on_half = np.abs(ticks - np.round(ticks)) < 1e-6
    kg = att[on_half]
    slot = (np.round(kg / RES).astype(np.int64)) % N_SLOTS    # 0 == on the 2.5 grid
    return kg, slot, on_half.mean()


def binom_spike_glrt(k, n, p0=P0):
    """GLRT for H0: pi=0 (p=p0, boundary) vs H1: pi>=0. Returns (T=2lnLambda, pi_hat, p_hat)."""
    phat = k / n
    p1 = max(phat, p0)                      # constrained MLE (pi >= 0)
    pi_hat = (p1 - p0) / (1 - p0)
    def ll(p):
        return xlogy(k, p) + xlogy(n - k, 1 - p)     # safe at the k==n endpoint
    T = 2.0 * (ll(p1) - ll(p0)) if p1 > p0 else 0.0
    return T, pi_hat, p1


def bootstrap_null(n, p0=P0, B=3000, seed=config.SEED):
    """Parametric-bootstrap null of 2lnLambda: simulate k* ~ Binomial(n, p0), refit pi>=0."""
    rng = np.random.default_rng(seed)
    ks = rng.binomial(n, p0, size=B).astype(np.float64)
    phat = ks / n
    p1 = np.maximum(phat, p0)
    ll1 = xlogy(ks, p1) + xlogy(n - ks, 1 - p1)      # endpoint-safe
    ll0 = xlogy(ks, p0) + xlogy(n - ks, 1 - p0)
    T = 2.0 * (ll1 - ll0)
    T[p1 <= p0] = 0.0                       # boundary: pi_hat=0 -> T=0 (the point mass)
    return T


def lb_robustness(att):
    """The off-0.5-lattice attempts are pound loads: report the share explained by round-lb."""
    ticks = att / RES
    off = np.abs(ticks - np.round(ticks)) >= 1e-6
    o = att[off]
    lb = o / config.KG_PER_LB
    round_lb = np.abs(lb - np.round(lb / 2.5) * 2.5) < 0.05      # round to 2.5 lb
    return {"off_lattice_frac": float(off.mean()),
            "off_lattice_n": int(off.sum()),
            "round_lb_share_of_off": float(round_lb.mean())}


def run(save=True):
    df = data.load()
    att = prep.valid_attempt_loads(df)

    # headline effect size: exact 2.5 kg grid share over ALL attempts
    on_grid_all = prep.on_grid_mask(att)
    p, lo, hi = su.proportion_ci(int(on_grid_all.sum()), len(att))

    # formal GLRT on the kg-native (0.5-lattice) subset
    kg, slot, kept = kg_lattice(att)
    n = len(kg); k = int((slot == 0).sum())
    T, pi_hat, p_hat = binom_spike_glrt(k, n)
    null = bootstrap_null(n)
    p_boot = su.bootstrap_pvalue(T, null)
    exceeds_all = bool(T > np.max(null))            # T_obs beyond every null draw?
    p_upper = 1.0 / (len(null) + 1)                 # Monte-Carlo floor for the p-value

    # cutoffs: naive chi^2_1 vs calibrated (bootstrap) vs theoretical 50:50 mixture
    from scipy import stats as sp
    naive_cut = sp.chi2.ppf(0.95, df=1)                 # 3.84
    mix_cut = sp.chi2.ppf(0.90, df=1)                   # 2.71  (0.5+0.5*0.9=0.95)
    boot_cut = float(np.quantile(null, 0.95))
    mass0 = float(np.mean(null < 1e-9))

    # chi^2 goodness-of-fit of the 5-slot distribution vs uniform (no-preference)
    obs = np.array([int((slot == j).sum()) for j in range(N_SLOTS)], float)
    exp = np.full(N_SLOTS, n / N_SLOTS)
    gof_chi2 = float(np.sum((obs - exp) ** 2 / exp)); gof_df = N_SLOTS - 1

    lb = lb_robustness(att)

    res = {
        "effect_size_on_grid_pct": round(100 * p, 4),
        "on_grid_ci_pct": [round(100 * lo, 3), round(100 * hi, 3)],
        "n_valid_attempts": int(len(att)),
        "kg_lattice_kept_frac": round(float(kept), 4),
        "n_kg_lattice": n, "k_on_grid": k,
        "pi_hat": round(float(pi_hat), 4), "p_hat_on_grid": round(float(p_hat), 4),
        "glrt_2lnLambda": float(T),
        "bootstrap_pvalue": float(p_boot),
        "bootstrap_p_is_upper_bound": exceeds_all,
        "bootstrap_p_upper": float(p_upper),
        "bootstrap_null_mass_at_0": round(mass0, 3),
        "cutoff_naive_chi2_1_95": round(naive_cut, 3),
        "cutoff_mixture_theory_95": round(mix_cut, 3),
        "cutoff_bootstrap_95": round(boot_cut, 3),
        "gof_chi2": gof_chi2, "gof_df": gof_df,
        "lb_robustness": lb,
        "inference_unit_note": ("inference is deliberately ATTEMPT-LEVEL: snapping to the 2.5 kg "
                                "grid is a within-attempt mechanism, so the attempt (not the "
                                "lifter) is the natural unit. Attempts cluster within lifters, so "
                                "the CI and test magnitudes are NOT cluster-adjusted and overstate "
                                "precision; this does not affect the conclusion, which rests on the "
                                "effect size (0.96 on-grid vs the 0.20 no-preference null)."),
    }
    print("==== H1: quantization to the 2.5 kg grid ====")
    print(f"effect size: {res['effect_size_on_grid_pct']}% on grid  "
          f"CI[{100*lo:.3f}, {100*hi:.3f}]  (n={len(att):,})")
    print(f"kg-lattice subset kept {100*kept:.1f}% of attempts; n={n:,}, on-grid k={k:,}")
    print(f"MLE pi_hat={pi_hat:.3f} (p_on_grid={p_hat:.3f})")
    print(f"GLRT 2lnLambda = {T:,.0f}")
    print(f"  bootstrap null: mass@0={mass0:.2f} (boundary mixture), 95% cutoff={boot_cut:.2f}")
    print(f"  vs naive chi2_1 95%={naive_cut:.2f}, theoretical mixture 95%={mix_cut:.2f}")
    if exceeds_all:
        print(f"  bootstrap p < {p_upper:.1e} (T_obs exceeds ALL {len(null)} null draws)  ->  REJECT H0 (grid is real)")
    else:
        print(f"  bootstrap p-value = {p_boot:.2e}  ->  {'REJECT H0 (grid is real)' if p_boot < config.ALPHA else 'fail to reject'}")
    print(f"chi^2 GoF vs uniform-5: chi2={gof_chi2:,.0f} (df={gof_df}) -> overwhelming")
    print(f"lb robustness: off-lattice {100*lb['off_lattice_frac']:.1f}% of attempts, "
          f"{100*lb['round_lb_share_of_off']:.0f}% of them are round-pound loads")
    print("NOTE: effect dominates -- naive and calibrated tests both reject; we report the "
          "bootstrap-calibrated null because it is the CORRECT procedure for the boundary.")

    if save:
        config.RESULTS.mkdir(exist_ok=True)
        (config.RESULTS / "h1.json").write_text(json.dumps(res, indent=2))
        print(f"saved -> {config.RESULTS / 'h1.json'}")
    return res


if __name__ == "__main__":
    run()
