import time

import streamlit as st

from metrics import (
    MODEL_LOAD_SECONDS,
    MODEL_LOADED,
    PREDICTED_PRICE,
    PREDICTION_ERRORS,
    PREDICTION_LATENCY,
    PREDICTIONS,
    SCRIPT_RUNS,
    observe_inputs,
    start_metrics_server,
)
from model import load_model


@st.cache_resource
def get_model():
    started = time.perf_counter()
    model = load_model()
    MODEL_LOAD_SECONDS.set(time.perf_counter() - started)
    MODEL_LOADED.set(1)
    return model


@st.cache_resource
def init_metrics():
    # Starts the Prometheus /metrics endpoint once per process (default :8000).
    return start_metrics_server()


st.set_page_config(page_title="House Price Predictor", page_icon="🏠")
init_metrics()
SCRIPT_RUNS.inc()

st.title("🏠 House Price Predictor")
st.caption("Estimate a property's market value using the local ML model.")

with st.form("prediction"):
    area = st.number_input("Living area (sq ft)", min_value=50.0, value=1500.0, step=50.0)
    bedrooms = st.number_input("Bedrooms", min_value=1, max_value=20, value=3)
    bathrooms = st.number_input("Bathrooms", min_value=1.0, max_value=20.0, value=2.0, step=0.5)
    age = st.number_input("Property age (years)", min_value=0.0, max_value=200.0, value=10.0)
    distance = st.number_input("Distance to city (km)", min_value=0.0, max_value=500.0, value=10.0)
    submitted = st.form_submit_button("Predict price")

if submitted:
    values = [[area, bedrooms, bathrooms, age, distance]]
    try:
        model = get_model()
        started = time.perf_counter()
        predicted_price = float(model.predict(values)[0])
        PREDICTION_LATENCY.observe(time.perf_counter() - started)
    except Exception:
        PREDICTION_ERRORS.inc()
        raise
    PREDICTIONS.inc()
    PREDICTED_PRICE.observe(predicted_price)
    observe_inputs(area, bedrooms, bathrooms, age, distance)
    st.success(f"Estimated price: ${predicted_price:,.2f}")
