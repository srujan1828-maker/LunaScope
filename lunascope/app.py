"""LunaScope: Lunar Mission Window, Horizon & Contingency Navigator.

NASA Space Apps 2026 "Lunar Landing Site Navigator" Challenge.
Architectural stack: Pure Python + Streamlit + Plotly + Vectorized NumPy/SciPy core.
"""

from datetime import datetime, timezone, timedelta
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# Configure sys.path so core and plugins can be imported seamlessly
_APP_DIR = Path(__file__).resolve().parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

from core.projections import latlon_to_xy, xy_to_latlon, great_circle_distance, R_MOON
from core.synthetic_data import load_candidate_sites, CANDIDATE_SITES_METADATA
from core.raycaster import compute_horizon_mask, interpolate_horizon
from core.ephemeris import (
    get_topocentric_sun,
    get_topocentric_earth,
    get_sun_trajectory_series,
    get_earth_libration_series,
    SOLAR_ANGULAR_RADIUS_DEG,
    EARTH_ANGULAR_RADIUS_DEG,
)
from core.visibility import (
    calculate_fractional_solar_illumination,
    calculate_dte_status,
    evaluate_site_timeline,
)
from core.contingency import evaluate_contingency
from plugins.dispersion_monte_carlo import run_dispersion_monte_carlo

# -----------------------------------------------------------------------------
# Streamlit App Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="LunaScope | Lunar Mission Navigator",
    page_icon="🌖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Dark Aerospace CSS
