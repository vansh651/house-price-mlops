"""Process entrypoint: start the Prometheus endpoint, then run Streamlit.

Streamlit only executes ``app.py`` once a browser session connects, so starting
the metrics server from the app script would leave ``/metrics`` unavailable on
idle replicas and Prometheus would report them as down. This launcher starts
the metrics server at process start and then runs Streamlit in the *same*
process, so the metrics recorded by ``app.py`` are the ones being served.

Usage (extra arguments are passed to ``streamlit run``):

    python streamlit_app/launcher.py
    python streamlit_app/launcher.py --server.port=8080
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # so ``import metrics`` resolves like it does in app.py

from metrics import start_metrics_server  # noqa: E402
from streamlit.web import cli as streamlit_cli  # noqa: E402


def main() -> None:
    start_metrics_server()
    sys.argv = [
        "streamlit",
        "run",
        str(HERE / "app.py"),
        "--server.address=0.0.0.0",
        "--server.port=8501",
        *sys.argv[1:],
    ]
    sys.exit(streamlit_cli.main())


if __name__ == "__main__":
    main()
