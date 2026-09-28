from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS device_telemetry (
    timestamp TEXT NOT NULL,
    site_id TEXT NOT NULL,
    device_id TEXT NOT NULL,
    device_type TEXT NOT NULL,
    uptime_status INTEGER NOT NULL CHECK (uptime_status IN (0, 1)),
    latency_ms REAL NOT NULL,
    packet_loss_pct REAL NOT NULL,
    bandwidth_usage_mbps REAL NOT NULL,
    bandwidth_capacity_mbps REAL NOT NULL,
    cpu_utilization_pct REAL NOT NULL,
    is_incident INTEGER NOT NULL CHECK (is_incident IN (0, 1))
)
"""


def create_database(db_path: str | Path, csv_path: str | Path) -> int:
    db_path, csv_path = Path(db_path), Path(csv_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    required = {"timestamp", "site_id", "device_id", "is_incident"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    with sqlite3.connect(db_path) as conn:
        conn.execute("DROP TABLE IF EXISTS device_telemetry")
        conn.execute(TABLE_SCHEMA)
        df.to_sql("device_telemetry", conn, if_exists="append", index=False)
    return len(df)


def connect(db_path: str | Path) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    count = create_database(root / "data/network_metrics.db", root / "data/raw_network_telemetry.csv")
    print(f"Loaded {count:,} records into SQLite")
