"""
Sereno - Data cleaning & unification (ETL)
==========================================

Cleans and unifies the two REAL source datasets into a single training table:

  Source A: data/raw/social_media_mental_health.csv  (5,000 students)
  Source B: data/raw/student_lifestyle_100k.csv      (100,000 students)

Both datasets describe student habits and a stress level. They use different
schemas, units and stress scales, so this script:

  1. Loads both sources.
  2. Maps each one onto a shared set of meaningful, comparable features.
  3. Normalises the stress target into Sereno's 3-level traffic light
     (green / yellow / red).
  4. Cleans the data (duplicates, missing values, out-of-range rows).
  5. Writes a single clean dataset: data/processed/clean_dataset.csv

Every major step prints a visible log line so the pipeline is auditable.

Run:
    python ml/clean_data.py
"""

from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed" / "clean_dataset.csv"

# Shared schema produced by this ETL:
SHARED_COLUMNS = [
    "age",
    "gender",
    "social_media_hours",   # average daily social-media use (hours)
    "sleep_hours",          # average sleep per night (hours)
    "study_hours",          # average study time per day (hours)
    "risk_level",           # target: green / yellow / red
    "source",               # which dataset the row came from
]


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}")


def _map_stress_a(label: str) -> str:
    """Source A stress (Low/Medium/High/Very High) -> traffic light."""
    return {
        "Low": "green",
        "Medium": "yellow",
        "High": "red",
        "Very High": "red",
    }.get(label, None)


def _map_stress_b(value: int) -> str:
    """Source B stress (numeric 2-10) -> traffic light, by severity band."""
    if value <= 3:
        return "green"
    if value <= 5:
        return "yellow"
    return "red"


def load_source_a() -> pd.DataFrame:
    path = RAW / "social_media_mental_health.csv"
    log(f"Loading Source A: {path.name}")
    df = pd.read_csv(path)
    log(f"  -> {len(df):,} rows loaded")

    out = pd.DataFrame({
        "age": df["Age"],
        "gender": df["Gender"].str.strip().str.lower(),
        "social_media_hours": df["Avg_Daily_Usage_Hours"],
        "sleep_hours": df["Sleep_Hours_Per_Night"],
        "study_hours": df["Study_Hours"],
        "risk_level": df["Stress_Level"].map(_map_stress_a),
        "source": "social_media_mental_health",
    })
    return out


def load_source_b() -> pd.DataFrame:
    path = RAW / "student_lifestyle_100k.csv"
    log(f"Loading Source B: {path.name}")
    df = pd.read_csv(path)
    log(f"  -> {len(df):,} rows loaded")

    out = pd.DataFrame({
        "age": df["Age"],
        "gender": df["Gender"].str.strip().str.lower(),
        "social_media_hours": df["Social_Media_Hours"],
        "sleep_hours": df["Sleep_Duration"],
        "study_hours": df["Study_Hours"],
        "risk_level": df["Stress_Level"].map(_map_stress_b),
        "source": "student_lifestyle_100k",
    })
    return out


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the cleaning operations, logging the effect of each one."""
    start = len(df)

    # 1. Standardise gender categories
    df["gender"] = df["gender"].replace({
        "m": "male", "f": "female", "male": "male", "female": "female",
    })
    df.loc[~df["gender"].isin(["male", "female"]), "gender"] = "other"
    log(f"Gender standardised -> {df['gender'].value_counts().to_dict()}")

    # 2. Drop rows with missing values in any shared column
    before = len(df)
    df = df.dropna(subset=SHARED_COLUMNS)
    log(f"Dropped rows with missing values: {before:,} -> {len(df):,}")

    # 3. Remove exact duplicates
    before = len(df)
    df = df.drop_duplicates()
    log(f"Dropped duplicate rows: {before:,} -> {len(df):,}")

    # 4. Remove physically impossible / out-of-range values
    before = len(df)
    df = df[
        (df["age"].between(10, 60))
        & (df["social_media_hours"].between(0, 24))
        & (df["sleep_hours"].between(0, 24))
        & (df["study_hours"].between(0, 24))
    ]
    log(f"Dropped out-of-range rows: {before:,} -> {len(df):,}")

    # 5. Round numeric columns for consistency
    for col in ["social_media_hours", "sleep_hours", "study_hours"]:
        df[col] = df[col].round(1)

    log(f"Cleaning complete: {start:,} -> {len(df):,} rows kept")
    return df.reset_index(drop=True)


def main() -> None:
    log("=== Sereno data-cleaning ETL ===")
    a = load_source_a()
    b = load_source_b()

    df = pd.concat([a, b], ignore_index=True)
    log(f"Unified both sources: {len(df):,} total rows")

    df = clean(df)

    log("Final class balance (traffic light):")
    print((df["risk_level"].value_counts(normalize=True) * 100).round(1).to_string())

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    log(f"Saved clean dataset -> {OUT.relative_to(ROOT)} ({len(df):,} rows)")


if __name__ == "__main__":
    main()
