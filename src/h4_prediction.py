#!/usr/bin/env python3
"""
H4 -- the prediction / learning half of the course (Lectures 3 + 10).

Two leakage-safe pieces (every split is GROUPED BY LIFTER), with fold-safe
preprocessing (imputation/encoding fit INSIDE each training fold via a Pipeline):

  A) Regression of TotalKg from controllable / basic variables (bodyweight, sex,
     equipment, age). Linear vs Random Forest, evaluated on POOLED out-of-fold
     predictions (GroupKFold): CV R^2 / RMSE / MAE, + permutation importance + VIF.
     Unit = one (random, seeded) meet per lifter, so the eval population is not
     biased toward frequent competitors. Circularity guard: predict TotalKg
     (bodyweight is a legitimate physiological predictor -- that IS H3); EXCLUDE
     Dots / attempt loads / class. Adjusted-R^2 is reported ONLY for the linear
     model, as an in-sample OLS diagnostic (it is not meaningful for RF or for CV).

  B) Logistic 'made-weight just below a class limit' classifier on the pure-kg
     (post-2014) IPF+USAPL men. Label = just-below(1) vs just-above(0). Features
     are genuinely exogenous and NON-bodyweight (age, tested, era, equipment).
     Dots is EXCLUDED: it is a function of TotalKg and bodyweight (circular /
     post-outcome). Grouped-CV pooled-OOF AUC + PR-AUC + balanced accuracy + confusion.
"""
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import (r2_score, mean_squared_error, mean_absolute_error,
                             roc_auc_score, average_precision_score,
                             balanced_accuracy_score, confusion_matrix)
from sklearn.inspection import permutation_importance
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools import add_constant

import config, data, prep

N_SAMPLE = 200_000
CUT_W = 1.0


def adj_r2(r2, n, p):
    return 1 - (1 - r2) * (n - 1) / (n - p - 1)


def regression_total(df, seed=config.SEED):
    d = df[(df.Event == "SBD") & (df.TotalKg > 0) & (df.BodyweightKg > 0)
           & df.Sex.isin(["M", "F"])
           & df.Equipment.isin(["Raw", "Wraps", "Single-ply", "Multi-ply"])].copy()
    n_clean = len(d)
    # one (random, seeded) meet per lifter -> removes frequent-competitor bias
    d = prep.dedup_per_lifter(d, keep="random", seed=seed)
    if len(d) > N_SAMPLE:
        d = d.sample(N_SAMPLE, random_state=seed).reset_index(drop=True)
    d["Age_num"] = pd.to_numeric(d["Age"], errors="coerce")
    d["Age_missing"] = d["Age_num"].isna().astype(float)
    d["male"] = (d.Sex == "M").astype(float)

    FEAT = ["BodyweightKg", "male", "Age_missing", "Age_num", "Equipment"]
    X = d[FEAT]; y = d["TotalKg"].to_numpy(); groups = d["Name"].to_numpy()
    pre = ColumnTransformer([
        ("age_imp", SimpleImputer(strategy="median"), ["Age_num"]),
        ("pass", "passthrough", ["BodyweightKg", "male", "Age_missing"]),
        ("eq", OneHotEncoder(drop="first", handle_unknown="ignore"), ["Equipment"]),
    ])
    gkf = GroupKFold(n_splits=5)

    models = {}
    for name, est in [("linear", LinearRegression()),
                      ("random_forest", RandomForestRegressor(
                          n_estimators=120, n_jobs=-1, random_state=seed, min_samples_leaf=5))]:
        pipe = Pipeline([("pre", pre), ("est", est)])
        oof = cross_val_predict(pipe, X, y, cv=gkf, groups=groups)   # pooled out-of-fold preds
        models[name] = {"cv_r2": round(float(r2_score(y, oof)), 3),
                        "cv_rmse_kg": round(float(np.sqrt(mean_squared_error(y, oof))), 1),
                        "cv_mae_kg": round(float(mean_absolute_error(y, oof)), 1)}
    # Adjusted-R^2: linear, in-sample OLS diagnostic only
    lin = Pipeline([("pre", pre), ("est", LinearRegression())]).fit(X, y)
    p_feat = lin.named_steps["pre"].transform(X.iloc[:5]).shape[1]
    r2_in = float(lin.score(X, y))
    models["linear"]["insample_r2"] = round(r2_in, 3)
    models["linear"]["insample_adj_r2"] = round(adj_r2(r2_in, len(X), p_feat), 3)

    # permutation importance: RF on a grouped holdout; permutes RAW features
    # (Equipment counted as ONE factor, avoiding the dummy-VIF artifact)
    tr, te = next(GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed).split(X, y, groups))
    rf = Pipeline([("pre", pre), ("est", RandomForestRegressor(
        n_estimators=120, n_jobs=-1, random_state=seed, min_samples_leaf=5))]).fit(X.iloc[tr], y[tr])
    pi = permutation_importance(rf, X.iloc[te], y[te], n_repeats=4, random_state=seed, n_jobs=-1)
    importance = {c: round(float(v), 3) for c, v in
                  sorted(zip(FEAT, pi.importances_mean), key=lambda t: -t[1])}

    # VIF on the CONTINUOUS features only (dummy-level VIF is a categorical artifact)
    cont = d[["BodyweightKg", "Age_num"]].copy()
    cont["Age_num"] = cont["Age_num"].fillna(cont["Age_num"].median())
    Xc = add_constant(cont)
    vif = {c: round(float(variance_inflation_factor(Xc.values, i)), 1)
           for i, c in enumerate(Xc.columns) if c != "const"}

    return {"n_clean_rows": int(n_clean), "n_lifters_used": int(len(d)),
            "features": FEAT, "models": models,
            "rf_permutation_importance": importance,
            "vif_continuous": vif,
            "vif_note": "equipment is categorical; dummy-level VIF is not interpreted as continuous collinearity"}


