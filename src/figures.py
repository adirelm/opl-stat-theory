#!/usr/bin/env python3
"""
Publication figures for the paper. All figures: >=300 DPI, English axis labels
(matplotlib bidi-safe; Hebrew interpretation lives in the text), meaningful
colors, descriptive titles. Writes PNGs into ../figures.

Run:  python src/figures.py      (loads the data once, builds every figure)
"""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from matplotlib.patches import Patch
from scipy import stats as sp

import config, data, prep, stats_utils as su

plt.rcParams.update({
    "figure.dpi": 300, "savefig.dpi": 300, "font.size": 11,
    "axes.titlesize": 12.5, "axes.titleweight": "bold", "axes.labelsize": 11,
    "axes.spines.top": False, "axes.spines.right": False, "figure.autolayout": True,
})
C_GRID, C_OFF, C_HL, C_LIM = "#C0392B", "#5499C7", "#E67E22", "#566573"
C_M, C_W = "#2E86C1", "#E67E22"
OUT = config.FIGURES


def save(fig, name):
    OUT.mkdir(exist_ok=True)
    fig.savefig(f"{OUT}/{name}", bbox_inches="tight"); plt.close(fig)
    print(f"  saved {name}")


def fig_quantization(att):
    on = prep.on_grid_mask(att); pct = 100 * on.mean()
    fig, ax = plt.subplots(figsize=(7.5, 4.0))
    lo, hi, bw = 100, 150, 0.5
    sub = att[(att >= lo) & (att < hi)]
    counts, edges, patches = ax.hist(sub, bins=np.arange(lo, hi + bw, bw), edgecolor="white", linewidth=0.2)
    for e, p in zip(edges[:-1], patches):
        p.set_facecolor(C_GRID if abs(e / 2.5 - round(e / 2.5)) < 1e-6 else C_OFF)
    ax.set_ylim(0, counts.max() * 1.18); ax.xaxis.set_major_locator(MultipleLocator(5))
    ax.set_xlabel("Attempt weight (kg)"); ax.set_ylabel("Count")
    ax.set_title("Fig 1. Attempt loads concentrate on the 2.5 kg plate grid")
    ax.legend(handles=[Patch(color=C_GRID, label="on 2.5 kg grid"),
                       Patch(color=C_OFF, label="off grid")], frameon=False)
    ax.text(0.98, 0.95, f"{pct:.1f}% of {len(att)/1e6:.1f}M attempts on the grid",
            transform=ax.transAxes, ha="right", va="top", fontsize=10,
            bbox=dict(boxstyle="round", fc="#FDEBD0", ec=C_HL))
    save(fig, "fig1_quantization.png")


def fig_bunching(men):
    binw = 0.25
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0))
    for ax, (L, lo, hi, title, real) in zip(axes, [
            (config.H2_REAL_LIMIT, 79, 87, "Real class limit (83 kg)", True),
            (config.H2_CONTROL, 87, 95, "Non-limit control (91 kg)", False)]):
        seg = prep.deheap(men[(men >= lo) & (men < hi)])
        counts, edges, patches = ax.hist(seg, bins=np.arange(lo, hi + binw, binw),
                                         edgecolor="white", linewidth=0.15)
        for e, p in zip(edges[:-1], patches):
            p.set_facecolor(C_HL if (L - 0.5 <= e < L) else C_OFF)
        ax.axvline(L, color=C_LIM, lw=2, ls="--")
        b, a = prep.bunching_counts(men, L); lr, half, ratio = su.log_ratio_ci(b, a)
        ax.set_title(title); ax.set_xlabel("Bodyweight (kg)"); ax.set_ylabel("Count")
        ax.text(0.04, 0.96, f"de-heaped\nlog(below/above)\n= {lr:+.2f} +/- {half:.2f}",
                transform=ax.transAxes, ha="left", va="top", fontsize=9.5,
                bbox=dict(boxstyle="round", fc="#FDEBD0" if real else "#EBF5FB", ec=C_HL if real else C_OFF))
    fig.suptitle("Fig 2. Bodyweight bunches just below a real class limit, not at a non-limit control",
                 fontweight="bold", fontsize=11.5)
    save(fig, "fig2_bunching.png")


