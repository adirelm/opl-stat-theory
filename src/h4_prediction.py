#!/usr/bin/env python3
"""
H4 internal check — does the prediction component give usable results?

Two pieces, both leakage-safe (split GROUPED BY LIFTER so the same person is never
in train and test):
  A) Regression of TotalKg from CONTROLLABLE/basic variables only (bodyweight, sex,
     equipment, age). Circularity guard: we predict Total (bodyweight is a legitimate
     physiological predictor) and deliberately exclude Dots / attempt weights / class.
     Compare Linear vs Random Forest with R^2 / Adjusted-R^2 / RMSE / MAE (GroupKFold),
     + permutation importance + VIF.
  B) Logistic "made-weight just below a class limit" classifier (IPF+USAPL men):
     label = just-below(1) vs just-above(0) a real class limit; features are NON-bodyweight
     (equipment, tested, era, eliteness=Dots, age). AUC / accuracy / confusion.

This is a STAGE-2 prototype run for an internal check; it does not touch the deck.
"""
import numpy as np, pandas as pd
from pathlib import Path
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold, GroupShuffleSplit
from sklearn.metrics import (r2_score, mean_squared_error, mean_absolute_error,
                             roc_auc_score, accuracy_score, confusion_matrix)
from sklearn.inspection import permutation_importance
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools import add_constant

ROOT = Path(__file__).resolve().parent.parent
CSV = str(ROOT / "data" / "openpowerlifting.csv")
rng = np.random.default_rng(7)

cols = ["Name","Sex","Equipment","Age","BodyweightKg","TotalKg","Event",
        "Federation","ParentFederation","Dots","Tested","Date"]
print("Loading ...")
df = pd.read_csv(CSV, usecols=cols, low_memory=False)
print(f"  {len(df):,} rows")

def adj_r2(r2, n, p): return 1 - (1 - r2) * (n - 1) / (n - p - 1)

# ===================== A) Regression of Total =====================
d = df[(df.Event == "SBD") & (df.TotalKg > 0) & (df.BodyweightKg > 0)
       & df.Sex.isin(["M","F"]) & df.Equipment.isin(["Raw","Wraps","Single-ply","Multi-ply"])].copy()
print(f"\n[A] full-power clean rows: {len(d):,}")
d["Age"] = pd.to_numeric(d["Age"], errors="coerce")
d["Age_missing"] = d["Age"].isna().astype(int)
d["Age"] = d["Age"].fillna(d["Age"].median())
d["male"] = (d.Sex == "M").astype(int)

# sample for speed (RF on millions of rows is slow); group split is by Name afterwards
N = 200_000
if len(d) > N:
    d = d.iloc[rng.choice(len(d), N, replace=False)].copy()
print(f"    sample used for models: {len(d):,} rows, {d.Name.nunique():,} lifters")

eq = pd.get_dummies(d["Equipment"], prefix="eq", drop_first=True)
X = pd.concat([d[["BodyweightKg","male","Age","Age_missing"]].reset_index(drop=True),
               eq.reset_index(drop=True)], axis=1).astype(float)
y = d["TotalKg"].to_numpy()
groups = d["Name"].to_numpy()
gkf = GroupKFold(n_splits=5)

print("\n[A] Regression of TotalKg (5-fold, grouped by lifter):")
for name, mk in [("Linear      ", lambda: LinearRegression()),
                 ("RandomForest", lambda: RandomForestRegressor(
                     n_estimators=120, n_jobs=-1, random_state=7, min_samples_leaf=5))]:
    r2s, rmses, maes = [], [], []
    for tr, te in gkf.split(X, y, groups):
        m = mk().fit(X.iloc[tr], y[tr]); pr = m.predict(X.iloc[te])
        r2s.append(r2_score(y[te], pr)); rmses.append(np.sqrt(mean_squared_error(y[te], pr)))
        maes.append(mean_absolute_error(y[te], pr))
    r2m = np.mean(r2s)
    print(f"   {name}: R2={r2m:.3f}  Adj-R2={adj_r2(r2m,len(X),X.shape[1]):.3f}  "
          f"RMSE={np.mean(rmses):.1f} kg  MAE={np.mean(maes):.1f} kg")

# permutation importance (RF, single grouped holdout)
tr, te = next(GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=7).split(X, y, groups))
rf = RandomForestRegressor(n_estimators=120, n_jobs=-1, random_state=7, min_samples_leaf=5).fit(X.iloc[tr], y[tr])
pi = permutation_importance(rf, X.iloc[te], y[te], n_repeats=4, random_state=7, n_jobs=-1)
print("\n[A] RF permutation importance (drop in R2 when shuffled):")
for f, v in sorted(zip(X.columns, pi.importances_mean), key=lambda t: -t[1]):
    print(f"     {f:<16} {v:.3f}")

# VIF (multicollinearity) on the linear feature set
Xc = add_constant(X)
print("\n[A] VIF (multicollinearity; >10 = concerning):")
for i, c in enumerate(Xc.columns):
    if c == "const": continue
    print(f"     {c:<16} {variance_inflation_factor(Xc.values, i):.1f}")

# ===================== B) Cut classifier =====================
LIMITS = [59,66,74,83,93,105,120]; W = 1.0
ipf = df[(df.BodyweightKg > 0) & (df.Sex == "M")
         & ((df.ParentFederation == "IPF") | (df.Federation.isin(["IPF","USAPL"])))].copy()
def lab(bw):
    for L in LIMITS:
        if L - W < bw <= L: return 1      # just below a limit
        if L < bw <= L + W: return 0      # just above
    return np.nan
ipf["label"] = ipf["BodyweightKg"].map(lab)
c = ipf.dropna(subset=["label"]).copy()
c["Age"] = pd.to_numeric(c["Age"], errors="coerce"); c["Age"] = c["Age"].fillna(c["Age"].median())
c["tested"] = (c["Tested"] == "Yes").astype(int)
c["year"] = pd.to_datetime(c["Date"], errors="coerce").dt.year.fillna(2015).astype(float)
c["dots"] = pd.to_numeric(c["Dots"], errors="coerce"); c["dots"] = c["dots"].fillna(c["dots"].median())
eqc = pd.get_dummies(c["Equipment"], prefix="eq", drop_first=True)
Xc2 = pd.concat([c[["Age","tested","year","dots"]].reset_index(drop=True),
                 eqc.reset_index(drop=True)], axis=1).astype(float).fillna(0)
yc = c["label"].astype(int).to_numpy(); grc = c["Name"].to_numpy()
print(f"\n[B] cut classifier sample (IPF+USAPL men near limits): {len(c):,} "
      f"(just-below={int(yc.sum()):,}, just-above={int((yc==0).sum()):,})")
trc, tec = next(GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=7).split(Xc2, yc, grc))
clf = LogisticRegression(max_iter=1000, class_weight="balanced").fit(Xc2.iloc[trc], yc[trc])
proba = clf.predict_proba(Xc2.iloc[tec])[:, 1]; pred = (proba >= 0.5).astype(int)
print(f"    AUC={roc_auc_score(yc[tec], proba):.3f}  Accuracy={accuracy_score(yc[tec], pred):.3f}")
print(f"    confusion [ [TN FP] [FN TP] ] = {confusion_matrix(yc[tec], pred).tolist()}")
print("\nDone.")
