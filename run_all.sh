#!/usr/bin/env bash
# Reproduce the full study end-to-end:
#   data -> results/*.json -> figures/*.png -> paper/main.pdf
# Usage:  ./run_all.sh        (set PYTHON=... to choose an interpreter)
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python}"

# 1. data: pinned snapshot (exact reproduction), then verify its SHA-256
if [ ! -f data/openpowerlifting.csv ]; then
  echo "== fetching data =="
  if [ -f data/openpowerlifting.csv.gz ]; then
    gunzip -c data/openpowerlifting.csv.gz > data/openpowerlifting.csv
  elif command -v gh >/dev/null 2>&1 && \
       gh release download data-snapshot-2026-06 -R adirelm/opl-stat-theory -p openpowerlifting.csv.gz -D data 2>/dev/null; then
    gunzip -c data/openpowerlifting.csv.gz > data/openpowerlifting.csv
  else
    "$PY" download_data.py     # fallback: current weekly data (numbers will differ slightly)
  fi
fi
EXPECT=660209e8624ddb22bc135d54d915b094bc0b9b5a2f30002542f7af879777cb37
GOT=$(shasum -a 256 data/openpowerlifting.csv | awk '{print $1}')
if [ "$GOT" = "$EXPECT" ]; then echo "snapshot SHA-256 verified (exact reproduction)"
else echo "WARNING: snapshot SHA-256 differs from the pinned one; numbers may differ from the paper"; fi

# 2. analyses -> results/*.json
echo "== analyses (H1-H5 + breadth) =="
for m in h1_quantization h2_bunching h3_allometry h4_prediction h5_supporting breadth_tools; do
  echo "-- $m"
  "$PY" "src/$m.py"
done

# 3. acceptance check (reproduces the descriptive headline numbers through the modules)
echo "== acceptance check (descriptive headline) =="
"$PY" src/smoke_check.py

# 4. publication figures (>=300 DPI)
echo "== figures =="
"$PY" src/figures.py

# 5. paper (optional: needs a LaTeX distribution, pdflatex/latexmk)
echo "== paper =="
PAPER="paper skipped (latexmk not found; build paper/main.tex on Overleaf)"
if command -v latexmk >/dev/null 2>&1; then
  ( cd paper && latexmk -pdf -interaction=nonstopmode main.tex >/dev/null ) && PAPER="paper/main.pdf"
fi
echo "$PAPER"

echo "DONE. Outputs: results/*.json, figures/*.png, notebooks/results.ipynb; $PAPER"
