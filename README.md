# Raw data directory

Drop raw downloads here. Files in this folder are gitignored except for
this README.

## Fetch commands

```bash
# Census ACS (requires free API key from api.census.gov/data/key_signup.html)
export CENSUS_API_KEY=your_key_here
python -m src.ingest --source census --year 2022 --out data/raw/census_acs.parquet

# HRSA AHRF
wget https://data.hrsa.gov/DataDownload/AHRF/AHRF_2023-2024.zip -P data/raw/
unzip data/raw/AHRF_2023-2024.zip -d data/raw/

# USDA Food Access Research Atlas
wget https://www.ers.usda.gov/webdocs/DataFiles/80591/FoodAccessResearchAtlasData2019.xlsx -P data/raw/

# IRS county-to-county migration
wget https://www.irs.gov/pub/irs-soi/countyinflow2122.csv -P data/raw/
wget https://www.irs.gov/pub/irs-soi/countyoutflow2122.csv -P data/raw/
```

Once files are in place, run `python -m src.ingest --all` to produce
`data/processed/county_master.csv`.
