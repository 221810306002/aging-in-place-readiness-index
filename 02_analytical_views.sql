-- =====================================================================
-- Aging-in-Place Readiness Index  |  Analytical views
-- These views power the Tableau / Power BI dashboard and the notebook.
-- =====================================================================

-- ---------------------------------------------------------------------
-- v_county_scorecard
-- One row per county (latest year) with everything the dashboard needs.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_county_scorecard AS
SELECT
    g.county_fips,
    g.county_name,
    g.state,
    g.latitude,
    g.longitude,
    r.rurality_label,
    f.snapshot_year,
    f.pop_65_plus,
    f.pct_65_plus,
    f.aipr_index,
    f.readiness_tier,
    f.archetype_label,
    f.clinical_access_score,
    f.social_infrastructure_score,
    f.economic_security_score,
    f.physical_safety_score,
    f.digital_access_score,
    f.food_security_score,
    f.caregiver_proximity_score
FROM fact_county_year f
JOIN dim_geography    g USING (geography_sk)
JOIN dim_rurality     r USING (rurality_sk)
WHERE f.snapshot_year = (SELECT MAX(snapshot_year) FROM fact_county_year);

-- ---------------------------------------------------------------------
-- v_state_rollup
-- Population-weighted state averages for the state-level view.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_state_rollup AS
SELECT
    g.state,
    COUNT(*)                                                       AS n_counties,
    SUM(f.pop_65_plus)                                             AS total_seniors,
    SUM(f.aipr_index * f.pop_65_plus) / NULLIF(SUM(f.pop_65_plus),0) AS weighted_aipr,
    SUM(CASE WHEN f.readiness_tier = 'Critical' THEN f.pop_65_plus ELSE 0 END) AS seniors_in_critical_counties,
    ROUND(
        100.0 * SUM(CASE WHEN f.readiness_tier = 'Critical' THEN f.pop_65_plus ELSE 0 END)
             / NULLIF(SUM(f.pop_65_plus), 0)
    , 1) AS pct_seniors_in_critical_counties
FROM fact_county_year f
JOIN dim_geography    g USING (geography_sk)
WHERE f.snapshot_year = (SELECT MAX(snapshot_year) FROM fact_county_year)
GROUP BY g.state
ORDER BY pct_seniors_in_critical_counties DESC;

-- ---------------------------------------------------------------------
-- v_archetype_profile
-- Cluster profile for the "four archetypes" slide / dashboard tile.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_archetype_profile AS
SELECT
    f.archetype_label,
    COUNT(*)                                 AS n_counties,
    SUM(f.pop_65_plus)                       AS total_seniors,
    ROUND(AVG(f.aipr_index),           1)    AS avg_aipr,
    ROUND(AVG(f.clinical_access_score),1)    AS avg_clinical_access,
    ROUND(AVG(f.social_infrastructure_score),1) AS avg_social_infra,
    ROUND(AVG(f.economic_security_score),1)  AS avg_econ_security,
    ROUND(AVG(f.physical_safety_score), 1)   AS avg_physical_safety,
    ROUND(AVG(f.digital_access_score),  1)   AS avg_digital_access,
    ROUND(AVG(f.food_security_score),   1)   AS avg_food_security,
    ROUND(AVG(f.caregiver_proximity_score),1) AS avg_caregiver_proximity
FROM fact_county_year f
WHERE f.snapshot_year = (SELECT MAX(snapshot_year) FROM fact_county_year)
GROUP BY f.archetype_label
ORDER BY avg_aipr;

-- ---------------------------------------------------------------------
-- v_intervention_worksheet
-- For each critical county: which sub-score is farthest below national mean?
-- This is the "what to fix first" view a state Medicaid officer would use.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_intervention_worksheet AS
WITH national_means AS (
    SELECT
        AVG(clinical_access_score)        AS nm_clinical,
        AVG(social_infrastructure_score)  AS nm_social,
        AVG(economic_security_score)      AS nm_econ,
        AVG(physical_safety_score)        AS nm_safety,
        AVG(digital_access_score)         AS nm_digital,
        AVG(food_security_score)          AS nm_food,
        AVG(caregiver_proximity_score)    AS nm_caregiver
    FROM fact_county_year
    WHERE snapshot_year = (SELECT MAX(snapshot_year) FROM fact_county_year)
),
gaps AS (
    SELECT
        g.county_fips, g.county_name, g.state, f.pop_65_plus, f.aipr_index,
        (f.clinical_access_score        - nm.nm_clinical)  AS gap_clinical,
        (f.social_infrastructure_score  - nm.nm_social)    AS gap_social,
        (f.economic_security_score      - nm.nm_econ)      AS gap_econ,
        (f.physical_safety_score        - nm.nm_safety)    AS gap_safety,
        (f.digital_access_score         - nm.nm_digital)   AS gap_digital,
        (f.food_security_score          - nm.nm_food)      AS gap_food,
        (f.caregiver_proximity_score    - nm.nm_caregiver) AS gap_caregiver
    FROM fact_county_year f
    JOIN dim_geography    g USING (geography_sk)
    CROSS JOIN national_means nm
    WHERE f.readiness_tier = 'Critical'
      AND f.snapshot_year = (SELECT MAX(snapshot_year) FROM fact_county_year)
)
SELECT
    county_fips, county_name, state, pop_65_plus, aipr_index,
    LEAST(gap_clinical, gap_social, gap_econ, gap_safety,
          gap_digital, gap_food, gap_caregiver) AS largest_gap_value,
    CASE LEAST(gap_clinical, gap_social, gap_econ, gap_safety,
               gap_digital, gap_food, gap_caregiver)
        WHEN gap_clinical  THEN 'Clinical access'
        WHEN gap_social    THEN 'Social infrastructure'
        WHEN gap_econ      THEN 'Economic security'
        WHEN gap_safety    THEN 'Physical safety'
        WHEN gap_digital   THEN 'Digital access'
        WHEN gap_food      THEN 'Food security'
        WHEN gap_caregiver THEN 'Caregiver proximity'
    END AS top_intervention_domain
FROM gaps
ORDER BY aipr_index ASC;
