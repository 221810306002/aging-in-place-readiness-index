"""
Compute the Aging-in-Place Readiness Index (AIPR) for U.S. counties.

The AIPR Index is a weighted composite score (0-100, higher = more
supportive for aging in place). It blends eight domain sub-scores into
a single interpretable number that can be mapped, ranked, or filtered.

Domains and weights (see /docs for methodology rationale):
    Clinical Access         25%   primary care + home health
    Social Infrastructure   15%   meals programs + transit
    Economic Security       15%   senior poverty + MA penetration
    Physical Safety         15%   fall hospitalization rate
    Digital Access          10%   broadband
    Food Security           10%   senior food insecurity
    Caregiver Proximity     10%   distance-to-adult-children gap

Usage:
    from src.score import score_counties
    scored = score_counties(df)

Author: Aishwarya Sharma
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# Weights must sum to 1.0
WEIGHTS = {
    "clinical_access":        0.25,
    "social_infrastructure":  0.15,
    "economic_security":      0.15,
    "physical_safety":        0.15,
    "digital_access":         0.10,
    "food_security":          0.10,
    "caregiver_proximity":    0.10,
}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def _minmax(series: pd.Series, invert: bool = False) -> pd.Series:
    """Min-max normalize a numeric series into [0, 100]."""
    lo, hi = series.min(), series.max()
    if hi - lo < 1e-9:
        return pd.Series(50, index=series.index)
    scaled = (series - lo) / (hi - lo) * 100
    return 100 - scaled if invert else scaled


def compute_subscores(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the seven domain sub-scores (each 0-100)."""
    out = pd.DataFrame(index=df.index)

    # Clinical Access (higher inputs = better)
    out["clinical_access"] = (
        _minmax(df["primary_care_per_100k"]) * 0.6
        + _minmax(df["home_health_agencies_per_10k_seniors"]) * 0.4
    )

    # Social Infrastructure
    out["social_infrastructure"] = (
        _minmax(df["meals_on_wheels_coverage_pct"]) * 0.5
        + _minmax(df["transit_access_score"]) * 0.5
    )

    # Economic Security (poverty is bad -> invert)
    out["economic_security"] = (
        _minmax(df["senior_poverty_pct"], invert=True) * 0.7
        + _minmax(df["medicare_advantage_pct"]) * 0.3
    )

    # Physical Safety (fall rate is bad -> invert)
    out["physical_safety"] = _minmax(
        df["senior_fall_hospitalizations_per_1k"], invert=True
    )

    # Digital Access
    out["digital_access"] = _minmax(df["broadband_access_pct"])

    # Food Security (insecurity is bad -> invert)
    out["food_security"] = _minmax(df["senior_food_insecurity_pct"], invert=True)

    # Caregiver Proximity (gap is bad -> invert)
    out["caregiver_proximity"] = _minmax(
        df["caregiver_distance_gap_pct"], invert=True
    )

    return out.round(2)


def compute_aipr(subscores: pd.DataFrame) -> pd.Series:
    """Combine sub-scores using WEIGHTS into the composite AIPR Index."""
    score = sum(subscores[k] * w for k, w in WEIGHTS.items())
    return score.round(2)


def label_tier(aipr: pd.Series) -> pd.Series:
    """Bin the AIPR into four readiness tiers."""
    return pd.cut(
        aipr,
        bins=[-0.01, 40, 55, 70, 100.01],
        labels=["Critical", "At risk", "Adequate", "Strong"],
    )


def score_counties(df: pd.DataFrame) -> pd.DataFrame:
    """End-to-end: take raw county features, return scored dataset."""
    subs = compute_subscores(df)
    aipr = compute_aipr(subs)
    scored = pd.concat([df, subs.add_suffix("_score"), aipr.rename("aipr_index")], axis=1)
    scored["readiness_tier"] = label_tier(aipr)
    return scored


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    raw = pd.read_csv(root / "data" / "sample" / "county_sample.csv")
    scored = score_counties(raw)
    out = root / "data" / "processed" / "county_aipr_scored.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    scored.to_csv(out, index=False)
    print(f"Wrote {len(scored):,} scored counties to {out}")
    print("\nTier distribution:")
    print(scored["readiness_tier"].value_counts().sort_index())
    print(f"\nMean AIPR by rurality:")
    print(scored.groupby("rurality")["aipr_index"].mean().round(1).sort_values())


if __name__ == "__main__":
    main()
