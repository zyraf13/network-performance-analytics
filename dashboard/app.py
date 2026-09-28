from pathlib import Path
import sqlite3
import joblib
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data/network_metrics.db"
MODEL = ROOT / "src/risk_model.pkl"

st.set_page_config(page_title="ISP Network Reliability", layout="wide")
st.title("ISP Network Reliability Dashboard")
st.caption("Synthetic telemetry • SLA monitoring • next-interval incident risk")

@st.cache_data
def load_data():
    with sqlite3.connect(DB) as conn:
        return pd.read_sql_query("SELECT * FROM device_telemetry", conn, parse_dates=["timestamp"])

df = load_data()
sites = st.sidebar.multiselect("Sites", sorted(df.site_id.unique()), default=sorted(df.site_id.unique()))
filtered = df[df.site_id.isin(sites)].copy()
if filtered.empty:
    st.warning("Select at least one site.")
    st.stop()
filtered["utilization_pct"] = 100 * filtered.bandwidth_usage_mbps / filtered.bandwidth_capacity_mbps

kpi = st.columns(4)
kpi[0].metric("Uptime SLA", f"{filtered.uptime_status.mean() * 100:.2f}%")
kpi[1].metric("Avg latency", f"{filtered.latency_ms.mean():.1f} ms")
kpi[2].metric("Avg packet loss", f"{filtered.packet_loss_pct.mean():.2f}%")
kpi[3].metric("Incidents", f"{filtered.is_incident.sum():,}")

summary = filtered.groupby("site_id", as_index=False).agg(uptime_sla=("uptime_status", lambda x: 100 * x.mean()), avg_latency=("latency_ms", "mean"), incidents=("is_incident", "sum"))
st.plotly_chart(px.bar(summary, x="site_id", y="uptime_sla", color="avg_latency", title="SLA uptime by site", text_auto=".2f"), use_container_width=True)

hourly = filtered.set_index("timestamp").resample("1h").agg(latency_ms=("latency_ms", "mean"), packet_loss_pct=("packet_loss_pct", "mean")).reset_index()
st.plotly_chart(px.line(hourly, x="timestamp", y=["latency_ms", "packet_loss_pct"], title="Hourly degradation trend"), use_container_width=True)

left, right = st.columns(2)
with left:
    st.plotly_chart(px.box(filtered, x="site_id", y="utilization_pct", title="Bandwidth utilization"), use_container_width=True)
with right:
    incidents = filtered[filtered.is_incident == 1].groupby(["site_id", "device_type"], as_index=False).size()
    st.plotly_chart(px.bar(incidents, x="site_id", y="size", color="device_type", barmode="group", title="Incidents by device type"), use_container_width=True)

st.subheader("Next-interval incident risk")
if MODEL.exists():
    bundle = joblib.load(MODEL)
    risk_input = filtered[["latency_ms", "packet_loss_pct", "utilization_pct", "cpu_utilization_pct"]].rename(columns={"utilization_pct": "bandwidth_util_pct"})
    filtered["risk_score"] = bundle["model"].predict_proba(risk_input[bundle["features"]])[:, 1]
    risk = filtered.groupby(["site_id", "device_id"], as_index=False).agg(max_risk=("risk_score", "max"), avg_cpu=("cpu_utilization_pct", "mean"), avg_loss=("packet_loss_pct", "mean")).sort_values("max_risk", ascending=False)
    st.dataframe(risk.style.format({"max_risk": "{:.1%}", "avg_cpu": "{:.1f}%", "avg_loss": "{:.2f}%"}), use_container_width=True, hide_index=True)
else:
    st.info("Run `python src/ml_model.py` first.")
