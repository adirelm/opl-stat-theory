#!/usr/bin/env python3
"""
Compute the headline results on the OpenPowerlifting data and render the
presentation figures (PNG) into ../figures, printing the numbers as it goes.

Axis labels are kept in ENGLISH on purpose (to avoid matplotlib bidi issues with
Hebrew); the Hebrew interpretation lives in the slide text, not on the figure.

Method notes:
- H1 (quantization): fraction of attempt loads that lie exactly on the 2.5 kg grid.
- H2 (weight-cutting): boundary-correct window (L-0.5, L]; log(below/above) is reported
  AFTER de-heaping (dropping exact 0.5-kg multiples / round numbers); a non-limit
  bodyweight (91 kg) is the control. Restricted to IPF + USAPL (shared class scheme).
- H5 (allometry): full-power results only (Event == 'SBD'); an isometric reference
  line at b = 2/3 is drawn for comparison.

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
CSV = str(ROOT / "data" / "openpowerlifting.csv")   # run `python download_data.py` first
OUT = str(ROOT / "figures")

plt.rcParams.update({
    "figure.dpi": 200, "savefig.dpi": 200, "font.size": 13,
    "axes.titlesize": 15, "axes.titleweight": "bold", "axes.labelsize": 13,
    "axes.spines.top": False, "axes.spines.right": False, "figure.autolayout": True,
})
C_GRID, C_OFF, C_HL, C_LIM = "#C0392B", "#5499C7", "#E67E22", "#566573"
C_M, C_W = "#2E86C1", "#E67E22"   # men=blue, women=orange (off-red, colorblind-friendlier)

att_cols = [f"{l}{i}Kg" for l in ("Squat", "Bench", "Deadlift") for i in (1, 2, 3)]
cols = ["Sex", "Equipment", "BodyweightKg", "WeightClassKg", "TotalKg", "Dots",
        "Tested", "Federation", "ParentFederation", "Event"] + att_cols
print("Loading data ...")
df = pd.read_csv(CSV, usecols=cols, low_memory=False)
print(f"  {len(df):,} rows")

# ---- H1: quantization to the 2.5 kg plate grid ----
att = np.abs(df[att_cols].to_numpy(dtype="float64").ravel())
att = att[(~np.isnan(att)) & (att > 0)]
on_grid = np.abs(att/2.5 - np.round(att/2.5)) < 1e-6   # tolerance 1e-6 (reproducible)
pct_grid = 100*on_grid.mean()
print(f"\n[H1] valid attempts: {len(att):,} | on the 2.5 kg grid: {pct_grid:.2f}%")

fig, ax = plt.subplots(figsize=(8.2, 4.4))
lo, hi, bw = 100, 150, 0.5
bins = np.arange(lo, hi+bw, bw)
sub = att[(att >= lo) & (att < hi)]
counts, edges, patches = ax.hist(sub, bins=bins, edgecolor="white", linewidth=0.2)
for c_edge, p in zip(edges[:-1], patches):
    p.set_facecolor(C_GRID if abs(c_edge/2.5 - round(c_edge/2.5)) < 1e-6 else C_OFF)
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

# ---- H2: bunching just below a class limit + a non-limit control ----
# Restrict to the IPF class scheme (IPF + USAPL): same limits 83/93/105; 91 is not a limit.
# USPA is excluded -- it uses different round classes (82.5/90/100) that would contaminate this.
ipf = df[(df["ParentFederation"] == "IPF") | (df["Federation"].isin(["IPF", "USAPL"]))]
men = ipf[ipf["Sex"] == "M"]["BodyweightKg"].dropna().to_numpy()
print(f"\n[H2] men (IPF+USAPL): {len(men):,}")

def asym(bw, L, w=0.5, deheap=False):
    """Boundary-correct window: below=(L-w, L], above=(L, L+w].
    deheap=True drops exact 0.5-kg multiples (round-number heaping)."""
    if deheap:
        frac = bw*2 - np.round(bw*2)
        bw = bw[np.abs(frac) > 1e-6]
    below = ((bw > L-w) & (bw <= L)).sum()
    above = ((bw > L) & (bw <= L+w)).sum()
    lr = np.log(below/above) if (below > 0 and above > 0) else np.nan
    return int(below), int(above), lr

REAL, CTRL = 83, 91
fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.3))
for ax, (L, lo, hi, title, is_real) in zip(axes, [
        (REAL, 79, 87, f"Real class limit ({REAL} kg)", True),
        (CTRL, 87, 95, f"Non-limit control ({CTRL} kg)", False)]):
    seg = men[(men >= lo) & (men < hi)]
    bins = np.arange(lo, hi+0.25, 0.25)
    counts, edges, patches = ax.hist(seg, bins=bins, edgecolor="white", linewidth=0.15)
    for c_edge, p in zip(edges[:-1], patches):
        p.set_facecolor(C_HL if (L-0.5 <= c_edge < L) else C_OFF)
    ax.axvline(L, color=C_LIM, lw=2, ls="--")
    _, _, dlr = asym(men, L, deheap=True)
    ax.set_title(title); ax.set_xlabel("Bodyweight (kg)"); ax.set_ylabel("Count")
    ax.text(0.04, 0.95, f"de-heaped\nlog(below/above)\n= {dlr:+.2f}",
            transform=ax.transAxes, ha="left", va="top", fontsize=11,
            bbox=dict(boxstyle="round", fc="#FDEBD0" if is_real else "#EBF5FB",
                      ec=C_HL if is_real else C_OFF))
axes[0].legend(handles=[Patch(color=C_HL, label="just-below window (0.5 kg)"),
                        Line2D([0], [0], color=C_LIM, lw=2, ls="--", label="limit / control point")],
               frameon=False, fontsize=9, loc="upper right")
fig.suptitle("Bodyweight clusters just below REAL class limits, not at non-limit controls",
             fontweight="bold", fontsize=13)
fig.savefig(f"{OUT}/fig_bunching.png"); plt.close(fig)
print("  saved fig_bunching.png")
for L in (REAL, CTRL):
    b, a, lr = asym(men, L); db, da, dlr = asym(men, L, deheap=True)
    print(f"   @ {L}: raw {b:,}/{a:,} {lr:+.2f} | de-heaped {db:,}/{da:,} {dlr:+.2f}")

# ---- H5: allometric scaling (full-power 'SBD' only) ----
al = df[(df["Event"] == "SBD") & (df["TotalKg"] > 0) & (df["BodyweightKg"] > 0)
        & df["Sex"].isin(["M", "F"])][["Sex", "BodyweightKg", "TotalKg"]].dropna()
fig, ax = plt.subplots(figsize=(9.0, 4.5))
slopes, rng = {}, np.random.default_rng(7)
allx = np.log(al["BodyweightKg"].to_numpy()); ally = np.log(al["TotalKg"].to_numpy())
for sex, col, lbl in [("M", C_M, "Men"), ("F", C_W, "Women")]:
    g = al[al["Sex"] == sex]
    x, y = np.log(g["BodyweightKg"].to_numpy()), np.log(g["TotalKg"].to_numpy())
    b, a = np.polyfit(x, y, 1); slopes[sex] = b
    idx = rng.choice(len(x), size=min(8000, len(x)), replace=False)
    ax.scatter(x[idx], y[idx], s=3, alpha=0.10, color=col)
    xs = np.linspace(x.min(), np.percentile(x, 99.5), 50)
    ax.plot(xs, a+b*xs, color=col, lw=2.8, label=f"{lbl}: b = {b:.2f}")
# isometric reference line (slope 2/3) through the pooled centroid
xbar, ybar = allx.mean(), ally.mean()
xr = np.linspace(np.percentile(allx, 1), np.percentile(allx, 99), 50)
ax.plot(xr, ybar + (2/3)*(xr-xbar), color=C_LIM, lw=2, ls="--",
        label="isometric: b = 2/3 ≈ 0.67")
ax.set_xlabel("log( Bodyweight )"); ax.set_ylabel("log( Total )")
ax.set_title("Allometric scaling of strength (full-power 'SBD' only)")
ax.legend(frameon=False, loc="lower right", fontsize=12)
fig.savefig(f"{OUT}/fig_allometry.png"); plt.close(fig)
print(f"  saved fig_allometry.png | SBD b: men={slopes['M']:.3f} women={slopes['F']:.3f} (n={len(al):,})")

print("\n===== numbers for the slides =====")
print(f"H1 grid%   = {pct_grid:.1f}  (n={len(att):,})")
b83, a83, lr83 = asym(men, REAL); _, _, d83 = asym(men, REAL, deheap=True)
print(f"H2 @83     = raw {b83:,}/{a83:,} logR {lr83:+.2f} | de-heaped {d83:+.2f}")
_, _, d91 = asym(men, CTRL, deheap=True)
print(f"H2 @91 ctrl= de-heaped {d91:+.2f}")
print(f"H5 SBD b   = men {slopes['M']:.2f} / women {slopes['F']:.2f}")
print(f"N rows     = {len(df):,}")
