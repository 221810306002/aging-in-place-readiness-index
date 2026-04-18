"""
Light-ML layer for the Aging-in-Place Readiness Index project.

Produces two interpretable outputs that a non-technical stakeholder
can reason about in a meeting:

    1. County archetypes via K-means clustering (k=4) on the seven
       domain sub-scores. Each archetype gets a narrative label.

    2. A logistic regression classifying counties as "critical"
       (bottom quartile of AIPR). Coefficients reveal which levers
       matter most.

Outputs saved to data/processed/:
    - county_archetypes.csv
    - regression_coefficients.csv

Author: Aishwarya Sharma
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from score import score_counties

SUBSCORE_COLS = [
    "clinical_access_score",
    "social_infrastructure_score",
    "economic_security_score",
    "physical_safety_score",
    "digital_access_score",
    "food_security_score",
    "caregiver_proximity_score",
]


def cluster_archetypes(scored: pd.DataFrame, k: int = 4, seed: int = 42):
    """Fit K-means on sub-scores and assign an interpretable label."""
    X = scored[SUBSCORE_COLS].values
    km = KMeans(n_clusters=k, random_state=seed, n_init=10)
    scored = scored.copy()
    scored["cluster_id"] = km.fit_predict(X)

    # Describe each cluster by how it deviates from the national average
    centers = pd.DataFrame(km.cluster_centers_, columns=SUBSCORE_COLS)
    national_mean = centers.mean()
    deviations = centers.subtract(national_mean, axis=1)

    labels = {}
    for cid, row in deviations.iterrows():
        # Most relatively-weak and relatively-strong domains for this cluster
        weakest = row.idxmin().replace("_score", "").replace("_", " ")
        strongest = row.idxmax().replace("_score", "").replace("_", " ")
        mean_score = centers.loc[cid].mean()
        if mean_score < 45:
            prefix = "High-risk"
        elif mean_score < 60:
            prefix = "Fragile"
        elif mean_score < 75:
            prefix = "Adequate"
        else:
            prefix = "Strong"
        labels[cid] = (
            f"{prefix} (avg {mean_score:.0f}) \u2014 relatively weak in "
            f"{weakest}, relatively strong in {strongest}"
        )

    scored["archetype"] = scored["cluster_id"].map(labels)
    return scored, centers, labels


def fit_regression(scored: pd.DataFrame):
    """Logistic regression: predict 'critical' counties from sub-scores."""
    y = (scored["readiness_tier"] == "Critical").astype(int)
    X = scored[SUBSCORE_COLS].values
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    clf = LogisticRegression(max_iter=1000, random_state=42)
    clf.fit(Xs, y)

    coefs = pd.DataFrame({
        "feature": SUBSCORE_COLS,
        "coef_standardized": clf.coef_.ravel().round(3),
        "odds_ratio": np.exp(clf.coef_.ravel()).round(3),
    }).sort_values("coef_standardized")

    train_acc = clf.score(Xs, y)
    return coefs, train_acc


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    raw = pd.read_csv(root / "data" / "sample" / "county_sample.csv")
    scored = score_counties(raw)

    scored, centers, labels = cluster_archetypes(scored)
    coefs, acc = fit_regression(scored)

    out_dir = root / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)

    scored.to_csv(out_dir / "county_archetypes.csv", index=False)
    centers.round(2).to_csv(out_dir / "cluster_centers.csv", index=True)
    coefs.to_csv(out_dir / "regression_coefficients.csv", index=False)

    print(f"Cluster labels:")
    for cid, lbl in labels.items():
        n = (scored["cluster_id"] == cid).sum()
        print(f"  [{cid}] {lbl}  ({n} counties)")

    print(f"\nLogistic regression training accuracy: {acc:.1%}")
    print("Standardized coefficients (most protective -> most harmful lack):")
    print(coefs.to_string(index=False))


if __name__ == "__main__":
    main()
