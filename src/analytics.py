from __future__ import annotations

import sqlite3

import pandas as pd


class NetworkAnalytics:
    def __init__(self, connection: sqlite3.Connection):
        self.conn = connection

    def calculate_site_kpis(self) -> pd.DataFrame:
        query = """
        SELECT site_id,
          ROUND(AVG(uptime_status) * 100, 2) AS uptime_sla_pct,
          ROUND(AVG(latency_ms), 2) AS avg_latency_ms,
          ROUND(AVG(packet_loss_pct), 2) AS avg_packet_loss_pct,
          ROUND(AVG(100.0 * bandwidth_usage_mbps / bandwidth_capacity_mbps), 2) AS avg_bandwidth_util_pct,
          SUM(is_incident) AS total_incidents
        FROM device_telemetry GROUP BY site_id ORDER BY uptime_sla_pct ASC
        """
        return pd.read_sql_query(query, self.conn)

    def get_hourly_trends(self, site_id: str | None = None) -> pd.DataFrame:
        if site_id:
            query = """
            SELECT strftime('%Y-%m-%d %H:00:00', timestamp) AS hour_bucket,
              AVG(latency_ms) AS avg_latency, AVG(packet_loss_pct) AS avg_packet_loss,
              AVG(100.0 * bandwidth_usage_mbps / bandwidth_capacity_mbps) AS avg_utilization
            FROM device_telemetry WHERE site_id = ? GROUP BY hour_bucket ORDER BY hour_bucket
            """
            return pd.read_sql_query(query, self.conn, params=[site_id])
        query = """
        SELECT strftime('%Y-%m-%d %H:00:00', timestamp) AS hour_bucket,
          AVG(latency_ms) AS avg_latency, AVG(packet_loss_pct) AS avg_packet_loss,
          AVG(100.0 * bandwidth_usage_mbps / bandwidth_capacity_mbps) AS avg_utilization
        FROM device_telemetry GROUP BY hour_bucket ORDER BY hour_bucket
        """
        return pd.read_sql_query(query, self.conn)
