#!/usr/bin/env python3
"""
Data preparation shared by the hypotheses:
- de-heaping (drop round/half-kg weigh-ins that contaminate the bunching signal),
- attempt-level expansion (the unit for H1 is a single attempt),
- the plate-grid test,
- one-row-per-lifter deduplication (the unit for the FORMAL tests, to kill
  pseudo-replication),
- grouped-by-lifter CV splits (so the same person is never in train and test).
"""
import numpy as np
import pandas as pd

import config
from data import ATT_COLS


# ---------- H1: attempt-level helpers ----------
def valid_attempt_loads(df, with_fed=False):
    """Flatten the 9 attempt columns to a 1-D array of |load| for valid (>0) attempts.

    Failed attempts are stored negative in OpenPowerlifting, so we take abs value.
    If with_fed, also return the per-attempt Federation tag (same length).
    """
    A = np.abs(df[ATT_COLS].to_numpy(dtype="float64"))
    mask = (~np.isnan(A)) & (A > 0)
    att = A[mask]
    if not with_fed:
        return att
    fed = np.repeat(df["Federation"].to_numpy()[:, None], len(ATT_COLS), axis=1)[mask]
    return att, fed


def on_grid_mask(att, grid=config.GRID_KG, tol=1e-6):
    """Boolean mask: which loads sit exactly on the `grid` kg lattice."""
    return np.abs(att / grid - np.round(att / grid)) < tol


# ---------- H2: bunching helpers ----------
def deheap(bw, tol=1e-6):
    """Drop exact round/half-kg weigh-ins (heaping) that mimic the bunching signal."""
    frac = bw * 2 - np.round(bw * 2)
    return bw[np.abs(frac) > tol]


def bunching_counts(bw, limit, w=config.H2_WINDOW, do_deheap=True):
    """Counts just below vs just above a limit, on de-heaped bodyweights.

    Returns (below, above) over windows (limit-w, limit] and (limit, limit+w].
    """
    b = deheap(bw) if do_deheap else bw
    below = int(((b > limit - w) & (b <= limit)).sum())
    above = int(((b > limit) & (b <= limit + w)).sum())
    return below, above


# ---------- formal-test unit: one row per lifter ----------
def dedup_per_lifter(df, name_col="Name", rank_col="TotalKg", keep="random", seed=7):
    """Collapse to one row per lifter to kill pseudo-replication for the formal tests.

    OpenPowerlifting disambiguates distinct people who share a name with a '#N'
    suffix in the Name field, so Name is a usable lifter key.

    keep:
      'random' -> a random (seeded) meet per lifter. Preferred for the bodyweight
                  density test: meet selection is INDEPENDENT of the outcome, so it
                  does not distort the bodyweight distribution near cutoffs.
      'max'    -> the lifter's PR meet (max rank_col). Outcome-dependent; use only
                  where the best meet is the intended unit.
      'first'  -> first row seen per lifter.
    """
    if keep == "random":
        return (df.sample(frac=1, random_state=seed)
                  .drop_duplicates(subset=[name_col], keep="first").reset_index(drop=True))
    if keep == "max":
        # drop all-NaN rank rows first: on pandas >=2.1 idxmax() raises on an all-NA group
        d = df.dropna(subset=[rank_col])
        idx = d.groupby(name_col)[rank_col].idxmax()
        return d.loc[idx].reset_index(drop=True)
    if keep == "first":
        return df.drop_duplicates(subset=[name_col], keep="first").reset_index(drop=True)
    raise ValueError(f"unknown keep={keep!r}")


# ---------- leakage-safe CV ----------
def grouped_folds(groups, n_splits=5):
    """Yield (train_idx, test_idx) split GROUPED by `groups` (e.g. lifter Name)."""
    from sklearn.model_selection import GroupKFold        # lazy: heavy import
    gkf = GroupKFold(n_splits=n_splits)
    dummy = np.zeros(len(groups))
    yield from gkf.split(dummy, dummy, groups)
