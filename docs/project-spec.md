# Final Project Spec — Statistical Theory
## "How Powerlifters 'Game' the Two Numbers They Control — and What the Data Reveals About Human Strength" (OpenPowerlifting)

> All numbers below are **reproducible results** computed on the real data (3,938,042 rows, CC0). The core is robust: **H1** (96.2% of attempts on the 2.5 kg grid) and **H2** (bodyweight bunching just below class thresholds; a non-limit control is flat — the effect is specific to the thresholds). Secondary results: **H4** = 24%/43% untested (population / top-1%); **H5** = b≈0.72 (men) / 0.49 (women) on full-power (SBD) results. **H3 is *not* a by-sex mixture** (Dots is already normalized for sex/weight; see below). Wherever a specification must be locked, this is marked explicitly.

---

## 0. Team, Logistics, and Language
- **Working in a pair: Adir Elmakais + David Levin** — consistent with the default in the instructions (pairs), so **no special approval is needed**. The preliminary email concerns only approval of the research direction.
- Register in the Google Sheet on Moodle (**both members' names** + dataset + date). We registered for **28.6.2026** (first-come-first-served; if crowded — 21.6 as an alternative). **Verify that David's name appears in the registration.**
- **Instructor's name:** the metadata of the official PDF reads "Oshrit Shtossel"; our contact is **Oshrit Viganesky (oshritvig@gmail.com)** — the email was sent to Viganesky. Verify before submission.
- **Language:** the presentation (stage A) is **in Hebrew**; the paper (stage B) is **in English**. Test/code names in English.
- **Code:** GitHub *or* Google Colab. The real bar: **the grader clones, runs clean** and obtains all the numbers/figures.

## 1. The Data and the Research Question
- **Data:** **OpenPowerlifting** — bulk CSV (`openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip`), **3,938,042 rows** (one row per competitor-meet entry), **CC0**. Validated — downloaded and processed. ⚠️ The `latest` file changes weekly → **lock a snapshot** (attach the CSV or document the exact download date), otherwise the grader's run will not match the numbers.
- **Key variables:** continuous — `BodyweightKg`, attempts (`Squat/Bench/Deadlift 1-3 Kg`), `TotalKg`, `Dots`/`Wilks`. Categorical — `Sex`, `Equipment`, `Tested`, `Federation`, `WeightClassKg`, `Division`, `Place`, `Event`, `Date`.
- **Research question (one story):** a competitor controls two numbers — **the weight on the bar** (attempt selection) and **bodyweight** (on the scale). How does he "game" both, and what does the data thereby reveal about **the limits of human strength**.

### Hypothesis Structure (by weight within the project — to fit ≤8 pages and one story)
**🟢 Leading (the heart of the story — "the two numbers"):**
- **H1 — quantization (the theoretical core):** attempt weights are not continuous but **quantized to a 2.5 kg grid** — a continuous "intended" weight observed through grid rounding. **Validated: 96.4% of best attempts / 96.2% including failed ones on the grid.** The reported result = **%on-grid + CI** (not the astronomical G).
- **H2 — weight-cutting bunching:** an excess just below a class threshold + a deficit above it. **Result (IPF + USAPL men, n≈1.18M, boundary-correct window (L-0.5, L], de-heaped):** log(below/above) ≈ **+1.92 at the 83 kg limit** (and ≈ +1.5 / +1.0 at 93 / 105), versus ≈ **-0.21 at a non-limit control (91 kg)** — the excess is specific to real class limits and survives removing round-number heaping. To be formalized with a McCrary / Cattaneo-Jansson-Ma density-discontinuity test (see section 2).

**🟡 Secondary:**
- **H3 — structure of the strength distribution:** ⚠️ **Not a by-sex mixture.** `Dots` is pre-normalized for sex+weight (mean Dots ≈254 *identical* across the two sexes) — so labeling the components as "men/women" is factually wrong. The bimodality is **real** (Anderson-Darling ≈687–1307) but originates in **single-lift/bench-only events, beginners/youth, and bomb-outs** (the low cluster is 78% men). **Framing:** (a) run the mixture on **raw strength** (not Dots), where sex *does* produce bimodality; or (b) filter to **full SBD + TotalKg>0** and frame it as "two competition regimes." Mixture-vs-single GLRT **via parametric bootstrap / AIC-BIC — not χ²** (see caveat in section 2).
- **H5 — allometric scaling:** `Total ~ Bodyweight^b` on full-power (Event=='SBD') results. **OLS: b≈0.72 (men) / 0.49 (women).** Men sit slightly **above** the isometric 2/3≈0.667, women well **below** — a sex difference in scaling. Report b+CI with heteroskedasticity-robust / clustered SE and a Sex×log(BW) interaction (section 2). The women's b<0.5 may be a range-restriction artifact → diagnose before publication.

**🔵 Additional observations / control (compact paragraph, not a main header):**
- **H4 — drugs/testing (control/moderator):** **24% untested in the population / 43% in the top-1%** (untested are over-represented in the elite tail). ⚠️ confound at the federation/equipment/era level — one cannot infer "drugs" from a raw comparison. Therefore: compare **top-1% versus bottom-99% (disjoint groups)** with **equipment stratification + regression** (Tested + Federation+Equipment+Sex+Era), and frame it **descriptively** / as a moderator of the dose-response in H2.
- **EVT (supporting):** GEV on the annual block-maxima of strength, ξ<0 → ceiling. **Report the number of blocks + a CI for ξ (profile-likelihood)**, a stable sub-window, and cite Einmahl & Magnus (the method is well known — its application to OPL is new).
- **Time trend (supporting):** mean strength and number of participants over the years; women/men ratio — compact.

## 2. Analysis Plan (Python)
**Stage 0 — loading, cleaning, and unit of analysis (declared in advance):**
- From the 803MB CSV → lean files by columns. Attempts = absolute value (failures are negative), reasonable range.
- **Independence / pseudo-replication — correction per-hypothesis (not a "note"):** the same competitor appears in many rows; this **biases estimates** (not merely inflates significance) in H3/H5/time-trend. **Declared dedup rule: one row per competitor = personal Total-best within the clean set**, for the cross-sectional hypotheses (H3/H5/EVT/time). For H1 the unit of analysis is **the attempt** (the mechanism is within-competitor ⇒ the grid is robust to clustering). Report a **sensitivity table** for 2–3 dedup rules.
- **Unit-source control (lb→kg):** identify lb-native rows (weight = a multiple of 0.45359237) and run H2 **first on the kg-native IPF rows**; show that the effect survives; report the lb-converted ones separately.
- **Explicit federation list, published in the repo:** IPF + USAPL/USPA (one modern schema). Exclude THSPA/THSWPA (Texas high school) and FPR/USPF/WPC (overlapping schemas).

**Stage 1 — Core A: quantization (H1).** %on-grid 2.5/5/integer **+ CI** as the primary result; **MLE for a grid-rounding model** (point mass on the grid + continuous background) + **nested likelihood-ratio (GLRT)**. ⚠️ The grid weight is on the **boundary** of the space under H0 → declare the df and use **Self–Liang / bootstrap** (not naive χ²_1). Sub-grid (lb→kg peaks) via a cited **lb-plate standard**.

**Stage 2 — Core B: bunching (H2).** A **density-discontinuity test (McCrary; preferably Cattaneo-Jansson-Ma `rddensity`)** of the **jump** at the threshold — not bare "asymmetry." Measure the **spike width** (cutting = a sharp spike in <0.5–1 kg; class assignment = a smooth slope). Falsification (mandatory):
- (i) **two placebos** to separate the confound: (a) round-non-legal (80/85 if not a threshold) to measure round-number attraction; (b) **non-round-and-non-legal** (70.0 etc.) = the true null. **The claim = asymmetry at legal thresholds greater than the round-number baseline** (a contrast, not "present/absent").
- (ii) **de-heaping** — show the effect also at **non-round** legal thresholds (83/93/105) → proves it is not round-number attraction.
- (iii) **dose (dose-response)** — stronger in the elite/tested/winners, **within the same federation** (otherwise it is a federation-composition confound), and at the competitor level (dedup).
- Bandwidth: a declared selection rule + a **sensitivity curve** + CI (not a bare number).

**Stage 3 — structure of the strength distribution (H3).** Normality (Anderson-Darling + KS + QQ) → rejected → **2-component Gaussian mixture model (EM)**. ⚠️ **The mixture LRT violates Wilks** (mixing weight on the boundary + non-identifiability) → **calibrate with a parametric bootstrap or lead with AIC/BIC**, and declare this explicitly (turns a pitfall into a beyond-course advantage). Run on **raw strength / full SBD** (not Dots), and interpret as "competition regimes"/sex-in-raw-strength.

**Stage 4 — control: tested versus untested (H4).** **top-1% versus bottom-99% (disjoint groups)** — two-proportions / χ² + CI for the difference + odds-ratio. **Equipment stratification (Raw vs Raw)** and **regression** with Tested+Federation+Equipment+Sex+Era (interaction term in-course). χ² test of independence **Federation×Tested** (+ Cramér's V). *Drop* the standalone equipment ANOVA and the sex×equipment χ² into a single control paragraph ("equipment inflates Total → controlled for"). Mean comparisons: **Welch *or* Mann-Whitney** (state the null of each) + a **rank-based effect size**; **no Levene as a gate**.

**Stage 5 — allometry (H5).** `log(Total) ~ log(Bodyweight)` OLS with **heteroskedasticity-robust standard errors (HC3) / clustered-by-competitor**; a **Wald test against 2/3** (and also presented against 1 as an anchor); a **Sex×log(BW) interaction term** to test the sex difference *formally* (instead of a separate fit). Diagnose the b≈0.49 for women (weight-range/leverage) before interpretation. Result = **b+CI**, not p.

**Stage 6 — extreme value theory (EVT, supporting).** GEV on the annual block-maxima; **report the number of blocks** + a CI for ξ; **POT/GPD** as an alternative; a stable sub-window (fixed federations/era) or a trend-model in location. ξ<0 = "a ceiling *in this competitive population*," not "a ceiling of the human species."

**Stage 7 — time trend (supporting, compact).** Regression of mean strength/number of participants over the years; change in the women/men ratio. Note the expansion of the sampling frame (selection).

**Stage 8 — reporting, multiple-testing correction, and power.**
- **Effect-first reporting:** in every test — the **effect size + CI are the result**, p/G are secondary. **Stability check:** run on a 1%/10% subsample and show that the effect is stable while p is not — demonstrates control over "n→everything is significant."
- A pre-declared family of tests; **Bonferroni (FWER) + Benjamini-Hochberg (FDR)**; an **a-priori power analysis** (α=0.05, target 0.90).
- **Paired test (new, on-story):** attempt-1 versus attempt-3 of the same competitor (Wilcoxon signed-rank) — covers an additional item from the toolbox and reinforces H1/H2 ("the number on the bar").

**Theory notes (the heart of the course):**
- **GLRT ↔ Pearson:** Pearson's χ² = a second-order Taylor approximation of the likelihood-ratio statistic (Wilks) — derived in Lecture 8 (verified against the transcript). A strong theoretical anchor.
- **MP/UMP — anchor in a real test:** frame the **Wald test of H5 (b versus 2/3)** or a one-sample test as the Neyman-Pearson/UMP point; the GLRTs (H1/H3/EVT) = a generalization of the MP-lemma to composite hypotheses (Wilks).
- **n warning:** at n≈3.9M every null is rejected — therefore the science rests on **effect size + the falsification**, not on p. State this in the Discussion.
- **Not directly relevant (state as a decision):** classification and learning metrics — intentionally out-of-scope (there is no prediction task that serves the story), cited against the multiple-comparisons warning.

## 3. Tool Classification: in-course versus beyond-course
- **In-course:** t/Welch, F, ANOVA, χ² (independence + goodness-of-fit), Pearson/Spearman, GLRT/LRT, Wald, MLE, power, Bonferroni, regression, **interaction term**, **paired test**.
- **Beyond-course (explain the method + *what the course tool lacks*):** quantization/rounded-likelihood model, **parametric bootstrap for the mixture-LRT**, density-discontinuity (McCrary / **Cattaneo-Jansson-Ma**), GEV/EVT, Kruskal-Wallis/Dunn, Anderson-Darling.
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
- **Introduction:** background (weight-cutting; McCrary 2008) + **explicit differentiation with citations**: **lead with H1 (rounded-likelihood — truly the original part)**; cite **Peyen et al. arXiv:2503.13040 (2025)** which already showed the accumulation below thresholds on OPL, and frame our contribution as a **formal test + falsification** (not "we discovered bunching"); cite **medRxiv 2021.05.07.21256806** (tested/untested) and frame H4 as a control. An originality claim that is **modest and defensible** ("to the best of our knowledge, no public OPL analysis combines a quantization model with bunching that has passed falsification").
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
Unique components (with introduction citations that differentiate from the existing literature): (1) **quantization core — rounded-likelihood MLE + GLRT with boundary correction** — truly the original part on OPL; (2) **bunching that has passed falsification** (two-placebos/de-heaping/dose, kg-native) — not an artifact, differentiates from the descriptive Peyen 2025; (3) **handling the mixture-LRT via bootstrap** with a Wilks-violation declaration; (4) **Sex×log(BW) interaction** in the allometry; (5) **EVT** (cite Einmahl-Magnus); (6) **GLRT↔Pearson**. One story ties it together ("the two numbers + the limits of strength"). *(Public OPL repos that were examined — aidanlfrench, ericbohner — deal only with EDA/metrics; none does formal bunching/mixture/EVT.)*

## 8. Grade and Timeline
- **Stage A 30% · Stage B (paper+repo) 70%.** Up to 10 creativity pts (competitive).
- Milestones: *now*→direction email sent + data+EDA (done) + **commit the script**; **toward 28.6**→presentation with real H1+H2; **before 15.8**→full analysis, IEEE paper, a clean-running repo with a locked snapshot.
