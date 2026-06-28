#!/usr/bin/env python3
"""
H2 -- bodyweight bunches just below real class limits (weight-cutting), formally.

Population: IPF + USAPL men (one modern class scheme), bodyweight de-heaped
(round/half-kg weigh-ins removed) so the signal is not just digit preference.

Three layers:
  1. EFFECT SIZE (headline, all meet rows): de-heaped log(below/above) at each of
     the 7 real limits and at the 91 kg non-limit control.
  2. FORMAL TEST: Cattaneo-Jansson-Ma density-discontinuity test (rddensity, the
     modern McCrary) at each limit + control + placebo points. To respect
     independence (the same lifter recurs), the formal test runs on ONE ROW PER
     LIFTER (their PR-meet bodyweight). t<0 / diff<0 = density drops at the cutoff
     = excess just below.
  3. ROBUSTNESS: spike-width (how tightly the excess hugs the limit), placebo
     points (should be flat), subgroup persistence (tested/untested, raw/equipped),
     and multiple-testing correction across the 7 limits.
"""
import json
import numpy as np
import pandas as pd

import config, data, prep, stats_utils as su

LIMITS = config.IPF_MEN_CLASSES                 # [59,66,74,83,93,105,120]
CONTROL = config.H2_CONTROL                     # 91 (between kg classes 83 and 93)
# clean placebos: BETWEEN modern kg classes AND away from historical lb-class
# equivalents. Only valid on the pure-kg subset (see ERA_MIN).
PLACEBOS = [70, 88, 99, 112]
MCWIN = 15.0                                    # +/- kg window passed to rddensity (local)
ERA_MIN = 2014                                  # USAPL adopted IPF kg classes ~2014; before that,
                                                # US feds used lb classes -> contaminates placebos.


def _mccrary(bw, cutoff, win=MCWIN):
    """CJM density-discontinuity test at `cutoff` on a local window. Returns dict."""
    from rddensity import rddensity
    seg = bw[(bw > cutoff - win) & (bw < cutoff + win)]
    try:
        out = rddensity(np.asarray(seg, float), c=float(cutoff))
        return {"t": float(out.test["t_jk"]), "p": float(out.test["p_jk"]),
                "f_left": float(out.hat["left"]), "f_right": float(out.hat["right"]),
                "f_diff": float(out.hat["diff"]), "n_window": int(len(seg))}
    except Exception as e:                       # degenerate window etc.
        return {"t": float("nan"), "p": float("nan"), "error": str(e)[:80],
                "n_window": int(len(seg))}


def _spike_width(bw, L):
    """How tightly the just-below excess hugs the limit: share of the (L-2,L] mass
    that falls in the innermost 0.5 kg. Sharp cut -> high share. Compare real vs control."""
    b = prep.deheap(bw)
    within2 = int(((b > L - 2) & (b <= L)).sum())
    within05 = int(((b > L - 0.5) & (b <= L)).sum())
    return {"n_within_2kg_below": within2,
            "share_in_innermost_0.5kg": round(within05 / within2, 3) if within2 else None}


