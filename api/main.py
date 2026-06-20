"""
SERENO · API (FastAPI)
======================

Esqueleto desplegable de la plataforma. Expone el flujo de las 4 capas:

    POST /responses   -> recibe el cuestionario, calcula el SRS y genera alerta
    GET  /responses/{id} -> consulta un resultado guardado
    GET  /health      -> verificación de salud (la usa GitHub Actions)

Ejecutar en local:
    uvicorn api.main:app --reload
Documentación interactiva:
    http://localhost:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from api import __version__
from api.database import get_connection, init_db
from api.models import (
    AlertOut,
    HealthOut,
    ResponseIn,
    ResponseOut,
    RiskScoreOut,
)
from api.scoring import alert_for, compute_srs


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # crea las tablas al arrancar
    yield


app = FastAPI(
    title="Sereno API",
    description="Detección temprana de riesgo de estrés a partir de hábitos digitales.",
    version=__version__,
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthOut, tags=["sistema"])
def health() -> HealthOut:
    return HealthOut(status="ok", service="sereno-api", version=__version__)


@app.post("/responses", response_model=ResponseOut, tags=["cuestionario"])
def submit_response(payload: ResponseIn) -> ResponseOut:
    """Capa 1->4: recibe respuestas, procesa, puntúa y alerta."""
    conn = get_connection()
    cur = conn.cursor()

    # Capa 1: ubicar/crear al usuario (anónimo)
    cur.execute("SELECT id FROM users WHERE external_uid = ?", (payload.external_uid,))
    row = cur.fetchone()
    if row:
        user_id = row["id"]
    else:
        cur.execute(
            "INSERT INTO users (external_uid, role) VALUES (?, 'adolescent')",
            (payload.external_uid,),
        )
        user_id = cur.lastrowid

    # Capa 1: guardar la respuesta
    cur.execute(
        """
        INSERT INTO responses
            (user_id, platforms, daily_usage_minutes, nocturnal_usage_min,
             last_session_hour, restlessness, worry, distraction, sleep_problems)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id, payload.platforms, payload.daily_usage_minutes,
            payload.nocturnal_usage_min, payload.last_session_hour,
            payload.restlessness, payload.worry, payload.distraction,
            payload.sleep_problems,
        ),
    )
    response_id = cur.lastrowid

    # Capa 3: calcular el puntaje de riesgo de estrés
    result = compute_srs(
        nocturnal_usage_min=payload.nocturnal_usage_min,
        restlessness=payload.restlessness,
        worry=payload.worry,
        distraction=payload.distraction,
        sleep_problems=payload.sleep_problems,
        platforms=payload.platforms,
    )
    cur.execute(
        """
        INSERT INTO risk_scores (response_id, srs, risk_level, model_version)
        VALUES (?, ?, ?, ?)
        """,
        (response_id, result.srs, result.risk_level, result.model_version),
    )
    risk_score_id = cur.lastrowid

    # Capa 4: generar la alerta (sin culpa)
    message = alert_for(result.risk_level)
    cur.execute(
        "INSERT INTO alerts (risk_score_id, level, message) VALUES (?, ?, ?)",
        (risk_score_id, result.risk_level, message),
    )

    cur.execute("SELECT submitted_at FROM responses WHERE id = ?", (response_id,))
    submitted_at = cur.fetchone()["submitted_at"]

    conn.commit()
    conn.close()

    return ResponseOut(
        response_id=response_id,
        external_uid=payload.external_uid,
        risk=RiskScoreOut(srs=result.srs, risk_level=result.risk_level,
                          model_version=result.model_version),
        alert=AlertOut(level=result.risk_level, message=message),
        submitted_at=submitted_at,
    )


@app.get("/responses/{response_id}", response_model=ResponseOut, tags=["cuestionario"])
def get_response(response_id: int) -> ResponseOut:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT r.id AS response_id, r.submitted_at, u.external_uid,
               s.srs, s.risk_level, s.model_version,
               a.level AS alert_level, a.message AS alert_message
        FROM responses r
        JOIN users u       ON u.id = r.user_id
        JOIN risk_scores s ON s.response_id = r.id
        JOIN alerts a      ON a.risk_score_id = s.id
        WHERE r.id = ?
        """,
        (response_id,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Respuesta no encontrada")

    return ResponseOut(
        response_id=row["response_id"],
        external_uid=row["external_uid"],
        risk=RiskScoreOut(srs=row["srs"], risk_level=row["risk_level"],
                          model_version=row["model_version"]),
        alert=AlertOut(level=row["alert_level"], message=row["alert_message"]),
        submitted_at=row["submitted_at"],
    )
