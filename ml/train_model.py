"""
Sereno - Stress-risk model training
====================================

Trains the classifier that powers the Sereno app: given a student's daily
habits it predicts the stress traffic-light (green / yellow / red).

Input : data/processed/clean_dataset.csv   (produced by ml/clean_data.py)
Output: model/sereno_stress_model.pkl       (scikit-learn pipeline)

The model is a pipeline = preprocessing (one-hot gender + scale numerics)
followed by a Random Forest classifier. We hold out 20% of the data to report
honest accuracy.

Run:
    python ml/train_model.py
"""

from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed" / "clean_dataset.csv"
MODEL_OUT = ROOT / "model" / "sereno_stress_model.pkl"

NUMERIC = ["age", "social_media_hours", "sleep_hours", "study_hours"]
CATEGORICAL = ["gender"]
FEATURES = NUMERIC + CATEGORICAL
TARGET = "risk_level"

# We clean & unify BOTH datasets in ml/clean_data.py, but only one of them
# carries a real signal between social-media use and stress:
#   - social_media_mental_health : social_media_hours vs stress  r = +0.77  (strong)
#   - student_lifestyle_100k     : social_media_hours vs stress  r = +0.003 (none)
# Training on the combined set lets the 100k noisy rows drown the real signal
# (accuracy collapses from 0.84 to 0.52). So the production model is trained on
# the high-signal source; the lifestyle dataset is kept as secondary context.
TRAIN_SOURCE = "social_media_mental_health"


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}")


def main() -> None:
    log("=== Sereno model training ===")
    if not DATA.exists():
        raise SystemExit("Missing clean dataset. Run `python ml/clean_data.py` first.")

    df = pd.read_csv(DATA)
    log(f"Loaded {len(df):,} clean rows (both sources)")

    df = df[df["source"] == TRAIN_SOURCE]
    log(f"Training on high-signal source '{TRAIN_SOURCE}': {len(df):,} rows")

    X = df[FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    log(f"Train: {len(X_train):,} rows · Test: {len(X_test):,} rows")

    preprocess = ColumnTransformer([
        ("num", StandardScaler(), NUMERIC),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
    ])
    model = Pipeline([
        ("prep", preprocess),
        ("clf", RandomForestClassifier(
            n_estimators=200, max_depth=14, n_jobs=-1, random_state=42
        )),
    ])

    log("Training Random Forest...")
    model.fit(X_train, y_train)

    acc = model.score(X_test, y_test)
    log(f"Test accuracy: {acc:.3f}")
    print("\nClassification report (held-out test set):")
    print(classification_report(y_test, model.predict(X_test)))

    # Feature importance (mapped back to readable names)
    clf = model.named_steps["clf"]
    ohe = model.named_steps["prep"].named_transformers_["cat"]
    names = NUMERIC + list(ohe.get_feature_names_out(CATEGORICAL))
    importance = (
        pd.Series(clf.feature_importances_, index=names)
        .sort_values(ascending=False)
    )
    log("Feature importance:")
    print(importance.round(3).to_string())

    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_OUT)
    log(f"Saved model -> {MODEL_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
