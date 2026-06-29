#!/usr/bin/env bash
# Reproduce the full study end-to-end:
#   data -> results/*.json -> figures/*.png -> paper/main.pdf
# Usage:  ./run_all.sh        (set PYTHON=... to choose an interpreter)
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python}"

# 1. data (pinned snapshot; see README + src/config.py for the SHA-256)
if [ ! -f data/openpowerlifting.csv ]; then
  echo "== downloading data =="
  "$PY" download_data.py
fi

# 2. analyses -> results/*.json
echo "== analyses (H1-H5 + breadth) =="
for m in h1_quantization h2_bunching h3_allometry h4_prediction h5_supporting breadth_tools; do
  echo "-- $m"
  "$PY" "src/$m.py"
done

# 3. acceptance check (reproduces the headline numbers through the shared modules)
echo "== acceptance check =="
"$PY" src/smoke_check.py

# 4. publication figures (>=300 DPI)
echo "== figures =="
"$PY" src/figures.py

# 5. paper (needs a LaTeX distribution: pdflatex/latexmk)
echo "== paper =="
if command -v latexmk >/dev/null 2>&1; then
  ( cd paper && latexmk -pdf -interaction=nonstopmode main.tex >/dev/null && echo "built paper/main.pdf" )
else
  echo "  (latexmk not found; skip -- build paper/main.tex on Overleaf or with a TeX install)"
fi

echo "DONE. Outputs: results/*.json, figures/*.png, paper/main.pdf, notebooks/results.ipynb"
