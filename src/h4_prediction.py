#!/usr/bin/env python3
"""
H4 -- the prediction / learning half of the course (Lectures 3 + 10).

Two leakage-safe pieces (every split is GROUPED BY LIFTER, so the same person is
never in both train and test):

  A) Regression of TotalKg from controllable / basic variables (bodyweight, sex,
     equipment, age). Linear vs Random Forest, evaluated with GroupKFold:
     R^2 / Adjusted-R^2 / RMSE / MAE, + permutation importance + VIF.
     Circularity guard: predict TotalKg (bodyweight is a legitimate physiological
     predictor -- that IS H3); deliberately EXCLUDE Dots / attempt loads / class.

  B) Logistic "made-weight just below a class limit" classifier on the pure-kg
     (post-2014) IPF+USAPL men (clean kg-class labels, consistent with H2):
     label = just-below(1) vs just-above(0). Features are NON-bodyweight
     (age, tested, era, eliteness=Dots, equipment) -- bodyweight defines the label,
     so it must not be a feature. Grouped-CV AUC + accuracy + confusion.
"""
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold, GroupShuffleSplit
from sklearn.metrics import (r2_score, mean_squared_error, mean_absolute_error,
                             roc_auc_score, accuracy_score, confusion_matrix)
from sklearn.inspection import permutation_importance
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools import add_constant

import config, data

N_SAMPLE = 200_000               # RF on millions of rows is slow; seeded subsample
CUT_W = 1.0                      # +/- kg window defining "just below" / "just above" a limit


def adj_r2(r2, n, p):
    return 1 - (1 - r2) * (n - 1) / (n - p - 1)


def regression_total(df, seed=config.SEED):
    rng = np.random.default_rng(seed)
    d = df[(df.Event == "SBD") & (df.TotalKg > 0) & (df.BodyweightKg > 0)
           & df.Sex.isin(["M", "F"])
           & df.Equipment.isin(["Raw", "Wraps", "Single-ply", "Multi-ply"])].copy()
    n_clean = len(d)
    d["Age"] = pd.to_numeric(d["Age"], errors="coerce")
    d["Age_missing"] = d["Age"].isna().astype(int)
    d["Age"] = d["Age"].fillna(d["Age"].median())
    d["male"] = (d.Sex == "M").astype(int)
    if len(d) > N_SAMPLE:
        d = d.iloc[rng.choice(len(d), N_SAMPLE, replace=False)].copy()

    eq = pd.get_dummies(d["Equipment"], prefix="eq", drop_first=True)
    X = pd.concat([d[["BodyweightKg", "male", "Age", "Age_missing"]].reset_index(drop=True),
                   eq.reset_index(drop=True)], axis=1).astype(float)
    y = d["TotalKg"].to_numpy(); groups = d["Name"].to_numpy()
    gkf = GroupKFold(n_splits=5)

    models = {}
    for name, mk in [("linear", lambda: LinearRegression()),
                     ("random_forest", lambda: RandomForestRegressor(
                         n_estimators=120, n_jobs=-1, random_state=seed, min_samples_leaf=5))]:
        r2s, rmses, maes = [], [], []
        for tr, te in gkf.split(X, y, groups):
            m = mk().fit(X.iloc[tr], y[tr]); pr = m.predict(X.iloc[te])
            r2s.append(r2_score(y[te], pr))
            rmses.append(float(np.sqrt(mean_squared_error(y[te], pr))))
            maes.append(mean_absolute_error(y[te], pr))
        r2m = float(np.mean(r2s))
        models[name] = {"r2": round(r2m, 3), "adj_r2": round(adj_r2(r2m, len(X), X.shape[1]), 3),
                        "rmse_kg": round(float(np.mean(rmses)), 1), "mae_kg": round(float(np.mean(maes)), 1)}

    # permutation importance (RF on a grouped holdout)
    tr, te = next(GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed).split(X, y, groups))
    rf = RandomForestRegressor(n_estimators=120, n_jobs=-1, random_state=seed,
                               min_samples_leaf=5).fit(X.iloc[tr], y[tr])
    pi = permutation_importance(rf, X.iloc[te], y[te], n_repeats=4, random_state=seed, n_jobs=-1)
    importance = {c: round(float(v), 3) for c, v in
                  sorted(zip(X.columns, pi.importances_mean), key=lambda t: -t[1])}

    # VIF (multicollinearity)
    Xc = add_constant(X)
    vif = {c: round(float(variance_inflation_factor(Xc.values, i)), 1)
           for i, c in enumerate(Xc.columns) if c != "const"}

    return {"n_clean_rows": int(n_clean), "n_sample": int(len(d)),
            "n_lifters": int(d.Name.nunique()), "features": list(X.columns),
            "models": models, "rf_permutation_importance": importance, "vif": vif}


