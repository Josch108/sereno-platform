"""
Sereno - Web app server
=======================

Serves the Sereno web page (web/index.html) and exposes a /predict endpoint
backed by the REAL trained model (ml/predict.py). Same origin, so the page can
call /predict without any CORS setup.

Run:
    uvicorn web_app:app --reload
Then open http://localhost:8000

(The page also works opened on its own as a static file: if /predict is not
reachable it falls back to a local estimate. The server gives the real model.)
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ml.predict import predict_risk

WEB = Path(__file__).resolve().parent / "web"

app = FastAPI(title="Sereno Web", description="Stress-risk screening web app")


class HabitsIn(BaseModel):
    age: int = Field(..., ge=10, le=60)
    gender: str
    social_media_hours: float = Field(..., ge=0, le=24)
    sleep_hours: float = Field(..., ge=0, le=24)
    study_hours: float = Field(..., ge=0, le=24)


@app.get("/")
def home() -> FileResponse:
    return FileResponse(WEB / "index.html")


@app.post("/predict")
def predict(habits: HabitsIn) -> dict:
    result = predict_risk(
        age=habits.age,
        gender=habits.gender,
        social_media_hours=habits.social_media_hours,
        sleep_hours=habits.sleep_hours,
        study_hours=habits.study_hours,
    )
    # Make probabilities plain floats for JSON
    result["probabilities"] = {k: float(v) for k, v in result["probabilities"].items()}
    return result