st.markdown(
    """
    <style>
    /* Dark Aerospace Palette */
    .stApp {
        background-color: #0B0F19;
        color: #E2E8F0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
    }
    
    /* Header styling */
    .telemetry-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        background: linear-gradient(135deg, #00F0FF 0%, #3B82F6 50%, #A855F7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.15rem;
    }
    .telemetry-subtitle {
        color: #94A3B8;
        font-size: 0.95rem;
        margin-bottom: 1.2rem;
    }
    
    /* Provenance Badges */
    .badge-published {
        display: inline-block;
        background: rgba(59, 130, 246, 0.2);
        color: #60A5FA;
        border: 1px solid rgba(59, 130, 246, 0.5);
        border-radius: 4px;
        padding: 1px 6px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-left: 4px;
    }
    .badge-derived {
        display: inline-block;
        background: rgba(168, 85, 247, 0.2);
        color: #C084FC;
        border: 1px solid rgba(168, 85, 247, 0.5);
        border-radius: 4px;
        padding: 1px 6px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-left: 4px;
    }
    .badge-assumed {
        display: inline-block;
        background: rgba(245, 158, 11, 0.2);
        color: #FBBF24;
        border: 1px solid rgba(245, 158, 11, 0.5);
        border-radius: 4px;
        padding: 1px 6px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-left: 4px;
    }
    
    /* Status Cards */
    .card-pass {
        background: linear-gradient(180deg, rgba(16, 185, 129, 0.12) 0%, rgba(16, 185, 129, 0.04) 100%);
        border: 1px solid #10B981;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    .card-fail {
        background: linear-gradient(180deg, rgba(239, 68, 68, 0.12) 0%, rgba(239, 68, 68, 0.04) 100%);
        border: 1px solid #EF4444;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    .metric-label {
        font-size: 0.82rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Cached Data Loaders
# -----------------------------------------------------------------------------
@st.cache_data
def get_sites() -> Tuple[pd.DataFrame, bool]:
    return load_candidate_sites()

@st.cache_data
def get_cached_horizon(x0: float, y0: float, z0: float, mast_h: float, site_id: str):
    return compute_horizon_mask(
        x0=x0,
        y0=y0,
        z0=z0,
        mast_height=mast_h,
        use_cache=True,
        cache_key=site_id,
    )

df_sites, is_synthetic_db = get_sites()

# -----------------------------------------------------------------------------
# 1. Sidebar Controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image(
        "https://images.unsplash.com/photo-1614728894747-a83421e2b9c9?w=300&auto=format&fit=crop&q=80",
        width="stretch",
    )
    st.markdown("### 🎛️ Mission Navigation Controls")

    # Audience Mode Toggle
    audience_mode = st.radio(
        "Audience Mode",
        options=["Mission Planner (Engineering)", "Educator / Public (Guided)"],
        index=0,
        help="Switch between technical telemetry and guided educational explanations.",
    )
    is_planner = audience_mode == "Mission Planner (Engineering)"

    st.markdown("---")

    # Primary Site Selector
    site_names = df_sites["name"].tolist()
    primary_site_name = st.selectbox(
        "Primary Landing Candidate",
        options=site_names,
        index=0,
        help="Target candidate site for Artemis III surface sortie.",
    )
    primary_row = df_sites[df_sites["name"] == primary_site_name].iloc[0]
    primary_id = str(primary_row["site_id"])

    # Target Exploration Year
    target_year = st.selectbox(
        "Target Campaign Year",
        options=list(range(2025, 2033)),
        index=1,  # 2026 default
        help="Model year from Wueller et al. (2026) multi-year solar illumination dataset.",
    )

    # Required Consecutive Illumination Days
    required_consecutive_days = st.slider(
        "Required Consecutive Days",
        min_value=6.0,
        max_value=15.0,
        value=10.0,
        step=0.5,
        help="Minimum uninterrupted continuous sunlight window for surface sortie power.",
    )

    # Mast Height Slider
    mast_height = st.slider(
        "Lander Mast Height (m)",
        min_value=1.0,
        max_value=15.0,
        value=3.0,
        step=0.5,
        help="Elevation of solar arrays/optical sensors above local ground surface [Assumed].",
    )

    # DTE Clearance Margin
    dte_margin_deg = st.slider(
        "DTE Clearance Margin (°)",
        min_value=0.5,
        max_value=3.0,
        value=1.0,
        step=0.25,
        help="Topographic angular buffer to prevent multipath RF fading [Assumed].",
    )

    st.markdown("---")
    # Date / Time window scrubber
    base_date = datetime(target_year, 1, 15, 12, 0, tzinfo=timezone.utc)
    day_offset = st.slider(
        "Mission Elapsed Time (Days from Southern Summer Solstice)",
        min_value=0.0,
        max_value=29.5,
        value=5.0,
        step=0.25,
        help="Scrub through one full synodic lunar day (~29.53 Earth days).",
    )
    current_sim_dt = base_date + timedelta(days=day_offset)
    st.caption(f"🕒 UTC Epoch: **{current_sim_dt.strftime('%Y-%b-%d %H:%M UTC')}**")

    # Data Source Notice
    if is_synthetic_db:
        st.info("ℹ️ Running in **Deterministic Synthetic Mode** (Wueller 2026 / LOLA fallback enabled).")

# -----------------------------------------------------------------------------
# Contingency Evaluation Computation
# -----------------------------------------------------------------------------
contingency_results = evaluate_contingency(
    df_sites=df_sites,
    primary_site_id=primary_id,
    target_year=target_year,
    required_consecutive_days=required_consecutive_days,
    min_dte_pct=48.0,
    max_slope_deg=8.0,
)

primary_eval = contingency_results["primary_evaluation"]
backups = contingency_results["backup_candidates"]
top_backup = backups[0] if backups else None

# Precompute 360 Horizon for Primary and Top Backup
p_az, p_horiz, p_metrics = get_cached_horizon(
    x0=float(primary_row["x_m"]),
    y0=float(primary_row["y_m"]),
    z0=float(primary_row["elevation_m"]),
    mast_h=mast_height,
    site_id=primary_id,
)

b_row = df_sites[df_sites["site_id"] == top_backup["site_id"]].iloc[0] if top_backup else primary_row
b_az, b_horiz, b_metrics = get_cached_horizon(
    x0=float(b_row["x_m"]),
    y0=float(b_row["y_m"]),
    z0=float(b_row["elevation_m"]),
    mast_h=mast_height,
    site_id=str(b_row["site_id"]),
)

# Ephemeris current positions
cur_sun_az, cur_sun_el = get_topocentric_sun(float(primary_row["lat_deg"]), float(primary_row["lon_deg"]), current_sim_dt)
cur_earth_az, cur_earth_el = get_topocentric_earth(float(primary_row["lat_deg"]), float(primary_row["lon_deg"]), current_sim_dt)

# Header banner
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown('<div class="telemetry-title">🌔 LunaScope: Lunar Mission Window & Horizon Navigator</div>', unsafe_allow_html=True)
    st.markdown('<div class="telemetry-subtitle">Artemis III Candidate Landing Site Analysis &bull; Topographic Horizon Raycasting &bull; Contingency Matcher</div>', unsafe_allow_html=True)
with col_h2:
    st.markdown(
        """
        <div style="text-align: right; padding-top: 10px;">
            <span class="badge-published">[Assumed] Demonstration inputs</span>
            <span class="badge-derived">[Derived] LunaScope</span>
            <span class="badge-assumed">[Assumed] Config</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# Top Row: (Col 1: Polar Site Map | Col 2: Primary vs Backup Contingency Card)
# -----------------------------------------------------------------------------
st.warning("Demonstration only: synthetic site metrics, procedural terrain, approximate astronomy, and statistical compatibility scores. No verified landing-safety assessment or NASA live feed.")
st.markdown("---")
row1_col1, row1_col2 = st.columns([1, 1], gap="medium")

with row1_col1:
    st.markdown(f"#### 🗺️ South Pole Stereographic Site Map <span class='badge-published'>[Reference only]</span>", unsafe_allow_html=True)
    if not is_planner:
        st.caption("Positions of 15 candidate landing sites around the lunar south pole (85°S to 90°S). Green sites meet your consecutive daylight requirement.")

    # Create Polar Stereographic Map using Plotly
    all_evals = contingency_results["all_evals_lookup"] = {e["site_id"]: e for e in contingency_results["all_evaluations"]}
    
    map_fig = go.Figure()

    # Draw South Pole concentric latitude rings
    for lat_ring in [-89.5, -89.0, -88.0, -86.0]:
        ring_x, ring_y = [], []
        for theta in np.linspace(0, 2 * np.pi, 100):
            r = 2.0 * R_MOON * np.tan(np.radians(90.0 + lat_ring) / 2.0)
            ring_x.append(r * np.sin(theta))
            ring_y.append(r * np.cos(theta))
        map_fig.add_trace(go.Scatter(
            x=ring_x, y=ring_y,
            mode="lines",
            line=dict(color="rgba(148, 163, 184, 0.2)", width=1, dash="dot"),
            hoverinfo="skip",
            showlegend=False,
        ))

    # Add Sites
    passed_x, passed_y, passed_names, passed_text = [], [], [], []
    failed_x, failed_y, failed_names, failed_text = [], [], [], []

    for _, s in df_sites.iterrows():
        sid = s["site_id"]
        ev = all_evals.get(sid, {})
        is_pass = ev.get("passed", False)
        c_days = ev.get("consecutive_days", 0.0)
        txt = (
            f"<b>{s['name']}</b><br>"
            f"Lat/Lon: {s['lat_deg']:.2f}°, {s['lon_deg']:.2f}°<br>"
            f"Consec Days ({target_year}): {c_days:.1f}d<br>"
            f"Annual Illum: {s['annual_illum_pct']:.1f}%<br>"
            f"Status: {'PASS' if is_pass else 'FAIL'}"
        )
        if is_pass:
            passed_x.append(s["x_m"])
            passed_y.append(s["y_m"])
            passed_names.append(s["name"])
            passed_text.append(txt)
        else:
            failed_x.append(s["x_m"])
            failed_y.append(s["y_m"])
            failed_names.append(s["name"])
            failed_text.append(txt)

    # Plot Passed sites (Green)
    map_fig.add_trace(go.Scatter(
        x=passed_x, y=passed_y,
        mode="markers+text",
        name=f"Qualified (≥{required_consecutive_days:.1f}d)",
        marker=dict(size=12, color="#10B981", symbol="circle", line=dict(color="#FFFFFF", width=1.5)),
        text=passed_names,
        textposition="top center",
        textfont=dict(size=10, color="#E2E8F0"),
        hoverinfo="text",
        hovertext=passed_text,
    ))

    # Plot Failed sites (Crimson)
    map_fig.add_trace(go.Scatter(
        x=failed_x, y=failed_y,
        mode="markers+text",
        name=f"Constrained (<{required_consecutive_days:.1f}d)",
        marker=dict(size=11, color="#EF4444", symbol="x", line=dict(color="#FFFFFF", width=1.5)),
        text=failed_names,
        textposition="top center",
        textfont=dict(size=9, color="#94A3B8"),
        hoverinfo="text",
        hovertext=failed_text,
    ))

    # Highlight Primary Site (Cyan Diamond)
    map_fig.add_trace(go.Scatter(
        x=[primary_row["x_m"]], y=[primary_row["y_m"]],
        mode="markers",
        name="Selected Primary",
        marker=dict(size=20, color="rgba(0, 240, 255, 0.4)", symbol="diamond", line=dict(color="#00F0FF", width=3)),
        hoverinfo="skip",
    ))

    # South Pole Center Marker
    map_fig.add_trace(go.Scatter(
        x=[0], y=[0],
        mode="markers+text",
        name="South Pole (90°S)",
        marker=dict(size=8, color="#F59E0B", symbol="cross"),
        text=["South Pole"],
        textposition="bottom center",
        textfont=dict(size=10, color="#F59E0B"),
        hoverinfo="skip",
    ))

    map_fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15, 23, 42, 0.6)",
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(title="Stereographic X (meters)", showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
        yaxis=dict(title="Stereographic Y (meters)", showgrid=True, gridcolor="rgba(255,255,255,0.08)", scaleanchor="x", scaleratio=1),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5, font=dict(size=11)),
        height=380,
    )
    st.plotly_chart(map_fig, width="stretch")