def cut_classifier(df, seed=config.SEED):
    d = df[(df.BodyweightKg > 0) & (df.Sex == "M") & config.is_h2_federation(df)].copy()
    d["year"] = pd.to_datetime(d["Date"], errors="coerce").dt.year
    d = d[d["year"] >= 2014]                     # pure-kg era: clean kg-class labels (matches H2)

    def lab(bw):
        for L in config.IPF_MEN_CLASSES:
            if L - CUT_W < bw <= L: return 1
            if L < bw <= L + CUT_W: return 0
        return np.nan
    d["label"] = d["BodyweightKg"].map(lab)
    c = d.dropna(subset=["label"]).copy()
    c["Age"] = pd.to_numeric(c["Age"], errors="coerce"); c["Age"] = c["Age"].fillna(c["Age"].median())
    c["tested"] = (c["Tested"] == "Yes").astype(int)
    c["dots"] = pd.to_numeric(c["Dots"], errors="coerce"); c["dots"] = c["dots"].fillna(c["dots"].median())
    eqc = pd.get_dummies(c["Equipment"], prefix="eq", drop_first=True)
    X = pd.concat([c[["Age", "tested", "year", "dots"]].reset_index(drop=True),
                   eqc.reset_index(drop=True)], axis=1).astype(float).fillna(0)
    yc = c["label"].astype(int).to_numpy(); grc = c["Name"].to_numpy()

    # grouped CV AUC (robust), + a held-out confusion matrix
    gkf = GroupKFold(n_splits=5); aucs, accs = [], []
    for tr, te in gkf.split(X, yc, grc):
        clf = LogisticRegression(max_iter=1000, class_weight="balanced").fit(X.iloc[tr], yc[tr])
        proba = clf.predict_proba(X.iloc[te])[:, 1]; pred = (proba >= 0.5).astype(int)
        aucs.append(float(roc_auc_score(yc[te], proba))); accs.append(float(accuracy_score(yc[te], pred)))
    trc, tec = next(GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=seed).split(X, yc, grc))
    clf = LogisticRegression(max_iter=1000, class_weight="balanced").fit(X.iloc[trc], yc[trc])
    pr = (clf.predict_proba(X.iloc[tec])[:, 1] >= 0.5).astype(int)
    cm = confusion_matrix(yc[tec], pr).tolist()
    return {"n": int(len(c)), "n_just_below": int(yc.sum()), "n_just_above": int((yc == 0).sum()),
            "features": list(X.columns),
            "auc_cv_mean": round(float(np.mean(aucs)), 3), "auc_cv_sd": round(float(np.std(aucs)), 3),
            "accuracy_cv_mean": round(float(np.mean(accs)), 3),
            "confusion_holdout_[[TN,FP],[FN,TP]]": cm}


def run(save=True):
    df = data.load()
    A = regression_total(df)
    B = cut_classifier(df)
    res = {"regression_total": A, "cut_classifier": B}

    print("==== H4: prediction (learning half) ====")
    print(f"[A] TotalKg regression -- clean SBD rows {A['n_clean_rows']:,}, "
          f"sample {A['n_sample']:,} ({A['n_lifters']:,} lifters), GroupKFold by lifter:")
    for m, v in A["models"].items():
        print(f"    {m:<14} R2={v['r2']}  Adj-R2={v['adj_r2']}  RMSE={v['rmse_kg']} kg  MAE={v['mae_kg']} kg")
    print("  RF permutation importance (drop in R2 when shuffled):")
    for f, v in A["rf_permutation_importance"].items():
        print(f"     {f:<16} {v}")
    print(f"  VIF (>10 concerning): {A['vif']}")
    print(f"\n[B] cut classifier (pure-kg post-2014 IPF+USAPL men): n={B['n']:,} "
          f"(below={B['n_just_below']:,}, above={B['n_just_above']:,})")
    print(f"    AUC(CV)={B['auc_cv_mean']} +/- {B['auc_cv_sd']}  Accuracy(CV)={B['accuracy_cv_mean']}")
    print(f"    confusion [[TN,FP],[FN,TP]] = {B['confusion_holdout_[[TN,FP],[FN,TP]]']}")
    print("\nNOTE: bodyweight dominates TotalKg prediction (it IS H3); the value is how much "
          "equipment/sex/age add beyond it. Classifier uses NON-bodyweight features only "
          "(bodyweight defines the label). All splits grouped by lifter -> no leakage.")

    if save:
        config.RESULTS.mkdir(exist_ok=True)
        (config.RESULTS / "h4.json").write_text(json.dumps(res, indent=2))
        print(f"saved -> {config.RESULTS / 'h4.json'}")
    return res


if __name__ == "__main__":
    run()
