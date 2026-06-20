"""Pruebas del esqueleto de Sereno (scoring + API end-to-end)."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

# Usar una base de datos temporal para no tocar la de desarrollo.
os.environ["SERENO_DB"] = str(Path(tempfile.gettempdir()) / "sereno_test.db")

from fastapi.testclient import TestClient  # noqa: E402

from api.database import init_db  # noqa: E402
from api.main import app  # noqa: E402
from api.scoring import compute_srs, risk_level_from_minutes  # noqa: E402

init_db()
client = TestClient(app)


def test_risk_level_thresholds():
    assert risk_level_from_minutes(10) == "green"
    assert risk_level_from_minutes(45) == "yellow"
    assert risk_level_from_minutes(90) == "red"


def test_srs_is_bounded():
    result = compute_srs(120, 5, 5, 5, 5, "TikTok")
    assert 0 <= result.srs <= 100
    assert result.risk_level == "red"


def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_submit_and_fetch_response():
    payload = {
        "external_uid": "test-teen-1",
        "platforms": "TikTok,Instagram",
        "daily_usage_minutes": 300,
        "nocturnal_usage_min": 80,
        "last_session_hour": 1,
        "restlessness": 4,
        "worry": 4,
        "distraction": 3,
        "sleep_problems": 5,
    }
    res = client.post("/responses", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["risk"]["risk_level"] == "red"
    assert body["alert"]["level"] == "red"

    rid = body["response_id"]
    res2 = client.get(f"/responses/{rid}")
    assert res2.status_code == 200
    assert res2.json()["external_uid"] == "test-teen-1"


def test_unknown_response_returns_404():
    assert client.get("/responses/999999").status_code == 404
