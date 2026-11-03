from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

MODEL_PATH = Path(__file__).resolve().parent / "house_price_model.joblib"


def _train_model() -> None:
    rng = np.random.default_rng(42)
    rows = 500
    area = rng.uniform(500, 4_000, rows)
    bedrooms = rng.integers(1, 7, rows)
    bathrooms = rng.integers(1, 5, rows).astype(float)
    age = rng.uniform(0, 60, rows)
    distance = rng.uniform(1, 50, rows)
    noise = rng.normal(0, 20_000, rows)
    target = (
        110 * area
        + 30_000 * bedrooms
        + 25_000 * bathrooms
        - 1_500 * age
        - 2_000 * distance
        + 75_000
        + noise
    )
    features = np.column_stack((area, bedrooms, bathrooms, age, distance))
    x_train, _, y_train, _ = train_test_split(features, target, test_size=0.2, random_state=42)
    pipeline = make_pipeline(
        StandardScaler(),
        RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
    )
    pipeline.fit(x_train, y_train)
    joblib.dump(pipeline, MODEL_PATH)


def load_model():
    if not MODEL_PATH.exists():
        _train_model()
    return joblib.load(MODEL_PATH)
