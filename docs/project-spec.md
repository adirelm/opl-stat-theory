# Final Project Spec — Statistical Theory
## "How Powerlifters 'Game' the Two Numbers They Control — and What the Data Reveals About Human Strength" (OpenPowerlifting)

> **Status: pre-analysis planning spec (June 2026), kept as the pre-registration of the hypotheses and test families.** The paper ([`paper/main.tex`](../paper/main.tex)) is the authoritative final record. Notable scope changes since this spec: the formal per-lifter deduplication rule became **one random (seeded) meet per lifter** (outcome-independent; the "personal Total-best" rule below was dropped as outcome-dependent), the formal H3 headline is the per-lifter HC3 fit (b=0.75/0.51; the 0.72/0.49 below is the all-row descriptive layer), and some planned extensions (dedup-rule sensitivity table, bandwidth-sensitivity curve, top-1% comparison, POT/GPD) were scoped down and appear in the paper as future work.

> All numbers below are **reproducible results** computed on the real data (3,941,811 rows, CC0). The core is robust: **H1** (96.2% of attempts on the 2.5 kg grid) and **H2** (bodyweight bunching just below class thresholds; a non-limit control is flat — the effect is specific to the thresholds). **H3** = allometric scaling b≈0.72 (men) / 0.49 (women) on full-power (SBD) results. **H4** = a strength-prediction model (regression + Random Forest) covering the course's learning half. Supporting analyses: tested/untested control (24%/43% untested, population / top-1%); strength-distribution structure (**not** a by-sex mixture — Dots is already normalized for sex/weight; see below); EVT; time-trend. Wherever a specification must be locked, this is marked explicitly.
>
> **🔢 Canonical hypothesis numbering (one scheme for the deck, the prep-guide, this spec, and the code).** The mid-presentation presents exactly these four; the paper keeps the same numbers:
> | # | Hypothesis | Status |
> |---|---|---|
> | **H1** | Attempt loads quantized to the 2.5 kg grid | Leading (core) |
> | **H2** | Bodyweight bunching just below class limits (weight-cutting) | Leading (core) |
> | **H3** | Allometric scaling of strength differs by sex (was "H5" in earlier drafts) | Presented result |
> | **H4** | Predicting strength — regression + Random Forest (was "H6 / Stage 9") | Presented as the Stage-2 learning component |
> | *Supporting (no H-number)* | strength-distribution structure (old "H3"), tested/untested control (old "H4"), EVT, time-trend | Paper only |
>
> Do a `grep -n "H3\|H4\|H5\|H6"` after any edit to confirm no two analyses share a number.

---

