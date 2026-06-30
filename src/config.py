#!/usr/bin/env python3
"""
Central configuration: paths, seeds, and the constants shared across the
analysis pipeline. Everything that another module might need to agree on
(class limits, the plate grid, the H2 federation rule, the locked snapshot)
lives here, so there is a single source of truth.
"""
from pathlib import Path

# ---- paths ----
ROOT = Path(__file__).resolve().parent.parent
DATA_CSV = ROOT / "data" / "openpowerlifting.csv"
FIGURES = ROOT / "figures"
RESULTS = ROOT / "results"          # numeric outputs (json/csv) land here

# ---- reproducibility ----
SEED = 7
ALPHA = 0.05

# ---- physical / domain constants ----
GRID_KG = 2.5                       # smallest standard plate is 1.25 kg, loaded both sides -> 2.5 kg step
KG_PER_LB = 0.45359237              # for the pounds<->kg units check (off-grid attempts)

# IPF modern weight classes (kg). H2 uses the men's scheme.
IPF_MEN_CLASSES = [59, 66, 74, 83, 93, 105, 120]

# H2 headline limit + the non-limit control (a point that should be "flat")
H2_REAL_LIMIT = 83
H2_CONTROL = 91
H2_WINDOW = 0.5                     # +/- window (kg) around a limit for the below/above counts

# H2 federation rule: same modern class scheme. USPA is excluded on purpose
# (it uses 82.5/90/100... which would mix heaping with the threshold).
def is_h2_federation(df):
    """Boolean mask: rows from IPF-scheme federations (IPF parent, or IPF/USAPL)."""
    return (df["ParentFederation"] == "IPF") | (df["Federation"].isin(["IPF", "USAPL"]))

# ---- locked data snapshot ----
# openpowerlifting-latest.zip updates ~weekly; pin the snapshot so the
# assessor's numbers match ours exactly. Verified row count of our snapshot:
EXPECTED_ROWS = 3_941_811
# SHA256 is expensive to compute on ~800 MB; record it once (see data.compute_sha256)
# and fill it in here to enable strict verification.
EXPECTED_SHA256 = "660209e8624ddb22bc135d54d915b094bc0b9b5a2f30002542f7af879777cb37"
