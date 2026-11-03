"""Capture screenshots of Prometheus and Grafana."""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SCREENSHOT_DIR = ROOT / "docs" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

PREFIX = sys.argv[1] if len(sys.argv) > 1 else "kind"

# Read password from .env
env_file = ROOT / ".env"
grafana_password = "admin"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("GRAFANA_ADMIN_PASSWORD="):
            grafana_password = line.split("=", 1)[1].strip()


def capture():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()

        # 1. Prometheus Targets
        print("Capturing Prometheus Targets...")
        page.goto("http://localhost:9090/targets", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(3000)
        page.screenshot(path=str(SCREENSHOT_DIR / f"prometheus_targets_{PREFIX}.png"), full_page=True)

        # 2. Prometheus Alerts
        print("Capturing Prometheus Alerts...")
        page.goto("http://localhost:9090/alerts", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(3000)
        page.screenshot(path=str(SCREENSHOT_DIR / f"prometheus_alerts_{PREFIX}.png"), full_page=True)

        # 3. Grafana Dashboard
        print("Capturing Grafana Dashboard...")
        page.goto("http://localhost:3000/login", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(2000)
        if page.locator("input[name='user']").is_visible():
            page.locator("input[name='user']").fill("admin")
            page.locator("input[name='password']").fill(grafana_password)
            page.locator("button[type='submit']").click()
            page.wait_for_timeout(3000)
            skip_btn = page.locator("button:has-text('Skip')")
            if skip_btn.is_visible():
                skip_btn.click()
                page.wait_for_timeout(2000)

        # Navigate to house-predictor dashboard
        page.goto("http://localhost:3000/d/house-predictor", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(5000)
        page.screenshot(path=str(SCREENSHOT_DIR / f"grafana_dashboard_{PREFIX}.png"), full_page=True)

        browser.close()
        print("Screenshots captured successfully.")


if __name__ == "__main__":
    capture()