## 0. Team, Logistics, and Language
- **Working in a pair: Adir Elmakais + David Levin** — consistent with the default in the instructions (pairs), so **no special approval is needed**. The preliminary email concerns only approval of the research direction.
- Registered in the Google Sheet on Moodle (both members' names + dataset); the mid-presentation was delivered on **28.6.2026**.
- The research-direction approval email was sent and the direction approved.
- **Language:** the presentation (stage A) is **in Hebrew**; the paper (stage B) is **in English**. Test/code names in English.
- **Code:** GitHub *or* Google Colab. The real bar: **the grader clones, runs clean** and obtains all the numbers/figures.

## 1. The Data and the Research Question
- **Data:** **OpenPowerlifting** — bulk CSV (`openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip`), **3,941,811 rows** (one row per competitor-meet entry), **CC0**. Validated — downloaded and processed. ⚠️ The `latest` file changes weekly → **lock a snapshot** (attach the CSV or document the exact download date), otherwise the grader's run will not match the numbers.
- **Key variables:** continuous — `BodyweightKg`, attempts (`Squat/Bench/Deadlift 1-3 Kg`), `TotalKg`, `Dots`/`Wilks`. Categorical — `Sex`, `Equipment`, `Tested`, `Federation`, `WeightClassKg`, `Division`, `Place`, `Event`, `Date`.
- **Research question (one story):** a competitor controls two numbers — **the weight on the bar** (attempt selection) and **bodyweight** (on the scale). How does he "game" both, and what does the data thereby reveal about **the limits of human strength**.

### Hypothesis Structure (by weight within the project — to fit ≤8 pages and one story)
**🟢 Leading (the heart of the story — "the two numbers"):**
- **H1 — quantization (the theoretical core):** attempt weights are not continuous but **quantized to a 2.5 kg grid** — a continuous "intended" weight observed through grid rounding. **Validated: 96.4% of best attempts / 96.2% including failed ones on the grid.** The reported result = **%on-grid + CI** (not the astronomical G).
- **H2 — weight-cutting bunching:** an excess just below a class threshold + a deficit above it. **Result (IPF-affiliated federations, men, n≈1.18M, boundary-correct window (L-0.5, L], de-heaped):** log(below/above) ≈ **+1.92 at the 83 kg limit** (and ≈ +1.65 / +1.17, i.e. x5.2 / x3.2, at 93 / 105), versus ≈ **-0.21 at a non-limit control (91 kg)** — the excess is specific to real class limits and survives removing round-number heaping. To be formalized with a McCrary / Cattaneo-Jansson-Ma density-discontinuity test (see section 2).

**🟡 Presented result (H3):**
- **H3 — allometric scaling (was "H5"):** `Total ~ Bodyweight^b` on full-power (Event=='SBD') results. **OLS: b≈0.72 (men) / 0.49 (women).** Men sit slightly **above** the isometric 2/3≈0.667, women well **below** — a sex difference in scaling. Report b+CI with heteroskedasticity-robust / clustered SE and a Sex×log(BW) interaction (section 2). The women's b<0.5 may be a range-restriction artifact → diagnose before publication.
- **H4 — predicting strength (was "H6 / Stage 9"; the course's learning half):** how well is `TotalKg` predicted from the controllable + basic variables? **Multiple regression + Random Forest**, evaluated on **held-out lifters** (grouped CV) with **R²/Adjusted-R²/RMSE/MAE** + feature importance, plus a small **logistic "made-weight-just-under-a-limit" classifier** (accuracy/AUC/confusion) to cover the *classification* item. ⚠️ **Avoid circularity:** when the target is `Dots` (already a function of bodyweight) drop bodyweight from the predictors; the headline model predicts **`TotalKg`** with bodyweight as a feature. No preliminary result at Stage A — presented as the planned Stage-2 learning component.

**🔵 Supporting analyses (paper only — NOT numbered hypotheses, NOT in the mid-deck):**
- **Supporting — structure of the strength distribution (old "H3"):** ⚠️ **Not a by-sex mixture.** `Dots` is pre-normalized for sex+weight (mean Dots ≈254 *identical* across the two sexes) — so labeling the components as "men/women" is factually wrong. The bimodality is **real** (Anderson-Darling ≈687–1307) but originates in **single-lift/bench-only events, beginners/youth, and bomb-outs** (the low cluster is 78% men). **Framing:** (a) run the mixture on **raw strength** (not Dots), where sex *does* produce bimodality; or (b) filter to **full SBD + TotalKg>0** and frame it as "two competition regimes." Mixture-vs-single GLRT **via parametric bootstrap / AIC-BIC — not χ²** (see caveat in section 2).
- **Supporting — drugs/testing control/moderator (old "H4"):** **24% untested in the population / 43% in the top-1%** (untested are over-represented in the elite tail). ⚠️ confound at the federation/equipment/era level — one cannot infer "drugs" from a raw comparison. Therefore: compare **top-1% versus bottom-99% (disjoint groups)** with **equipment stratification + regression** (Tested + Federation+Equipment+Sex+Era), and frame it **descriptively** / as a moderator of the dose-response in H2.
- **EVT (supporting):** GEV on the annual block-maxima of strength, ξ<0 → ceiling. **Report the number of blocks + a CI for ξ (profile-likelihood)**, a stable sub-window, and cite Einmahl & Magnus (the method is well known — its application to OPL is new).
- **Time trend (supporting):** mean strength and number of participants over the years; women/men ratio — compact.

## 2. Analysis Plan (Python)
**Stage 0 — loading, cleaning, and unit of analysis (declared in advance):**
- From the ~767MB CSV → lean files by columns. Attempts = absolute value (failures are negative), reasonable range.
- **Independence / pseudo-replication — correction per-hypothesis (not a "note"):** the same competitor appears in many rows; this **biases estimates** (not merely inflates significance) in allometry/structure/time-trend. **Declared dedup rule: one row per competitor = personal Total-best within the clean set**, for the cross-sectional analyses (H3-allometry / structure / EVT / time). For H1 the unit of analysis is **the attempt** (the mechanism is within-competitor ⇒ the grid is robust to clustering). Report a **sensitivity table** for 2–3 dedup rules.
- **Unit-source control (lb→kg):** identify lb-native rows (weight = a multiple of 0.45359237) and run H2 **first on the kg-native IPF rows**; show that the effect survives; report the lb-converted ones separately.
- **Explicit federation list, published in the repo:** all federations under the IPF (ParentFederation == IPF: IPF, USAPL, FPR, CPU, and other national affiliates), which share the modern kg class scheme, plus USAPL. Non-IPF schemes are excluded (USPA 82.5/90/100, WPC, and THSPA/THSWPA Texas high school). ⚠️ **Weight-class schemas changed over time** even within IPF/USAPL (older eras used 82.5/90/100 kg classes, the modern men's set is 59/66/74/83/93/105/120). For H2, **restrict to the modern-schema era** (or filter by the published `WeightClassKg` set) and run a **schema-era sensitivity check** so the 83-vs-91 contrast is not muddied by legacy classes near 90.

**Stage 1 — Core A: quantization (H1).** %on-grid 2.5/5/integer **+ CI** as the primary result; **MLE for a grid-rounding model** (point mass on the grid + continuous background) + **nested likelihood-ratio (GLRT)**. ⚠️ The grid weight is on the **boundary** of the space under H0 → declare the df and use **Self–Liang / bootstrap** (not naive χ²_1). Frame the on-grid test *also* as a **χ² goodness-of-fit** of attempt-loads against the 2.5 kg-grid expected distribution — this earns the "goodness-of-fit"/"χ²" toolbox items for free. Sub-grid (lb→kg peaks) via a cited **lb-plate standard**.

**Stage 2 — Core B: bunching (H2).** A **density-discontinuity test (McCrary; preferably Cattaneo-Jansson-Ma `rddensity`)** of the **jump** at the threshold — not bare "asymmetry." Measure the **spike width** (cutting = a sharp spike in <0.5–1 kg; class assignment = a smooth slope). Falsification (mandatory):
- (i) **two placebos** to separate the confound: (a) round-non-legal (80/85 if not a threshold) to measure round-number attraction; (b) **non-round-and-non-legal** (70.0 etc.) = the true null. **The claim = asymmetry at legal thresholds greater than the round-number baseline** (a contrast, not "present/absent").
- (ii) **de-heaping** — show the effect also at **non-round** legal thresholds (83/93/105) → proves it is not round-number attraction.
- (iii) **dose (dose-response)** — stronger in the elite/tested/winners, **within the same federation** (otherwise it is a federation-composition confound), and at the competitor level (dedup).
- Bandwidth: a declared selection rule + a **sensitivity curve** + CI (not a bare number).

**Stage 3 — structure of the strength distribution (supporting).** Normality (Anderson-Darling + KS + QQ) → rejected → **2-component Gaussian mixture model (EM)**. ⚠️ **The mixture LRT violates Wilks** (mixing weight on the boundary + non-identifiability) → **calibrate with a parametric bootstrap or lead with AIC/BIC**, and declare this explicitly (turns a pitfall into a beyond-course advantage). Run on **raw strength / full SBD** (not Dots), and interpret as "competition regimes"/sex-in-raw-strength.

**Stage 4 — control: tested versus untested (supporting).** **top-1% versus bottom-99% (disjoint groups)** — two-proportions / χ² + CI for the difference + odds-ratio. **Equipment stratification (Raw vs Raw)** and **regression** with Tested+Federation+Equipment+Sex+Era (interaction term in-course). χ² test of independence **Federation×Tested** (+ Cramér's V). *Drop* the standalone equipment ANOVA and the sex×equipment χ² into a single control paragraph ("equipment inflates Total → controlled for"). Mean comparisons: **Welch *or* Mann-Whitney** (state the null of each) + a **rank-based effect size**; **no Levene as a gate**. Report **standardized residuals** for the Federation×Tested χ² (which cell drives the association — Lecture 9); when converting a Mann-Whitney/Wilcoxon rank statistic to z, apply the **continuity correction** (Lecture 8).

**Stage 5 — allometry (H3).** `log(Total) ~ log(Bodyweight)` OLS with **heteroskedasticity-robust standard errors (HC3) / clustered-by-competitor**; a **Wald test against 2/3** (and also presented against 1 as an anchor); a **Sex×log(BW) interaction term** to test the sex difference *formally* (instead of a separate fit). Report the fit's **R²**; for the Pearson/Spearman correlations give CIs via the **Fisher transformation** (Lecture 9). Diagnose the b≈0.49 for women (weight-range/leverage) before interpretation. Result = **b+CI**, not p. (The preliminary deck figure uses plain OLS SE; the **HC3/clustered SE is the formal Stage-2 version** — keep the deck's "ייבדק פורמלית (SE חסין)" framing.)
- **(H4 prediction is specified in Stage 9 below.)**

**Stage 6 — extreme value theory (EVT, supporting).** GEV on the annual block-maxima; **report the number of blocks** + a CI for ξ; **POT/GPD** as an alternative; a stable sub-window (fixed federations/era) or a trend-model in location. ξ<0 = "a ceiling *in this competitive population*," not "a ceiling of the human species."

**Stage 7 — time trend (supporting, compact).** Regression of mean strength/number of participants over the years; change in the women/men ratio. Note the expansion of the sampling frame (selection).

**Stage 8 — reporting, multiple-testing correction, and power.**
- **Effect-first reporting:** in every test — the **effect size + CI are the result**, p/G are secondary. **Stability check:** run on a 1%/10% subsample and show that the effect is stable while p is not — demonstrates control over "n→everything is significant."
- A pre-declared family of tests; apply **all four corrections the TA requires — Bonferroni, Holm-Bonferroni, Šidák (FWER family) + Benjamini-Hochberg (FDR)** (via `statsmodels.stats.multitest.multipletests`, methods `bonferroni`/`holm`/`sidak`/`fdr_bh`), reported as a #-rejected comparison table → note robustness across methods (FWER vs FDR agree because the effects are strong). An **a-priori power analysis** (α=0.05, target 0.90).
- **Paired test (new, on-story):** attempt-1 versus attempt-3 of the same competitor (Wilcoxon signed-rank) — covers an additional item from the toolbox and reinforces H1/H2 ("the number on the bar").

**Stage 9 — prediction / learning (H4; the course's ML half).** Target **`TotalKg`** (headline; bodyweight is a legitimate feature). ⚠️ If also modelling `Dots`, **drop bodyweight from the predictors** — `Dots` is already a function of bodyweight, so keeping it is circular. Features: bodyweight, sex, equipment, age (+ federation/era). Models: **multiple linear regression** (log transforms, Sex×log(BW) interaction, one-hot for categoricals) and a **Random Forest** baseline. Evaluate with a **train/test split grouped by lifter** (no leakage) + **k-fold CV**; report **R² / Adjusted R² / RMSE / MAE**, compare linear-vs-RF, and **feature / permutation importance**. Check **multicollinearity (VIF / correlation matrix)** on the linear model (Lecture 10). **Classification add-on (covers the instructions' "קלאסיפיקציה" item):** a **logistic regression** predicting the binary "made weight just under a class limit" (the H2 cut indicator) from features, reported with **accuracy / AUC / confusion matrix** — on-story (ties to "the two numbers") and gives genuine learning-evaluation metrics for both regression and classification. Keep it modest — one focused regression + one small classifier, not a model zoo.

**Theory notes (the heart of the course):**
- **GLRT ↔ Pearson:** Pearson's χ² = a second-order Taylor approximation of the likelihood-ratio statistic (Wilks) — derived in Lecture 8 (verified against the transcript). A strong theoretical anchor.
- **MP/UMP — anchor in a real test:** frame a **one-sided** test (e.g. the allometry **H3** test of b versus 2/3, stated one-sided so UMP is valid for the one-parameter exponential family) as the Neyman-Pearson/UMP point — a *two-sided* Wald is not automatically UMP, so state the one-sided version or downgrade the label to "Neyman-Pearson motivation." The GLRTs (H1 / structure / EVT) = a generalization of the MP-lemma to composite hypotheses (Wilks).
- **n warning:** at n≈3.9M every null is rejected — therefore the science rests on **effect size + the falsification**, not on p. State this in the Discussion.
- **Prediction / learning (now INCLUDED — Stage 9 / H4):** a modest regression + Random Forest strength-prediction with R²/Adjusted-R²/CV + a small logistic "made-weight" classifier (AUC/confusion) covers the course's ML half (Lectures 3 + 10) — both **regression** and **classification** and the learning-evaluation metrics. A full model zoo (XGBoost/NN) stays out — focused models that serve the story are enough.

## 3. Tool Classification: in-course versus beyond-course
- **In-course:** t/Welch, F, ANOVA, χ² (independence + goodness-of-fit + **standardized residuals**), Pearson/Spearman (+ **Fisher transform**, Cramér's V), GLRT/LRT, Wald, MLE, power, multiple-testing corrections (Bonferroni/Holm/Šidák/BH), **regression + R²/Adjusted-R² + VIF**, **interaction term**, **paired test**, **multiple regression + learning-evaluation metrics (train/test, k-fold CV, RMSE) — Lectures 3+10**.
- **Beyond-course (explain the method + *what the course tool lacks*):** quantization/rounded-likelihood model, **parametric bootstrap for the mixture-LRT**, density-discontinuity (McCrary / **Cattaneo-Jansson-Ma**), GEV/EVT, Kruskal-Wallis/Dunn, Anderson-Darling, **Random Forest** (as a non-linear prediction baseline vs the linear model).
- **Cross-cutting principle:** for every assumption violation — (a) name the assumption, (b) what the standard approach would do, (c) the corrected tool and why.

## 4. Stage A — Midterm Presentation (30%, 28.6.2026)
- **Hebrew**, in-person, **Adir and David present**, ~9 slides (cap 10), ~5 min (hard cap 10), **rehearse in advance**.
- Structure (like the Animal Adoption example): title+names → the data and its source → main thrust of the work+background → **research question** → methods → **real preliminary results** → conclusions → summary+questions.
- **Real results to present (already run):** an attempts histogram with the peaks on the grid (96.2%), the bunching below the threshold versus **a flat non-limit control**, and a raw-output screenshot. **Lead with H1+H2** (the strong core). Don't over-invest — a checkpoint for feedback.
- Every result with a short **caveat**; a list of challenges (federation schemas, multi-meet competitors, lb→kg).

## 5. Stage B — The Paper (70%, deadline 15.8.2026 — hard)
- **Two-column IEEE template**. **Title block on the page** (no cover): title + **the two authors (Adir Elmakais, David Levin)** + ID + email. **GitHub/Colab link below the Abstract.** *(IEEE/ID/email are derived from the example, not from the explicit instructions — but better to follow.)*
- **Locked order:** Abstract → Introduction → **Results → Methods** → Discussion.
- **Abstract** (~150–250 words): background + question + main results + conclusion.
- **Introduction:** background (weight-cutting; McCrary 2008) + **explicit differentiation with citations**: **lead with H1 (rounded-likelihood — truly the original part)**; for **H2 (bunching)** cite **McCrary 2008** (manipulation test) + the general weight-cutting literature, and note that to our knowledge no public OPL analysis applies a *formal manipulation test + falsification* to bunching (so H2 is original there); cite **Peyen et al. arXiv:2503.13040 (2025)** — *"Discussing Diminishing Returns: A New Scoring System for Powerlifting"* — in the **H3 / scaling** context (it uses OPL to study strength-vs-bodyweight and finds increasing returns below a bodyweight threshold; it is NOT a bunching paper, so do not cite it for H2); cite **medRxiv 2021.05.07.21256806** (tested/untested) and frame the tested/untested analysis as a supporting control. An originality claim that is **modest and defensible** ("to the best of our knowledge, no public OPL analysis combines a quantization model with bunching that has passed falsification").
- **Results:** the leading + secondary hypotheses by name, **tables/figures**; **every statistic = effect size + CI + interpretation in words** (p secondary).
- **Methods (a softened rule!):** the instructions *and the example* do **define standard tests** → give a short formal description (statistic + H0/H1 + decision rule) **also for in-course** (Welch, χ², Wald, regression, GLRT), and depth for the creative tools (rounded-likelihood, mixture-bootstrap, GEV).
- **Discussion:** conclusions + limitations (observational; federation schemas; multi-meet competitors; bias in Tested; selection/survivorship in EVT; n→significance) + **null results as valid findings**.
- **References:** IEEE numbered, live URLs; **OpenPowerlifting (CC0)** mandatory + McCrary + Cattaneo-Jansson-Ma + Peyen 2025 + Einmahl-Magnus + (as needed) medRxiv.

## 6. Repo (Code)
- Python: numpy, pandas, scipy.stats, statsmodels, matplotlib/seaborn (+ `rddensity`/EVT as needed).
- **Locked requirements.txt** + Python version; **a single entry point**; a **README** with exact run instructions.
- **Lock a snapshot of the data** (attach the CSV or document the date) + a CC0 citation. **Publish the federation list and the helper tables.**
- **Combining datasets (instructor feedback):** attach as cited accompanying CSVs — (a) a **table of weight-class limits by federation/era** (feeds H2), (b) an **lb/kg plate standard** (feeds the H1 sub-grid). This satisfies "combine datasets" without breaking the story.
- **Acceptance gate:** clean clone → `pip install -r` → an end-to-end run reproduces everything. **Commit the script even before 28.6** and verify that the numbers (96.2%, +1.92, 24%/43%, b≈0.72/0.49) are reproduced.
- **Figures:** vector/≥300DPI, numbered caption, axis titles, meaningful colors.

## 7. Differentiation and Creativity (up to 10 pts, competitive)
Unique components (with introduction citations that differentiate from the existing literature): (1) **quantization core — rounded-likelihood MLE + GLRT with boundary correction** — truly the original part on OPL; (2) **bunching that has passed falsification** (two-placebos/de-heaping/dose, kg-native) — not an artifact; to our knowledge the first formal manipulation test of weight-cutting bunching on OPL; (3) **handling the mixture-LRT via bootstrap** with a Wilks-violation declaration; (4) **Sex×log(BW) interaction** in the allometry; (5) **EVT** (cite Einmahl-Magnus); (6) **GLRT↔Pearson**. One story ties it together ("the two numbers + the limits of strength"). *(Public OPL repos that were examined — aidanlfrench, ericbohner — deal only with EDA/metrics; none does formal bunching/mixture/EVT.)*

## 8. Grade and Timeline
- **Stage A 30% · Stage B (paper+repo) 70%.** Up to 10 creativity pts (competitive).
- Milestones: *now*→direction email sent + data+EDA (done) + **commit the script**; **toward 28.6**→presentation with real H1+H2; **before 15.8**→full analysis, IEEE paper, a clean-running repo with a locked snapshot.
