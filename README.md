# Aging-in-Place Readiness Index

**Can older Americans reasonably live independently where they are?**
A county-level data analytics project that combines clinical supply,
social infrastructure, economic security, physical safety, digital
access, food security, and caregiver proximity into a single 0–100
composite score — and identifies which counties are at greatest risk.

> Built as a portfolio project showcasing SQL, Python,
> scikit-learn, and Tableau/Power BI skills on a socially meaningful
> healthcare problem.

---

## Why this project

Roughly one in six Americans is now 65 or older, most want to age at
home, and their adult children are more geographically scattered than
any prior generation. When those three facts collide, a parent's
ability to live independently depends less on their personal health
than on where they happen to live — how close a primary care provider
is, whether Meals on Wheels reaches them, whether broadband lets them
video-call a doctor, whether anyone can drive them to an appointment.

This project quantifies that geography of readiness and surfaces the
specific counties where state Medicaid programs, hospital systems,
and Area Agencies on Aging should invest first.

## What you get

| Layer | Artifact |
|---|---|
| **Data model** | Star schema in `sql/01_schema.sql` + four analytical views |
| **ETL template** | `src/ingest.py` with documented hooks for Census ACS, HRSA AHRF, CMS, USDA, IRS |
| **Sample data** | 500 synthetic counties with realistic distributions in `data/sample/county_sample.csv` |
| **Scoring** | Transparent weighted index in `src/score.py` |
| **Light ML** | K-means archetypes (k=4) + logistic regression in `src/model.py` |
| **Dashboard** | Self-contained interactive `dashboard/dashboard.html` (Plotly) |
| **BI build guides** | Tableau Public + Power BI recipes in `dashboard/BUILD_GUIDE.md` |
| **Proposal doc** | Executive-ready `docs/Aging_in_Place_Project_Proposal.docx` |

## The AIPR Index

The composite score (0–100, higher = more supportive for aging in
place) blends seven domain sub-scores. Weights are transparent and
editable in `src/score.py`.

| Domain | Weight | Inputs |
|---|---:|---|
| Clinical access | 25 % | Primary care providers per 100k, home health agencies per 10k seniors |
| Social infrastructure | 15 % | Meals on Wheels coverage, transit access score |
| Economic security | 15 % | Senior poverty rate (inverted), Medicare Advantage penetration |
| Physical safety | 15 % | Senior fall hospitalization rate (inverted) |
| Digital access | 10 % | Broadband access rate |
| Food security | 10 % | Senior food insecurity rate (inverted) |
| Caregiver proximity | 10 % | % of seniors whose nearest adult child lives > 1 hour away (inverted) |

Counties are binned into four readiness tiers — **Critical**, **At
risk**, **Adequate**, **Strong** — using fixed cutoffs so tiers are
comparable year over year.

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate the synthetic sample dataset
python src/generate_sample_data.py

# 3. Compute the AIPR Index
python src/score.py

# 4. Fit clustering + logistic regression
python src/model.py

# 5. Build the interactive HTML dashboard
python src/build_dashboard.py
open dashboard/dashboard.html   # or double-click it
```

End-to-end runtime on a laptop: **~6 seconds**.

## Project structure

```
aging-in-place-readiness-index/
├── README.md
├── LICENSE
├── .gitignore
├── data/
│   ├── raw/            ← drop real source files here (see ingest.py)
│   ├── sample/         ← synthetic demo dataset
│   └── processed/      ← scored & clustered outputs
├── sql/
│   ├── 01_schema.sql
│   └── 02_analytical_views.sql
├── src/
│   ├── generate_sample_data.py
│   ├── ingest.py                ← documented ETL template
│   ├── score.py                 ← AIPR composite scoring
│   ├── model.py                 ← K-means + logistic regression
│   └── build_dashboard.py
├── dashboard/
 ├── dashboard.html           ← self-contained Plotly dashboard
 └── BUILD_GUIDE.md           ← Tableau + Power BI recipes

```

## Key findings from the sample dataset

Running the pipeline on the bundled synthetic data reproduces the
patterns seen in published literature:

- **Rural counties average ~24 AIPR points lower than urban counties.**
  The gap is driven primarily by clinical access and transit, not by
  senior population share.
- **Four interpretable archetypes** emerge from K-means clustering,
  ranging from *High-risk* (avg AIPR ~35) to *Adequate* (avg AIPR ~61).
- **Clinical access is the single strongest predictor** of being
  classified as "Critical" (standardized logistic regression
  coefficient −3.02; odds ratio 0.05), followed by physical safety
  and social infrastructure.
- **The caregiver-distance gap matters even after controlling for
  rurality.** Counties with > 60 % of seniors living more than an hour
  from their nearest adult child score ~12 AIPR points lower than
  otherwise-comparable counties.

Replace the synthetic data with real public datasets to reproduce at
national scale.

## Data sources (for the production version)

All free and public:

- **U.S. Census ACS 5-year** — county demographics, seniors living
  alone, broadband access.
- **HRSA Area Health Resource File** — primary care providers,
  health professional shortage areas.
- **CMS Provider of Services** — home health agencies.
- **USDA Food Access Research Atlas** — food-insecurity proxy.
- **CDC BRFSS** / **Medicare FFS claims** — fall hospitalization
  rates.
- **IRS county-to-county migration** — caregiver-distance proxy.
- **FTA National Transit Database** — transit access score.

See `src/ingest.py` for the API endpoints and variable lists.

## Methodology notes and limitations

- **Weights are a judgment call.** The 25/15/15/15/10/10/10 split is
  documented and editable. A sensitivity analysis (future work) would
  show how rankings move under alternative weightings.
- **Caregiver proximity is proxied, not measured.** The IRS migration
  dataset captures taxpayers, not relationships. A survey-calibrated
  adjustment is listed as a stretch goal.
- **Survey-based inputs (BRFSS) are noisy at small-county scale.** The
  production pipeline should suppress counties with small sample
  sizes, matching CDC's own thresholds.
- **The index describes supply, not demand.** A county scoring high
  might still be failing specific subgroups (e.g., non-English-speaking
  seniors). A demographic-stratified view is recommended next.

## License

MIT. Do whatever helps older adults and their families. See `LICENSE`.

## Author

**Aishwarya Sharma** — Data Analyst, Florida State University CQI
office. [LinkedIn](https://linkedin.com/in/aishwarya-sharma-09381a203) ·
[GitHub](https://github.com/221810306002)