def fig_all_limits(men):
    fig, ax = plt.subplots(figsize=(7.5, 4.0))
    xs, lrs, errs, cols = [], [], [], []
    for L in config.IPF_MEN_CLASSES + [config.H2_CONTROL]:
        b, a = prep.bunching_counts(men, L); lr, half, _ = su.log_ratio_ci(b, a)
        xs.append(str(L)); lrs.append(lr); errs.append(half)
        cols.append(C_LIM if L == config.H2_CONTROL else C_HL)
    ax.bar(xs, lrs, yerr=errs, color=cols, edgecolor="white", capsize=3)
    ax.axhline(0, color="#333", lw=1)
    ax.set_xlabel("Class limit (kg); grey = non-limit control")
    ax.set_ylabel("de-heaped log(below / above)")
    ax.set_title("Fig 3. Excess just-below mass at every real limit; control near zero")
    save(fig, "fig3_all_limits.png")


def fig_allometry(al):
    rng = np.random.default_rng(config.SEED)
    fig, ax = plt.subplots(figsize=(7.8, 4.3))
    allx = np.log(al["BodyweightKg"].to_numpy()); ally = np.log(al["TotalKg"].to_numpy())
    for sex, col, lbl in [("M", C_M, "Men"), ("F", C_W, "Women")]:
        g = al[al["Sex"] == sex]
        x, y = np.log(g["BodyweightKg"].to_numpy()), np.log(g["TotalKg"].to_numpy())
        fit = su.ols_loglog(x, y); b, r2 = fit["b"], fit["r2"]
        idx = rng.choice(len(x), size=min(6000, len(x)), replace=False)
        ax.scatter(x[idx], y[idx], s=4, alpha=0.15, color=col, edgecolors="none")
        xs = np.linspace(x.min(), np.percentile(x, 99.5), 50)
        ax.plot(xs, fit["a"] + b * xs, color=col, lw=3.0, label=f"{lbl}: b = {b:.2f} (R2={r2:.2f})")
    xbar, ybar = allx.mean(), ally.mean()
    xr = np.linspace(np.percentile(allx, 1), np.percentile(allx, 99), 50)
    ax.plot(xr, ybar + (2 / 3) * (xr - xbar), color="#222", lw=2.5, ls="--", label="isometric: b = 2/3")
    ax.set_xlabel("log( Bodyweight )"); ax.set_ylabel("log( Total )")
    ax.set_title("Fig 4. Allometric scaling by sex (all-row OLS fits; formal per-lifter HC3: 0.75 / 0.51)")
    ax.legend(frameon=True, framealpha=0.9, loc="lower right", fontsize=10)
    save(fig, "fig4_allometry.png")


def fig_prediction():
    h4 = json.loads((config.RESULTS / "h4.json").read_text())
    imp = h4["regression_total"]["rf_permutation_importance"]
    mods = h4["regression_total"]["models"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.0))
    feats = list(imp)[::-1]
    a1.barh(feats, [imp[f] for f in feats], color=C_M, edgecolor="white")
    a1.set_xlabel("permutation importance (drop in R2)"); a1.set_title("RF feature importance")
    names = [m for m in mods]; r2s = [mods[m]["cv_r2"] for m in names]
    a2.bar(names, r2s, color=[C_OFF, C_HL], edgecolor="white")
    for i, v in enumerate(r2s): a2.text(i, v + 0.01, f"{v:.2f}", ha="center", fontsize=10)
    a2.set_ylim(0, 1); a2.set_ylabel("CV R2 (grouped by lifter)"); a2.set_title("Strength prediction (TotalKg)")
    fig.suptitle("Fig 5. Predicting strength: bodyweight + sex dominate; RF beats linear",
                 fontweight="bold", fontsize=11.5)
    save(fig, "fig5_prediction.png")


def fig_structure(pl):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.0))
    for ax, col, title in [(a1, "TotalKg", "Raw Total (pooled): two components = sex"),
                           (a2, "Dots", "Dots (sex-normalized): one component")]:
        for sex, c in [("M", C_M), ("F", C_W)]:
            v = pl.loc[pl.Sex == sex, col].to_numpy()
            ax.hist(v, bins=80, density=True, alpha=0.5, color=c, label=sex)
        ax.set_xlabel(col); ax.set_ylabel("density"); ax.set_title(title); ax.legend(frameon=False)
    fig.suptitle("Fig 6. The apparent 'mixture' in raw Total is just sex; Dots removes it",
                 fontweight="bold", fontsize=11.5)
    save(fig, "fig6_structure.png")


