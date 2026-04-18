"""
Documented ingest layer for the Aging-in-Place Readiness Index.

This module is a template showing how you would replace the synthetic
sample data with real public data sources. Each function returns a
pandas DataFrame keyed on 5-digit county FIPS code.

In the weekend build the sample dataset (see generate_sample_data.py)
stands in for real ingestion. Once you have network access and time,
fill in the TODO blocks below.

Author: Aishwarya Sharma
"""
from __future__ import annotations

import pandas as pd

# ---------------------------------------------------------------------------
# 1. U.S. Census ACS — county demographics, broadband, living-alone rates
# ---------------------------------------------------------------------------
# Endpoint: https://api.census.gov/data/2022/acs/acs5
# Variables used:
#   B01001_001E  Total population
#   B01001_020E..B01001_025E  Males 65+
#   B01001_044E..B01001_049E  Females 65+
#   B28002_004E  Households with broadband
#   B11010_012E  Seniors living alone
# Sign up for a free API key at https://api.census.gov/data/key_signup.html
def fetch_census_acs(api_key: str, year: int = 2022) -> pd.DataFrame:
    """Fetch ACS 5-year estimates at county level."""
    # TODO: implement with requests + pandas
    raise NotImplementedError("Replace with live ACS API call")


# ---------------------------------------------------------------------------
# 2. HRSA Area Health Resource File — clinical supply
# ---------------------------------------------------------------------------
# Source: https://data.hrsa.gov/topics/health-workforce/ahrf
# Fields used: primary_care_per_100k, home_health_agencies
def fetch_hrsa_ahrf(local_path: str) -> pd.DataFrame:
    """AHRF is distributed as a large zipped ASCII file; load from local."""
    raise NotImplementedError("Download AHRF once, then parse with pandas")


# ---------------------------------------------------------------------------
# 3. CMS Home Health Agency directory
# ---------------------------------------------------------------------------
# Source: https://data.cms.gov/provider-data/dataset/6jpm-sxkc
def fetch_cms_home_health() -> pd.DataFrame:
    """Open CMS endpoint; aggregate to county."""
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 4. FCC Broadband Data Collection (optional cross-check for ACS)
# ---------------------------------------------------------------------------
# Source: https://broadbandmap.fcc.gov/data-download
def fetch_fcc_broadband() -> pd.DataFrame:
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 5. USDA Food Access Research Atlas — senior food insecurity proxy
# ---------------------------------------------------------------------------
# Source: https://www.ers.usda.gov/data-products/food-access-research-atlas/
def fetch_usda_food_access(local_path: str) -> pd.DataFrame:
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 6. CDC BRFSS / Medicare claims — fall hospitalization rate
# ---------------------------------------------------------------------------
# Option A: CDC Behavioral Risk Factor Surveillance System (survey-based)
# Option B: CMS Medicare FFS claims for ICD-10 W00-W19 (higher quality,
#           requires credentialed access)
def fetch_fall_rates() -> pd.DataFrame:
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 7. IRS county-to-county migration flows — caregiver distance gap proxy
# ---------------------------------------------------------------------------
# Source: https://www.irs.gov/statistics/soi-tax-stats-migration-data
# Derive: % of working-age out-migrants whose destination is > 1 hr drive
#         from their origin county, weighted by origin 65+ population.
def fetch_irs_migration() -> pd.DataFrame:
    raise NotImplementedError


def assemble_master(year: int = 2022) -> pd.DataFrame:
    """Join all sources on county_fips. Placeholder for real implementation."""
    raise NotImplementedError(
        "Once each fetch_* function is implemented, join them here and "
        "write to data/processed/county_master.csv"
    )


if __name__ == "__main__":
    print(__doc__)
