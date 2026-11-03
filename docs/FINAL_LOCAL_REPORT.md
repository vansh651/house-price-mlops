# Final Local Verification Report: House Price Predictor MLOps Stack

**Author / Role**: Autonomous Senior DevOps / MLOps Engineer  
**Verification Date**: 2026-11-02  
**Target Project**: House Price Predictor (`vedika-mlops-project`)  
**Host Environment**: Windows 11 Home Single Language (ARM64), 16 GB RAM, Docker Desktop 4.45.0, Kubernetes v1.29.2 (kind)

---

## 1. Executive Summary & Verification Matrix

| Component | Status | One-Line Evidence Reference |
|-----------|--------|-----------------------------|
| **Python / ML** | TESTED | 6/6 pytest unit tests passed; model trained and loaded from `streamlit_app/house_price_model.joblib`. |
| **Docker** | TESTED | Built `house-predictor:local` (792 MB); verified non-root execution (`uid=10001`) and `:8000/metrics` up before browser visit. |
| **Docker Compose** | TESTED | `docker compose up --build -d` ran `app`, `prometheus`, `grafana` with 200 OK on 8501, 8000, 9090, 3000; clean `docker compose down`. |
| **Terraform (AWS EKS + VPC)** | TESTED | `terraform fmt -check`, `terraform init` (AWS v5.100.0, modules `eks ~> 20.0`, `vpc ~> 5.0`), and `terraform validate` passed. |
| **Terraform Plan / Apply** | NOT VERIFIED | Apply prohibited by rule (cloud cost drivers: EKS $73/mo, NAT Gateway $32/mo, 2x t3.medium $60/mo). Plan requires explicit user cloud authorization. |
| **Kubernetes (local kind)** | RUNNING | Kind cluster `house-predictor` created with local image loaded; 2 app replicas running 1/1 with probes and resource limits. |
| **Prometheus** | RUNNING | Prometheus active on port 9090; scraping 2/2 app pods in kind; all 8 PromQL metrics returning non-empty series. |
| **Alerts** | TESTED | 3 alert rules loaded (`HousePredictorDown`, `HousePredictorHighErrorRate`, `HousePredictorHighLatency`) verified via `/api/v1/rules`. |
| **Grafana** | RUNNING | Grafana 13.3.0 running on port 3000; datasource healthy; all 20 panel PromQL queries verified returning data frames via API. |
| **Standalone Mode** | TESTED | Plain `streamlit run` confirmed `:8000/metrics` stays closed (000) until first user interaction; `launcher.py` opens metrics immediately (200). |
| **GitHub Actions** | TESTED | Validated with `actionlint`; reproduced all CI checks locally (py_compile, smoke test, json, sync, promtool config validation). |
| **Remote GitHub Runs** | NOT VERIFIED | Local GitHub CLI (`gh`) is unauthenticated (`You are not logged into any GitHub hosts`); remote runs not checked. |

---

## 2. Model Facts & Synthetic Data Notice

