# Gaming the Two Numbers: OpenPowerlifting Statistical Study

How powerlifters work the two numbers they control, the weight on the bar and their
bodyweight at weigh-in, and what ~3.94 million competition results say about the
limits of strength.

Bar-Ilan University, M.Sc. *Statistical Theory*. Authors: **Adir Elmakais, David Levin**.

The paper is in [`paper/main.tex`](paper/main.tex) (built PDF: `paper/main.pdf`); a
narrative walk-through is in [`notebooks/results.ipynb`](notebooks/results.ipynb).

## Findings (verified on the real data)
- **H1 quantization.** 96.20% of 13.4M attempt loads sit exactly on the 2.5 kg plate
  grid. A boundary GLRT, with its null calibrated by parametric bootstrap (Wilks fails
  on the boundary), rejects overwhelmingly.
- **H2 weight-cut bunching.** Bodyweight piles up just below every IPF men's class
  limit (de-heaped log(below/above) = +1.92 at 83 kg). A Cattaneo-Jansson-Ma
  density-discontinuity test rejects at all seven limits (Holm and BH corrected); a
  non-limit control (91 kg) is flat and placebos show no bunching-direction effect.
- **H3 allometry.** Strength scales as bodyweight^b with b = 0.75 (men) / 0.51 (women)
  vs the isometric 2/3; a Sex x log(BW) interaction is significant and survives a
  common-support refit.
- **H4 prediction.** A random forest predicts the total with R^2 = 0.70 (leakage-safe,
  grouped-by-lifter CV); a logistic made-weight classifier covers classification.
- **Supporting.** Strength structure is not a latent mixture (it is sex); tested vs
  untested; an EVT/GEV tail (no ceiling supported); a time trend; and a breadth set
  (paired Wilcoxon, ANOVA/Kruskal-Wallis, independence chi-square, a sequential Wald
  test, an a-priori power analysis, all four multiple-testing corrections).

At n ~ 3.9M almost any departure is "significant", so we lead with effect sizes and
confidence intervals, not p-values.

## Repository layout
| Path | What |
|---|---|
| `download_data.py` | Downloads the OpenPowerlifting bulk CSV into `data/`. |
| `run_all.sh` | One command: data -> `results/*.json` -> `figures/` -> `paper/main.pdf`. |
| `src/config.py` | Paths, constants, class limits, the pinned-snapshot SHA-256. |
| `src/data.py`, `src/prep.py`, `src/stats_utils.py` | Loader, preprocessing (de-heaping, per-lifter dedup, grouped CV), shared statistics. |
| `src/h1_quantization.py` ... `src/h5_supporting.py`, `src/breadth_tools.py` | The analyses; each writes a `results/*.json`. |
| `src/figures.py` | Publication figures (>=300 DPI). |
| `src/smoke_check.py` | Acceptance check: reproduces the headline numbers through the shared modules. |
| `src/make_deck.py`, `src/make_figures.py` | Stage-1 mid-presentation deck + its figures. |
| `results/` | Machine-readable numeric outputs (`h1.json` ... `breadth.json`). |
| `figures/` | Generated figures (PNG). |
| `notebooks/results.ipynb` | Narrative report. |
| `paper/` | IEEE paper (`main.tex`, built `main.pdf`). |
| `presentation/` | Stage-1 mid-presentation deck (`.pptx`). |
| `docs/` | Project spec, checklist, course-alignment, implementation plan. |
| `reference/` | Course-provided material (instructions, examples, lecture transcript). |

## Reproduce
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python download_data.py     # ~160 MB zip -> data/openpowerlifting.csv (~800 MB)
./run_all.sh                # analyses + acceptance check + figures + paper
```
`run_all.sh` runs each `src/*.py` analysis (writing `results/*.json`), the acceptance
check, `src/figures.py`, and builds `paper/main.pdf` (if `latexmk` is installed).
Building the paper needs a LaTeX distribution; the deck (`src/make_deck.py`) needs
`python-pptx`, and exporting it to PDF needs LibreOffice.

## Data
**OpenPowerlifting** (https://www.openpowerlifting.org; data dictionary:
https://openpowerlifting.gitlab.io/opl-csv/bulk-csv-docs.html). The competition data is
in the **public domain (CC0-style waiver)**; this project's code is separately licensed.

`openpowerlifting-latest.zip` updates ~weekly, so re-downloading later gives slightly
different numbers. The exact snapshot behind the reported results is pinned by its
**SHA-256 in `src/config.py`** (`660209e8...`; verified by `src/data.py`) and is
published as a GitHub Release asset for exact reproduction:
```bash
gh release download data-snapshot-2026-06 -R adirelm/opl-stat-theory -p openpowerlifting.csv.gz
gunzip -c openpowerlifting.csv.gz > data/openpowerlifting.csv
```

## Notes
- Figures use **English axis labels** (matplotlib bidi); interpretation is in the text.
- Formal tests use **one row per lifter** (independence); H1 uses attempt-level data.
- `make_deck.py` sets RTL per paragraph via the OOXML `a:pPr rtl="1"` attribute.
