"""
Sereno - Inference helper
=========================

Loads the trained model once and turns a set of habit inputs into a stress
traffic-light prediction plus a no-blame, supportive message.

Kept separate from the Streamlit UI so it can be reused and unit-tested.
"""

from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

MODEL_PATH = Path(__file__).resolve().parent.parent / "model" / "sereno_stress_model.pkl"

# Non-punishing feedback per traffic-light level (Sereno principle).
ADVICE = {
    "green": (
        "Low stress signals. Your digital and sleep habits look balanced — "
        "keep protecting your night-time rest."
    ),
    "yellow": (
        "Moderate stress signals. A good moment to review screen-time and sleep "
        "routines calmly, before they build up. No alarm needed."
    ),
    "red": (
        "High stress signals. Consider a calm, no-blame conversation and small "
        "changes to night-time social-media use. Remember: this is early "
        "screening, not a medical diagnosis."
    ),
}

LABELS = {"green": "🟢 Low risk", "yellow": "🟡 Caution", "red": "🔴 High risk"}


@lru_cache(maxsize=1)
def _load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Model not found. Run `python ml/train_model.py` first."
        )
    return joblib.load(MODEL_PATH)


def predict_risk(age, gender, social_media_hours, sleep_hours, study_hours) -> dict:
    """Return the predicted traffic-light level, probabilities and advice."""
    model = _load_model()
    row = pd.DataFrame([{
        "age": age,
        "gender": gender,
        "social_media_hours": social_media_hours,
        "sleep_hours": sleep_hours,
        "study_hours": study_hours,
    }])

    level = model.predict(row)[0]
    proba = dict(zip(model.classes_, model.predict_proba(row)[0].round(3)))

    return {
        "level": level,
        "label": LABELS[level],
        "probabilities": proba,
        "advice": ADVICE[level],
    }


if __name__ == "__main__":
    # Quick manual check
    demo = predict_risk(age=15, gender="male", social_media_hours=8,
                        sleep_hours=5, study_hours=2)
    print(demo)
