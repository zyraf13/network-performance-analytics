from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score

FEATURES = ["latency_ms", "packet_loss_pct", "bandwidth_util_pct", "cpu_utilization_pct"]


def prepare_training_data(csv_path: str | Path) -> tuple[pd.DataFrame, pd.Series]:
    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    df = df.sort_values(["device_id", "timestamp"]).copy()
    df["bandwidth_util_pct"] = 100 * df["bandwidth_usage_mbps"] / df["bandwidth_capacity_mbps"]
    # Predict next interval incident; current incident is never used as a feature.
    df["target_next_incident"] = df.groupby("device_id")["is_incident"].shift(-1)
    df = df.dropna(subset=["target_next_incident"])
    return df[FEATURES], df["target_next_incident"].astype(int)


def train_risk_model(csv_path: str | Path, model_output: str | Path) -> dict:
    X, y = prepare_training_data(csv_path)
    cutoff = int(len(X) * 0.8)
    model = RandomForestClassifier(n_estimators=120, max_depth=10, random_state=42, class_weight="balanced")
    model.fit(X.iloc[:cutoff], y.iloc[:cutoff])
    probabilities = model.predict_proba(X.iloc[cutoff:])[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    metrics = {
        "roc_auc": float(roc_auc_score(y.iloc[cutoff:], probabilities)),
        "report": classification_report(y.iloc[cutoff:], predictions, zero_division=0),
        "test_rows": len(y) - cutoff,
    }
    output = Path(model_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURES}, output)
    return metrics


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = train_risk_model(root / "data/raw_network_telemetry.csv", root / "src/risk_model.pkl")
    print(f"ROC-AUC: {result['roc_auc']:.4f}\n{result['report']}")
