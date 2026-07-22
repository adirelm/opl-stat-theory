#!/usr/bin/env python3
"""
Acceptance check: reproduce the headline descriptive numbers THROUGH the
new infrastructure modules (config/data/prep/stats_utils). If these match the
known values, the foundation is wired correctly and the hypotheses can build on it.

Run:  python src/smoke_check.py
"""
import numpy as np

import config, data, prep, stats_utils as su


def approx(got, exp, tol):
    return abs(got - exp) <= tol


def main():
    print("loading locked snapshot ...")
    df = data.load()
    checks = []

    # ---- H1: fraction of attempts on the 2.5 kg grid ----
    att = prep.valid_attempt_loads(df)
    on = prep.on_grid_mask(att)
    p, lo, hi = su.proportion_ci(int(on.sum()), len(att))
    print(f"[H1] valid attempts {len(att):,} | on-grid {100*p:.3f}%  CI[{100*lo:.2f}, {100*hi:.2f}]")
    checks.append(("H1 on-grid 96.20%", approx(100 * p, 96.20, 0.05)))

    # ---- H2: de-heaped log(below/above) at the real limit vs the control ----
    men = df.loc[config.is_h2_federation(df) & (df["Sex"] == "M"), "BodyweightKg"].dropna().to_numpy()
    b83, a83 = prep.bunching_counts(men, config.H2_REAL_LIMIT)
    lr83, h83, x83 = su.log_ratio_ci(b83, a83)
    b91, a91 = prep.bunching_counts(men, config.H2_CONTROL)
    lr91, h91, x91 = su.log_ratio_ci(b91, a91)
    print(f"[H2] @83  below {b83:,}/above {a83:,}  log-ratio {lr83:+.2f} +/- {h83:.2f}  (x{x83:.1f})")
    print(f"[H2] @91  below {b91:,}/above {a91:,}  log-ratio {lr91:+.2f} +/- {h91:.2f}  (x{x91:.1f})")
    checks.append(("H2 @83 log-ratio +1.92", approx(lr83, 1.92, 0.03)))
    checks.append(("H2 @91 control -0.21", approx(lr91, -0.21, 0.03)))

    # ---- H3: log-log allometry slope per sex ----
    al = df[(df["Event"] == "SBD") & (df["TotalKg"] > 0) & (df["BodyweightKg"] > 0)
            & df["Sex"].isin(["M", "F"])][["Sex", "BodyweightKg", "TotalKg"]].dropna()
    for sex, eb, er2 in [("M", 0.72, 0.36), ("F", 0.49, 0.19)]:
        g = al[al["Sex"] == sex]
        fit = su.ols_loglog(np.log(g["BodyweightKg"]), np.log(g["TotalKg"]))
        print(f"[H3] {sex}: b={fit['b']:.2f} +/- {fit['ci_b']:.3f}  R2={fit['r2']:.2f}  n={fit['n']:,}")
        checks.append((f"H3 {sex} b={eb}", approx(fit["b"], eb, 0.01)))
        checks.append((f"H3 {sex} R2={er2}", approx(fit["r2"], er2, 0.01)))

    # ---- infra sanity: dedup-per-lifter + bootstrap engine ----
    ded = prep.dedup_per_lifter(al.assign(Name=df.loc[al.index, "Name"]))
    print(f"[infra] dedup-per-lifter: {len(al):,} SBD rows -> {len(ded):,} unique lifters")
    checks.append(("dedup reduces rows", len(ded) < len(al)))

    # parametric bootstrap engine: recover a boundary 50:50 mixture (max(Z,0)^2)
    null = su.parametric_bootstrap(lambda rng: rng.normal(size=1),
                                   lambda d: max(d[0], 0.0) ** 2, B=4000, seed=config.SEED)
    frac0 = np.mean(null < 1e-9)
    print(f"[infra] bootstrap engine: mass at 0 = {frac0:.2f} (expect ~0.50, boundary mixture)")
    checks.append(("bootstrap mass~0.50", approx(frac0, 0.50, 0.05)))

    # ---- verdict ----
    print("\n==== acceptance ====")
    ok = True
    for name, passed in checks:
        print(f"  {'PASS' if passed else 'FAIL'}  {name}")
        ok &= passed
    print(f"\n{'ALL PASS - acceptance check' if ok else 'SOME FAILED - check above'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
