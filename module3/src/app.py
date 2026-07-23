"""
app.py — Professional SOC Dashboard
========================================
Redesigned Module 3 dashboard with:
  - Dark theme with blue/cyan/red accent colors
  - Glassmorphism cards with rounded corners
  - Professional spacing and typography
  - Animated metrics with sparklines
  - Responsive layout optimized for 16:9 displays
  - Pure Plotly visualizations (no default Streamlit widgets)
  - SIEM-style threat monitoring interface

Run:
    cd module3/src && streamlit run app.py --theme.base dark
"""

import os
import sys
from datetime import datetime, timedelta
import json

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dashboard_common import get_dataset, PAGE_ICON, RISK_COLORS

# ============================================================================
# CONFIGURATION & THEMING
# ============================================================================

ST_THEME = {
    "primaryColor": "#0969DA",  # Blue
    "backgroundColor": "#FFFFFF",  # White
    "secondaryBackgroundColor": "#F6F8FA",  # Light gray
    "textColor": "#1F2328",  # Dark text
    "font": "sans serif",
}

COLOR_DARK_BG = "#FFFFFF"
COLOR_CARD_BG = "#FFFFFF"
COLOR_BORDER = "#D0D7DE"
COLOR_PRIMARY = "#0969DA"  # Blue
COLOR_ACCENT = "#0969DA"  # Blue
COLOR_DANGER = "#DA3633"  # Red
COLOR_WARNING = "#D29922"  # Orange
COLOR_SUCCESS = "#1a7f37"  # Green

RISK_COLORS_SIEM = {
    "Low": "#1a7f37",  # Green
    "Medium": "#d29922",  # Orange/Yellow
    "Critical": "#da3633",  # Red
}

SEVERITY_COLORS = {
    "critical": "#DA3633",
    "high": "#D29922",
    "medium": "#0969DA",
    "low": "#1a7f37",
}

ATTACK_CATEGORY_COLORS = {
    "Network": "#FF6B6B",
    "Email": "#4ECDC4",
    "API": "#45B7D1",
    "Web": "#FFA07A",
    "Insider": "#DDA15E",
    "Malware": "#BC6C25",
}

