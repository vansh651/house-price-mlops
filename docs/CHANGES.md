# Changes Log

This document tracks every file edited, created, or removed during local verification, along with the rationale for each change.

| File | Action | Reason |
|------|--------|--------|
| `.gitignore` | Modified | Added `.env` and `powershell.bat` to keep sensitive credentials and temporary shell wrappers out of version control. |
| `Dockerfile` | Modified | Fixed entrypoint command to run `["python", "streamlit_app/launcher.py"]` so metrics endpoint on port 8000 is started immediately before browser visits; added non-root user `appuser` (uid 10001) with appropriate `/app` directory ownership for container security. |
| `requirements-dev.txt` | Created | Added developer requirements (`pytest`, `playwright`, `requests`) referencing `requirements.txt` for local verification and automated testing. |
| `tests/__init__.py` | Created | Python package marker for test suite. |
| `tests/test_model.py` | Created | Added automated tests for model training, lazy loading, and prediction output shape/validity. |
| `tests/test_metrics.py` | Created | Added automated tests for Prometheus metrics registration reload-safety and input observations. |
| `tests/test_launcher.py` | Created | Added automated tests for launcher metrics server startup and scrape response. |
| `scripts/drive_ui.py` | Created | Headless browser script using Playwright to drive Streamlit UI predictions, test edge inputs, attempt forced failures, and capture screenshots. |
| `scripts/capture_screenshots.py` | Created | Headless browser script to capture visual evidence of Prometheus Targets, Prometheus Alerts, and Grafana Dashboard. |
| `scripts/verify_prometheus_and_grafana.py` | Created | Automated verification script to test all Prometheus targets, execute all 8 required Prometheus queries, verify alert rules, test Grafana datasource health, and query all 20 Grafana dashboard panel expressions. |
| `terraform/main.tf` | Formatted | Formatted via `terraform fmt` to resolve formatting discrepancies. |
| `terraform/versions.tf` | Formatted | Formatted via `terraform fmt` to resolve formatting discrepancies. |
| `terraform/.terraform.lock.hcl` | Created | Created by `terraform init` to lock provider versions. |
| `k8s/streamlit-deployment.yaml` | Modified | Added container resource requests (`100m` cpu, `256Mi` memory) and limits (`1000m` cpu, `1Gi` memory), added readiness and liveness HTTP probes on path `/_stcore/health` (port 8501), and added the container metrics port (8000) to the Service for port-forwarding while preserving the placeholder image `ghcr.io/your-org/house-predictor:latest`. |
| `.github/workflows/ci-cd.yml` | Modified | Added `build-and-push` job to build and publish Docker image to GitHub Container Registry (GHCR) on push to `main`, aligning the workflow with the README description; validated with `actionlint`. |
| `docs/evidence/*` | Created | Saved raw command outputs for `docker images`, `docker ps`, `kubectl get all -n house-predictor -o wide`, and `kubectl get all -n monitoring -o wide`. |
| `docs/screenshots/*` | Created | Captured visual evidence screenshots of Streamlit prediction UI, Prometheus Targets, Prometheus Alerts, and Grafana Dashboard. |
| `docs/LOCAL_VERIFICATION.md` | Created | Full step-by-step verification log recording commands, outputs, and PASS/FAIL statuses. |
| `docs/FINAL_LOCAL_REPORT.md` | Created | Comprehensive final verification report. |
