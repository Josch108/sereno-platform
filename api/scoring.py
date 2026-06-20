"""
Capa predictiva de Sereno · Stress Risk Score (SRS)
====================================================

En producción esta capa la ocupa un modelo de machine learning
(regresión logística / random forest) entrenado con el dataset SMMH.

Para el *esqueleto* desplegable usamos una heurística transparente y
reproducible que combina las mismas variables que recibe el modelo.
Así la API funciona de extremo a extremo sin necesidad del modelo
entrenado, que se integra más adelante (semana 5 del plan).

La función `compute_srs` está aislada a propósito: el día que el modelo
esté listo solo se reemplaza el cuerpo, sin tocar el resto de la API.
"""

from dataclasses import dataclass

# Umbrales del semáforo, calibrados con la literatura sobre uso nocturno.
GREEN_MAX_MINUTES = 30   # < 30 min de uso nocturno  -> riesgo bajo
YELLOW_MAX_MINUTES = 60  # 30-60 min                 -> precaución

# Peso por plataforma: TikTok pesa más por su algoritmo de recompensa variable.
PLATFORM_WEIGHTS = {
    "tiktok": 1.3,
    "instagram": 1.15,
    "youtube": 1.05,
    "snapchat": 1.1,
    "facebook": 1.0,
    "twitter": 1.05,
}

MODEL_VERSION = "heuristic-1.0"


@dataclass
class SrsResult:
    srs: float          # 0-100
    risk_level: str     # 'green' | 'yellow' | 'red'
    model_version: str


def _platform_factor(platforms: str | None) -> float:
    """Devuelve el mayor peso entre las plataformas reportadas."""
    if not platforms:
        return 1.0
    factor = 1.0
    for raw in platforms.split(","):
        factor = max(factor, PLATFORM_WEIGHTS.get(raw.strip().lower(), 1.0))
    return factor


def risk_level_from_minutes(nocturnal_minutes: int) -> str:
    """Semáforo de 3 niveles según minutos de uso nocturno."""
    if nocturnal_minutes < GREEN_MAX_MINUTES:
        return "green"
    if nocturnal_minutes <= YELLOW_MAX_MINUTES:
        return "yellow"
    return "red"


def compute_srs(
    nocturnal_usage_min: int,
    restlessness: int,
    worry: int,
    distraction: int,
    sleep_problems: int,
    platforms: str | None = None,
) -> SrsResult:
    """
    Calcula el Stress Risk Score (0-100) y su nivel de semáforo.

    Combina:
      - tiempo de uso nocturno (componente conductual)
      - dominancia de plataforma (TikTok pesa más)
      - señales psicológicas: inquietud, preocupación, distracción, sueño
    """
    # Componente de uso nocturno (0-50). Se satura a los 120 min.
    usage_component = min(nocturnal_usage_min, 120) / 120 * 50
    usage_component *= _platform_factor(platforms)

    # Componente psicológico (0-50). Cada variable aporta hasta 12.5.
    psych_raw = restlessness + worry + distraction + sleep_problems  # 4-20
    psych_component = (psych_raw - 4) / 16 * 50

    srs = round(min(usage_component + psych_component, 100), 2)
    return SrsResult(
        srs=srs,
        risk_level=risk_level_from_minutes(nocturnal_usage_min),
        model_version=MODEL_VERSION,
    )


# Mensajes de retroalimentación SIN culpa, por nivel de riesgo.
ALERT_MESSAGES = {
    "green": (
        "Uso nocturno bajo. Buen hábito digital: el descanso está protegido. "
        "Sigan así."
    ),
    "yellow": (
        "Uso nocturno moderado. Buen momento para conversar sin alarma sobre "
        "rutinas de sueño y horarios de pantalla."
    ),
    "red": (
        "Uso nocturno alto. Sugerencia: abran una conversación tranquila y sin "
        "culpa. La app incluye guías para hablar del tema en familia."
    ),
}


def alert_for(level: str) -> str:
    return ALERT_MESSAGES.get(level, ALERT_MESSAGES["yellow"])
