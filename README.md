# OpenPowerlifting — Statistical Theory Final Project

How lifters **"game" the two numbers they control** — the weight on the bar and their
bodyweight — and what ~3.94 million competition results reveal about the limits of human
strength.

Bar-Ilan University · MSc · *Statistical Theory*.
Authors: **Adir Elmakais, David Levin**.

> **Status:** Stage 1 (mid-presentation) materials. The final IEEE paper and the full
> analysis pipeline will be added here.

## Repository layout
| Path | What |
|---|---|
| `download_data.py` | Downloads the OpenPowerlifting bulk CSV into `data/`. |
| `src/make_figures.py` | Computes the headline results on the real data and writes the figures. |
| `src/make_deck.py` | Builds the Hebrew mid-presentation (native `.pptx`, paragraph-level RTL). |
| `figures/` | Generated figures (PNG). |
| `presentation/` | The generated mid-presentation deck. |
| `requirements.txt` | Pinned Python dependencies. |
| `docs/project-spec.md` | Full project spec / brainstorm (English). |
| `docs/checklist.md` | Stage-1 / Stage-2 checklist (English). |
| `reference/` | Course-provided reference material (Hebrew): the assignment instructions PDF, the example paper (Chess) & example deck (Animal Adoption), the lecture-8 transcript, and data-source screenshots. |

## Reproduce
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python download_data.py        # ~160 MB zip -> data/openpowerlifting.csv (~800 MB)
python src/make_figures.py     # writes figures/ and prints the headline numbers
python src/make_deck.py        # writes presentation/mid_presentation_OpenPowerlifting.pptx
```
Open the `.pptx` in **Google Slides** / PowerPoint / LibreOffice to view or present (Hebrew RTL).

## Preliminary findings (verified on the real data)
- **Quantization (H1):** 96.2% of ~13.4M attempt loads sit exactly on the **2.5 kg plate grid**
  (smallest standard plate is 1.25 kg, loaded on both sides → 2.5 kg minimum increment).
- **Weight-cutting (H2):** a strong bodyweight pile-up just **below real IPF class limits**
  (de-heaped log(below/above) ≈ **+1.92** at 83 kg) vs a **non-limit control** (91 kg, ≈ **-0.21**).
  Restricted to **IPF + USAPL** (same class scheme 59/66/74/83/93/105/120).
- **Allometry (H3):** strength ~ bodyweight^b, **b ≈ 0.72 (men) / 0.49 (women)** for full-power
  (SBD) results; isometric reference 2/3 ≈ 0.67.

> Headline numbers lead with **effect sizes**, not p-values: at n ≈ 3.9M almost any departure is
> "statistically significant". The bunching result is preliminary (formal McCrary + de-heaping to come).

## Data
**OpenPowerlifting** — https://www.openpowerlifting.org (data dictionary:
https://openpowerlifting.gitlab.io/opl-csv/bulk-csv-docs.html). The competition data is released
into the **public domain (CC0-style)**; the project's code is separately AGPLv3+.
`openpowerlifting-latest.zip` updates ~weekly — **pin/record the download date** for exact
reproducibility.

## Notes
- Figures use **English axis labels** (to avoid matplotlib bidi issues); Hebrew captions live on the slides.
- `make_deck.py` sets RTL per paragraph via the OOXML `a:pPr rtl="1"` attribute (python-pptx has no RTL API).
