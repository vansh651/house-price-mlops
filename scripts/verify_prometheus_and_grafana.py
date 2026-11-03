"""Comprehensive verification of Prometheus targets, queries, rules, and Grafana panels."""

import json
import re
import sys
import time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent

# Read Grafana password from .env
env_file = ROOT / ".env"
grafana_password = ""
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("GRAFANA_ADMIN_PASSWORD="):
            grafana_password = line.split("=", 1)[1].strip()

PROM_URL = "http://localhost:9090"
GRAF_URL = "http://localhost:3000"


def check_prometheus_targets():
    print("--- 1. Prometheus Targets ---")
    resp = requests.get(f"{PROM_URL}/api/v1/targets", timeout=10)
    data = resp.json()
    targets = data.get("data", {}).get("activeTargets", [])
    print(f"Total active targets: {len(targets)}")
    for t in targets:
        job = t.get("labels", {}).get("job")
        health = t.get("health")
        pod = t.get("labels", {}).get("pod", "N/A")
        ns = t.get("labels", {}).get("namespace", "N/A")
        url = t.get("scrapeUrl")
        print(f"  Job: {job} | Health: {health} | Namespace: {ns} | Pod: {pod} | URL: {url}")
    return targets


def check_prometheus_queries():
    print("\n--- 2. Prometheus Required Queries ---")
    queries = [
        ("house_predictor_predictions_total", "house_predictor_predictions_total"),
        ("latency_p95", "histogram_quantile(0.95, sum by (le) (rate(house_predictor_prediction_latency_seconds_bucket[5m])))"),
        ("script_runs", "house_predictor_script_runs_total"),
        ("prediction_errors", "house_predictor_prediction_errors_total"),
        ("model_loaded", "house_predictor_model_loaded"),
        ("model_load_seconds", "house_predictor_model_load_seconds"),
        ("app_info", "house_predictor_app_info"),
        ("process_resident_memory_bytes", "process_resident_memory_bytes"),
    ]
    for label, q in queries:
        resp = requests.get(f"{PROM_URL}/api/v1/query", params={"query": q}, timeout=10)
        res = resp.json().get("data", {}).get("result", [])
        print(f"Query [{label}]: {q}")
        print(f"  Result count: {len(res)}")
        for item in res[:3]:
            metric = item.get("metric", {})
            val = item.get("value", [])
            print(f"    Metric: {metric} => Value: {val}")


def check_prometheus_rules():
    print("\n--- 3. Prometheus Alert Rules ---")
    resp = requests.get(f"{PROM_URL}/api/v1/rules", timeout=10)
    groups = resp.json().get("data", {}).get("groups", [])
    print(f"Rule groups found: {len(groups)}")
    for g in groups:
        print(f"Group: {g.get('name')} (file: {g.get('file')})")
        for r in g.get("rules", []):
            print(f"  Rule: {r.get('name')} | State: {r.get('state')} | Query: {r.get('query')}")


def check_grafana():
    print("\n--- 4. Grafana API Verification ---")
    auth = ("admin", grafana_password)

    # 4.1 Datasource health
    ds_resp = requests.get(f"{GRAF_URL}/api/datasources/uid/prometheus/health", auth=auth, timeout=10)
    print(f"Datasource 'prometheus' health check status: {ds_resp.status_code}")
    print(f"Datasource health response: {ds_resp.text}")

    # 4.2 Dashboard check
    dash_resp = requests.get(f"{GRAF_URL}/api/dashboards/uid/house-predictor", auth=auth, timeout=10)
    print(f"Dashboard 'house-predictor' fetch status: {dash_resp.status_code}")
    dash_json = dash_resp.json()
    meta = dash_json.get("meta", {})
    folder_title = meta.get("folderTitle")
    title = dash_json.get("dashboard", {}).get("title")
    print(f"Dashboard Title: '{title}', Folder: '{folder_title}'")

    # 4.3 Query every panel's PromQL
    panels = dash_json.get("dashboard", {}).get("panels", [])
    print(f"\nEvaluating queries for {len(panels)} panels:")
    now_ms = int(time.time() * 1000)
    from_ms = now_ms - (60 * 60 * 1000)  # last 1h

    for p in panels:
        p_title = p.get("title", f"Panel {p.get('id')}")
        targets = p.get("targets", [])
        for t in targets:
            expr = t.get("expr")
            if not expr:
                continue
            # Substitute Grafana template variables
            # $instance -> .*
            # $__rate_interval -> 1m
            # $__range -> 1h
            sub_expr = expr.replace("$instance", ".*").replace("${instance}", ".*")
            sub_expr = sub_expr.replace("$__rate_interval", "1m").replace("${__rate_interval}", "1m")
            sub_expr = sub_expr.replace("$__range", "1h").replace("${__range}", "1h")

            # Query via Grafana ds query API
            payload = {
                "queries": [
                    {
                        "refId": t.get("refId", "A"),
                        "datasource": {"uid": "prometheus", "type": "prometheus"},
                        "expr": sub_expr,
                        "instant": t.get("instant", False),
                        "range": not t.get("instant", False),
                    }
                ],
                "from": str(from_ms),
                "to": str(now_ms),
            }
            q_resp = requests.post(f"{GRAF_URL}/api/ds/query", json=payload, auth=auth, timeout=10)
            status = q_resp.status_code
            result_frames = q_resp.json().get("results", {}).get(t.get("refId", "A"), {}).get("frames", [])
            print(f"  Panel '{p_title}' [ref: {t.get('refId')}]: Expr='{expr}'")
            print(f"    Substituted: '{sub_expr}' => HTTP {status}, Frames: {len(result_frames)}")


if __name__ == "__main__":
    check_prometheus_targets()
    check_prometheus_queries()
    check_prometheus_rules()
    check_grafana()