with row1_col2:
    st.markdown(f"#### 🎯 Primary Candidate & Backup Matcher <span class='badge-derived'>[Derived]</span>", unsafe_allow_html=True)
    if not is_planner:
        st.caption("Automated decision logic assessing mission feasibility and ranking optimal secondary landing sites.")

    # Primary Site Status Card
    p_passed = primary_eval["passed"]
    card_class = "card-pass" if p_passed else "card-fail"
    status_icon = "✅ PASS" if p_passed else "⚠️ CONTINGENCY REQUIRED (FAIL)"
    status_color = "#10B981" if p_passed else "#EF4444"

    st.markdown(
        f"""
        <div class="{card_class}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-weight: 800; font-size: 1.15rem; color: #FFFFFF;">{primary_eval['name']}</span>
                <span style="font-weight: 800; font-size: 0.95rem; color: {status_color};">{status_icon}</span>
            </div>
            <div style="font-size: 0.88rem; color: #CBD5E1; margin-bottom: 8px;">
                <b>Flight Rule Evaluation:</b> {primary_eval['reasons'][0]}
            </div>
            <div style="display: flex; gap: 24px; font-size: 0.82rem; color: #94A3B8;">
                <div>Continuous Daylight: <b style="color: #FFFFFF;">{primary_eval['consecutive_days']:.1f} d</b> <span class="badge-published">[Assumed]</span></div>
                <div>Surplus Margin: <b style="color: {status_color};">{primary_eval['margin_days']:+.1f} d</b> <span class="badge-derived">[Der]</span></div>
                <div>Annual DTE: <b style="color: #FFFFFF;">{primary_eval['annual_dte_pct']:.1f}%</b> <span class="badge-published">[Assumed]</span></div>
                <div>Mean Slope: <b style="color: #FFFFFF;">{primary_eval['avg_slope_deg']:.1f}°</b> <span class="badge-published">[Assumed]</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Ranked Backup Candidates Table
    st.markdown("##### 🥈 Recommended Backup Landing Sites")
    backup_rows = []
    for b in backups[:4]:
        b_pass_tag = "✅ Pass" if b["passed"] else "⚠️ Marginal"
        backup_rows.append({
            "Rank": f"#{b['rank']}",
            "Candidate Site": b["name"],
            "Status": b_pass_tag,
            f"Consec Days ({target_year})": f"{b['consecutive_days']:.1f} d",
            "Daylight Margin": f"{b['margin_days']:+.1f} d",
            "DTE Link": f"{b['annual_dte_pct']:.1f}%",
            "Slope": f"{b['avg_slope_deg']:.1f}°",
        })
    df_backup_table = pd.DataFrame(backup_rows)
    st.dataframe(df_backup_table, hide_index=True, width="stretch")

    if top_backup:
        st.caption(f"💡 **Top Secondary Option:** {top_backup['name']} ({top_backup['recommendation']})")

# -----------------------------------------------------------------------------
# Middle Row: 360° Panoramic Horizon Skyline Viewer (Full Width)
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    f"""
    <div style="display: flex; justify-content: space-between; align-items: baseline;">
        <h4 style="margin-bottom: 4px;">🌄 360° Panoramic Horizon Skyline & Celestial Ephemeris</h4>
        <div>
            <span class="badge-derived">[Derived] Raycaster H(α)</span>
            <span class="badge-published">[Assumed] Procedural terrain</span>
            <span class="badge-assumed">[Assumed] Mast Height {mast_height:.1f}m</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not is_planner:
    st.caption("Imagine standing on the Moon looking in all directions (0° North to 360°). The terrain blocks the low-grazing Sun and Earth whenever they dip below the ridge silhouettes.")

# Compute ephemeris trajectories
sun_series = get_sun_trajectory_series(
    obs_lat_deg=float(primary_row["lat_deg"]),
    obs_lon_deg=float(primary_row["lon_deg"]),
    start_dt=base_date,
    n_steps=360,
    total_hours=708.7,
)

earth_series = get_earth_libration_series(
    obs_lat_deg=float(primary_row["lat_deg"]),
    obs_lon_deg=float(primary_row["lon_deg"]),
    start_dt=base_date,
    n_days=28.0,
    n_steps=140,
)

# Plotly 360 Horizon Chart
fig_skyline = go.Figure()

# Primary Site Terrain Horizon Silhouette (Dark Grey Fill with Cyan Edge)
fig_skyline.add_trace(go.Scatter(
    x=p_az,
    y=p_horiz,
    mode="lines",
    name=f"{primary_row['name']} Horizon (Primary)",
    line=dict(color="#00F0FF", width=2.5),
    fill="tozeroy",
    fillcolor="rgba(15, 23, 42, 0.85)",
    hoverinfo="x+y",
    hovertemplate="Azimuth: %{x:.1f}°<br>Horizon Elevation: %{y:.2f}°<extra></extra>",
))

# Top Backup Site Terrain Silhouette (Dotted Amber Line for comparison)
if top_backup:
    fig_skyline.add_trace(go.Scatter(
        x=b_az,
        y=b_horiz,
        mode="lines",
        name=f"{b_row['name']} Horizon (Backup #{top_backup['rank']})",
        line=dict(color="#F59E0B", width=1.5, dash="dash"),
        hoverinfo="x+y",
        hovertemplate="Backup Horizon: %{y:.2f}°<extra></extra>",
    ))

# 0° Geometric Horizon Line
fig_skyline.add_trace(go.Scatter(
    x=[0, 360], y=[0, 0],
    mode="lines",
    name="Geometric 0° Horizontal Plane",
    line=dict(color="rgba(255, 255, 255, 0.25)", width=1, dash="dot"),
    hoverinfo="skip",
))

# Sun 360° Trajectory Curve across Synodic Month
fig_skyline.add_trace(go.Scatter(
    x=sun_series["azimuth_deg"],
    y=sun_series["elevation_deg"],
    mode="lines",
    name="Sun 360° Trajectory (1 Synodic Month)",
    line=dict(color="#FCD34D", width=2),
    hoverinfo="x+y",
    hovertemplate="Sun Azimuth: %{x:.1f}°<br>Sun Elevation: %{y:.2f}°<extra></extra>",
))

# Earth Optical Libration Loop (Closed Lissajous Wobble)
fig_skyline.add_trace(go.Scatter(
    x=earth_series["azimuth_deg"],
    y=earth_series["elevation_deg"],
    mode="lines",
    name="Earth Optical Libration Loop (±6.7° Lat, ±7.9° Lon)",
    line=dict(color="#38BDF8", width=2, dash="dashdot"),
    hoverinfo="x+y",
    hovertemplate="Earth Azimuth: %{x:.1f}°<br>Earth Elevation: %{y:.2f}°<extra></extra>",
))

# Current Sun Position Marker
p_horiz_at_sun = interpolate_horizon(cur_sun_az, p_az, p_horiz)
sun_illuminated = cur_sun_el >= p_horiz_at_sun
sun_marker_color = "#FCD34D" if sun_illuminated else "#78716C"

fig_skyline.add_trace(go.Scatter(
    x=[cur_sun_az],
    y=[cur_sun_el],
    mode="markers+text",
    name=f"Current Sun ({cur_sun_el:.2f}°)",
    marker=dict(size=14, color=sun_marker_color, line=dict(color="#FFFFFF", width=2)),
    text=["☀️ Sun Now"],
    textposition="top center",
    textfont=dict(color="#FCD34D", size=11),
    hoverinfo="text",
    hovertext=f"Current Sun<br>Azimuth: {cur_sun_az:.1f}°<br>Elevation: {cur_sun_el:.2f}°<br>Horizon at Azimuth: {p_horiz_at_sun:.2f}°",
))

# Current Earth Position Marker
p_horiz_at_earth = interpolate_horizon(cur_earth_az, p_az, p_horiz)
dte_active = (cur_earth_el - p_horiz_at_earth) >= dte_margin_deg
earth_marker_color = "#38BDF8" if dte_active else "#EF4444"

fig_skyline.add_trace(go.Scatter(
    x=[cur_earth_az],
    y=[cur_earth_el],
    mode="markers+text",
    name=f"Current Earth ({cur_earth_el:.2f}°)",
    marker=dict(size=13, color=earth_marker_color, symbol="circle", line=dict(color="#FFFFFF", width=2)),
    text=["🌍 Earth Now"],
    textposition="top center",
    textfont=dict(color="#38BDF8", size=11),
    hoverinfo="text",
    hovertext=f"Current Earth<br>Azimuth: {cur_earth_az:.1f}°<br>Elevation: {cur_earth_el:.2f}°<br>Horizon: {p_horiz_at_earth:.2f}°<br>RF Link: {'ONLINE' if dte_active else 'BLOCKED'}",
))

fig_skyline.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(11, 15, 25, 0.9)",
    margin=dict(l=40, r=40, t=20, b=40),
    xaxis=dict(
        title="Compass Azimuth (° from North: 0° N, 90° E, 180° S, 270° W)",
        range=[0, 360],
        tickmode="linear",
        tick0=0,
        dtick=30,
        showgrid=True,
        gridcolor="rgba(255, 255, 255, 0.08)",
    ),
    yaxis=dict(
        title="Topocentric Elevation (° above Local Horizontal)",
        range=[-5, 15],
        showgrid=True,
        gridcolor="rgba(255, 255, 255, 0.08)",
        zeroline=True,
        zerolinecolor="rgba(255, 255, 255, 0.2)",
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5,
        font=dict(size=10),
    ),
    height=400,
)

