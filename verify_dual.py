from playwright.sync_api import sync_playwright
import os

def test_dual_chart():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"file://{os.path.abspath('temp_dual_test.html')}")

        # Inject mock data
        page.route("**/api/economics*", lambda route: route.fulfill(
            status=200,
            body='{"data": [{"date": "2023-01-01", "symbol": "M1_YOY", "value": 5}, {"date": "2023-02-01", "symbol": "M2_YOY", "value": 3}]}'
        ))

        # Open Modal
        page.click("#liquidity-badge")
        page.wait_for_selector("#chartModal", state="visible")

        # Switch to M1 vs M2
        page.click("#btn-M1_M2_YOY")

        # Verify Title
        title = page.locator("#chart-title").inner_text()
        print(f"Chart Title: {title}")
        assert "M1 vs M2" in title

        # Verify Description
        desc = page.locator("#chart-desc").inner_text()
        print(f"Desc: {desc}")
        assert "黃金交叉" in desc

        page.screenshot(path="verification_dual.png")

        browser.close()

if __name__ == "__main__":
    test_dual_chart()