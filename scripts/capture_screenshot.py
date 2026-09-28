"""Capture a full-page screenshot of the running dashboard for the README."""
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8513/"
OUT = Path(__file__).resolve().parents[1] / "docs" / "dashboard_overview.png"

# Streamlit scrolls inside an inner container, so full_page=True only grabs the
# viewport. Force the app shell to grow to its natural height first.
EXPAND_CSS = """
html, body, .stApp, [data-testid="stAppViewContainer"], .stMain,
[data-testid="stMainBlockContainer"], section.main { height: auto !important; overflow: visible !important; }
.stMain { overflow: visible !important; }
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], #MainMenu, .stAppDeployButton,
[data-testid="stAppDeployButton"], [data-testid="stSidebarCollapseButton"] { display: none !important; }
"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1600, "height": 1200}, device_scale_factor=1)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_selector("text=ISP Network Reliability Dashboard", timeout=30000)
    page.wait_for_timeout(7000)
    page.add_style_tag(content=EXPAND_CSS)
    page.wait_for_timeout(1500)
    page.screenshot(path=str(OUT), full_page=True)
    browser.close()
print(f"saved {OUT}")
