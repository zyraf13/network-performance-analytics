import pandas as pd

from src.ml_model import FEATURES, prepare_training_data


def test_training_features_do_not_leak_current_incident(tmp_path):
    path = tmp_path / "telemetry.csv"
    rows = []
    for i in range(4):
        rows.append({"timestamp": f"2026-01-01 00:0{i}:00", "device_id": "R1", "latency_ms": 10, "packet_loss_pct": 0, "bandwidth_usage_mbps": 50, "bandwidth_capacity_mbps": 100, "cpu_utilization_pct": 20, "is_incident": i % 2, "site_id": "S", "device_type": "Router", "uptime_status": 1})
    pd.DataFrame(rows).to_csv(path, index=False)
    X, y = prepare_training_data(path)
    assert list(X.columns) == FEATURES
    assert "is_incident" not in X.columns
    assert len(y) == 3
