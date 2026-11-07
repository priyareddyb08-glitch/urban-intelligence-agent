import os
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from memory import MemoryManager
from agent import analyze_incident, recommend_action

load_dotenv()
ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
INCIDENTS_FILE = DATA_DIR / "hyderabad_road_incidents.csv"
HISTORY_FILE = DATA_DIR / "reported_incidents.json"

st.set_page_config(page_title="Urban Intelligence Agent", page_icon="🚌", layout="wide")

@st.cache_data
def load_sample_data():
    return pd.read_csv(INCIDENTS_FILE)

def load_history():
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_history(items):
    HISTORY_FILE.write_text(json.dumps(items, indent=2), encoding="utf-8")

st.markdown("""
<style>
.main-header {padding: 1.1rem 1.3rem; border-radius: 14px; background: linear-gradient(110deg,#102b46,#176b87); color:white; margin-bottom:1rem;}
.main-header h1 {color:white; margin:0;}
.main-header p {color:#dcecf5; margin:.35rem 0 0 0;}
div[data-testid="stMetric"] {background:#f4f8fb; padding:12px; border-radius:12px; border:1px solid #e3edf3;}
</style>
<div class="main-header">
<h1>🚌 Urban Incident Response & Predictive Intelligence</h1>
<p>Public-transport incident reporting • Persistent memory • Safer route suggestions</p>
</div>
""", unsafe_allow_html=True)

sample = load_sample_data()
history = load_history()
memory = MemoryManager()

with st.sidebar:
    st.header("Project controls")
    st.caption("Hackathon MVP • Hyderabad sample dataset")
    if memory.is_hindsight_enabled:
        st.success("Hindsight: connected")
    else:
        st.warning("Hindsight: demo memory mode")
    st.caption("Add HINDSIGHT_API_KEY and HINDSIGHT_BASE_URL in .env to connect the real Hindsight service.")
    st.divider()
    st.markdown("**Data note**")
    st.caption("The bundled Hyderabad incident records are synthetic demonstration data, not verified live reports.")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "➕ Report incident", "🧠 Agent memory", "🗺️ Incident map"])

# Combine example CSV rows and reports entered in this app
reported_df = pd.DataFrame(history)
if not reported_df.empty:
    reported_df["source"] = "User report"
combined = pd.concat([sample.assign(source="Sample dataset"), reported_df], ignore_index=True, sort=False) if not reported_df.empty else sample.assign(source="Sample dataset")

