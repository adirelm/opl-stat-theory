# Final Project — Statistical Theory · Summary and Checklist

Based on the project instructions + Lecture 8. Lecturer/contact: **Dr. Oshrit Viganesky** (the instructions list "Shtossel") · Teaching assistant: Itamar Zarnitsky.

## In Brief
- **Pair work: Adir Elmakais + David Levin** — matches the default (pairs); no special approval needed.
- **Selected dataset: OpenPowerlifting** (~3.94M competition results, CC0). A single question: how do competitors "game" the weight on the bar and bodyweight, and what does the data reveal about human strength. **Full specification:** `project-spec.md`.
- **Hypothesis structure:** leading = **H1 quantization (96.2% on-grid) + H2 bunching** (empirically confirmed; non-limit control flat); secondary = H3 (*not* a sex mixture) + H5 allometry; supporting = H4/EVT/time-trend. Full details in `project-spec.md`.
- Two stages: midterm presentation (30%) ← final project (70%).

## ⏰ Deadlines
| What | When |
|---|---|
| Midterm presentation (Stage A) | **28.6.2026** (registered; alternative 21.6) |
| In-class presentations | Lectures 11 and 12 |
| Final project submission (Stage B) | **15.8.2026 — no extensions** |

## Stage A — Midterm Presentation (30%)
- [ ] ~5 minutes (maximum 10), **up to 10 slides**, **in Hebrew**.
- [ ] Content: research question · investigation methods · preliminary results · preliminary conclusions.
- [x] Register in the Google Sheet (names + date) — **registered for 28.6** (verify David's name appears in the registration).
- [ ] Sit and listen to the other presenters' talks.
- This is a **very preliminary** stage — meant to get feedback from the lecturer and adjust direction before the final. No pressure.
- 💡 **Direction approval from the lecturer:** direction email about OpenPowerlifting **sent**.

## Stage B — The Final Project (70%)
- [ ] **PDF in English, up to 8 pages** (two-column IEEE template), structured as — **note: Results before Methods**:
  - **Abstract** — background, main results and conclusion (+ GitHub/Colab link below).
  - **Introduction** — literature review + differentiation (an original question, not a replication).
  - **Results** — the hypotheses and how they are answered using the course tools; tables/figures; every statistic with interpretation.
  - **Methods** — how the tools were applied; give a short formal description of the in-course tests too (as the sample paper does), with full formulas reserved for the beyond-course/creative tools.
  - **Discussion** — conclusions and limitations (including null results as valid findings).
- [ ] **GitHub/Colab** with organized code + **README** + precise reproduction instructions + the data/download script + source citation (CC0).
- [ ] **Acceptance gate:** clone into a clean environment → `pip install -r` → end-to-end run reproduces everything.
- [ ] Readable figures: axis titles, meaningful colors, figure captions, vector/≥300DPI export (not screenshots).

## ⚠️ What Is Actually Being Assessed
- **Choosing the correct test** according to the nature/constraints of the data — the heart of the course (categorical discrete→χ²; continuous-vs-ordinal→Spearman; independent categories).
- **Telling a single story** — not a heap of tests. As many relevant tools/concepts as possible.
- Up to **10 points for creativity and general impression** (competitive).
- **Key methodological points:** (1) at n≈3.9M everything is significant → **lead with effect size + CI**, not p/G; (2) **pseudo-replication** (same competitor) → declared deduplication per-hypothesis; (3) **mixture LRT violates Wilks** → bootstrap/AIC, not χ²; (4) cite prior OPL works (Peyen 2025) and differentiate; (5) lock a snapshot of the data.

## Toolbox (from the instructions)
Hypothesis testing · confidence interval · significance level · p-value · Type I/II errors and power · MP · UMP · GLRT · one-/two-sided test · one sample · two independent samples · paired samples · χ² · F · sequential Wald test · stopping times · parametric/non-parametric tests · goodness-of-fit · independence · correlations (Pearson/Spearman) · multiple-testing corrections (post-hoc) · regression · classification · interaction terms · learning evaluation metrics · and every concept from the lectures/recitations.

*Actually used in the project (not name-dropping):* MLE+GLRT (H1/H3) · χ² goodness-of-fit + independence + Cramér's V · Welch/Mann-Whitney · F/ANOVA + Kruskal-Wallis · Pearson/Spearman · Wald (H5 against 2/3) · **interaction term Sex×log(BW)** · **paired test** (attempt-1 vs attempt-3) · a-priori power · Bonferroni/BH · regression. *Classification/learning-metrics — intentionally out-of-scope (no prediction task that serves the story).*

## Dataset
- **Selected: OpenPowerlifting** (CC0) — verified end-to-end on the real data (downloaded and analyzed).
- ⚠️ **Lock a snapshot:** `openpowerlifting-latest.zip` changes weekly → attach the CSV or document the download date, otherwise the assessor's numbers won't match.
- *(The sources the lecturer suggested — SurvSet, USA COVID, Kaggle, ML — were considered; OPL was chosen because it is original, surprising, and review-resilient.)*

## Supporting Materials in the Folder
- `project-spec.md` — **the full specification** ✅
- `הוראות פרויקט סוף תאוריה סטטיסטית.pdf` — the official instructions
- `דוגמאות/` — sample final project (Chess) + sample midterm presentation (Animal Adoption)
- `תמלול הרצאה 8 (הסבר הפרויקט) - מתוקן.txt` · `מקורות דאטה - *.png`
