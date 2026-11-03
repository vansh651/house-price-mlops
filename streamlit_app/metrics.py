"""Prometheus instrumentation for the House Price Predictor.

Streamlit re-executes ``app.py`` on every user interaction, but imported
modules are cached by Python, so the metric objects defined here are created
once per process and shared by all user sessions.

A small HTTP server exposing ``/metrics`` is started on ``METRICS_PORT``
(default 8000), separate from the Streamlit UI port (8501), so Prometheus can
scrape it without going through the Streamlit server.
"""

import logging
import os
import threading
from typing import Callable, Optional, Sequence

from prometheus_client import REGISTRY, Counter, Gauge, Histogram, Info, start_http_server

logger = logging.getLogger(__name__)

METRICS_PORT = int(os.getenv("METRICS_PORT", "8000"))
APP_VERSION = os.getenv("APP_VERSION", "dev")

NAMESPACE = "house_predictor"


def _get_or_create(factory: Callable, name: str, documentation: str, **kwargs):
    """Create a metric, or return the existing one if it is already registered.

    Streamlit's file watcher can re-import a changed module during local
    development, which would otherwise raise "Duplicated timeseries" errors.
    """
    try:
        return factory(name, documentation, **kwargs)
    except ValueError:
        # prometheus_client indexes every collector by its base name in this dict.
        existing = REGISTRY._names_to_collectors.get(name)  # noqa: SLF001
        if existing is None:
            raise
        return existing


def _histogram(name: str, documentation: str, buckets: Sequence[float]) -> Histogram:
    return _get_or_create(Histogram, f"{NAMESPACE}_{name}", documentation, buckets=buckets)


# --------------------------------------------------------------------------- #
# Application / traffic metrics
# --------------------------------------------------------------------------- #
APP_INFO = _get_or_create(Info, f"{NAMESPACE}_app", "Static information about the application")

SCRIPT_RUNS = _get_or_create(
    Counter,
    f"{NAMESPACE}_script_runs",
    "Number of Streamlit script executions (page loads and widget interactions)",
)

PREDICTIONS = _get_or_create(
    Counter,
    f"{NAMESPACE}_predictions",
    "Number of successful price predictions served",
)

PREDICTION_ERRORS = _get_or_create(
    Counter,
    f"{NAMESPACE}_prediction_errors",
    "Number of predictions that failed with an exception",
)

PREDICTION_LATENCY = _histogram(
    "prediction_latency_seconds",
    "Time spent inside model.predict()",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)

# --------------------------------------------------------------------------- #
# Model metrics
# --------------------------------------------------------------------------- #
MODEL_LOAD_SECONDS = _get_or_create(
    Gauge,
    f"{NAMESPACE}_model_load_seconds",
    "Seconds taken to load (or train, on first start) the model",
)

MODEL_LOADED = _get_or_create(
    Gauge,
    f"{NAMESPACE}_model_loaded",
    "1 once the model is in memory (it is loaded lazily on the first prediction), else 0",
)

# --------------------------------------------------------------------------- #
# Data-drift style metrics: distribution of inputs and outputs seen in production
# --------------------------------------------------------------------------- #
PREDICTED_PRICE = _histogram(
    "predicted_price_dollars",
    "Distribution of predicted prices",
    buckets=(50e3, 100e3, 150e3, 200e3, 300e3, 400e3, 500e3, 750e3, 1e6, 1.5e6, 2e6),
)

INPUT_AREA = _histogram(
    "input_area_sqft",
    "Distribution of living area inputs (sq ft)",
    buckets=(250, 500, 750, 1000, 1500, 2000, 2500, 3000, 4000, 5000),
)

INPUT_BEDROOMS = _histogram(
    "input_bedrooms",
    "Distribution of bedroom count inputs",
    buckets=(1, 2, 3, 4, 5, 6, 8, 10, 20),
)

INPUT_BATHROOMS = _histogram(
    "input_bathrooms",
    "Distribution of bathroom count inputs",
    buckets=(1, 1.5, 2, 3, 4, 5, 8, 10, 20),
)

INPUT_AGE = _histogram(
    "input_age_years",
    "Distribution of property age inputs (years)",
    buckets=(1, 5, 10, 20, 30, 50, 75, 100, 200),
)

INPUT_DISTANCE = _histogram(
    "input_distance_km",
    "Distribution of distance-to-city inputs (km)",
    buckets=(1, 2, 5, 10, 20, 30, 50, 100, 500),
)

_server_lock = threading.Lock()
_server_started = False


def start_metrics_server(port: Optional[int] = None) -> bool:
    """Start the ``/metrics`` HTTP endpoint once per process.

    Returns True if this call started the server, False if it was already
    running (or the port is taken by another process).
    """
    global _server_started
    port = port or METRICS_PORT
    with _server_lock:
        if _server_started:
            return False
        try:
            start_http_server(port)
        except OSError as exc:
            # Most likely the server was already started by a previous import of
            # this module (Streamlit hot reload) or another process owns the port.
            logger.warning("Metrics server not started on port %s: %s", port, exc)
            _server_started = True
            return False
        _server_started = True
        APP_INFO.info({"version": APP_VERSION})
        logger.info("Prometheus metrics available on :%s/metrics", port)
        return True


def observe_inputs(area: float, bedrooms: float, bathrooms: float, age: float, distance: float) -> None:
    """Record the feature values of a prediction request."""
    INPUT_AREA.observe(area)
    INPUT_BEDROOMS.observe(bedrooms)
    INPUT_BATHROOMS.observe(bathrooms)
    INPUT_AGE.observe(age)
    INPUT_DISTANCE.observe(distance)