def run(save=True):
    df = data.load()
    men_mask = config.is_h2_federation(df) & (df["Sex"] == "M")
    men_rows = df.loc[men_mask].copy()
    men_rows["year"] = pd.to_datetime(men_rows["Date"], errors="coerce").dt.year
    bw_all = men_rows["BodyweightKg"].dropna().to_numpy()

    # one row per lifter (PR meet) -> independent sample for the formal test
    clean = men_rows.dropna(subset=["BodyweightKg", "TotalKg"])
    per_lifter = prep.dedup_per_lifter(clean)
    bw_pl = per_lifter["BodyweightKg"].to_numpy()

    # PURE-KG subset (post-2014): only the modern kg class scheme, so placebos /
    # control are not contaminated by historical lb classes. Formal test uses this.
    pk_rows = clean[clean["year"] >= ERA_MIN]
    pk_per_lifter = prep.dedup_per_lifter(pk_rows)
    bw_pk = pk_per_lifter["BodyweightKg"].to_numpy()

    # ---- 1. effect sizes (all rows, de-heaped) at every limit + control ----
    effect = {}
    for L in LIMITS + [CONTROL]:
        below, above = prep.bunching_counts(bw_all, L)
        lr, half, ratio = su.log_ratio_ci(below, above)
        effect[L] = {"below": below, "above": above, "log_ratio": round(lr, 3),
                     "ci_half": round(half, 3), "ratio": round(ratio, 2),
                     "is_limit": L in LIMITS}
    # confirm the headline (83 kg) survives on the pure-kg subset
    pk_below, pk_above = prep.bunching_counts(bw_pk, config.H2_REAL_LIMIT)
    pk_lr, pk_half, pk_ratio = su.log_ratio_ci(pk_below, pk_above)
    effect["83_pure_kg"] = {"log_ratio": round(pk_lr, 3), "ci_half": round(pk_half, 3),
                            "ratio": round(pk_ratio, 2), "n_per_lifter": int(len(pk_per_lifter))}

    # ---- 2. formal McCrary on the PURE-KG per-lifter subset ----
    formal = {}
    for c in LIMITS + [CONTROL] + PLACEBOS:
        formal[c] = _mccrary(bw_pk, c)
        formal[c]["kind"] = ("limit" if c in LIMITS else
                             "control" if c == CONTROL else "placebo")

    # multiple-testing correction across the 7 real limits
    limit_ps = [formal[L]["p"] for L in LIMITS]
    valid = [p for p in limit_ps if np.isfinite(p)]
    corr = {}
    if valid:
        p_holm, rej_holm = su.correct_pvalues(limit_ps, method="holm")
        p_bh, rej_bh = su.correct_pvalues(limit_ps, method="fdr_bh")
        corr = {"limits": LIMITS,
                "p_raw": [float(p) for p in limit_ps],
                "p_holm": [float(p) for p in p_holm], "reject_holm": [bool(b) for b in rej_holm],
                "p_bh": [float(p) for p in p_bh], "reject_bh": [bool(b) for b in rej_bh]}

    # ---- 3. spike-width + subgroup robustness at the headline limit (83) ----
    spike = {L: _spike_width(bw_all, L) for L in (config.H2_REAL_LIMIT, CONTROL)}

    sub = {}
    L = config.H2_REAL_LIMIT
    for label, m in [("tested", men_rows["Tested"] == "Yes"),
                     ("untested", men_rows["Tested"] != "Yes"),
                     ("raw", men_rows["Equipment"] == "Raw"),
                     ("equipped", men_rows["Equipment"].isin(["Single-ply", "Multi-ply", "Wraps"]))]:
        bw_s = men_rows.loc[m, "BodyweightKg"].dropna().to_numpy()
        if len(bw_s) > 100:
            below, above = prep.bunching_counts(bw_s, L)
            if below and above:
                lr, half, ratio = su.log_ratio_ci(below, above)
                sub[label] = {"log_ratio": round(lr, 3), "ratio": round(ratio, 2), "n": int(len(bw_s))}

    res = {"n_rows_men_ipf": int(len(men_rows)), "n_per_lifter": int(len(per_lifter)),
           "effect_sizes": effect, "formal_mccrary": formal,
           "multiple_testing": corr, "spike_width": spike, "subgroups_at_83": sub}

    # ---- report ----
    print("==== H2: bunching below class limits ====")
    print(f"men IPF+USAPL: {len(men_rows):,} rows -> {len(per_lifter):,} unique lifters")
    print(f"pure-kg subset (year>={ERA_MIN}): {len(pk_per_lifter):,} unique lifters (FORMAL-test unit)")
    pk = effect["83_pure_kg"]
    print(f"headline 83kg holds on pure-kg? log-ratio {pk['log_ratio']:+.2f} (x{pk['ratio']})")
    print("\neffect sizes (de-heaped log(below/above), all rows):")
    for L in LIMITS:
        e = effect[L]; print(f"  {L:>4} kg : {e['log_ratio']:+.2f} +/- {e['ci_half']:.2f}  (x{e['ratio']})")
    e = effect[CONTROL]; print(f"  {CONTROL:>4} kg (control): {e['log_ratio']:+.2f}  (x{e['ratio']})")
    print("\nformal McCrary (rddensity, PURE-KG per-lifter):  t<0 = density drops at cutoff = excess below")
    for c in LIMITS + [CONTROL] + PLACEBOS:
        f = formal[c]
        tag = f["kind"]
        if np.isfinite(f.get("t", float("nan"))):
            print(f"  {c:>4} kg [{tag:>8}]: t={f['t']:+.2f}  p={f['p']:.2e}  "
                  f"(f_left={f['f_left']:.4f} > f_right={f['f_right']:.4f}? diff={f['f_diff']:+.4f})")
        else:
            print(f"  {c:>4} kg [{tag:>8}]: (no estimate) {f.get('error','')}")
    if corr:
        print("\nmultiple-testing across 7 limits: all reject after Holm?",
              all(corr["reject_holm"]), "| after BH?", all(corr["reject_bh"]))
    print("\nspike-width (share of (L-2,L] mass in innermost 0.5 kg):")
    for L, s in spike.items():
        print(f"  {L} kg: {s['share_in_innermost_0.5kg']}  (n_below2={s['n_within_2kg_below']:,})")
    print("\nsubgroup log-ratios at 83 kg:")
    for k, v in sub.items():
        print(f"  {k:>9}: {v['log_ratio']:+.2f} (x{v['ratio']}, n={v['n']:,})")

    if save:
        config.RESULTS.mkdir(exist_ok=True)
        (config.RESULTS / "h2.json").write_text(json.dumps(res, indent=2))
        print(f"\nsaved -> {config.RESULTS / 'h2.json'}")
    return res


if __name__ == "__main__":
    run()