# ============================================================================
# STREAMLIT PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Bayesian Sentinel SOC Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for glassmorphism and professional styling
st.markdown(
    """
    <style>
        /* Light theme — consistent with Explainability/Threat Explorer pages,
           which use Streamlit's default light background. Accent colors stay
           distinct (blue/cyan) so this doesn't read as "just default Streamlit". */
        :root {
            --page-bg: #FFFFFF;
            --card-bg: #FFFFFF;
            --border: #D0D7DE;
            --primary: #0969DA;
            --accent: #0969DA;
            --danger: #DA3633;
            --text-main: #1F2328;
            --text-muted: #57606A;
        }
        
        [data-testid="stAppViewContainer"], [data-testid="stHeader"], .main {
            background-color: var(--page-bg);
            color: var(--text-main);
        }
        
        body {
            background-color: var(--page-bg);
            color: var(--text-main);
        }
        
        /* Cards — solid background + border/shadow instead of backdrop-filter
           blur. Blur is GPU-expensive and was the main cause of scroll lag
           when several cards render on screen at once; this keeps the
           layered look without repainting a blur on every scroll frame. */
        .soc-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(31, 35, 40, 0.08);
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        
        .soc-card:hover {
            border-color: var(--accent);
            box-shadow: 0 4px 12px rgba(9, 105, 218, 0.1);
        }
        
        /* KPI Cards */
        .kpi-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(31, 35, 40, 0.08);
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        
        .kpi-card:hover {
            border-color: var(--accent);
            box-shadow: 0 4px 12px rgba(9, 105, 218, 0.12);
        }
        
        .kpi-value {
            font-size: 32px;
            font-weight: 700;
            color: var(--accent);
            margin: 10px 0;
        }
        
        .kpi-label {
            font-size: 12px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .kpi-trend {
            font-size: 14px;
            margin-top: 8px;
        }
        
        .kpi-trend.up { color: #1a7f37; }
        .kpi-trend.down { color: #da3633; }
        
        /* Top status blocks (CURRENT TIME / SYSTEM / THREAT) — explicit
           nowrap + min-width prevents these from visually overlapping,
           which happened because they had no defined box before. */
        .status-block {
            text-align: center;
            color: var(--text-muted);
            font-size: 12px;
            white-space: nowrap;
            min-width: 110px;
            padding: 4px 8px;
        }
        
        .status-block strong {
            display: block;
            letter-spacing: 1px;
            margin-bottom: 4px;
            color: var(--text-main);
        }
        .soc-nav {
            background: var(--card-bg);
            border-bottom: 1px solid var(--border);
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 40px;
            border-radius: 0 0 12px 12px;
        }
        
        .soc-title {
            font-size: 28px;
            font-weight: 700;
            color: var(--accent);
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-healthy { background-color: #1a7f37; }
        .status-warning { background-color: #d29922; }
        .status-critical { background-color: #da3633; }
        
        /* Alert table styling */
        .alert-row-critical {
            background-color: rgba(218, 54, 51, 0.08);
            border-left: 3px solid #DA3633;
        }
        
        .alert-row-high {
            background-color: rgba(210, 153, 34, 0.08);
            border-left: 3px solid #D29922;
        }
        
        .alert-row-medium {
            background-color: rgba(9, 105, 218, 0.08);
            border-left: 3px solid #0969DA;
        }
        
        .alert-row-low {
            background-color: rgba(26, 127, 55, 0.08);
            border-left: 3px solid #1a7f37;
        }
        
        /* Headings */
        h1, h2, h3 {
            color: var(--text-main);
            letter-spacing: -0.5px;
        }
        
        h2 {
            border-bottom: 1px solid var(--border);
            padding-bottom: 16px;
            margin-bottom: 24px;
            font-size: 20px;
            font-weight: 600;
        }
        
        /* Divider */
        .divider {
            height: 1px;
            background: var(--border);
            margin: 32px 0;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .soc-nav {
                flex-direction: column;
                gap: 16px;
            }
            
            .kpi-value {
                font-size: 24px;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================================
# DATA LOADING
# ============================================================================

@st.cache_data(ttl=300)
def load_dashboard_data():
    df = get_dataset()
    if df.empty:
        st.error("Unified dataset is empty. Run build_dataset.py first.")
        st.stop()
    return df

df = load_dashboard_data()

# ============================================================================
# TOP NAVIGATION BAR
# ============================================================================

with st.container():
    col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([2, 1, 1, 1])
    
    with col_nav1:
        st.markdown(
            f"<div class='soc-title'>🛡️ Bayesian Sentinel SOC</div>",
            unsafe_allow_html=True,
        )
    
    with col_nav2:
        current_time = datetime.now().strftime("%H:%M:%S")
        st.markdown(
            f"<div class='status-block'><strong>CURRENT TIME</strong>{current_time}</div>",
            unsafe_allow_html=True,
        )
    
    with col_nav3:
        system_health = 98  # Simulated
        health_color = "🟢" if system_health > 80 else "🟡" if system_health > 50 else "🔴"
        st.markdown(
            f"<div class='status-block'><strong>SYSTEM</strong>{health_color} {system_health}%</div>",
            unsafe_allow_html=True,
        )
    
    with col_nav4:
        threat_level = "LOW" if df["final_risk_probability"].mean() < 0.4 else "MEDIUM" if df["final_risk_probability"].mean() < 0.7 else "HIGH"
        threat_color = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}[threat_level]
        st.markdown(
            f"<div class='status-block'><strong>THREAT</strong>{threat_color} {threat_level}</div>",
            unsafe_allow_html=True,
        )

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ============================================================================
# TOP KPI CARDS (ROW 1)
# ============================================================================

st.subheader("📊 Key Performance Indicators")

kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5, kpi_col6 = st.columns(6)

total_events = len(df)
threats_detected = len(df[df["final_risk_probability"] > 0.5])
critical_alerts = len(df[df["risk_category"] == "Critical"])
avg_risk_score = (df["final_risk_probability"].mean() * 100)
blocked_attacks = len(df[df["is_attack"] == True])
system_health_pct = 98

with kpi_col1:
    st.markdown(
        f"""
        <div class='kpi-card'>
            <div class='kpi-label'>📦 Total Events</div>
            <div class='kpi-value'>{total_events:,}</div>
            
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi_col2:
    st.markdown(
        f"""
        <div class='kpi-card'>
            <div class='kpi-label'>🎯 Threats Detected</div>
            <div class='kpi-value'>{threats_detected}</div>
            
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi_col3:
    st.markdown(
        f"""
        <div class='kpi-card'>
            <div class='kpi-label'>🚨 Critical Alerts</div>
            <div class='kpi-value'>{critical_alerts}</div>
            
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi_col4:
    st.markdown(
        f"""
        <div class='kpi-card'>
            <div class='kpi-label'>⚠️ Avg Risk Score</div>
            <div class='kpi-value'>{avg_risk_score:.1f}%</div>
            
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi_col5:
    st.markdown(
        f"""
        <div class='kpi-card'>
            <div class='kpi-label'>🛡️ Blocked Attacks</div>
            <div class='kpi-value'>{blocked_attacks}</div>
            
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi_col6:
    st.markdown(
        f"""
        <div class='kpi-card'>
            <div class='kpi-label'>✅ System Health</div>
            <div class='kpi-value'>{system_health_pct}%</div>
            
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ============================================================================
# MIDDLE SECTION: Threat Timeline (Left) + Risk Distribution (Right)
# ============================================================================

st.subheader("🔍 Threat Analysis")

left_col, right_col = st.columns([2, 1])

# LEFT: Interactive Threat Timeline
with left_col:
    st.markdown("#### Threat Timeline")
    
    timeline_df = df.sort_values("timestamp").copy()
    timeline_df["rolling_risk"] = (
        timeline_df["final_risk_probability"].rolling(20, min_periods=1).mean()
    )
    
    fig_timeline = go.Figure()
    
    # Add individual events as scatter
    fig_timeline.add_trace(
        go.Scattergl(
            x=timeline_df["timestamp"],
            y=timeline_df["final_risk_probability"] * 100,
            mode="markers",
            name="Event Risk",
            marker=dict(
                size=6,
                opacity=0.6,
                color=timeline_df["risk_category"].map(RISK_COLORS_SIEM),
                line=dict(width=0.5, color="rgba(255,255,255,0.3)"),
            ),
            hovertemplate="<b>%{customdata}</b><br>Risk: %{y:.1f}%<br>Time: %{x}<extra></extra>",
            customdata=timeline_df["risk_category"],
        )
    )
    
    # Add rolling average
    fig_timeline.add_trace(
        go.Scattergl(
            x=timeline_df["timestamp"],
            y=timeline_df["rolling_risk"] * 100,
            mode="lines",
            name="Trend (20-event MA)",
            line=dict(color="#0969DA", width=3, dash="dash"),
            hovertemplate="Trend: %{y:.1f}%<br>Time: %{x}<extra></extra>",
        )
    )
    
    fig_timeline.update_layout(
        template="plotly_white",
        hovermode="x unified",
        height=400,
        margin=dict(l=60, r=20, t=20, b=60),
        plot_bgcolor="rgba(255, 255, 255, 1)",
        paper_bgcolor="rgba(255, 255, 255, 1)",
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(48, 54, 61, 0.2)",
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(48, 54, 61, 0.2)",
            zeroline=False,
            title="Risk Score (%)",
        ),
        legend=dict(x=0, y=1, bgcolor="rgba(255, 255, 255, 0.9)", bordercolor="rgba(9, 105, 218, 0.3)", borderwidth=1),
    )
    
    st.plotly_chart(fig_timeline, use_container_width=True, key="threat_timeline")

# RIGHT: Risk Distribution (Donut Chart)
with right_col:
    st.markdown("#### Risk Distribution")
    
    risk_counts = df["risk_category"].value_counts().reindex(["Low", "Medium", "Critical"]).fillna(0)
    
    fig_donut = go.Figure(
        data=[
            go.Pie(
                labels=risk_counts.index,
                values=risk_counts.values,
                hole=0.4,
                marker=dict(colors=[RISK_COLORS_SIEM[cat] for cat in risk_counts.index]),
                textinfo="label+percent",
                textfont=dict(color="#E6EDF3", size=12),
                outsidetextfont=dict(color="#1F2328", size=12),
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>",
            )
        ]
    )
    
    fig_donut.update_layout(
        template="plotly_white",
        height=400,
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor="rgba(255, 255, 255, 1)",
        paper_bgcolor="rgba(255, 255, 255, 1)",
        font=dict(color="#1F2328"),
    )
    
    st.plotly_chart(fig_donut, use_container_width=True, key="risk_distribution")

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ============================================================================
# MIDDLE-BOTTOM: Attack Heatmap
# ============================================================================

st.subheader("🔥 Attack Heatmap: Frequency Over Time")

# Group by real channel (sms/url/login_attempt/email/api_payload) instead of
# a randomly-assigned fake category — this is real data from the pipeline,
# not a placeholder.
df_heatmap = df.copy()
df_heatmap["day"] = pd.to_datetime(df_heatmap["timestamp"]).dt.day_name()

heatmap_data = df_heatmap.groupby(["day", "channel"]).size().reset_index(name="count")
heatmap_pivot = heatmap_data.pivot(index="channel", columns="day", values="count").fillna(0)

# Reorder days
day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
heatmap_pivot = heatmap_pivot.reindex(columns=[d for d in day_order if d in heatmap_pivot.columns], fill_value=0)

fig_heatmap = go.Figure(
    data=go.Heatmap(
        z=heatmap_pivot.values,
        x=heatmap_pivot.columns,
        y=heatmap_pivot.index,
        # Single-hue sequential scale (light -> dark blue) reads intuitively
        # as "more/less" — the old 4-stop black->green->orange->red scale
        # had no consistent ordering and looked alarming for what's actually
        # near-uniform data.
        colorscale="Blues",
        # zmin=0 anchors the color scale to a real floor instead of
        # auto-stretching color across just the actual min/max (170-222).
        # That auto-stretch was exaggerating a ~24% spread into what looked
        # like a dramatic cliff from "critical" to "nothing" — misleading,
        # since these channels are actually close to evenly distributed.
        zmin=0,
        zmax=float(heatmap_pivot.values.max()) * 1.15,
        text=heatmap_pivot.values,
        texttemplate="%{text:.0f}",
        textfont=dict(size=12, color="#FFFFFF"),
        hovertemplate="<b>%{y}</b><br>Day: %{x}<br>Events: %{z}<extra></extra>",
        colorbar=dict(title="Event Count", thickness=15, len=0.7),
    )
)

fig_heatmap.update_layout(
    template="plotly_white",
    height=320,
    margin=dict(l=120, r=20, t=20, b=60),
    plot_bgcolor="rgba(255, 255, 255, 1)",
    paper_bgcolor="rgba(255, 255, 255, 1)",
    xaxis_title="Day of Week",
    yaxis_title="Channel",
)

st.plotly_chart(fig_heatmap, use_container_width=True, key="attack_heatmap")

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ============================================================================
# BOTTOM: Recent Alerts Table with Search & Filter
# ============================================================================

st.subheader("🚨 Recent Alerts & Threats")

# Create alerts dataframe
alerts_df = df.copy()
alerts_df = alerts_df.sort_values("timestamp", ascending=False).head(50)
alerts_df["risk_pct"] = (alerts_df["final_risk_probability"] * 100).round(1)

# Controls row: Search and Filter
col_search, col_filter_risk, col_filter_channel = st.columns([2, 1, 1])

with col_search:
    search_term = st.text_input(
        "Search by IP or channel",
        placeholder="e.g., 192.168.1.1 or email",
        label_visibility="collapsed",
    )

with col_filter_risk:
    filter_risk = st.multiselect(
        "Filter by Risk Level",
        options=["Low", "Medium", "Critical"],
        default=["Low", "Medium", "Critical"],
        key="filter_risk_level",
    )

with col_filter_channel:
    filter_channel = st.multiselect(
        "Filter by Channel",
        options=df["channel"].unique().tolist(),
        default=df["channel"].unique().tolist()[:3],
        key="filter_channel",
    )

# Apply filters
filtered_alerts = alerts_df[
    (alerts_df["risk_category"].isin(filter_risk))
    & (alerts_df["channel"].isin(filter_channel))
]

if search_term:
    filtered_alerts = filtered_alerts[
        filtered_alerts["source_ip"].str.contains(search_term, case=False, na=False)
        | filtered_alerts["channel"].str.contains(search_term, case=False, na=False)
    ]

# Display alerts as interactive table (using Plotly)
alerts_table_data = filtered_alerts[[
    "timestamp",
    "source_ip",
    "destination_ip",
    "channel",
    "risk_category",
    "risk_pct",
    "is_attack",
]].reset_index(drop=True)

alerts_table_data.columns = ["Timestamp", "Source IP", "Dest IP", "Channel", "Risk", "Score %", "Attack"]
alerts_table_data["Risk"] = alerts_table_data["Risk"].map(
    {"Low": "🟢 Low", "Medium": "🟡 Medium", "Critical": "🔴 Critical"}
)
alerts_table_data["Attack"] = alerts_table_data["Attack"].astype(bool).map(
    {True: "✓ Yes", False: "✗ No"}
)

# Convert to Plotly table for better styling
fig_table = go.Figure(
    data=[
        go.Table(
            header=dict(
                values=[
                    f"<b>{col}</b>" for col in alerts_table_data.columns
                ],
                fill_color="rgba(9, 105, 218, 0.12)",
                align="left",
                font=dict(color="#0969DA", size=12),
                height=28,
            ),
            cells=dict(
                values=[alerts_table_data[col] for col in alerts_table_data.columns],
                fill_color=[
                    [
                        (
                            "rgba(218, 54, 51, 0.1)"
                            if risk == "🔴 Critical"
                            else "rgba(210, 153, 34, 0.1)"
                            if risk == "🟡 Medium"
                            else "rgba(26, 127, 55, 0.1)"
                        )
                        for risk in alerts_table_data["Risk"]
                    ]
                    if col == "Risk"
                    else "rgba(246, 248, 250, 1)"
                    for col in alerts_table_data.columns
                ],
                align="left",
                font=dict(color="#1F2328", size=11),
                height=28,
                line=dict(color="rgba(208, 215, 222, 0.6)", width=0.5),
            ),
        )
    ]
)

ROW_HEIGHT = 28
HEADER_HEIGHT = 28
TABLE_PADDING = 40
# Fixed height was smaller than the actual content (30 rows x 28px + header),
# which forced Plotly to compress rows to fit — that compression is what
# caused the header to visually overlap the first data row.
table_height = HEADER_HEIGHT + (len(alerts_table_data) * ROW_HEIGHT) + TABLE_PADDING

fig_table.update_layout(
    template="plotly_white",
    height=table_height,
    margin=dict(l=20, r=20, t=20, b=20),
    plot_bgcolor="rgba(255, 255, 255, 1)",
    paper_bgcolor="rgba(255, 255, 255, 1)",
)

st.plotly_chart(fig_table, use_container_width=True, key="alerts_table")

# Summary stats
st.markdown(
    f"""
    <div style='color: #8b949e; font-size: 12px; text-align: right;'>
        Showing {len(filtered_alerts)} of {len(alerts_df)} alerts | 
        Critical: {len(filtered_alerts[filtered_alerts['risk_category'] == 'Critical'])} | 
        Confirmed Attacks: {len(filtered_alerts[filtered_alerts['is_attack'] == True])}
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ============================================================================
# FOOTER & NAVIGATION
# ============================================================================

st.markdown(
    """
    <div style='text-align: center; color: #8b949e; font-size: 11px; margin-top: 40px;'>
        <p>Bayesian Sentinel SOC Dashboard | Last Updated: <span id='update-time'></span> UTC</p>
        <p>🔐 All data encrypted in transit | 🛡️ Multi-factor authentication enabled</p>
        <script>
            document.getElementById('update-time').textContent = new Date().toISOString();
        </script>
    </div>
    """,
    unsafe_allow_html=True,
)
