# Course-alignment analysis — does our project + mid-presentation fit the course?

Cross-reference of **what the course actually teaches** (lectures 3/8/9/10 slides + recitations + Neyman-Pearson/GLRT theory) against our **project plan** (`project-spec.md`) and the **mid-presentation deck**.

> Built from the lecture slides (authoritative) + recitation/lecture transcripts. The instructor's name appears as **Oshrit Shtossel (אושרית שטוסל)** on the lecture slides and instructions, while the Zoom room / contact email is **Viganesky (ויגננסקי)** — likely the same person; use "Shtossel" in any formal acknowledgment to match the official materials.

## 1. What the course teaches (the real toolbox)

| Lecture / source | Topics |
|---|---|
| **Recitations + theory** | test statistics, critical values, **MP / UMP / Neyman-Pearson lemma (p₁/p₀)**, **GLRT (λ)** |
| **Lecture 8** | nonparametric tests, **normality testing**, ranking, **Wilcoxon signed-rank (paired)**, **Wilcoxon rank-sum = Mann-Whitney (independent)**, normal approximation + continuity correction |
| **Lecture 9** | **multiple-comparisons** (FWER), a-priori vs post-hoc, **ANOVA / Kruskal-Wallis** omnibus → post-hoc, **Bonferroni / Dunn-Šidák / Benjamini-Hochberg (FDR)**, orthogonal comparisons, **standardized residuals** (χ² cell contribution), McNemar, **correlations: Pearson / Spearman / Fisher transform / point-biserial / Cramér's V / phi** |
| **Lecture 10** | least squares, MSE, **R²**, **multiple regression**, Adjusted R², **multicollinearity / VIF**, categorical/binary predictors, **interaction terms**, logistic regression |
| **Lecture 3** | supervised learning, linear & **logistic regression**, **decision trees, Random Forest, XGBoost / gradient boosting, neural nets (FCN)**, **learning-evaluation metrics**, regularization, train/validation |

## 2. Coverage map — course tool → our project

| Course tool | In our plan / deck? | Notes |
|---|---|---|
| Hypothesis testing, p, Type I/II, **power** | ✅ | a-priori power analysis (Stage 8) |
| **MP / UMP / Neyman-Pearson** | ✅ | anchored on the Wald-vs-2/3 / one-sample test |
| **GLRT (λ)** | ✅ | H1 core (rounded-likelihood MLE + nested GLRT) |
| **Mann-Whitney / Wilcoxon** | ✅ | H4 (MWU), paired Wilcoxon (attempt-1 vs attempt-3) |
| **Normality tests** | ✅ | Anderson-Darling + KS + QQ (H3) |
| Normal-approx **continuity correction** | ⚠️ partial | mention it when reporting the rank-test z |
| **Bonferroni / Šidák / BH** | ✅✅ | all four (+ Holm) per the TA — exceeds the course |
| **ANOVA / Kruskal-Wallis + post-hoc (Dunn)** | ✅ | equipment / group comparisons |
| **Standardized residuals** (χ² cells) | ❌ | EASY ADD — report which cell drives the Federation×Tested χ² |
| Pearson / Spearman | ✅ | H5 / correlations |
| **Cramér's V / phi** | ✅ | with the χ² independence |
| **Fisher transformation** (corr CI) | ❌ | minor add — gives a proper CI on the correlations |
| point-biserial / McNemar | N/A | no paired-categorical / dichotomous-vs-ordinal need |
| OLS / **R²** / MSE | ⚠️ partial | H5 reports slope+CI; should also report **R²** (already noted R²≈0.06) |
| **Multiple regression** | ✅ | H4 regression (Tested + Federation + Equipment + Sex + Era) |
| **Adjusted R² / VIF (multicollinearity)** | ❌ | ADD when the multiple regression runs (covariates are correlated) |
| **Interaction terms** | ✅ | Sex × log(Bodyweight) in H5 |
| Categorical/binary predictors, one-hot | ✅ | H4 regression |
| **Logistic regression** | ❌ | not used — but natural for a "cut weight? / tested?" model |
| **Classification: trees / RF / XGBoost / NN** | ❌ | **absent entirely** |
| **Learning-evaluation metrics, train/test, CV** | ❌ | **absent entirely** |

## 3. The one real gap — DECIDED ✅

> **Decision (adopted):** add the **regression + Random Forest strength-prediction** (option below). Now in `project-spec.md` as **Stage 9 / H6**, with R²/Adjusted-R²/CV/RMSE + feature importance. This closes the ML/learning gap. The §4 quick wins were also folded into the spec (standardized residuals → Stage 4; R²/VIF/Fisher → Stage 5; continuity correction → Stage 4).


**The course devotes a whole lecture (3) + half of lecture 10 to ML / prediction — logistic regression, decision trees, Random Forest, XGBoost, neural nets, and learning-evaluation metrics — and the instructions list "classification, learning-evaluation metrics" explicitly. Our project is almost entirely *classical inference* and has no predictive/learning component.**

- **In our favor:** the high-scoring exemplar (Chess) was also classical inference (KS, Mann-Whitney, correlation, one MLE mixture) with no ML, and the instructions qualify the toolbox with "if relevant." So omitting ML is *defensible*.
- **The risk:** the course's own emphasis is heavily ML, so a grader may expect at least *some* engagement with prediction + learning-evaluation. Right now we'd be using ~half the course.

**Recommendation — add ONE modest predictive piece that serves the story (low cost, high alignment):**
- **Best fit:** extend H5 into a small **prediction model of strength**: multiple regression (and a **Random Forest** baseline) predicting `TotalKg`/`Dots` from bodyweight + sex + equipment + age, reported with **R² / Adjusted R² / train-test (or CV) / RMSE** — this directly exercises Lectures 3 + 10 and the "learning-evaluation metrics" requirement, and stays on the "two numbers + strength" story.
- **Alternative (ties to H2):** a **logistic regression** classifying "made weight just under a class limit" (cut indicator) from features, with accuracy / AUC / confusion matrix — covers logistic + classification + learning metrics.

Either one closes the gap and lets us honestly say the project spans both halves of the course.

## 4. Quick wins (cheap, course-aligned additions)
1. **Standardized residuals** on the Federation×Tested χ² (Lecture 9) — names which cell drives the association.
2. **R² + Adjusted R²** for the allometry/regression, and a **VIF / correlation-matrix** multicollinearity check once covariates are added (Lecture 10).
3. **Fisher transformation** for a CI on Pearson/Spearman correlations (Lecture 9).
4. **Continuity correction** noted when converting the Wilcoxon/MWU rank statistic to a z/p (Lecture 8).

## 5. Mid-presentation alignment (28.6)
- The deck's methods are **all on the course's toolbox** (GLRT, Mann-Whitney, multiple-testing corrections, regression, effect-size-over-p) — no foreign tool. ✅
- **Conventions match** what the course grades: GLRT phrased as alternative/null reject-large, critical values quantile-style χ²₍df,1−α₎ (in the prep doc for Q&A); no χ² critical-value notation printed on slides. ✅
- The deck does **not** show an ML/prediction result — consistent with it being preliminary, but if we adopt §3 above, add one line to the "next steps" slide ("מודל ניבוי לכוח: רגרסיה + Random Forest עם R²/CV").

## Bottom line
The plan + deck **fit the course well on the classical-inference side and even exceed it** (multiple-testing, GLRT, falsification). The **only material gap is the ML / prediction / learning-evaluation half of the course** — defensible to omit (the exemplar did), but adding one modest predictive model (§3) would make the project unambiguously span the whole course and is low-cost. The §4 quick wins are easy course-aligned polish.