with tab1:
    st.subheader("🌆 Hyderabad Smart City Intelligence")
    st.caption(
        "AI-assisted incident monitoring, recurring hotspot detection "
        "and historical risk intelligence"
    )

    # Prepare data
    df = combined.copy()

    total = len(df)

    high_risk = int(
        df["severity"].astype(str).str.lower()
        .isin(["high", "critical"]).sum()
    )

    waterlogging = int(
        (df["incident_type"] == "Waterlogging").sum()
    )

    areas = int(df["area"].nunique())

    vehicles = int(df["vehicle_id"].nunique())

    # KPI Dashboard
    st.markdown("### 📊 Live Incident Intelligence")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Incidents", total)
    c2.metric("High Severity", high_risk)
    c3.metric("Waterlogging Reports", waterlogging)
    c4.metric("Affected Areas", areas)

    st.divider()

    # Additional KPI
    st.markdown("### 🚌 Fleet Impact")

    a1, a2 = st.columns(2)

    a1.metric("Vehicles Involved", vehicles)
    a2.metric(
        "Incident Categories",
        df["incident_type"].nunique()
    )

    st.divider()

    # Incident charts
    st.markdown("### 📈 Incident Analytics")

    left, right = st.columns(2)

    with left:
        counts = (
            df["incident_type"]
            .value_counts()
            .rename_axis("Incident Type")
            .reset_index(name="Reports")
        )

        fig = px.bar(
            counts,
            x="Incident Type",
            y="Reports",
            color="Incident Type",
            title="Incidents by Category",
            template="plotly_white"
        )

        fig.update_layout(
            showlegend=False,
            height=350
        )

        st.plotly_chart(fig, use_container_width=True)

    with right:
        area_counts = (
            df.groupby("area")
            .size()
            .reset_index(name="Reports")
            .sort_values("Reports", ascending=False)
        )

        fig = px.bar(
            area_counts,
            x="area",
            y="Reports",
            color="Reports",
            title="Incident Hotspots by Area",
            template="plotly_white"
        )

        fig.update_layout(height=350)

        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Predictive risk intelligence
    st.markdown("### 🔮 Historical Road Risk Intelligence")

    risk_df = df.copy()

    risk_df["severity_points"] = (
        risk_df["severity"]
        .astype(str)
        .str.lower()
        .map({
            "low": 1,
            "medium": 2,
            "high": 4,
            "critical": 6
        })
        .fillna(1)
    )

    risk_df["waterlogging_points"] = (
        risk_df["incident_type"] == "Waterlogging"
    ).astype(int) * 2

    risk = (
        risk_df.groupby("area")
        .agg(
            Reports=("incident_id", "count"),
            Severity_Points=("severity_points", "sum"),
            Waterlogging=("waterlogging_points", "sum")
        )
        .reset_index()
    )

    risk["Risk Score"] = (
        risk["Reports"] * 2
        + risk["Severity_Points"]
        + risk["Waterlogging"]
    )

    def risk_level(score):
        if score >= 20:
            return "High"
        elif score >= 10:
            return "Moderate"
        return "Low"

    risk["Risk Level"] = risk["Risk Score"].apply(risk_level)

    risk = risk.sort_values(
        "Risk Score",
        ascending=False
    )

    fig = px.bar(
        risk,
        x="area",
        y="Risk Score",
        color="Risk Level",
        color_discrete_map={
            "High": "#e53935",
            "Moderate": "#ff9800",
            "Low": "#2e9d65"
        },
        title="Historical Road Risk Ranking",
        template="plotly_white"
    )

    fig.update_layout(height=400)

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        risk[
            ["area", "Reports", "Waterlogging",
             "Risk Score", "Risk Level"]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.info(
        "Risk scores are transparent historical screening indicators "
        "based on incident frequency, severity and waterlogging reports. "
        "They are not live sensor readings or validated future predictions."
    )

    st.divider()

    # Recent reports
    st.markdown("### 🚨 Recent Incident Reports")

    recent = df.sort_values(
        "reported_at",
        ascending=False
    ).head(15)

    st.dataframe(
        recent,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Urban Intelligence Agent | Hyderabad | "
        "Historical incident monitoring and decision support"
    )
with tab2:
    st.subheader("Submit a fleet road-incident report")
    st.write("Enter a report as if it was sent by a bus driver or fleet sensor.")
    with st.form("incident_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            area_options = sorted(sample["area"].dropna().unique().tolist())
            area = st.selectbox("Hyderabad area", area_options + ["Other / not listed"])
            if area == "Other / not listed":
                area = st.text_input("Enter area name", value="Hyderabad")
            incident_type = st.selectbox("Incident type", ["Pothole", "Waterlogging", "Traffic congestion", "Road obstruction"])
            severity = st.select_slider("Severity", options=["Low", "Medium", "High", "Critical"], value="Medium")
        with col2:
            road = st.text_input("Road / landmark", placeholder="e.g. Near metro station")
            reporter = st.text_input("Bus / vehicle ID", value="TSRTC-DEMO-01")
            description = st.text_area("What was observed?", placeholder="Describe the road condition...")
        submitted = st.form_submit_button("Analyze and remember incident", type="primary", use_container_width=True)
    if submitted:
        if not road.strip() or not description.strip():
            st.error("Please enter both a road/landmark and an incident description.")
        else:
            now = datetime.now().isoformat(timespec="seconds")
            item = {
                "incident_id": f"HYD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "reported_at": now, "area": area, "road": road.strip(),
                "incident_type": incident_type, "severity": severity,
                "vehicle_id": reporter.strip(), "description": description.strip(),
                "latitude": None, "longitude": None, "source": "User report"
            }
            past = load_history()
            past.append(item)
            save_history(past)
            st.session_state["latest_report"] = item
            memory.store_incident(item)
            st.success("Incident saved. The agent has processed the report.")
            st.rerun()
    latest = st.session_state.get("latest_report")
    if latest:
        st.divider()
        st.markdown("### Agent analysis")
        prior = memory.recall_incidents(f"{latest['incident_type']} at {latest['area']} {latest['road']}")
        result = analyze_incident(latest, combined, prior)
        st.info(result["summary"])
        st.markdown("**Recommended action**")
        st.write(result["action"])
        st.caption(result["memory_note"])

with tab3:
    st.subheader("Hindsight: what the agent remembers")
    st.write("This page demonstrates the memory loop: retain each incident, recall related history, then make a more informed recommendation.")
    query = st.text_input("Ask about past road incidents", placeholder="Have we seen repeated waterlogging in Kukatpally?")
    if st.button("Recall relevant incidents", type="primary"):
        if query.strip():
            recalled = memory.recall_incidents(query)
            if recalled:
                for i, entry in enumerate(recalled, 1):
                    st.markdown(f"**Memory {i}**")
                    st.write(entry)
            else:
                st.info("No matching memories returned yet. Report an incident first, or try the sample-data search.")
    st.divider()
    st.markdown("**Memory demonstration**")
    st.write("1. Report a waterlogging incident at a location.")
    st.write("2. Report the same or a related incident again.")
    st.write("3. Ask the agent about previous incidents at that location.")
    st.write("4. The agent uses recalled history plus the current report to suggest an action.")
    if st.button("Seed Hindsight with sample incidents"):
        count = memory.seed_from_dataframe(sample)
        st.success(f"Sent {count} sample incident memories to the configured memory backend.")
    if not memory.is_hindsight_enabled:
        st.warning("Demo mode uses a local JSON history file. For judging the Hindsight requirement, configure and demonstrate the actual Hindsight service.")

with tab4:
    st.subheader("🗺️ Hyderabad Smart Incident Hotspots")
    st.caption(
        "Geographical view of reported incidents and recurring road hazards"
    )

    map_df = combined.dropna(
        subset=["latitude", "longitude"]
    ).copy()

    if not map_df.empty:

        # Incident summary
        total_locations = map_df["area"].nunique()
        total_reports = len(map_df)

        c1, c2 = st.columns(2)

        c1.metric("Mapped Incidents", total_reports)
        c2.metric("Affected Areas", total_locations)

        st.divider()

        # Interactive map
        st.markdown("### 📍 Incident Location Map")

        st.map(
            map_df.rename(
                columns={
                    "latitude": "lat",
                    "longitude": "lon"
                }
            )[["lat", "lon"]],
            color="#e53935",
            size=100,
            use_container_width=True
        )

        st.caption(
            "Map markers represent approximate coordinates "
            "from the demonstration dataset."
        )

        st.divider()

        # Hotspot ranking
        st.markdown("### 🔥 Recurring Incident Hotspots")

        hotspots = (
            map_df.groupby(["area", "road"])
            .agg(
                Reports=("incident_id", "count"),
                Incident_Types=("incident_type", "nunique")
            )
            .reset_index()
            .sort_values("Reports", ascending=False)
        )

        st.dataframe(
            hotspots,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        # Incident category breakdown
        st.markdown("### 🚨 Incident Category Breakdown")

        category = (
            map_df["incident_type"]
            .value_counts()
            .reset_index()
        )

        category.columns = ["Incident Type", "Reports"]

        fig = px.pie(
            category,
            names="Incident Type",
            values="Reports",
            hole=0.45,
            title="Geographical Incident Distribution"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:
        st.warning(
            "No geographical coordinates available for incidents."
        )