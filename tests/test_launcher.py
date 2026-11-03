import sys
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "streamlit_app"))

from metrics import start_metrics_server


def test_start_metrics_server_and_scrape():
    # Use port 8000 (default) or an ephemeral test port
    started = start_metrics_server(port=8000)
    # Even if already started, calling again returns False safely
    second_start = start_metrics_server(port=8000)
    assert second_start is False

    # Scrape metrics endpoint
    url = "http://127.0.0.1:8000/metrics"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=5) as response:
        assert response.status == 200
        content = response.read().decode("utf-8")
        assert "house_predictor_app_info" in content
