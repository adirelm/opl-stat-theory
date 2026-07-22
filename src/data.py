#!/usr/bin/env python3
"""
Data loading + snapshot pinning.

One entry point, `load()`, returns the OpenPowerlifting table with the columns
the pipeline actually uses (a defined schema, not all 42). `verify_snapshot()`
checks we are on the locked snapshot so results are reproducible.
"""
import hashlib
import pandas as pd

import config

# the 9 attempt-load columns (3 attempts x squat/bench/deadlift)
ATT_COLS = [f"{lift}{i}Kg" for lift in ("Squat", "Bench", "Deadlift") for i in (1, 2, 3)]

# columns used across all hypotheses + supporting analyses (kept lean on purpose)
ANALYSIS_COLS = [
    "Name", "Sex", "Event", "Equipment", "Age",
    "BodyweightKg", "TotalKg", "Dots", "Tested",
    "Federation", "ParentFederation", "Date",
] + ATT_COLS


def load(cols=ANALYSIS_COLS, verify=True):
    """Load the locked snapshot. Pass cols=None to load everything (42 columns)."""
    df = pd.read_csv(config.DATA_CSV, usecols=cols, low_memory=False)
    if verify:
        verify_snapshot(df, strict=False)
    return df


def verify_snapshot(df, strict=False):
    """Check we are on the pinned snapshot. Warns (or raises, if strict)."""
    n = len(df)
    if n != config.EXPECTED_ROWS:
        msg = (f"snapshot row count {n:,} != expected {config.EXPECTED_ROWS:,} "
               f"-- you are NOT on the locked snapshot; results may not reproduce.")
        if strict:
            raise RuntimeError(msg)
        print("WARNING:", msg)
        return False
    if strict and config.EXPECTED_SHA256:
        h = compute_sha256(config.DATA_CSV)
        if h != config.EXPECTED_SHA256:
            raise RuntimeError(f"snapshot sha256 {h} != expected {config.EXPECTED_SHA256}")
    return True


def compute_sha256(path, chunk=1 << 20):
    """Stream the file through SHA256 (run once to record EXPECTED_SHA256)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


if __name__ == "__main__":
    df = load()
    print(f"rows: {len(df):,} | cols: {df.shape[1]} | snapshot ok: {verify_snapshot(df)}")