def fig_breadth(men_recent_chrono):
    # SPRT cumulative log-likelihood-ratio path (chronological) + power curve
    p0, p1, alpha, beta = 0.5, 0.6, 0.05, 0.10
    def lab(bw):
        for L in config.IPF_MEN_CLASSES:
            if L - 1 < bw <= L: return 1
            if L < bw <= L + 1: return 0
        return np.nan
    obs = men_recent_chrono["BodyweightKg"].map(lab).dropna().astype(int).to_numpy()
    A = np.log((1 - beta) / alpha); B = np.log(beta / (1 - alpha))
    s1, s0 = np.log(p1 / p0), np.log((1 - p1) / (1 - p0))
    inc = np.where(obs == 1, s1, s0); llr = np.cumsum(inc)
    crossed = (llr >= A) | (llr <= B)               # stop at first crossing of EITHER boundary
    stop = int(np.argmax(crossed)) + 1 if crossed.any() else len(llr)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.0))
    a1.plot(np.arange(1, min(stop + 15, len(llr)) + 1), llr[:min(stop + 15, len(llr))], color=C_M, lw=1.8)
    a1.axhline(A, color=C_GRID, ls="--", lw=1.5, label=f"accept H1 (A={A:.2f})")
    a1.axhline(B, color=C_LIM, ls="--", lw=1.5, label=f"accept H0 (B={B:.2f})")
    a1.axvline(stop, color="#333", ls=":", lw=1); a1.text(stop, B, f" stop N={stop}", fontsize=9, va="bottom")
    a1.set_xlabel("observation (chronological)"); a1.set_ylabel("cumulative log-LR")
    a1.set_title("SPRT: sequential cut detection"); a1.legend(frameon=False, fontsize=9)
    z_a = sp.norm.ppf(1 - alpha)
    ns = np.arange(10, 600)
    def pw(n): crit = p0 + z_a * np.sqrt(p0 * (1 - p0) / n); return sp.norm.sf((crit - p1) / np.sqrt(p1 * (1 - p1) / n))
    powers = [pw(n) for n in ns]
    a2.plot(ns, powers, color=C_HL, lw=2)
    a2.axhline(0.90, color="#333", ls="--", lw=1); n90 = next(n for n in ns if pw(n) >= 0.90)
    a2.axvline(n90, color="#333", ls=":", lw=1); a2.text(n90 + 8, 0.5, f"n={n90} for power 0.90", fontsize=9)
    a2.set_xlabel("sample size n"); a2.set_ylabel("power (1 - beta)")
    a2.set_title("A-priori power (detect p=0.6 vs 0.5, alpha=0.05)")
    fig.suptitle("Fig 7. Sequential test (stopping time) and a-priori power",
                 fontweight="bold", fontsize=11.5)
    save(fig, "fig7_breadth.png")


def run():
    print("loading data ...")
    df = data.load()
    att = prep.valid_attempt_loads(df)
    men = df.loc[config.is_h2_federation(df) & (df["Sex"] == "M"), "BodyweightKg"].dropna().to_numpy()
    al = df[(df.Event == "SBD") & (df.TotalKg > 0) & (df.BodyweightKg > 0)
            & df.Sex.isin(["M", "F"])][["Sex", "BodyweightKg", "TotalKg"]].dropna()
    sbd = df[(df.Event == "SBD") & (df.TotalKg > 0) & (df.BodyweightKg > 0) & df.Sex.isin(["M", "F"])].copy()
    sbd["Dots"] = pd.to_numeric(sbd["Dots"], errors="coerce")
    pl = prep.dedup_per_lifter(sbd.dropna(subset=["Dots"]), keep="random").sample(40000, random_state=config.SEED)
    mr = df[(df.Sex == "M") & (df.BodyweightKg > 0) & config.is_h2_federation(df)].copy()
    mr["year"] = pd.to_datetime(mr["Date"], errors="coerce").dt.year
    mr = prep.dedup_per_lifter(mr[mr.year >= 2014], keep="random").sort_values("Date")

    print("building figures (300 DPI) ...")
    fig_quantization(att); fig_bunching(men); fig_all_limits(men); fig_allometry(al)
    fig_prediction(); fig_structure(pl); fig_breadth(mr)
    print("done.")


if __name__ == "__main__":
    run()
