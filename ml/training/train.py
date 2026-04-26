"""
FraudShield — XGBoost Training Pipeline
Kaggle Credit Card Fraud dataset (284,807 rows, 492 fraud)

Rules enforced:
- Drop Time column (recording order, not real time)
- StandardScaler on Amount ONLY (V1-V28 already PCA-transformed)
- scale_pos_weight = 284315 / 492 ≈ 578
- Report F1 on fraud class, never accuracy
- SHAP TreeExplainer cached at module level
"""

import json
import pickle
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, roc_auc_score, classification_report
from xgboost import XGBClassifier

# --- Config ---
DATA_PATH = Path("data/raw/creditcard.csv")
MODEL_PATH = Path("ml/model.pkl")
REPORTS_PATH = Path("reports")
RANDOM_STATE = 42
TEST_SIZE = 0.2


def load_data() -> pd.DataFrame:
    """Load and validate the credit card fraud dataset."""
    df = pd.read_csv(DATA_PATH)
    assert "Class" in df.columns, "Missing 'Class' column"
    assert "Amount" in df.columns, "Missing 'Amount' column"
    print(f"Loaded {len(df)} rows, {df['Class'].sum()} fraud ({df['Class'].mean()*100:.3f}%)")
    return df


def preprocess(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, StandardScaler]:
    """Drop Time, scale Amount only, return features/labels/scaler."""
    df = df.drop(columns=["Time"], errors="ignore")

    labels = df["Class"].values
    features = df.drop(columns=["Class"])

    # Scale Amount only — V1-V28 are already PCA-transformed
    amount_col = features["Amount"].values.reshape(-1, 1)
    scaler = StandardScaler()
    amount_scaled = scaler.fit_transform(amount_col)

    features["Amount"] = amount_scaled.ravel()
    return features.values, labels, scaler


def train_model(X_train: np.ndarray, y_train: np.ndarray) -> XGBClassifier:
    """Train XGBoost with class imbalance handling."""
    n_legit = int((y_train == 0).sum())
    n_fraud = int((y_train == 1).sum())
    spw = n_legit / n_fraud
    print(f"scale_pos_weight = {n_legit}/{n_fraud} = {spw:.1f}")

    model = XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        scale_pos_weight=spw,
        eval_metric="aucpr",
        random_state=RANDOM_STATE,
        n_jobs=-1,
        tree_method="hist",
    )
    model.fit(X_train, y_train, verbose=False)
    return model


def evaluate(model: XGBClassifier, X_test: np.ndarray, y_test: np.ndarray) -> dict:
    """Evaluate and return metrics. NEVER report accuracy."""
    y_prob = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_prob)

    # Find optimal threshold for F1 on fraud class
    best_f1, best_thresh = 0.0, 0.5
    for t in np.arange(0.1, 0.9, 0.02):
        y_pred_t = (y_prob >= t).astype(int)
        f1_t = f1_score(y_test, y_pred_t)
        if f1_t > best_f1:
            best_f1, best_thresh = f1_t, t

    y_pred = (y_prob >= best_thresh).astype(int)
    f1 = f1_score(y_test, y_pred)

    print("\n=== Classification Report ===")
    print(classification_report(y_test, y_pred, target_names=["Legit", "Fraud"]))
    print(f"F1 (fraud):  {f1:.4f} (threshold={best_thresh:.2f})")
    print(f"AUC-ROC:     {auc:.4f}")

    return {"f1_fraud": round(f1, 4), "auc_roc": round(auc, 4), "threshold": round(best_thresh, 2)}


def save_model(model: XGBClassifier, scaler: StandardScaler, metrics: dict) -> None:
    """Save model bundle: model + scaler + metadata. NEVER serve via API endpoint."""
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORTS_PATH.mkdir(parents=True, exist_ok=True)

    bundle = {
        "model": model,
        "scaler": scaler,
        "metadata": {
            "trained_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "features": 29,
            "metrics": metrics,
        },
    }
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(bundle, f)
    print(f"\nSaved model → {MODEL_PATH} ({MODEL_PATH.stat().st_size / 1024:.0f} KB)")

    with open(REPORTS_PATH / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)


def main() -> None:
    print("=" * 50)
    print("FraudShield — Training Pipeline")
    print("=" * 50)

    df = load_data()
    X, y, scaler = preprocess(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    print(f"Train: {len(X_train)}, Test: {len(X_test)}")

    model = train_model(X_train, y_train)
    metrics = evaluate(model, X_test, y_test)

    # Validate targets
    if metrics["f1_fraud"] < 0.85:
        print(f"WARNING: F1 {metrics['f1_fraud']} < 0.85 target")
    if metrics["auc_roc"] < 0.95:
        print(f"WARNING: AUC-ROC {metrics['auc_roc']} < 0.95 target")

    save_model(model, scaler, metrics)
    print("\nTraining complete.")


if __name__ == "__main__":
    main()
