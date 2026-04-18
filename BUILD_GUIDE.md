# Dashboard Build Guide

This folder contains a **self-contained, interactive HTML dashboard** built with Plotly, plus instructions for recreating the same views in Tableau or Power BI.

## 1. Plotly HTML (ships in this repo)

`dashboard.html` is a single file that loads Plotly from CDN. You can:

- Open it locally by double-clicking.
- Host it free on **GitHub Pages** — enable Pages on this repo and point it to `/dashboard`.
- Host it on **Netlify** or **Vercel** by dragging the `dashboard/` folder into a new site.

Rebuild it any time the underlying data changes:

```bash
python src/build_dashboard.py
```

## 2. Tableau Public version

**Data source.** Connect to `data/processed/county_archetypes.csv`.

**Suggested worksheets.**

| Sheet | Marks | Shelves |
|---|---|---|
| National map | Filled map on `county_fips` | Color = `aipr_index`, Detail = `county_name`, Tooltip = all sub-scores |
| Tier strip | Bar | Rows = `readiness_tier`, Columns = COUNT, Color = tier palette |
| Archetype radar | Line (polar trick with `TC_Angle`) | One series per `archetype` |
| State rollup | Horizontal bar | Rows = `state`, Columns = AVG(`aipr_index`), sorted ascending |
| Caregiver scatter | Scatter | X = `caregiver_distance_gap_pct`, Y = `aipr_index`, Size = `pop_65_plus`, Color = `rurality` |
| Intervention worksheet | Text table | Rows = `county_name`, Columns = lowest sub-score, filter to Critical tier |

Assemble these into a dashboard called **"Aging-in-Place Readiness Index"**, publish to Tableau Public, and paste the URL into the project README.

## 3. Power BI version

Same data source. Use the following visuals:

1. **Filled map** — `county_fips` (format as State-County) + `aipr_index` color scale.
2. **Slicer row** — `state`, `rurality`, `readiness_tier`.
3. **Matrix** — rows = `readiness_tier`, columns = `rurality`, values = count and population.
4. **Radial chart (custom visual)** — archetype profile.
5. **Page navigation** — one page for "National", one for "State deep-dive", one for "Intervention worksheet".

Publish to the Power BI service and embed the link in the README.

## 4. What a hiring manager should see in 5 seconds

When someone lands on the dashboard they should immediately read:

- One headline number (e.g. "12 % of U.S. seniors live in a 'Critical' county").
- A map that tells them where the problem concentrates.
- A clear "what do I do about it" tile (the intervention worksheet).

Everything else is supporting evidence. Keep the story first; keep the charts quiet.