def cut_classifier(df, seed=config.SEED):
    d = df[(df.BodyweightKg > 0) & (df.Sex == "M") & config.is_h2_federation(df)].copy()
    d["year"] = pd.to_datetime(d["Date"], errors="coerce").dt.year
    d = d[d["year"] >= 2014]                     # pure-kg era: clean kg-class labels

    def lab(bw):
        for L in config.IPF_MEN_CLASSES:
            if L - CUT_W < bw <= L: return 1
            if L < bw <= L + CUT_W: return 0
        return np.nan
    d["label"] = d["BodyweightKg"].map(lab)
    c = d.dropna(subset=["label"]).copy()
    c["Age_num"] = pd.to_numeric(c["Age"], errors="coerce")
    c["tested"] = (c["Tested"] == "Yes").astype(float)
    # NOTE: Dots is deliberately EXCLUDED -- it is f(TotalKg, bodyweight): circular + post-outcome.
    FEAT = ["Age_num", "tested", "year", "Equipment"]
    X = c[FEAT]; yc = c["label"].astype(int).to_numpy(); grc = c["Name"].to_numpy()
    pre = ColumnTransformer([
        ("age_imp", SimpleImputer(strategy="median"), ["Age_num"]),
        ("pass", "passthrough", ["tested", "year"]),
        ("eq", OneHotEncoder(drop="first", handle_unknown="ignore"), ["Equipment"]),
    ])
    pipe = Pipeline([("pre", pre),
                     ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))])
    gkf = GroupKFold(n_splits=5)
    proba = cross_val_predict(pipe, X, yc, cv=gkf, groups=grc, method="predict_proba")[:, 1]
    pred = (proba >= 0.5).astype(int)
    return {"n": int(len(c)), "n_just_below": int(yc.sum()), "n_just_above": int((yc == 0).sum()),
            "features": FEAT, "dots_excluded": True,
            "auc": round(float(roc_auc_score(yc, proba)), 3),
            "pr_auc": round(float(average_precision_score(yc, proba)), 3),
            "balanced_accuracy": round(float(balanced_accuracy_score(yc, pred)), 3),
            "confusion_[[TN,FP],[FN,TP]]": confusion_matrix(yc, pred).tolist()}


def run(save=True):
    df = data.load()
    A = regression_total(df)
    B = cut_classifier(df)
    res = {"regression_total": A, "cut_classifier": B}

    print("==== H4: prediction (learning half) ====")
    print(f"[A] TotalKg regression -- clean SBD rows {A['n_clean_rows']:,}; one random meet per "
          f"lifter, {A['n_lifters_used']:,} lifters; GroupKFold (pooled OOF):")
    for m, v in A["models"].items():
        line = f"    {m:<14} CV R2={v['cv_r2']}  RMSE={v['cv_rmse_kg']} kg  MAE={v['cv_mae_kg']} kg"
        if "insample_adj_r2" in v:
            line += f"   (in-sample OLS Adj-R2={v['insample_adj_r2']})"
        print(line)
    print("  RF permutation importance (raw features; Equipment as one factor):")
    for f, v in A["rf_permutation_importance"].items():
        print(f"     {f:<14} {v}")
    print(f"  VIF (continuous only): {A['vif_continuous']}  [{A['vif_note']}]")
    print(f"\n[B] cut classifier (pure-kg post-2014 men; Dots EXCLUDED as circular): n={B['n']:,} "
          f"(below={B['n_just_below']:,}, above={B['n_just_above']:,})")
    print(f"    AUC={B['auc']}  PR-AUC={B['pr_auc']}  balanced-acc={B['balanced_accuracy']}")
    print(f"    confusion [[TN,FP],[FN,TP]] = {B['confusion_[[TN,FP],[FN,TP]]']}")
    print("\nNOTE: bodyweight dominates TotalKg prediction (it IS H3); the value is how much "
          "equipment/sex/age add beyond it. Classifier uses ONLY exogenous non-bodyweight "
          "features (Dots dropped). All splits grouped by lifter; preprocessing is fold-safe.")

    if save:
        config.RESULTS.mkdir(exist_ok=True)
        (config.RESULTS / "h4.json").write_text(json.dumps(res, indent=2))
        print(f"saved -> {config.RESULTS / 'h4.json'}")
    return res


if __name__ == "__main__":
    run()
