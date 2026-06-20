"""
Conexión a base de datos del esqueleto.

Para que la plataforma sea desplegable y ejecutable en local SIN un servidor
PostgreSQL, el esqueleto usa SQLite por defecto. El esquema lógico es el mismo
de `database/schema.sql`; aquí se crea una versión mínima compatible.

En producción se cambia `DATABASE_URL` a una cadena de PostgreSQL y se aplica
`database/schema.sql`.
"""

import os
import sqlite3
from pathlib import Path

DB_PATH = os.environ.get("SERENO_DB", str(Path(__file__).resolve().parent.parent / "sereno.db"))


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Crea las tablas mínimas para que la API funcione end-to-end."""
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            external_uid TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL DEFAULT 'adolescent',
            age INTEGER,
            gender TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            platforms TEXT,
            daily_usage_minutes INTEGER,
            nocturnal_usage_min INTEGER,
            last_session_hour INTEGER,
            restlessness INTEGER,
            worry INTEGER,
            distraction INTEGER,
            sleep_problems INTEGER,
            submitted_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS risk_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            response_id INTEGER NOT NULL REFERENCES responses(id),
            srs REAL NOT NULL,
            risk_level TEXT NOT NULL,
            model_version TEXT NOT NULL,
            computed_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            risk_score_id INTEGER NOT NULL REFERENCES risk_scores(id),
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )
    conn.commit()
    conn.close()