> [!WARNING]
> **SYNTHETIC TRAINING DATA NOTICE**:
> The training data used by this application is **SYNTHETIC BY DESIGN**, generated procedurally inside [`streamlit_app/model.py`](file:///C:/Users/jainam/Downloads/vedika-mlops-project/streamlit_app/model.py#L13-L39) using `numpy.random.default_rng(42)` across 500 generated rows.
> Therefore, any model accuracy, $R^2$ score, or prediction valuation is strictly a **synthetic demonstration of an MLOps pipeline** and constitutes **no real-world housing quality or price claim**.

- **Active Model Path**: `streamlit_app/house_price_model.joblib` (generated in-process at first load).
- **Unused Artifact**: The pre-existing file `models/house_price_model.joblib` located at the root of the repository is **NOT used** by the application runtime.
- **Model Architecture**: Scikit-learn `Pipeline` composed of `StandardScaler()` and `RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)`.
- **Inference Input Shape**: 5 features `[area, bedrooms, bathrooms, age, distance]`.

---

## 3. Real Runtime Evidence

### 3.1 Docker Images (`docker images`)
```text
REPOSITORY        TAG       IMAGE ID       CREATED          SIZE
house-predictor   local     fd5650f46d2b   25 minutes ago   792MB
prom/prometheus   v3.15.1   345c03f8738a   11 days ago      250MB
grafana/grafana   13.3.0    d2bd57647b75   6 days ago       1.36GB
```

### 3.2 Docker Process Status (`docker ps`)
```text
CONTAINER ID   IMAGE                  COMMAND                  CREATED          STATUS          PORTS                       NAMES
99d85cbf11c4   kindest/node:v1.29.2   "/usr/local/bin/entr…"   20 minutes ago   Up 19 minutes   127.0.0.1:58497->6443/tcp   house-predictor-control-plane
```

### 3.3 Kubernetes: `house-predictor` Namespace (`kubectl get all -n house-predictor -o wide`)
```text
NAME                                      READY   STATUS    RESTARTS   AGE     IP            NODE                            NOMINATED NODE   READINESS GATES
pod/house-predictor-ui-687b46c966-g5hdl   1/1     Running   0          5m42s   10.244.0.19   house-predictor-control-plane   <none>           <none>
pod/house-predictor-ui-687b46c966-tw5kq   1/1     Running   0          5m42s   10.244.0.20   house-predictor-control-plane   <none>           <none>

NAME                         TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)                       AGE   SELECTOR
service/house-predictor-ui   LoadBalancer   10.96.116.33   <pending>     80:31316/TCP,8000:31021/TCP   17m   app=house-predictor-ui

NAME                                 READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                  SELECTOR
deployment.apps/house-predictor-ui   2/2     2            2           17m   streamlit    house-predictor:local   app=house-predictor-ui

NAME                                            DESIRED   CURRENT   READY   AGE   CONTAINERS   IMAGES                  SELECTOR
replicaset.apps/house-predictor-ui-687b46c966   2         2         2       11m   streamlit    house-predictor:local   app=house-predictor-ui,pod-template-hash=687b46c966
```

### 3.4 Kubernetes: `monitoring` Namespace (`kubectl get all -n monitoring -o wide`)
```text
NAME                             READY   STATUS    RESTARTS   AGE   IP            NODE                            NOMINATED NODE   READINESS GATES
pod/grafana-67f59dddcb-6b8mv     1/1     Running   0          11m   10.244.0.17   house-predictor-control-plane   <none>           <none>
pod/prometheus-887c4cb69-n59nr   1/1     Running   0          11m   10.244.0.16   house-predictor-control-plane   <none>           <none>

NAME                 TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE   SELECTOR
service/grafana      ClusterIP   10.96.45.27    <none>        3000/TCP   17m   app=grafana
service/prometheus   ClusterIP   10.96.101.54   <none>        9090/TCP   17m   app=prometheus

NAME                         READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                    SELECTOR
deployment.apps/grafana      1/1     1            1           17m   grafana      grafana/grafana:13.3.0    app=grafana
deployment.apps/prometheus   1/1     1            1           17m   prometheus   prom/prometheus:v3.15.1   app=prometheus

NAME                                   DESIRED   CURRENT   READY   AGE   CONTAINERS   IMAGES                    SELECTOR
replicaset.apps/grafana-67f59dddcb     1         1         1       11m   grafana      grafana/grafana:13.3.0    app=grafana,pod-template-hash=67f59dddcb
replicaset.apps/prometheus-887c4cb69   1         1         1       11m   prometheus   prom/prometheus:v3.15.1   app=prometheus,pod-template-hash=887c4cb69
```

---

## 4. Live Local Access Endpoints

The stack is currently **RUNNING** on the local kind Kubernetes cluster via active port-forward daemons:

| Service | Local URL | Authentication / Credentials |
|---------|-----------|------------------------------|
| **Streamlit UI** | [http://localhost:8501](http://localhost:8501) | None (Public) |
| **Prometheus Metrics Endpoint** | [http://localhost:8000/metrics](http://localhost:8000/metrics) | None (Scraped by Prometheus) |
| **Prometheus Dashboard & API** | [http://localhost:9090](http://localhost:9090) | None (Targets: `/targets`, Alerts: `/alerts`) |
| **Grafana Dashboard** | [http://localhost:3000](http://localhost:3000) | Username: `admin` \| Password: stored in gitignored `.env` (`GRAFANA_ADMIN_PASSWORD`) |

---

## 5. Summary of Files Changed

1. **`.gitignore`**: Added `.env` and `powershell.bat` to prevent secret leakage and local environment artifacts from entering git.
2. **`Dockerfile`**:
   - Replaced direct `streamlit run` CMD with `["python", "streamlit_app/launcher.py"]` so Prometheus metrics on port 8000 start immediately at container launch.
   - Added unprivileged user `appuser` (`uid 10001`) with ownership of `/app` to run as non-root securely.
3. **`k8s/streamlit-deployment.yaml`**:
   - Added container resource requests (`100m` CPU, `256Mi` RAM) and limits (`1000m` CPU, `1Gi` RAM).
   - Added `readinessProbe` and `livenessProbe` on path `/_stcore/health` (port 8501).
   - Added container port `metrics` (8000) to the Service to support local port-forwarding while preserving the placeholder image `ghcr.io/your-org/house-predictor:latest`.
4. **`requirements-dev.txt`**: Added `pytest`, `playwright`, and `requests` for development, automated testing, and headless verification.
5. **`tests/` (`test_model.py`, `test_metrics.py`, `test_launcher.py`)**: Added unit test suite covering model shapes, metric reload-safety, and launcher HTTP server.
6. **`scripts/` (`drive_ui.py`, `capture_screenshots.py`, `verify_prometheus_and_grafana.py`)**: Created automation scripts for headless browsing, screenshot evidence, and end-to-end API verification.
7. **`terraform/main.tf` & `terraform/versions.tf`**: Formatted with `terraform fmt`.
8. **`.github/workflows/ci-cd.yml`**: Added `build-and-push` job to build and publish the container image to GHCR upon pushing to `main`, fixing the README/workflow mismatch; validated with `actionlint`.

---

## 6. Stack Lifecycle Commands

### Start the Stack (Kubernetes / Kind)
```powershell
# 1. Switch context to kind
kubectl cluster-info --context kind-house-predictor

# 2. Start port-forwards
kubectl port-forward svc/house-predictor-ui -n house-predictor 8501:80 8000:8000 --address 0.0.0.0
kubectl port-forward svc/prometheus -n monitoring 9090:9090 --address 0.0.0.0
kubectl port-forward svc/grafana -n monitoring 3000:3000 --address 0.0.0.0
```

### Alternative Start with Docker Compose
```powershell
docker compose up --build -d
```

### Stop & Tear Down
```powershell
# Stop Docker Compose (if active)
docker compose down

# Delete Kind Cluster (if removing local k8s stack)
kind delete cluster --name house-predictor
```
