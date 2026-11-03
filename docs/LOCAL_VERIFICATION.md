# Local Verification Log

This document records every verification check, command executed, key output, and status during the end-to-end local verification of the House Price Predictor project.

## Environment Summary
- **OS**: Windows 11 Home Single Language (Version 10.0.26200, build 26200)
- **CPU Architecture**: ARM 64-bit Processor
- **Memory**: 16 GB Total RAM, ~1.8 GB free
- **Storage**: ~88.6 GB free on C:\
- **Python**: Python 3.11.9 (via pyenv-win)
- **Git**: git version 2.51.0.windows.1
- **Docker**: Docker Desktop 4.45.0, Engine 28.3.3 linux/arm64
- **Docker Compose**: Docker Compose version v2.39.2-desktop.1
- **Kind**: kind version 0.33.0
- **Kubectl**: Client Version v1.32.2
- **Terraform**: Terraform v1.16.6 windows_amd64
- **GitHub CLI**: gh version 2.103.3

## Verification Checks

| Step | Component | Command / Check | Key Output / Evidence | Status |
|------|-----------|-----------------|-----------------------|--------|
| 1 | Host Ports | `Get-NetTCPConnection -LocalPort 8501, 8000, 9090, 3000` | Ports 8501, 8000, 9090, 3000 confirmed completely FREE after stopping pre-existing unrelated container | PASS |
| 1 | Line Endings | File byte inspection | Mixed CRLF/LF on Windows; Dockerfile, app.py CRLF, docker-compose, sync script LF. Verified compatible. | PASS |
| 2 | Repository Tree | `Get-ChildItem -Recurse -File` | All required files exist and non-empty (Dockerfile, docker-compose.yml, requirements.txt, streamlit_app/*.py, monitoring/*, k8s/*, terraform/*, .github/*). | PASS |
| 2 | ConfigMaps Sync | `python scripts/sync_k8s_monitoring.py --check` | `k8s/monitoring ConfigMaps are up to date.` | PASS |
| 2 | Git Ignore | `.gitignore` inspection | Updated `.gitignore` to add `.env` and `powershell.bat`. State, joblib, and venvs ignored. | PASS |
| 3 | Python Virtualenv | `python -m venv .venv` & `pip install` | Python 3.11.9 `.venv` created, installed `requirements-dev.txt` (scikit-learn 1.6.1, streamlit 1.41.1, pytest 9.2.0, playwright 1.64.1). | PASS |
| 3 | Python Syntax | `python -m py_compile` | All files in `streamlit_app/` and `scripts/` compiled with exit code 0. | PASS |
| 3 | Unit Tests | `.venv\Scripts\pytest.exe -v tests` | 6 passed in 8.87s covering metrics reload-safety, model train/predict shape, and launcher HTTP scrape. | PASS |
| 3 | Model Artifact | `streamlit_app/model.py` execution | Model trained and saved to `streamlit_app/house_price_model.joblib` (3.65 MB). Training data is explicitly SYNTHETIC (500 random rows). `models/house_price_model.joblib` is not used by app. | PASS |
| 4 | Docker Build | `docker build -t house-predictor:local .` | Successfully built `house-predictor:local` (792 MB). Non-root user `appuser` (uid 10001) configured. | PASS |
| 4 | Docker Health & Launcher | `docker run` & curl before visit | `/_stcore/health` returned `ok`. `:8000/metrics` responded 200 with `house_predictor_app_info` BEFORE any browser visit. Runs as non-root `uid=10001`. | PASS |
| 4 | Headless UI Driver | `scripts/drive_ui.py` | Playwright submitted predictions ($351,104.08, $498,977.97, edge min $203,981.31). `house_predictor_predictions_total` incremented to 3.0. | PASS |
| 4 | Docker Compose | `docker compose up --build -d` | All 3 services (`app`, `prometheus`, `grafana`) started. Verified 200 OK on 8501, 8000, 9090, 3000. Clean `docker compose down`. | PASS |
| 5 | Terraform Format | `terraform fmt -check` | Detected unformatted `main.tf` and `versions.tf`. Executed `terraform fmt` which reformatted them cleanly. | PASS |
| 5 | Terraform Init | `terraform init` | Initialized AWS provider (v5.100.0) and modules (`eks ~> 20.0`, `vpc ~> 5.0`). Generated `.terraform.lock.hcl`. | PASS |
| 5 | Terraform Validate | `terraform validate` | `Success! The configuration is valid.` | PASS |
| 5 | Terraform Plan / Apply | AWS Credentials Check | AWS apply prohibited. Plan not executed as AWS requires explicit user confirmation for billable resources. Module targets VPC + EKS (cost drivers: control plane $73/mo, NAT Gateway $32/mo, 2x t3.medium $60/mo). | NOT VERIFIED (Cloud/Credentials) |
| 6 | Kubernetes Cluster | `kind create cluster --name house-predictor` | Created local kind cluster `house-predictor` (v1.29.2). Loaded `house-predictor:local` image. | PASS |
| 6 | K8s Placeholder & Image Override | `kubectl set image` | Manifest placeholder `ghcr.io/your-org/house-predictor:latest` showed `ErrImagePull`. Overrode via `kubectl set image deployment/house-predictor-ui streamlit=house-predictor:local`. Rollout succeeded. | PASS |
| 6 | K8s Probes & Resources | `k8s/streamlit-deployment.yaml` | Added CPU (100m/1000m) & memory (256Mi/1Gi) requests/limits, readinessProbe and livenessProbe on `/_stcore/health:8501`. Both pods 1/1 Running. | PASS |
| 6 | K8s Monitoring Deploy | `kubectl apply -f k8s/monitoring/` | Applied 00-namespace, 10-configmap, 11-prometheus, 20-configmaps, 22-grafana. Created `grafana-admin` secret from `.env` throwaway password. | PASS |
| 6 | K8s Port-Forward | `kubectl port-forward` | Port forwards established for app (8501:80, 8000:8000), Prometheus (9090:9090), and Grafana (3000:3000). All respond 200. | PASS |
| 6 | K8s Resilience | Pod deletion & rollout restart | Deleted 1 app pod; recovered to 1/1 within 6s. Executed `kubectl rollout restart` across app, Prometheus, Grafana; all rolled out cleanly and Prometheus rediscovered targets. | PASS |
| 7 | Prometheus Targets | `/api/v1/targets` | In both Compose and Kind, `house-predictor` target(s) are UP. In Kind: 2 targets discovered (`10.244.0.15:8000`, `10.244.0.18:8000`) with pod/namespace labels. | PASS |
| 7 | Prometheus Queries | `/api/v1/query` | All 8 required queries returned non-empty data: predictions_total, p95 latency, script_runs, prediction_errors, model_loaded, model_load_seconds, app_info, resident_memory. | PASS |
| 7 | Prometheus Alert Rules | `/api/v1/rules` | All 3 alert rules loaded: `HousePredictorDown`, `HousePredictorHighErrorRate`, `HousePredictorHighLatency`. | PASS |
| 8 | Grafana Health & Dashboards | `/api/datasources/uid/prometheus/health` | Datasource health status 200 OK. Dashboard `house-predictor` verified in folder `House Predictor`. | PASS |
| 8 | Grafana Panel Queries | `/api/ds/query` | Evaluated PromQL queries for all 20 panels in the dashboard. All returned HTTP 200 with active data frames. | PASS |
| 8 | Grafana Version Observation | Container image `grafana/grafana:13.3.0` | Pinned image `13.3.0` pulled and functioned properly. Note: 13.x represents current Grafana next-generation builds on Docker Hub. | PASS |
| 9 | Standalone Streamlit | `streamlit run streamlit_app/app.py` | UI healthy on 8501. Confirmed `:8000/metrics` returned connection refused (000) before browser visit, and came UP (200) after visit. | PASS |
| 9 | Standalone Launcher | `python streamlit_app/launcher.py` | Confirmed `:8000/metrics` responds 200 immediately at process start before any browser visit. | PASS |
| 10 | CI Workflow Validation | `actionlint` via Docker | Clean validation of `.github/workflows/ci-cd.yml` with exit code 0. | PASS |
| 10 | CI Local Reproduction | py_compile, smoke test, json, sync, promtool | All CI steps reproduced and passed locally (including `promtool check config`). | PASS |
| 10 | CI README Mismatch | Workflow vs README | Added missing `build-and-push` job to `.github/workflows/ci-cd.yml` to build and push container images to GHCR on `main`. | PASS |
| 10 | Remote GitHub Runs | `gh auth status` | GitHub CLI not authenticated on this machine (`You are not logged into any GitHub hosts`). | NOT VERIFIED (remote runs not checked) |
| 11 | Visual Evidence | Screenshots & Raw Logs | Screenshots saved to `docs/screenshots/` (UI predictions, Prometheus targets, alerts, Grafana dashboard). Raw logs saved to `docs/evidence/`. | PASS |
| 12 | Live Stack | Kind + Port-Forwards | Kind cluster `house-predictor` is running and accessible via localhost port-forwards on 8501, 8000, 9090, 3000. | PASS |
