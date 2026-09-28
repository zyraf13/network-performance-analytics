import sqlite3

import pandas as pd

from src.analytics import NetworkAnalytics


def test_site_kpis_and_parameterized_trend_query():
    conn = sqlite3.connect(":memory:")
    pd.DataFrame([
        {"timestamp": "2026-01-01 00:00:00", "site_id": "SITE-01", "device_id": "R1", "device_type": "Router", "uptime_status": 1, "latency_ms": 10, "packet_loss_pct": 0, "bandwidth_usage_mbps": 50, "bandwidth_capacity_mbps": 100, "cpu_utilization_pct": 20, "is_incident": 0},
    ]).to_sql("device_telemetry", conn, index=False)
    analytics = NetworkAnalytics(conn)
    assert analytics.calculate_site_kpis().iloc[0]["uptime_sla_pct"] == 100
    assert len(analytics.get_hourly_trends("SITE-01")) == 1
