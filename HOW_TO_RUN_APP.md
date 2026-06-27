# Sereno — Model & Web App (first version)

The runnable first version of Sereno: a student enters a few daily habits and a
trained model returns a **stress traffic-light** (🟢 / 🟡 / 🔴) with supportive,
no-blame guidance.

## What's here

| File | What it does |
|------|--------------|
| `ml/clean_data.py` | Cleans and unifies the **two real datasets** into one training table |
| `ml/train_model.py` | Trains the stress classifier (Random Forest, ~86% accuracy) |
| `ml/predict.py` | Loads the model and turns habit inputs into a prediction |
| `web/index.html` | The web page (front end) |
| `web_app.py` | FastAPI server: serves the page + `/predict` (real model) |

## Data sources

Place the two CSVs in `data/raw/` (they are git-ignored, not committed):

- **`social_media_mental_health.csv`** (5,000 students) — social-media use, sleep,
  study and a Low/Medium/High stress label. **This drives the model.**
- **`student_lifestyle_100k.csv`** (100,000 students) — kept as a second source
  in the cleaning step only.

> We evaluated both datasets: in the lifestyle dataset, social-media use has **no**
> relationship with stress (correlation ≈ 0.00), so mixing it in dropped accuracy
> from 0.86 to 0.52. The model is trained on the high-signal social-media dataset
> (social-media use correlates **+0.77** with stress). Both are still cleaned by
> the ETL.

## How to run it

From the project root:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Clean and unify the two datasets  ->  data/processed/clean_dataset.csv
python ml/clean_data.py

# 3. Train the model  ->  model/sereno_stress_model.pkl
python ml/train_model.py

# 4. Launch the web app
uvicorn web_app:app --reload
```

Open **http://localhost:8000**, move the sliders, and press
**“Reveal my Sereno reading”**.

> The page also works opened on its own (`web/index.html`): if the server is not
> running it falls back to a local estimate, so it never looks broken — but the
> server gives the real 86%-accuracy model.

## What the model learned

The strongest predictor of stress is **daily social-media use** (importance 0.40),
followed by **sleep** (0.28) and **study time** (0.24) — Sereno's core hypothesis,
backed by a real dataset.

> Screening prototype, **not** a medical diagnosis. The production target remains a
> Flutter mobile app; this version validates the flow: inputs → model → traffic light.
