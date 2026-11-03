# House Price Prediction MLOps Project

An end-to-end, self-contained Streamlit house price prediction system with:

- Streamlit user interface
- Scikit-learn model training
- Docker image and a docker-compose stack
- Prometheus metrics and a Grafana dashboard
- GitHub Actions CI and container publishing
- Kubernetes deployment
- Terraform infrastructure for AWS EKS

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app/app.py
```

Open `http://localhost:8501`. The model trains or loads inside the Streamlit
process; no separate backend or API URL is required.

To also expose Prometheus metrics from the first second the process is up (rather
than after the first page visit), start the app through the launcher instead:

```bash
python streamlit_app/launcher.py     # UI on :8501, metrics on :8000/metrics
```

## Deploy the Streamlit app

1. Push this repository to GitHub.
2. On [share.streamlit.io](https://share.streamlit.io), choose **New app**,
   select this repository and branch, and set the main file to
   `streamlit_app/app.py`.
3. Click **Deploy**. The model is trained/loaded inside the Streamlit app.

## Docker

```bash
docker build -t house-predictor:local .
docker run --rm -p 8501:8501 house-predictor:local
```

## Monitoring (Prometheus + Grafana)

The app exposes Prometheus metrics on port `8000` (`/metrics`, configurable with
`METRICS_PORT`), separate from the Streamlit UI on `8501`.

| Metric | Type | What it tells you |
| --- | --- | --- |
| `house_predictor_predictions_total` | counter | Successful predictions served |
| `house_predictor_prediction_errors_total` | counter | Predictions that raised an exception |
| `house_predictor_prediction_latency_seconds` | histogram | Time spent in `model.predict()` |
| `house_predictor_script_runs_total` | counter | Page loads and widget interactions |
| `house_predictor_model_loaded`, `house_predictor_model_load_seconds` | gauge | Whether the model is in memory and how long loading/training took |
| `house_predictor_predicted_price_dollars` | histogram | Distribution of predictions (output drift) |
| `house_predictor_input_*` (area, bedrooms, bathrooms, age, distance) | histogram | Distribution of user inputs (input drift) |
| `house_predictor_app_info` | info | App version (set `APP_VERSION`) |
| `process_*`, `python_*` | various | CPU, memory, GC and file descriptors of the app process |

### Locally with docker-compose

```bash
docker compose up --build
```

| Service | URL |
| --- | --- |
| Streamlit app | http://localhost:8501 |
| Raw metrics | http://localhost:8000/metrics |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (`admin` / `admin`, override with `GRAFANA_ADMIN_PASSWORD`) |

Grafana provisions the Prometheus datasource and the **House Price Predictor**
dashboard (folder *House Predictor*) automatically. Make a few predictions in the
app and the panels fill in within ~15 seconds.

### On Kubernetes

Prometheus and Grafana run in a separate `monitoring` namespace. Prometheus discovers
the `house-predictor-ui` pods through the Kubernetes API and scrapes their `metrics`
container port, so new replicas are picked up automatically.

```bash
kubectl apply -f k8s/namespace.yaml                      # app namespace (Prometheus has a Role in it)
kubectl apply -f k8s/streamlit-deployment.yaml

# 1. set a real Grafana admin password in k8s/monitoring/21-grafana-secret.yaml
#    (or create the secret yourself and delete that file)
# 2. then:
kubectl apply -f k8s/monitoring/

kubectl -n monitoring port-forward svc/grafana 3000:3000        # http://localhost:3000
kubectl -n monitoring port-forward svc/prometheus 9090:9090     # http://localhost:9090
```

Notes:

- The Prometheus and Grafana data directories use `emptyDir`, so metric history is lost
  if the pod is rescheduled. Switch to a PersistentVolumeClaim (on EKS this needs the
  EBS CSI driver add-on) if you need retention.
- Alert rules (`monitoring/prometheus/alerts.yml`) are evaluated by Prometheus and visible
  in its **Alerts** page. No Alertmanager is deployed, so nothing is sent anywhere yet.
- `monitoring/` is the single source of truth for the dashboard, datasource and alert rules.
  After editing them, regenerate the Kubernetes ConfigMaps (CI fails if they are stale):

  ```bash
  python scripts/sync_k8s_monitoring.py
  ```

## Kubernetes

Build and publish the image, then replace
`ghcr.io/your-org/house-predictor:latest` in
`k8s/streamlit-deployment.yaml`:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/streamlit-deployment.yaml
```

The Streamlit manifest uses a `LoadBalancer` service. For local clusters, use
`minikube tunnel` or `kubectl port-forward`.

## AWS infrastructure

The Terraform module provisions an EKS cluster and node group. Configure AWS
credentials and run:

```bash
cd terraform
terraform init
terraform plan -var='cluster_name=house-predictor'
terraform apply -var='cluster_name=house-predictor'
```

## CI/CD

`.github/workflows/ci-cd.yml` checks Python syntax, smoke-tests the metrics module,
validates the Grafana dashboard / Prometheus config and builds the image on every
pull request. On pushes to `main`, it publishes the image to GitHub Container
Registry and updates the Streamlit Kubernetes deployment. Set repository
permissions to allow `packages: write` and configure a cluster context secret
named `KUBE_CONFIG` for deployment.

## Model

The included Streamlit model helper creates a deterministic demonstration
dataset using common housing features. Replace the training logic in
`streamlit_app/model.py` with your production dataset pipeline when real data
is available.
