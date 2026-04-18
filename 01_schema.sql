-- =====================================================================
-- Aging-in-Place Readiness Index  |  Star schema
-- Target:  Postgres 14+  |  portable to SQL Server / SQLite with minor
--          syntax changes (INTEGER vs INT, TIMESTAMP vs DATETIME).
-- =====================================================================
-- Design notes:
--   * One fact table (fact_county_year) holds the annual snapshot.
--   * Three conformed dimensions: geography, rurality, data-source.
--   * Surrogate keys (*_sk) are assigned in the ETL layer.
--   * All sub-score and index columns live in the fact table because
--     they change year over year.
-- =====================================================================

DROP TABLE IF EXISTS fact_county_year CASCADE;
DROP TABLE IF EXISTS dim_geography CASCADE;
DROP TABLE IF EXISTS dim_rurality CASCADE;
DROP TABLE IF EXISTS dim_source CASCADE;

-- ---------------------------------------------------------------------
-- Dimension: geography (county-level identity)
-- ---------------------------------------------------------------------
CREATE TABLE dim_geography (
    geography_sk        SERIAL       PRIMARY KEY,
    county_fips         CHAR(5)      NOT NULL UNIQUE,
    county_name         VARCHAR(80)  NOT NULL,
    state               CHAR(2)      NOT NULL,
    census_region       VARCHAR(20),
    latitude            NUMERIC(9,6),
    longitude           NUMERIC(9,6)
);

-- ---------------------------------------------------------------------
-- Dimension: rurality classification
-- ---------------------------------------------------------------------
CREATE TABLE dim_rurality (
    rurality_sk         SERIAL       PRIMARY KEY,
    rurality_label      VARCHAR(20)  NOT NULL UNIQUE,   -- Urban / Suburban / Small town / Rural
    ruc_code_min        INT,
    ruc_code_max        INT,
    description         TEXT
);

-- ---------------------------------------------------------------------
-- Dimension: data source (lineage for audit / recompute)
-- ---------------------------------------------------------------------
CREATE TABLE dim_source (
    source_sk           SERIAL       PRIMARY KEY,
    source_name         VARCHAR(80)  NOT NULL UNIQUE,
    source_url          VARCHAR(300),
    last_refreshed_at   TIMESTAMP
);

-- ---------------------------------------------------------------------
-- Fact: one row per (county, year)
-- ---------------------------------------------------------------------
CREATE TABLE fact_county_year (
    fact_sk                                SERIAL       PRIMARY KEY,
    geography_sk                           INT          NOT NULL REFERENCES dim_geography(geography_sk),
    rurality_sk                            INT          NOT NULL REFERENCES dim_rurality(rurality_sk),
    snapshot_year                          INT          NOT NULL,

    -- Raw inputs
    total_population                       INT,
    pop_65_plus                            INT,
    pct_65_plus                            NUMERIC(5,2),
    pct_seniors_living_alone               NUMERIC(5,2),
    broadband_access_pct                   NUMERIC(5,2),
    primary_care_per_100k                  NUMERIC(6,2),
    home_health_agencies_per_10k_seniors   NUMERIC(5,2),
    meals_on_wheels_coverage_pct           NUMERIC(5,2),
    transit_access_score                   NUMERIC(5,2),
    senior_poverty_pct                     NUMERIC(5,2),
    medicare_advantage_pct                 NUMERIC(5,2),
    senior_food_insecurity_pct             NUMERIC(5,2),
    senior_fall_hospitalizations_per_1k    NUMERIC(5,2),
    caregiver_distance_gap_pct             NUMERIC(5,2),

    -- Derived sub-scores (0-100)
    clinical_access_score                  NUMERIC(5,2),
    social_infrastructure_score            NUMERIC(5,2),
    economic_security_score                NUMERIC(5,2),
    physical_safety_score                  NUMERIC(5,2),
    digital_access_score                   NUMERIC(5,2),
    food_security_score                    NUMERIC(5,2),
    caregiver_proximity_score              NUMERIC(5,2),

    -- Composite index and tier
    aipr_index                             NUMERIC(5,2),
    readiness_tier                         VARCHAR(12),  -- Critical / At risk / Adequate / Strong
    cluster_id                             INT,
    archetype_label                        VARCHAR(120),

    CONSTRAINT uq_county_year UNIQUE (geography_sk, snapshot_year)
);

CREATE INDEX idx_fact_year   ON fact_county_year (snapshot_year);
CREATE INDEX idx_fact_tier   ON fact_county_year (readiness_tier);
CREATE INDEX idx_fact_aipr   ON fact_county_year (aipr_index);
