#!/usr/bin/env python3
"""
Compute the headline results on the OpenPowerlifting data and render the
presentation figures (PNG) into ../figures, printing numbers + CIs.

Axis labels are kept in ENGLISH on purpose (matplotlib bidi); Hebrew interpretation
lives on the slide. Method notes:
- H1: fraction of attempt loads exactly on the 2.5 kg grid (+ Wilson-ish CI).
- H2: bodyweight near a real class limit vs a non-limit control; the histogram and the
  reported log(below/above) are BOTH de-heaped (exact round/half-kg weigh-ins removed),
  so the figure matches the headline number; window (L-0.5, L]; + CI.
- H5: allometry on full-power (Event=='SBD') results; OLS slope b + CI + R²; isometric 2/3 ref.

Input: ../data/openpowerlifting.csv (run download_data.py first).
"""
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV = str(ROOT / "data" / "openpowerlifting.csv")
OUT = str(ROOT / "figures")

plt.rcParams.update({
    "figure.dpi": 200, "savefig.dpi": 200, "font.size": 13,
    "axes.titlesize": 15, "axes.titleweight": "bold", "axes.labelsize": 13,
    "axes.spines.top": False, "axes.spines.right": False, "figure.autolayout": True,
})
C_GRID, C_OFF, C_HL, C_LIM = "#C0392B", "#5499C7", "#E67E22", "#566573"
C_M, C_W = "#2E86C1", "#E67E22"

att_cols = [f"{l}{i}Kg" for l in ("Squat", "Bench", "Deadlift") for i in (1, 2, 3)]
cols = ["Sex", "Equipment", "BodyweightKg", "WeightClassKg", "TotalKg", "Dots",
        "Tested", "Federation", "ParentFederation", "Event"] + att_cols
print("Loading data ...")
df = pd.read_csv(CSV, usecols=cols, low_memory=False)
print(f"  {len(df):,} rows")

# ---- H1: quantization to the 2.5 kg plate grid ----
att = np.abs(df[att_cols].to_numpy(dtype="float64").ravel())
att = att[(~np.isnan(att)) & (att > 0)]
on_grid = np.abs(att/2.5 - np.round(att/2.5)) < 1e-6
k, N = int(on_grid.sum()), len(att)
p = k/N
ci_h = 1.96*np.sqrt(p*(1-p)/N)            # normal-approx CI (n is huge → very tight)
pct_grid = 100*p
print(f"\n[H1] valid attempts: {N:,} | on grid: {pct_grid:.4f}%  95% CI [{100*(p-ci_h):.2f}, {100*(p+ci_h):.2f}]")

fig, ax = plt.subplots(figsize=(8.2, 4.4))
lo, hi, bw = 100, 150, 0.5
bins = np.arange(lo, hi+bw, bw)
sub = att[(att >= lo) & (att < hi)]
counts, edges, patches = ax.hist(sub, bins=bins, edgecolor="white", linewidth=0.2)
for c_edge, pa in zip(edges[:-1], patches):
    pa.set_facecolor(C_GRID if abs(c_edge/2.5 - round(c_edge/2.5)) < 1e-6 else C_OFF)
ax.set_ylim(0, counts.max()*1.18)
ax.xaxis.set_major_locator(MultipleLocator(5))
ax.set_xlabel("Attempt weight (kg)"); ax.set_ylabel("Count")
ax.set_title("Attempt weights pile up on the 2.5 kg plate grid")
ax.legend(handles=[Patch(color=C_GRID, label="On 2.5 kg grid"),
                   Patch(color=C_OFF, label="Off grid")], frameon=False)
ax.text(0.98, 0.95, f"{pct_grid:.1f}% of all attempts\nfall on the 2.5 kg grid",
        transform=ax.transAxes, ha="right", va="top", fontsize=12,
        bbox=dict(boxstyle="round", fc="#FDEBD0", ec=C_HL))
fig.savefig(f"{OUT}/fig_quantization.png"); plt.close(fig)
print("  saved fig_quantization.png")

# ---- H2: bunching just below a class limit vs a non-limit control ----
ipf = df[(df["ParentFederation"] == "IPF") | (df["Federation"].isin(["IPF", "USAPL"]))]
men = ipf[ipf["Sex"] == "M"]["BodyweightKg"].dropna().to_numpy()

def deheap(bw):                              # drop exact round/half-kg weigh-ins
    frac = bw*2 - np.round(bw*2)
    return bw[np.abs(frac) > 1e-6]

def asym(bw, L, w=0.5):                       # de-heaped log(below/above) + 95% CI
    bwd = deheap(bw)
    below = int(((bwd > L-w) & (bwd <= L)).sum())
    above = int(((bwd > L) & (bwd <= L+w)).sum())
    lr = np.log(below/above)
    se = np.sqrt(1/below + 1/above)
    return below, above, lr, 1.96*se

REAL, CTRL = 83, 91
panels = [(REAL, 79, 87, f"Real class limit ({REAL} kg)", True),
          (CTRL, 87, 95, f"Non-limit control ({CTRL} kg)", False)]
segs = {L: deheap(men[(men >= lo) & (men < hi)]) for L, lo, hi, *_ in panels}
binw = 0.25
ymax = max(np.histogram(s, bins=np.arange(lo, hi+binw, binw))[0].max()
           for (L, lo, hi, *_), s in zip(panels, segs.values())) * 1.15

