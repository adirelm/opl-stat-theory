# Stage 2 — Implementation Plan (the full project)

How we build the final analysis pipeline + IEEE paper from the locked spec
(`project-spec.md`). Decided structure: **hybrid** (modular `src/` for compute +
a results notebook for narrative/figures); **full scope** (H1–H4 + supporting
analyses); **shared infrastructure first**.

> **Note on timing:** the mid-presentation (28.6) is a feedback checkpoint.
> Phase 0 (infrastructure) is direction-agnostic and safe to build now.
> Lock the per-hypothesis specifics *after* folding in the lecturer's feedback.

## Non-negotiable methodological commitments (carry into every phase)
1. **Effect size + CI lead, not p** — n ≈ 3.9M makes almost anything "significant".
2. **Pseudo-replication** — same lifter recurs → dedup to one row per lifter (PR), or clustered/robust SE. Declared per hypothesis.
3. **Boundary / mixture LRTs violate Wilks** → calibrate the null with **parametric bootstrap** (and/or AIC), never naive χ².
4. **Multiple-testing corrections** — Bonferroni/Holm/Šidák (FWER) + Benjamini-Hochberg (FDR) across thresholds/hypotheses.
5. **Leakage guards** — H4 split grouped by lifter; drop bodyweight when the target is Dots.
6. **Locked snapshot** — pin the CSV (download date + row count + hash); reproduction must match exactly.
7. **Right test for the data** — discrete→GLRT/χ², density-jump→McCrary, power-law→log-log OLS, prediction→grouped-CV.

## Target architecture (hybrid)
```
src/
  config.py          paths, seeds, alpha, class limits, federations, grid step, snapshot id
  data.py            load_raw(), snapshot pin (date+rowcount+sha), column schema
  prep.py            de-heaping, dedup-per-lifter (PR), attempt-level expansion, grouped-CV splits
  stats_utils.py     effect-size+CI, robust/clustered SE, FWER/FDR, parametric-bootstrap engine, log-ratio+CI
  h1_quantization.py rounded-likelihood grid model, MLE, GLRT, boundary bootstrap, χ² GoF, pound-grid robustness
  h2_bunching.py     McCrary/rddensity, de-heap, spike-width, placebo, all 7 limits + control, subgroups
  h3_allometry.py    log-log OLS, HC3/clustered SE, Wald vs 2/3, Sex×log(BW), Fisher-CI, women-b diagnosis
  h4_prediction.py   (exists) finalize: reg+RF grouped-CV (R²/Adj/RMSE/MAE) + perm-importance + VIF; logistic classifier (AUC/conf)
  supporting.py      distribution structure (NOT a sex mixture), tested-vs-untested, EVT/GEV tails, time-trend
  figures.py         publication figures (≥300 DPI, captioned, English labels) — refactor of make_figures.py
notebooks/
  results.ipynb      narrative layer: pulls src modules → every figure + table + interpretation
paper/               IEEE 2-column LaTeX (Overleaf), ≤8 pages, Results-before-Methods
README.md            exact reproduction steps; requirements pinned; snapshot documented
```

## Phases & milestones

### Phase 0 — Shared infrastructure (foundation) — *start here*
- `config.py`, `data.py` (snapshot pin), `prep.py` (de-heap, dedup-per-lifter, attempt expansion, grouped-CV), `stats_utils.py` (effect-size+CI, clustered SE, FWER/FDR, parametric-bootstrap engine).
- **Acceptance:** a smoke check reproduces the headline descriptive numbers (96.2% on-grid; +1.92 / −0.21 log-ratios; b≈0.72/0.49) through the new modules.

### Phase 1 — H1 quantization (grid + GLRT + boundary bootstrap)
- Rounded-likelihood model (continuous null vs grid alternative), MLE, GLRT statistic, **bootstrap-calibrated null** (boundary problem), χ² goodness-of-fit. Pound-grid units artifact as robustness (≈90% of off-grid = round-lb / 0.5 kg).
- **Lead:** 96.2% as effect size; the test is the formal confirmation.

### Phase 2 — H2 bunching (the headline)
- Formal **McCrary density-discontinuity** (Cattaneo-Jansson-Ma `rddensity` if available, else implement), de-heaping, **spike-width**, **placebo** (non-limit points), all 7 limits + the 91 control, subgroup robustness (federation/era/equipment).
- **Lead:** de-heaped log-ratio + CI; control flat.

### Phase 3 — H3 allometry
- log-log OLS with **HC3 / clustered-by-lifter SE**, **Wald vs 2/3** (and vs 1), **Sex×log(BW)** interaction, Pearson/Spearman with **Fisher-transform CI**, diagnose women b≈0.49 (weight-range/leverage).
- **Lead:** b + CI, sex difference tested formally.

### Phase 4 — H4 prediction (ML + classification)
- Finalize `h4_prediction.py`: Linear + Random Forest, **grouped-by-lifter CV**, R²/Adj-R²/RMSE/MAE, permutation importance, VIF; logistic "made-weight" classifier (AUC/accuracy/confusion). Leakage guards.

### Phase 5 — Supporting analyses (full)
- Strength-distribution structure (argue **not** a sex mixture; mixture-LRT via bootstrap/AIC), tested-vs-untested control, **EVT/GEV** tails (ξ sign → population ceiling; cite Einmahl & Magnus), time-trend.

### Phase 6 — Results notebook + publication figures
- `notebooks/results.ipynb` + `figures.py`: every final figure (≥300 DPI, captioned) and table (every statistic with interpretation), driven by the src modules.

### Phase 7 — Paper (Stage B, IEEE, English, ≤8 pages)
- Abstract · Introduction (lit review + differentiation) · **Results (before Methods)** · Methods (short formal description of in-course tests) · Discussion (conclusions + limitations + null results). GitHub/Colab link.

### Phase 8 — Reproduction + polish
- README reproduction steps, pinned `requirements.txt`, documented snapshot, **clean-env acceptance test** (clone → `pip install -r` → run → reproduces everything). Readable vector/≥300 DPI figures.

## Rough timeline (28.6 → 15.8, ~7 weeks)
| Week | Focus |
|---|---|
| 1 | Phase 0 (infra) + Phase 1 (H1) + fold in presentation feedback |
| 2 | Phase 2 (H2 — the big one) |
| 3 | Phase 3 (H3) + Phase 4 (H4) |
| 4 | Phase 5 (supporting analyses) |
| 5 | Phase 6 (figures + results notebook) + start paper |
| 6 | Phase 7 (paper writing) |
| 7 | Phase 8 (reproduction test, polish, buffer) |