st.plotly_chart(fig_skyline, width="stretch")

# -----------------------------------------------------------------------------
# Bottom Row: Tabs (Timeline, Monte Carlo 250-Run Stress Test, Transparency)
# -----------------------------------------------------------------------------
st.markdown("---")
tab1, tab2, tab3 = st.tabs([
    "📈 Illumination & DTE Comms Timeline",
    "🎲 250-Run Monte Carlo Landing Ellipse Stress Test",
    "📚 Data Transparency & Citations",
])

# -----------------------------------------------------------------------------
# TAB 1: Dual-Track Synchronized Timeline
# -----------------------------------------------------------------------------
with tab1:
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: baseline;">
            <h5>Synchronized Solar Penumbra Fraction f(t) & Direct-to-Earth Link Availability</h5>
            <div>
                <span class="badge-derived">[Derived] Fractional Penumbra r⊙=0.266°</span>
                <span class="badge-assumed">[Assumed] DTE Clearance Margin {dte_margin_deg:.1f}°</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    timeline_hours = np.linspace(0, 336, 168)  # 14 days, 2-hour increments
    t_start = current_sim_dt

    p_tl_sun_az, p_tl_sun_el = [], []
    p_tl_earth_az, p_tl_earth_el = [], []
    for h in timeline_hours:
        t_sample = t_start + timedelta(hours=float(h))
        s_az, s_el = get_topocentric_sun(float(primary_row["lat_deg"]), float(primary_row["lon_deg"]), t_sample)
        e_az, e_el = get_topocentric_earth(float(primary_row["lat_deg"]), float(primary_row["lon_deg"]), t_sample)
        p_tl_sun_az.append(s_az)
        p_tl_sun_el.append(s_el)
        p_tl_earth_az.append(e_az)
        p_tl_earth_el.append(e_el)

    p_timeline = evaluate_site_timeline(
        sun_azimuth_deg=np.array(p_tl_sun_az),
        sun_elevation_deg=np.array(p_tl_sun_el),
        earth_azimuth_deg=np.array(p_tl_earth_az),
        earth_elevation_deg=np.array(p_tl_earth_el),
        horizon_azimuths_deg=p_az,
        horizon_elevations_deg=p_horiz,
        dte_margin_deg=dte_margin_deg,
    )

    # Subplots: Row 1 = Solar fraction f(t), Row 2 = DTE RF Link
    fig_tl = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=[
            f"Fractional Solar Disk Exposure f(t) ∈ [0, 1] — {primary_row['name']}",
            f"Direct-to-Earth Link Margin (Clearance above Horizon ≥ {dte_margin_deg:.1f}°)",
        ]
    )

    # Trace 1: Solar Penumbra Fraction
    fig_tl.add_trace(
        go.Scatter(
            x=timeline_hours / 24.0,
            y=p_timeline["solar_fraction"] * 100.0,
            mode="lines",
            name="Solar Illumination %",
            line=dict(color="#FCD34D", width=2),
            fill="tozeroy",
            fillcolor="rgba(252, 211, 77, 0.15)",
            hovertemplate="Day +%{x:.1f}: %{y:.1f}% Solar Disk<extra></extra>",
        ),
        row=1, col=1,
    )

    # Trace 2: DTE Clearance Margin
    earth_clearance = p_timeline["earth_clearance_deg"]
    fig_tl.add_trace(
        go.Scatter(
            x=timeline_hours / 24.0,
            y=earth_clearance,
            mode="lines",
            name="Earth Clearance Margin (°)",
            line=dict(color="#38BDF8", width=2),
            hovertemplate="Day +%{x:.1f}: %{y:.2f}° Clearance<extra></extra>",
        ),
        row=2, col=1,
    )

    # Margin threshold line
    fig_tl.add_trace(
        go.Scatter(
            x=[0, 14], y=[dte_margin_deg, dte_margin_deg],
            mode="lines",
            name=f"Minimum RF Margin ({dte_margin_deg:.1f}°)",
            line=dict(color="#EF4444", width=1.5, dash="dash"),
            hoverinfo="skip",
        ),
        row=2, col=1,
    )

    fig_tl.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15, 23, 42, 0.6)",
        margin=dict(l=40, r=40, t=30, b=30),
        height=360,
        showlegend=False,
    )
    fig_tl.update_xaxes(title="Elapsed Days from Epoch", row=2, col=1)
    fig_tl.update_yaxes(title="Illumination %", range=[0, 105], row=1, col=1)
    fig_tl.update_yaxes(title="Clearance (°)", row=2, col=1)

    st.plotly_chart(fig_tl, width="stretch")

