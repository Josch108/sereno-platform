"""Esquemas de datos (Pydantic) de la API de Sereno."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# --- Entrada: una respuesta de cuestionario ---------------------------------
class ResponseIn(BaseModel):
    external_uid: str = Field(..., examples=["teen-0001"])
    platforms: str | None = Field(None, examples=["TikTok,Instagram"])
    daily_usage_minutes: int = Field(..., ge=0, examples=[240])
    nocturnal_usage_min: int = Field(..., ge=0, examples=[75])
    last_session_hour: int = Field(..., ge=0, le=23, examples=[1])
    restlessness: int = Field(..., ge=1, le=5)
    worry: int = Field(..., ge=1, le=5)
    distraction: int = Field(..., ge=1, le=5)
    sleep_problems: int = Field(..., ge=1, le=5)


# --- Salida: respuesta + puntaje + alerta -----------------------------------
class RiskScoreOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    srs: float
    risk_level: str
    model_version: str


class AlertOut(BaseModel):
    level: str
    message: str


class ResponseOut(BaseModel):
    response_id: int
    external_uid: str
    risk: RiskScoreOut
    alert: AlertOut
    submitted_at: datetime


class HealthOut(BaseModel):
    status: str
    service: str
    version: str
