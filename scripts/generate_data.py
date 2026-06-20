"""
Generador de datos de ejemplo para Sereno
==========================================

Crea un conjunto de respuestas sintéticas (no son datos reales de personas)
con las mismas variables que el dataset SMMH de Kaggle, calcula el puntaje de
riesgo de cada una con la capa de scoring de la API y exporta el resultado en
tres formatos: CSV, JSON y Excel.

Uso:
    python scripts/generate_data.py --n 200

Salida (carpeta data/):
    sample_responses.csv
    sample_responses.json
    sample_responses.xlsx
"""

import argparse
import json
import random
import sys
from pathlib import Path

import pandas as pd

# Permitir importar la capa de scoring de la API
sys.path.append(str(Path(__file__).resolve().parent.parent))
from api.scoring import compute_srs  # noqa: E402

PLATFORMS = ["TikTok", "Instagram", "YouTube", "Snapchat", "Facebook", "Twitter"]
GENDERS = ["M", "F", "Otro"]
OUT_DIR = Path(__file__).resolve().parent.parent / "data"


def random_platform_mix() -> str:
    k = random.randint(1, 3)
    return ",".join(random.sample(PLATFORMS, k))


def generate(n: int, seed: int = 42) -> pd.DataFrame:
    random.seed(seed)
    rows = []
    for i in range(1, n + 1):
        platforms = random_platform_mix()
        nocturnal = random.choice(
            [random.randint(0, 29), random.randint(30, 60), random.randint(61, 150)]
        )
        restlessness = random.randint(1, 5)
        worry = random.randint(1, 5)
        distraction = random.randint(1, 5)
        sleep_problems = random.randint(1, 5)

        result = compute_srs(
            nocturnal_usage_min=nocturnal,
            restlessness=restlessness,
            worry=worry,
            distraction=distraction,
            sleep_problems=sleep_problems,
            platforms=platforms,
        )

        rows.append({
            "external_uid": f"teen-{i:04d}",
            "age": random.randint(13, 17),
            "gender": random.choice(GENDERS),
            "platforms": platforms,
            "daily_usage_minutes": random.randint(60, 480),
            "nocturnal_usage_min": nocturnal,
            "last_session_hour": random.choice([21, 22, 23, 0, 1, 2]),
            "restlessness": restlessness,
            "worry": worry,
            "distraction": distraction,
            "sleep_problems": sleep_problems,
            "srs": result.srs,
            "risk_level": result.risk_level,
            "model_version": result.model_version,
        })
    return pd.DataFrame(rows)


def export(df: pd.DataFrame) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    df.to_csv(OUT_DIR / "sample_responses.csv", index=False)
    with open(OUT_DIR / "sample_responses.json", "w", encoding="utf-8") as fh:
        json.dump(df.to_dict(orient="records"), fh, ensure_ascii=False, indent=2)
    df.to_excel(OUT_DIR / "sample_responses.xlsx", index=False, sheet_name="responses")
    print(f"Generadas {len(df)} respuestas en {OUT_DIR}/ (CSV, JSON, XLSX)")
    print(df["risk_level"].value_counts().to_string())


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera datos de ejemplo de Sereno.")
    parser.add_argument("--n", type=int, default=200, help="número de respuestas")
    parser.add_argument("--seed", type=int, default=42, help="semilla aleatoria")
    args = parser.parse_args()
    export(generate(args.n, args.seed))


if __name__ == "__main__":
    main()