# -----------------------------------------------------------------------------
# TAB 2: Vectorized 250-Run Monte Carlo Landing Ellipse Stress Test
# -----------------------------------------------------------------------------
with tab2:
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: baseline;">
            <h5>Vectorized 250-Point Landing Ellipse Dispersion Verification</h5>
            <div>
                <span class="badge-derived">[Derived] Vectorized NumPy &lt;0.2s</span>
                <span class="badge-assumed">[Assumed] Dispersion Radius 100m</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not is_planner:
        st.caption("A lander cannot target an exact millimeter point in space; guidance dispersion scatters touchdowns across a 100-meter radius ellipse. This simulation stress-tests 250 randomized touchdowns to ensure slopes and shadows do not jeopardize the mission.")

    col_mc_ctrl1, col_mc_ctrl2, col_mc_ctrl3 = st.columns([1, 1, 1])
    with col_mc_ctrl1:
        mc_radius = st.slider("Landing Ellipse Radius (m)", 50.0, 250.0, 100.0, 10.0)
    with col_mc_ctrl2:
        mc_max_slope = st.slider("Critical Tip-Over Slope (°)", 6.0, 15.0, 10.0, 0.5)
    with col_mc_ctrl3:
        mc_seed = st.number_input("Deterministic Random Seed", min_value=1, max_value=9999, value=42)

    # Execute Monte Carlo
    mc_results = run_dispersion_monte_carlo(
        site_x=float(primary_row["x_m"]),
        site_y=float(primary_row["y_m"]),
        site_base_elevation=float(primary_row["elevation_m"]),
        base_annual_illum_pct=float(primary_row["annual_illum_pct"]),
        base_annual_dte_pct=float(primary_row["annual_dte_pct"]),
        base_avg_slope_deg=float(primary_row["avg_slope_deg"]),
        dispersion_radius_m=mc_radius,
        n_samples=250,
        seed=int(mc_seed),
        max_safe_slope_deg=mc_max_slope,
    )

    mc_summary = mc_results["summary"]

    # Metrics Summary Row
    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
    m_col1.metric("Illustrative compatibility score", f"{mc_summary['survival_probability_pct']}%", delta=f"{mc_summary['n_pass']} / 250 Pass")
    m_col2.metric("Nominal Safe Landings", f"{mc_summary['n_pass']}", "Pass (Green)")
    m_col3.metric("Marginal Touchdowns", f"{mc_summary['n_marginal']}", "Caution (Yellow)")
    m_col4.metric("Hazardous Aborts", f"{mc_summary['n_fail']}", "Fail (Red)")
    m_col5.metric("Simulation Runtime", f"{mc_summary['runtime_ms']:.1f} ms", "< 200 ms Target")

    # Plot Scatter of 250 Landing Points
    fig_mc = go.Figure()

    # Draw 100m dispersion ellipse boundary ring
    theta_ring = np.linspace(0, 2 * np.pi, 100)
    fig_mc.add_trace(go.Scatter(
        x=mc_radius * np.cos(theta_ring),
        y=mc_radius * np.sin(theta_ring),
        mode="lines",
        name=f"Landing 3σ Boundary ({mc_radius:.0f}m)",
        line=dict(color="rgba(0, 240, 255, 0.6)", width=2, dash="dash"),
        hoverinfo="skip",
    ))

    # Split by status
    status_arr = np.array(mc_results["status"])
    color_map = {"PASS": "#10B981", "MARGINAL": "#F59E0B", "FAIL": "#EF4444"}

    for st_name, col_code in color_map.items():
        mask = status_arr == st_name
        if np.any(mask):
            sub_dx = mc_results["dx_m"][mask]
            sub_dy = mc_results["dy_m"][mask]
            sub_slope = mc_results["slope_deg"][mask]
            sub_illum = mc_results["illumination_pct"][mask]
            sub_dte = mc_results["dte_pct"][mask]
            sub_reasons = [mc_results["fail_reasons"][i] for i in np.where(mask)[0]]

            hover_text = [
                f"<b>Touchdown Point #{i+1}</b><br>"
                f"Offset: ΔX={dx:.1f}m, ΔY={dy:.1f}m (dist={np.sqrt(dx**2+dy**2):.1f}m)<br>"
                f"Slope: {slp:.1f}°<br>"
                f"Illum: {ilm:.1f}%<br>"
                f"DTE: {dt:.1f}%<br>"
                f"Status: <b>{st_name}</b><br>"
                f"Note: {rsn}"
                for i, (dx, dy, slp, ilm, dt, rsn) in enumerate(zip(sub_dx, sub_dy, sub_slope, sub_illum, sub_dte, sub_reasons))
            ]

            fig_mc.add_trace(go.Scatter(
                x=sub_dx,
                y=sub_dy,
                mode="markers",
                name=f"{st_name} ({np.sum(mask)})",
                marker=dict(size=9, color=col_code, line=dict(color="#FFFFFF", width=1)),
                hoverinfo="text",
                hovertext=hover_text,
            ))

    # Center target marker
    fig_mc.add_trace(go.Scatter(
        x=[0], y=[0],
        mode="markers",
        name="Target Landing Center",
        marker=dict(size=14, color="#FFFFFF", symbol="cross"),
        hoverinfo="skip",
    ))

    fig_mc.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15, 23, 42, 0.6)",
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(title="Cross-Track Offset ΔX (meters)", scaleanchor="y", scaleratio=1, showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
        yaxis=dict(title="Along-Track Offset ΔY (meters)", showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        height=420,
    )

    st.plotly_chart(fig_mc, width="stretch")

# -----------------------------------------------------------------------------
# TAB 3: Data Transparency & Scientific Citations
# -----------------------------------------------------------------------------
with tab3:
    st.markdown("##### 🔬 Scientific Methodology & Dataset Provenance")
    st.markdown(
        """
        Published references are listed below for context. This prototype uses synthetic demonstration inputs; reference citations do not authenticate the displayed values.

        1. **Wueller et al. (2026) Candidate Landing Sites Dataset** <span class="badge-published">[Reference only]</span>
           - **Citation:** Wueller, L., et al. (2026). *Assessing Potential Landing Sites With Favorable Illumination and Accessible, Potentially Volatile-Rich Permanently Shadowed Regions Within Artemis Candidate Landing Regions*. Zenodo Record 17084058.
           - Reference only. The hard-coded 2025–2032 values displayed here have not been verified against the publication.

        2. **NASA Lunar Orbiter Laser Altimeter (LOLA) DEM** <span class="badge-published">[Reference only]</span>
           - Potential source only. Current horizons use procedural terrain; no verified LOLA data is bundled.
           - Curvature drop correction $\\Delta Z_{curve} = \\frac{d^2}{2 R_{Moon}}$ ($R_{Moon} = 1,737.4\\text{ km}$) ensures realistic horizon masks.

        3. **Approximate analytical astronomy (no JPL kernel integration)** <span class="badge-derived">[Derived]</span>
           - Topocentric Sun sweep ($360^\\circ$ synodic cycle) and Earth optical libration loops ($\\pm 6.7^\\circ$ latitude, $\\pm 7.9^\\circ$ longitude).
           - Fractional solar penumbra formula accounts for the $0.266^\\circ$ solar disk radius.

        4. **Scope Boundaries & Engineering Disclaimers:**
           - **Geometric Line-of-Sight vs. Electrical Link Budget:** LunaScope calculates strict geometric line-of-sight clearance. Practical surface power balance also depends on solar panel conversion efficiency, regolith dust accumulation, solar incidence angle, and battery depth-of-discharge.
           - **RF Link Budget:** Communication clearance uses a configured multipath margin (default $1.0^\\circ$). Real-world missions must also evaluate X-band/S-band transceiver gain, DSN ground station elevations, and atmospheric path loss.
        """,
        unsafe_allow_html=True,
    )
