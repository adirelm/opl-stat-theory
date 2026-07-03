# Final Project — Statistical Theory · Summary and Checklist

Based on the project instructions + Lecture 8.

## In Brief
- **Pair work: Adir Elmakais + David Levin** — matches the default (pairs); no special approval needed.
- **Selected dataset: OpenPowerlifting** (~3.94M competition results, CC0). A single question: how do competitors "game" the weight on the bar and bodyweight, and what does the data reveal about human strength. **Full specification:** `project-spec.md`.
- **Hypothesis structure (canonical H1–H4):** leading = **H1 quantization (96.2% on-grid) + H2 bunching** (empirically confirmed; non-limit control flat); **H3 allometry**; **H4 prediction** (regression + Random Forest + logistic classifier — the course's learning half, built for Stage B). Supporting (paper only, *not* numbered): strength-distribution structure (*not* a sex mixture), tested/untested control, EVT, time-trend. Full details in `project-spec.md`.
- Two stages: midterm presentation (30%) ← final project (70%).

## ⏰ Deadlines
| What | When |
|---|---|
| Midterm presentation (Stage A) | **28.6.2026** (registered; alternative 21.6) |
| In-class presentations | Lectures 11 and 12 |
| Final project submission (Stage B) | **15.8.2026 — no extensions** |

## Stage A — Midterm Presentation (30%) — ✅ delivered 28.6
- [x] ~5 minutes (maximum 10), **up to 10 slides**, **in Hebrew** — presented 28.6.
- [x] Content: research question · investigation methods · preliminary results · preliminary conclusions.
- [x] Register in the Google Sheet (names + date) — **registered for 28.6**.
- [x] Sit and listen to the other presenters' talks.
- This is a **very preliminary** stage — meant to get feedback from the lecturer and adjust direction before the final. No pressure.
- 💡 **Direction approval from the lecturer:** direction email about OpenPowerlifting **sent**.

## Stage B — The Final Project (70%)
- [x] **PDF in English, up to 8 pages** (two-column IEEE template, 6 pages), structured as — **note: Results before Methods**:
  - **Abstract** — background, main results and conclusion (+ GitHub/Colab link below).
  - **Introduction** — literature review + differentiation (an original question, not a replication).
  - **Results** — the hypotheses and how they are answered using the course tools; tables/figures; every statistic with interpretation.
  - **Methods** — how the tools were applied; give a short formal description of the in-course tests too (as the sample paper does), with full formulas reserved for the beyond-course/creative tools.
  - **Discussion** — conclusions and limitations (including null results as valid findings).
- [x] **GitHub/Colab** with organized code + **README** + precise reproduction instructions + the data/download script + source citation (CC0) — public repo + pinned data release.
- [x] **Acceptance gate:** clone into a clean environment → `pip install -r` → end-to-end run reproduces everything — no-login curl path verified; SHA-256 checked by `run_all.sh`.
- [x] Readable figures: axis titles, meaningful colors, figure captions, ≥300 DPI export (not screenshots).

## Assessment criteria (from the instructions)
- **Choosing the correct test** according to the nature/constraints of the data — the heart of the course (categorical discrete→χ²; continuous-vs-ordinal→Spearman; independent categories).
- **Telling a single story** — not a heap of tests. As many relevant tools/concepts as possible.
- Up to **10 points for creativity and general impression** (competitive).
- **Key methodological points:** (1) at n≈3.9M everything is significant → **lead with effect size + CI**, not p/G; (2) **pseudo-replication** (same competitor) → declared deduplication per-hypothesis; (3) **mixture LRT violates Wilks** → bootstrap/AIC, not χ²; (4) cite prior OPL works (Peyen 2025) and differentiate; (5) lock a snapshot of the data.

## Toolbox (from the instructions)
Hypothesis testing · confidence interval · significance level · p-value · Type I/II errors and power · MP · UMP · GLRT · one-/two-sided test · one sample · two independent samples · paired samples · χ² · F · sequential Wald test · stopping times · parametric/non-parametric tests · goodness-of-fit · independence · correlations (Pearson/Spearman) · multiple-testing corrections (post-hoc) · regression · classification · interaction terms · learning evaluation metrics · and every concept from the lectures/recitations.

*Actually used in the project (not name-dropping):* MLE+GLRT (H1 + the mixture) · χ² goodness-of-fit (H1 grid) + independence + Cramér's V · Welch/Mann-Whitney · Kruskal-Wallis + regression overall-F · Pearson/Spearman (+ Fisher transform) · Wald (H3 against 2/3) · **interaction term Sex×log(BW)** · **paired test** (attempt-1 vs attempt-3) · a-priori power · Bonferroni/Holm/Šidák/BH · **regression + Random Forest + logistic "made-weight" classifier, with R²/Adjusted-R²/RMSE/grouped-CV and AUC/confusion — H4, the learning + classification half.**

## Dataset
- **Selected: OpenPowerlifting** (CC0) — verified end-to-end on the real data (downloaded and analyzed).
- ⚠️ **Lock a snapshot:** `openpowerlifting-latest.zip` changes weekly → attach the CSV or document the download date, otherwise the assessor's numbers won't match.
- *(The suggested sources — SurvSet, USA COVID, Kaggle, ML — were considered; OpenPowerlifting was chosen as an original question on a large, public-domain dataset.)*

## Supporting Materials
- `docs/project-spec.md` — **the full specification** ✅
- Course materials (official instructions PDF, sample projects, lecture transcript,
  data-source references) are provided separately by the course and are intentionally
  **not committed** to this repo (they are gitignored and were purged from history).
