# ⚡ Energy Transition Atlas

**Observed-data geographic intelligence for electricity, emissions and economic development.** An interactive navy/mint Streamlit dashboard with world maps, rankings, country trajectories, indicator relationships, **adjacent-year transition momentum**, data coverage and CSV exports.

> **Verification status (2026-11-22):** Source code committed to this standalone repository. Six original deterministic unit tests passed previously; six new momentum tests passed in an isolated local run (6/6), but the combined repository suite has not been run; GitHub CI and live data ingestion have not yet been verified. No browser screenshots or deployment claims are made. Dataset counts are computed from publisher data at runtime; no synthetic analytical observations are included.

## Analytical workspaces

| Workspace | Interactions | Purpose |
|---|---|---|
| World explorer | Metric/year, projection, choropleth/bubbles, rank direction/count | Map, rank and compare country observations |
| Country trajectories | Country selection, start year, raw/indexed trends | Compare historical patterns and gaps |
| Transition relationships | X/Y metrics and log scale | Investigate matched cross-country associations |
| Transition momentum | Reporting year, paired renewable/fossil share changes | Classify observed annual shifts, examine quadrants, export changes |\n| Source & coverage lab | Year, missingness, observed CSV export | Audit lineage, completeness and temporal coverage |

## Architecture

```mermaid
flowchart LR
  A[OWID renewables] --> V[Schema, ISO3 and key validation]
  B[OWID fossil electricity] --> V
  C[OWID electricity demand] --> V
  D[OWID CO2 per capita] --> V
  E[World Bank GDP per capita] --> V
  V --> J[Outer join on ISO3 and calendar year]
  J --> Q[Cached observed-data model]
  Q --> M[World map and rankings]
  Q --> T[Country trends]
  Q --> R[Indicator relationships]
  Q --> L[Coverage audit and CSV export]\n  Q --> N[Exact adjacent-year change engine]\n  N --> P[Transition quadrant analysis]
```

## Primary publisher sources

| Publisher | Indicator | URL |
|---|---|---|
| Our World in Data | Renewable share | https://ourworldindata.org/grapher/electricity-mix?frequency=annual&metric=share_of_generation&source=renewables |
| Our World in Data | Fossil share | https://ourworldindata.org/grapher/electricity-mix?frequency=annual&metric=share_of_generation&source=fossil |
| Our World in Data | Electricity demand | https://ourworldindata.org/grapher/electricity-mix?frequency=annual&metric=demand&source=total |
| Our World in Data | CO2 per capita | https://ourworldindata.org/grapher/co-emissions-per-capita.csv |
| World Bank | GDP per capita, current USD | https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.CD?format=json |

**Data policy:** The application fetches publisher observations directly. It does not ship raw observations, synthetic samples, demo rows or fallback fabricated datasets. A failed download produces an explicit error. Small deterministic fixtures exist only inside `tests/` for validating code behavior.

**Provenance and licensing:** OWID Grapher datasets can inherit original publisher licenses; consult each source's metadata before redistributing underlying observations. OWID website licensing does not automatically authorize redistribution of all third-party observations. World Bank indicators are generally CC BY 4.0, subject to exceptions: https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets . Source attribution, licenses and update frequency should be checked against current metadata.

**Coverage:** Exact merged record counts, date spans and country counts remain unverified until the full ingestion runs. The coverage lab calculates non-null country-years, country counts, first and last reporting years from actual retrieved records. The OWID publisher-wide energy catalog separately reports 19,494 rows and 130 columns, updated 2026-09-10 (https://catalog.ourworldindata.org/energy/owid_energy/); this is **not** the size of this dashboard's joined panel.

**Join/validation:** ISO 3166-1 alpha-3 and calendar year, excluding aggregates not in `pycountry`. Reject missing/ambiguous schemas and duplicate keys. Outer joins retain missing values; no imputation. Relationship analyses use matched complete observations. Country trend indexing starts at each country's first observed year in the selected interval.

**Limitations:** GDP in current USD is not inflation-adjusted. Correlation does not imply causation. Electricity demand and generation differ. Reporting coverage is uneven; publisher CSV schemas and URLs may change. Live endpoint validation and responsive browser visual QA are still pending.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

For Windows, activate the virtual environment using `.venv\\Scripts\\activate`.

Docker:

```bash
docker build -t energy-atlas .
docker run -p 8501:8501 energy-atlas
```

Run tests:

```bash
pip install -r requirements-dev.txt
python -m pytest -q
python -m compileall -q app.py src
```

## Design and release acceptance

The app includes a custom responsive theme, hero/KPI treatment, four analytical workspaces, multiple world-map projections, bubble/choropleth modes, country comparisons, rankings, distributions and missingness auditing. Browser screenshot validation at desktop and mobile sizes is **not yet complete**. Do not describe the app as production-ready until live data ingestion, CI and browser QA are verified.


### 2026-11-23 — R scientific companion

Added `r/renewable_electricity.R`, a reproducible tidyverse/ggplot2 workflow that downloads the **published** OWID renewable electricity share CSV, validates the schema, calculates only observed adjacent-year percentage-point changes, exports observed records and renders country trends. Install `jsonlite`, `dplyr`, and `ggplot2`, then run `Rscript r/renewable_electricity.R`. GitHub Actions now checks the R script parses. **The R download/execution and CI outcome are not yet verified**; this addition does not claim a live dataset size or successful browser render.


### 2026-11-23 — Transition Momentum research workspace

The fifth workspace introduces **observed, exact adjacent-year energy-mix diagnostics**. It calculates renewable and fossil electricity-generation share changes in **percentage points**, plus CO₂-per-capita changes in **tonnes/person** when available. Only matching consecutive calendar years qualify. Missing years and missing metric pairs remain missing rather than being interpolated or silently converted to zero.

The interactive quadrant scatter classifies countries into *renewables up/fossil down*, *renewables down/fossil up*, *both up*, *both down*, or *mixed/unchanged*. It includes year filters, pattern counts, country-level tables and a CSV download of observed changes. This is descriptive accounting, **not** a claim about causal emissions effects, absolute generation or electricity-sector emissions. Nuclear and other non-fossil sources mean renewable and fossil shares need not sum to 100%.

**Implementation:** `src/momentum.py` is a reusable pure-Pandas analytical engine; `tests/test_momentum.py` covers exact adjacent-year differences, skipped years, missing values, duplicate keys, invalid years and nonfinite values. The six new tests passed locally in isolation. The full repository test suite, live publisher API calls, rendered Streamlit interface, Docker image and GitHub Actions have **not** been verified for this update.

**Reproduce:** Install dependencies using the commands above, run `python -m pytest -q`, then `streamlit run app.py`. Select **Transition momentum**, choose a reporting year, inspect the quadrants and export `energy_transition_changes_<year>.csv`.

**Engineering tradeoff:** The module computes observed deltas without adding forecast models, interpolation or statistical significance claims. The first reported year for a country cannot have a change, and a reporting gap deliberately produces a null delta. Future work: regional aggregation with explicit denominators, country drill-downs, and visual QA across screen sizes.
