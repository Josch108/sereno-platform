"""
Carga de datos de ejemplo a la base de datos local de Sereno
============================================================

Lee data/sample_responses.csv y lo inserta en la base SQLite del esqueleto,
recreando el flujo de las 4 capas (usuario -> respuesta -> puntaje -> alerta).

Uso:
    python scripts/load_data.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))
from api.database import get_connection, init_db  # noqa: E402
from api.scoring import alert_for  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data" / "sample_responses.csv"


def main() -> None:
    if not DATA.exists():
        raise SystemExit("No existe data/sample_responses.csv. Corre generate_data.py primero.")

    init_db()
    df = pd.read_csv(DATA)
    conn = get_connection()
    cur = conn.cursor()
    inserted = 0

    for _, r in df.iterrows():
        cur.execute(
            "INSERT OR IGNORE INTO users (external_uid, role, age, gender) "
            "VALUES (?, 'adolescent', ?, ?)",
            (r["external_uid"], int(r["age"]), r["gender"]),
        )
        cur.execute("SELECT id FROM users WHERE external_uid = ?", (r["external_uid"],))
        user_id = cur.fetchone()["id"]

        cur.execute(
            """INSERT INTO responses
               (user_id, platforms, daily_usage_minutes, nocturnal_usage_min,
                last_session_hour, restlessness, worry, distraction, sleep_problems)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, r["platforms"], int(r["daily_usage_minutes"]),
             int(r["nocturnal_usage_min"]), int(r["last_session_hour"]),
             int(r["restlessness"]), int(r["worry"]), int(r["distraction"]),
             int(r["sleep_problems"])),
        )
        response_id = cur.lastrowid

        cur.execute(
            "INSERT INTO risk_scores (response_id, srs, risk_level, model_version) "
            "VALUES (?, ?, ?, ?)",
            (response_id, float(r["srs"]), r["risk_level"], r["model_version"]),
        )
        risk_score_id = cur.lastrowid

        cur.execute(
            "INSERT INTO alerts (risk_score_id, level, message) VALUES (?, ?, ?)",
            (risk_score_id, r["risk_level"], alert_for(r["risk_level"])),
        )
        inserted += 1

    conn.commit()
    conn.close()
    print(f"Cargadas {inserted} respuestas en la base local.")


if __name__ == "__main__":
    main()
