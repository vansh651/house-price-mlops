import sys
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "streamlit_app"))

from model import MODEL_PATH, load_model


def test_load_model_and_predict():
    model = load_model()
    assert model is not None
    assert MODEL_PATH.exists()

    # Predict single sample: [area, bedrooms, bathrooms, age, distance]
    sample = [[1500.0, 3, 2.0, 10.0, 10.0]]
    prediction = model.predict(sample)

    assert isinstance(prediction, np.ndarray)
    assert prediction.shape == (1,)
    price = float(prediction[0])
    assert price > 0, f"Expected positive price, got {price}"


def test_batch_prediction_shape():
    model = load_model()
    batch = [
        [1000.0, 2, 1.0, 5.0, 5.0],
        [2500.0, 4, 3.0, 15.0, 20.0],
        [3500.0, 5, 4.0, 2.0, 2.0],
    ]
    predictions = model.predict(batch)
    assert isinstance(predictions, np.ndarray)
    assert predictions.shape == (3,)
    for p in predictions:
        assert float(p) > 0
