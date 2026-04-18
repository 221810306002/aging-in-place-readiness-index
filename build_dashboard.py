"""
Build a self-contained interactive HTML dashboard for the
Aging-in-Place Readiness Index project.

Uses Plotly with CDN mode so the output is a single .html file that can
be uploaded to GitHub Pages, Netlify, or attached to a resume.

Output:
    dashboard/dashboard.html

Author: Aishwarya Sharma
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parent.parent


_PLOTLY_INCLUDED = False


def _fig_to_html(fig: go.Figure, div_id: str) -> str:
    # First figure includes Plotly inline so the whole dashboard is one
    # portable file; subsequent figures reuse the same runtime.
    global _PLOTLY_INCLUDED
    include = "inline" if not _PLOTLY_INCLUDED else False
    _PLOTLY_INCLUDED = True
    return fig.to_html(
        include_plotlyjs=include, full_html=False, div_id=div_id,
        config={"displayModeBar": False, "responsive": True},
    )


def build():
    df = pd.read_csv(ROOT / "data" / "processed" / "county_archetypes.csv")

    # ---- KPI strip ---------------------------------------------------
    total_counties = len(df)
    total_seniors = int(df["pop_65_plus"].sum())
    critical_counties = int((df["readiness_tier"] == "Critical").sum())
    seniors_in_critical = int(
        df.loc[df["readiness_tier"] == "Critical", "pop_65_plus"].sum()
    )
    pct_at_risk = 100 * seniors_in_critical / max(total_seniors, 1)

    kpis = [
        ("Counties analyzed", f"{total_counties:,}"),
        ("Seniors covered",   f"{total_seniors/1e6:.1f} M"),
        ("Critical counties", f"{critical_counties:,}"),
        ("Seniors in critical counties", f"{pct_at_risk:.1f}%"),
    ]

    # ---- Chart 1: AIPR distribution by rurality ----------------------
    fig1 = px.box(
        df, x="rurality", y="aipr_index", color="rurality",
        category_orders={"rurality": ["Urban", "Suburban", "Small town", "Rural"]},
        color_discrete_sequence=px.colors.sequential.Teal,
        points="outliers",
        title="AIPR distribution by rurality",
        labels={"aipr_index": "AIPR Index (0\u2013100)", "rurality": ""},
    )
    fig1.update_layout(
        showlegend=False, height=380,
        paper_bgcolor="white", plot_bgcolor="#f7f9fb",
        margin=dict(l=40, r=20, t=60, b=40),
    )

    # ---- Chart 2: Tier counts ---------------------------------------
    tier_order = ["Critical", "At risk", "Adequate", "Strong"]
    tier_counts = df["readiness_tier"].value_counts().reindex(tier_order).fillna(0)
    fig2 = px.bar(
        x=tier_counts.index, y=tier_counts.values,
        color=tier_counts.index,
        color_discrete_map={
            "Critical": "#C0504D", "At risk": "#E8A33D",
            "Adequate": "#4F81BD", "Strong": "#2E8B57",
        },
        title="Counties by readiness tier",
        labels={"x": "", "y": "Number of counties"},
    )
    fig2.update_layout(
        showlegend=False, height=380,
        paper_bgcolor="white", plot_bgcolor="#f7f9fb",
        margin=dict(l=40, r=20, t=60, b=40),
    )

    # ---- Chart 3: Archetype radar -----------------------------------
    archetype_cols = [
        "clinical_access_score", "social_infrastructure_score",
        "economic_security_score", "physical_safety_score",
        "digital_access_score", "food_security_score",
        "caregiver_proximity_score",
    ]
    profile = df.groupby("archetype")[archetype_cols].mean()
    # Shorten legend labels
    profile.index = [a.split(" \u2014 ")[0] for a in profile.index]
    labels = [c.replace("_score", "").replace("_", " ").title() for c in archetype_cols]

    fig3 = go.Figure()
    palette = ["#1F4E79", "#2E75B6", "#C0504D", "#E8A33D"]
    for i, (name, row) in enumerate(profile.iterrows()):
        vals = row.tolist()
        fig3.add_trace(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=labels + [labels[0]],
            fill="toself",
            name=name,
            line=dict(color=palette[i % len(palette)], width=2),
            opacity=0.55,
        ))
    fig3.update_layout(
        title="County archetypes (K-means, k=4): domain profile",
        polar=dict(radialaxis=dict(range=[0, 100], showticklabels=True)),
        height=480, paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
        margin=dict(l=40, r=40, t=80, b=80),
    )

    # ---- Chart 4: State rollup --------------------------------------
    state = df.groupby("state").agg(
        avg_aipr=("aipr_index", "mean"),
        seniors=("pop_65_plus", "sum"),
        critical_counties=("readiness_tier", lambda s: (s == "Critical").sum()),
    ).reset_index()
    state = state.sort_values("avg_aipr").head(20)

    fig4 = px.bar(
        state, x="avg_aipr", y="state", orientation="h",
        color="avg_aipr",
        color_continuous_scale="RdYlGn",
        range_color=[20, 80],
        title="20 lowest-AIPR states (sample data)",
        labels={"avg_aipr": "Average AIPR Index", "state": ""},
        hover_data={"seniors": ":,", "critical_counties": True, "avg_aipr": ":.1f"},
    )
    fig4.update_layout(
        height=560, paper_bgcolor="white", plot_bgcolor="#f7f9fb",
        coloraxis_showscale=False,
        margin=dict(l=40, r=20, t=60, b=40),
    )

    # ---- Chart 5: Caregiver gap vs AIPR scatter ---------------------
    fig5 = px.scatter(
        df, x="caregiver_distance_gap_pct", y="aipr_index",
        color="rurality",
        size="pop_65_plus",
        size_max=28,
        opacity=0.75,
        title="Where caregivers are far, readiness drops",
        labels={
            "caregiver_distance_gap_pct": "% of seniors with nearest adult child > 1 hr away",
            "aipr_index": "AIPR Index",
        },
        category_orders={"rurality": ["Urban", "Suburban", "Small town", "Rural"]},
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig5.update_layout(
        height=480, paper_bgcolor="white", plot_bgcolor="#f7f9fb",
        margin=dict(l=40, r=20, t=60, b=40),
    )

    # ---- Assemble HTML ----------------------------------------------
    kpi_html = "".join(
        f'<div class="kpi"><div class="kpi-v">{v}</div>'
        f'<div class="kpi-l">{l}</div></div>'
        for l, v in kpis
    )

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Aging-in-Place Readiness Index \u2014 Dashboard</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<style>
  :root {{
    --ink:#1F4E79; --ink2:#2E75B6; --bg:#f4f6fa; --card:#ffffff;
    --muted:#6b7280; --rose:#C0504D;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family: -apple-system, BlinkMacSystemFont,"Segoe UI", Roboto, Helvetica, Arial, sans-serif; background:var(--bg); color:#1f2937; }}
  header {{ background:linear-gradient(135deg,#1F4E79,#2E75B6); color:white; padding:36px 48px 28px; }}
  header .eyebrow {{ font-size:12px; letter-spacing:2px; text-transform:uppercase; opacity:.75; }}
  header h1 {{ margin:6px 0 4px; font-size:34px; font-weight:700; }}
  header p  {{ margin:0; opacity:.85; max-width:820px; line-height:1.55; }}
  main {{ padding:24px 48px 48px; max-width:1400px; margin:0 auto; }}
  .kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin:18px 0 28px; }}
  .kpi {{ background:var(--card); border-radius:12px; padding:18px 20px; box-shadow:0 1px 2px rgba(0,0,0,.05); border-left:4px solid var(--ink2); }}
  .kpi-v {{ font-size:28px; font-weight:700; color:var(--ink); }}
  .kpi-l {{ font-size:12px; color:var(--muted); margin-top:4px; text-transform:uppercase; letter-spacing:1px; }}
  .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
  .card {{ background:var(--card); border-radius:12px; padding:12px; box-shadow:0 1px 2px rgba(0,0,0,.05); }}
  .full {{ grid-column: 1 / -1; }}
  .note {{ font-size:13px; color:var(--muted); padding:14px 20px; line-height:1.55; background:#eef3f8; border-left:3px solid var(--ink2); border-radius:6px; margin:24px 0 6px; }}
  footer {{ margin-top:28px; font-size:12px; color:var(--muted); text-align:center; }}
  @media (max-width:900px) {{
    .kpis {{ grid-template-columns:repeat(2,1fr); }}
    .grid {{ grid-template-columns:1fr; }}
    header, main {{ padding-left:20px; padding-right:20px; }}
  }}
</style>
</head>
<body>
<header>
  <div class="eyebrow">Data Analyst Portfolio Project</div>
  <h1>Aging-in-Place Readiness Index</h1>
  <p>A county-level view of whether older adults in the United States can reasonably live independently \u2014 combining clinical supply, social infrastructure, economic security, physical safety, digital access, food security, and caregiver proximity into a single 0\u2013100 score.</p>
</header>
<main>
  <div class="note"><strong>Demo note.</strong> This dashboard is built on 500 synthetic counties that preserve realistic distributions and relationships. Swap <code>data/sample/county_sample.csv</code> for real ingested data (see <code>src/ingest.py</code>) to produce the production version.</div>
  <div class="kpis">{kpi_html}</div>
  <div class="grid">
    <div class="card">{_fig_to_html(fig1, "f1")}</div>
    <div class="card">{_fig_to_html(fig2, "f2")}</div>
    <div class="card full">{_fig_to_html(fig3, "f3")}</div>
    <div class="card">{_fig_to_html(fig4, "f4")}</div>
    <div class="card">{_fig_to_html(fig5, "f5")}</div>
  </div>
  <footer>Built by Aishwarya Sharma \u00b7 Data from CDC, HRSA, USDA, U.S. Census (synthetic stand-in in this demo) \u00b7 MIT License</footer>
</main>
</body>
</html>
"""

    out = ROOT / "dashboard" / "dashboard.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Wrote dashboard to {out} ({out.stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    build()
