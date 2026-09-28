from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


def generate_synthetic_telemetry(days: int = 14, num_sites: int = 5, seed: int = 42) -> pd.DataFrame:
    """Generate reproducible 15-minute ISP telemetry with realistic degradation."""
    if days < 1 or num_sites < 1:
        raise ValueError("days and num_sites must be positive")
    rng = np.random.default_rng(seed)
    sites = [f"SITE-{i:02d}" for i in range(1, num_sites + 1)]
    end_time = datetime.now().replace(second=0, microsecond=0)
    timestamps = pd.date_range(end=end_time, start=end_time - timedelta(days=days), freq="15min")
    records: list[dict] = []
    for site in sites:
        for index in range(1, 4):
            device_type = "Router" if index == 1 else "Access Point"
            device_id = f"{site}-{device_type[:3].upper()}-{index:02d}"
            capacity = 1000.0 if device_type == "Router" else 300.0
            degradation = 1.8 if site == "SITE-03" else 1.0
            for ts in timestamps:
                peak = 13 <= ts.hour <= 21
                latency = max(2.0, rng.normal(25 if not peak else 65, 5 if not peak else 15) * degradation)
                loss = max(0.0, rng.exponential(0.5 if not peak else 1.5) * degradation)
                usage = np.clip(rng.normal(capacity * (0.4 if not peak else 0.7), 50), 10, capacity)
                cpu = np.clip((usage / capacity) * 80 + rng.normal(10, 5), 5, 100)
                uptime = int(not (loss > 15 or cpu > 95 or rng.random() < 0.002))
                incident = int(uptime == 0 or loss > 5 or latency > 120)
                records.append({
                    "timestamp": ts,
                    "site_id": site,
                    "device_id": device_id,
                    "device_type": device_type,
                    "uptime_status": uptime,
                    "latency_ms": round(float(latency), 2),
                    "packet_loss_pct": round(float(loss), 2),
                    "bandwidth_usage_mbps": round(float(usage), 2),
                    "bandwidth_capacity_mbps": capacity,
                    "cpu_utilization_pct": round(float(cpu), 2),
                    "is_incident": incident,
                })
    return pd.DataFrame(records)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    output = root / "data" / "raw_network_telemetry.csv"
    output.parent.mkdir(exist_ok=True)
    df = generate_synthetic_telemetry()
    df.to_csv(output, index=False)
    print(f"Generated {len(df):,} telemetry records -> {output}")
