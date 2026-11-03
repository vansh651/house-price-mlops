"""Headless browser script to drive the Streamlit UI, generate traffic, test edge inputs and forced error."""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SCREENSHOT_DIR = ROOT / "docs" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
OUTPUT_SCREENSHOT = sys.argv[2] if len(sys.argv) > 2 else "streamlit_prediction_kind.png"


def run():
    print(f"Connecting to Streamlit UI at {URL}...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)

        # Wait for Streamlit title
        page.wait_for_selector("h1:has-text('House Price Predictor')", timeout=15000)
        print("Page loaded successfully.")

        predict_button = page.locator("button:has-text('Predict price')")
        predict_button.wait_for(state="visible", timeout=10000)

        # 1. Prediction with default inputs
        predict_button.click()
        page.wait_for_timeout(2000)
        success_alert = page.locator("[data-testid='stAlert']:has-text('Estimated price')")
        success_alert.wait_for(state="visible", timeout=10000)
        print(f"Prediction 1 (defaults): {success_alert.inner_text()}")

        # Capture screenshot for evidence
        screenshot_path = SCREENSHOT_DIR / OUTPUT_SCREENSHOT
        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"Saved screenshot to {screenshot_path}")

        # 2. Varied inputs: larger house
        inputs = page.locator("input[type='number']")
        if inputs.count() >= 5:
            inputs.nth(0).fill("3200")
            inputs.nth(1).fill("5")
            inputs.nth(2).fill("3.5")
            inputs.nth(3).fill("2")
            inputs.nth(4).fill("5")
            predict_button.click()
            page.wait_for_timeout(2000)
            success_alert.wait_for(state="visible", timeout=10000)
            print(f"Prediction 2 (large house): {success_alert.inner_text()}")

            # 3. Varied inputs: older suburban house
            inputs.nth(0).fill("1800")
            inputs.nth(1).fill("3")
            inputs.nth(2).fill("1.5")
            inputs.nth(3).fill("45")
            inputs.nth(4).fill("25")
            predict_button.click()
            page.wait_for_timeout(2000)
            success_alert.wait_for(state="visible", timeout=10000)
            print(f"Prediction 3 (suburban): {success_alert.inner_text()}")

            # 4. Edge inputs (minimum possible valid inputs)
            inputs.nth(0).fill("100")
            inputs.nth(1).fill("1")
            inputs.nth(2).fill("1.0")
            inputs.nth(3).fill("0.0")
            inputs.nth(4).fill("0.0")
            predict_button.click()
            page.wait_for_timeout(2000)
            success_alert.wait_for(state="visible", timeout=10000)
            print(f"Prediction 4 (edge minimum): {success_alert.inner_text()}")

            # 5. Forced failure test: clear an input field or pass invalid text so model throws
            try:
                print("Attempting to trigger a prediction error safely...")
                inputs.nth(0).click()
                inputs.nth(0).press("Control+A")
                inputs.nth(0).press("Backspace")
                # When living area is cleared (None), Streamlit form submits None which triggers ValueError in RandomForest
                predict_button.click()
                page.wait_for_timeout(2000)
                # Look for exception box or error message
                error_box = page.locator("[data-testid='stException'], [data-testid='stAlert']:has-text('Error')")
                if error_box.count() > 0:
                    print(f"Forced error successfully triggered: {error_box.first.inner_text()[:80]}...")
                else:
                    print("Form submission completed.")
            except Exception as e:
                print(f"Error triggering attempt handled: {e}")

        browser.close()


if __name__ == "__main__":
    run()
