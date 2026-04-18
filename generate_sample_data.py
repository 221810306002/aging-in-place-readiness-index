"""
Generate a realistic synthetic county-level dataset for the
Aging-in-Place Readiness Index project.

This script is included so the project runs end-to-end without requiring
the user to first download ~1 GB of public data. Once you replace this
with real ingested data (see src/ingest.py), delete this file.

Output:
    data/sample/county_sample.csv  (~500 synthetic U.S. counties)

Author: Aishwarya Sharma
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(seed=42)
N_COUNTIES = 500

STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA",
    "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM",
    "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD",
    "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]

RURAL_LEVELS = ["Urban", "Suburban", "Small town", "Rural"]
RURAL_WEIGHTS = [0.18, 0.22, 0.25, 0.35]


def _clip(arr, lo, hi):
    return np.clip(arr, lo, hi)


def generate() -> pd.DataFrame:
    fips = RNG.integers(1001, 56045, size=N_COUNTIES)
    fips = np.unique(fips)
    # Top up if duplicates were removed
    while len(fips) < N_COUNTIES:
        extra = RNG.integers(1001, 56045, size=N_COUNTIES - len(fips))
        fips = np.unique(np.concatenate([fips, extra]))
    fips = fips[:N_COUNTIES]

    rurality = RNG.choice(RURAL_LEVELS, size=N_COUNTIES, p=RURAL_WEIGHTS)
    state = RNG.choice(STATES, size=N_COUNTIES)

    # Total population: more rural = smaller
    base_pop = np.where(
        rurality == "Urban", RNG.normal(250_000, 120_000, N_COUNTIES),
        np.where(rurality == "Suburban", RNG.normal(90_000, 45_000, N_COUNTIES),
        np.where(rurality == "Small town", RNG.normal(28_000, 12_000, N_COUNTIES),
                 RNG.normal(9_000, 4_500, N_COUNTIES)))
    )
    total_pop = _clip(base_pop, 1500, 900_000).astype(int)

    # % age 65+: rural counties skew older
    pct_65_plus = np.where(
        rurality == "Urban", RNG.normal(14, 2.5, N_COUNTIES),
        np.where(rurality == "Suburban", RNG.normal(17, 3.0, N_COUNTIES),
        np.where(rurality == "Small town", RNG.normal(20, 3.5, N_COUNTIES),
                 RNG.normal(23, 4.5, N_COUNTIES)))
    )
    pct_65_plus = _clip(pct_65_plus, 7, 38)
    pop_65_plus = (total_pop * pct_65_plus / 100).astype(int)

    # % living alone (of 65+)
    pct_living_alone = _clip(RNG.normal(27, 6, N_COUNTIES), 10, 45)

    # Broadband access (%) — rural lags badly
    broadband = np.where(
        rurality == "Urban", RNG.normal(92, 4, N_COUNTIES),
        np.where(rurality == "Suburban", RNG.normal(86, 6, N_COUNTIES),
        np.where(rurality == "Small town", RNG.normal(72, 9, N_COUNTIES),
                 RNG.normal(58, 12, N_COUNTIES)))
    )
    broadband = _clip(broadband, 25, 99)

    # Primary care providers per 100k (lower is worse)
    pcp_rate = np.where(
        rurality == "Urban", RNG.normal(85, 18, N_COUNTIES),
        np.where(rurality == "Suburban", RNG.normal(65, 15, N_COUNTIES),
        np.where(rurality == "Small town", RNG.normal(45, 14, N_COUNTIES),
                 RNG.normal(28, 12, N_COUNTIES)))
    )
    pcp_rate = _clip(pcp_rate, 5, 180)

    # Home health agencies per 10k seniors
    hh_agencies = _clip(RNG.gamma(shape=2.0, scale=1.2, size=N_COUNTIES), 0.0, 12.0)

    # Meals on Wheels coverage (%) — fraction of food-insecure seniors reached
    mow_coverage = _clip(RNG.normal(38, 14, N_COUNTIES), 3, 88)

    # Transit access score (0-100) — urban advantage
    transit = np.where(
        rurality == "Urban", RNG.normal(72, 14, N_COUNTIES),
        np.where(rurality == "Suburban", RNG.normal(48, 15, N_COUNTIES),
        np.where(rurality == "Small town", RNG.normal(28, 12, N_COUNTIES),
                 RNG.normal(14, 9, N_COUNTIES)))
    )
    transit = _clip(transit, 2, 98)

    # Poverty rate among seniors (%)
    senior_poverty = _clip(RNG.normal(10.5, 3.8, N_COUNTIES), 3, 28)

    # Medicare Advantage penetration (%)
    ma_penetration = _clip(RNG.normal(52, 14, N_COUNTIES), 12, 88)

    # Food insecurity among seniors (%)
    food_insecurity = _clip(
        RNG.normal(11 + senior_poverty * 0.4, 2.5, N_COUNTIES), 2, 30
    )

    # Fall hospitalization rate per 1k seniors (higher is worse)
    fall_rate = _clip(
        RNG.normal(18 - (pcp_rate - 50) * 0.08 + (pct_living_alone - 27) * 0.15,
                   3.5, N_COUNTIES),
        4, 45,
    )

    # Caregiver distance gap — % of 65+ whose nearest adult child lives
    # more than 1 hr away. Proxied by out-migration index + rurality.
    caregiver_gap = np.where(
        rurality == "Urban", RNG.normal(32, 8, N_COUNTIES),
        np.where(rurality == "Suburban", RNG.normal(38, 9, N_COUNTIES),
        np.where(rurality == "Small town", RNG.normal(48, 11, N_COUNTIES),
                 RNG.normal(57, 12, N_COUNTIES)))
    )
    caregiver_gap = _clip(caregiver_gap, 12, 82)

    df = pd.DataFrame({
        "county_fips": fips,
        "state": state,
        "rurality": rurality,
        "total_population": total_pop,
        "pop_65_plus": pop_65_plus,
        "pct_65_plus": pct_65_plus.round(2),
        "pct_seniors_living_alone": pct_living_alone.round(2),
        "broadband_access_pct": broadband.round(2),
        "primary_care_per_100k": pcp_rate.round(2),
        "home_health_agencies_per_10k_seniors": hh_agencies.round(2),
        "meals_on_wheels_coverage_pct": mow_coverage.round(2),
        "transit_access_score": transit.round(2),
        "senior_poverty_pct": senior_poverty.round(2),
        "medicare_advantage_pct": ma_penetration.round(2),
        "senior_food_insecurity_pct": food_insecurity.round(2),
        "senior_fall_hospitalizations_per_1k": fall_rate.round(2),
        "caregiver_distance_gap_pct": caregiver_gap.round(2),
    })
    return df


def main() -> None:
    out_dir = Path(__file__).resolve().parent.parent / "data" / "sample"
    out_dir.mkdir(parents=True, exist_ok=True)
    df = generate()
    out_path = out_dir / "county_sample.csv"
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df):,} rows to {out_path}")


if __name__ == "__main__":
    main()