fig, axes = plt.subplots(1, 2, figsize=(9.8, 4.3))
for ax, (L, lo, hi, title, is_real) in zip(axes, panels):
    seg = segs[L]; bins = np.arange(lo, hi+binw, binw)
    counts, edges, patches = ax.hist(seg, bins=bins, edgecolor="white", linewidth=0.15)
    for c_edge, pa in zip(edges[:-1], patches):
        pa.set_facecolor(C_HL if (L-0.5 <= c_edge < L) else C_OFF)
    ax.axvline(L, color=C_LIM, lw=2, ls="--")
    ax.set_ylim(0, ymax)
    b, a, lr, ci = asym(men, L)
    ax.set_title(title); ax.set_xlabel("Bodyweight (kg)"); ax.set_ylabel("Count")
    ax.text(0.04, 0.96, f"de-heaped\nlog(below/above)\n= {lr:+.2f} ± {ci:.2f}",
            transform=ax.transAxes, ha="left", va="top", fontsize=10.5,
            bbox=dict(boxstyle="round", fc="#FDEBD0" if is_real else "#EBF5FB",
                      ec=C_HL if is_real else C_OFF))
axes[0].legend(handles=[Patch(color=C_HL, label="just-below window (L-0.5, L]"),
                        Line2D([0], [0], color=C_LIM, lw=2, ls="--", label="class limit / control")],
               frameon=False, fontsize=8.5, loc="upper right")
fig.suptitle("Bodyweight just below a real class limit (83 kg) vs a non-limit control (91 kg)\n"
             "round-number weigh-ins removed (de-heaped)", fontweight="bold", fontsize=11.5)
fig.savefig(f"{OUT}/fig_bunching.png"); plt.close(fig)
print("  saved fig_bunching.png")
for L in (REAL, CTRL):
    b, a, lr, ci = asym(men, L)
    print(f"   @ {L}: de-heaped below {b:,} / above {a:,} | log-ratio {lr:+.3f} ± {ci:.3f} (x{np.exp(lr):.1f})")

# ---- H5: allometric scaling (full-power 'SBD' only) ----
al = df[(df["Event"] == "SBD") & (df["TotalKg"] > 0) & (df["BodyweightKg"] > 0)
        & df["Sex"].isin(["M", "F"])][["Sex", "BodyweightKg", "TotalKg"]].dropna()
fig, ax = plt.subplots(figsize=(9.0, 4.6))
rng = np.random.default_rng(7); stats = {}
allx = np.log(al["BodyweightKg"].to_numpy()); ally = np.log(al["TotalKg"].to_numpy())
for sex, col, lbl in [("M", C_M, "Men"), ("F", C_W, "Women")]:
    g = al[al["Sex"] == sex]
    x, y = np.log(g["BodyweightKg"].to_numpy()), np.log(g["TotalKg"].to_numpy())
    b, a = np.polyfit(x, y, 1)
    yhat = a + b*x
    ssres = np.sum((y-yhat)**2); sstot = np.sum((y-y.mean())**2)
    r2 = 1 - ssres/sstot
    sxx = np.sum((x-x.mean())**2); se_b = np.sqrt(ssres/(len(x)-2)/sxx); ci_b = 1.96*se_b
    stats[sex] = (b, ci_b, r2)
    idx = rng.choice(len(x), size=min(6000, len(x)), replace=False)
    ax.scatter(x[idx], y[idx], s=3, alpha=0.05, color=col, edgecolors="none")
    xs = np.linspace(x.min(), np.percentile(x, 99.5), 50)
    ax.plot(xs, a+b*xs, color=col, lw=3.0, label=f"{lbl}: b = {b:.2f} (R²={r2:.2f})")
xbar, ybar = allx.mean(), ally.mean()
xr = np.linspace(np.percentile(allx, 1), np.percentile(allx, 99), 50)
ax.plot(xr, ybar + (2/3)*(xr-xbar), color="#222", lw=2.2, ls="--",
        label="isometric: b = 2/3 ≈ 0.67")
ax.set_xlabel("log( Bodyweight )"); ax.set_ylabel("log( Total )")
ax.set_title("Allometric scaling of strength (full-power 'SBD')")
ax.legend(frameon=True, framealpha=0.9, loc="lower right", fontsize=11)
fig.savefig(f"{OUT}/fig_allometry.png"); plt.close(fig)
print(f"  saved fig_allometry.png")

print("\n===== numbers for the slides =====")
print(f"H1: {pct_grid:.1f}% (95% CI [{100*(p-ci_h):.2f},{100*(p+ci_h):.2f}]), n={N:,}")
b83, a83, lr83, c83 = asym(men, REAL); _, _, lr91, c91 = asym(men, CTRL)
print(f"H2 @83 de-heaped: {lr83:+.2f} ± {c83:.2f}  (x{np.exp(lr83):.1f})  |  @91 control: {lr91:+.2f} ± {c91:.2f}")
for s, name in [("M", "men"), ("F", "women")]:
    b, ci, r2 = stats[s]; print(f"H5 {name}: b={b:.2f} ± {ci:.2f}, R²={r2:.2f}")
