import sys
from pathlib import Path
from prometheus_client import Counter, REGISTRY

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "streamlit_app"))

import metrics
from metrics import _get_or_create, observe_inputs, NAMESPACE


def test_metric_reload_safety():
    """Verify that calling _get_or_create with an already registered metric name

    does not raise ValueError and returns the existing collector.
    """
    first = _get_or_create(Counter, f"{NAMESPACE}_test_metric", "Test metric documentation")
    second = _get_or_create(Counter, f"{NAMESPACE}_test_metric", "Test metric documentation")
    assert first is second


def test_metrics_definitions():
    """Ensure all core metrics are defined and registered with house_predictor_ prefix."""
    expected_metrics = [
        "house_predictor_app_info",
        "house_predictor_script_runs_total",
        "house_predictor_predictions_total",
        "house_predictor_prediction_errors_total",
        "house_predictor_prediction_latency_seconds_count",
        "house_predictor_model_load_seconds",
        "house_predictor_model_loaded",
        "house_predictor_predicted_price_dollars_count",
        "house_predictor_input_area_sqft_count",
    ]
    registered_names = set(REGISTRY._names_to_collectors.keys())
    for metric_name in [
        "house_predictor_app",
        "house_predictor_script_runs",
        "house_predictor_predictions",
        "house_predictor_prediction_errors",
        "house_predictor_prediction_latency_seconds",
        "house_predictor_model_load_seconds",
        "house_predictor_model_loaded",
    ]:
        assert metric_name in registered_names


def test_observe_inputs():
    """Verify observe_inputs records observations without errors."""
    observe_inputs(area=1800.0, bedrooms=3, bathrooms=2.0, age=5.0, distance=12.0)
