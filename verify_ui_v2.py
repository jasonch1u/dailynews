from playwright.sync_api import sync_playwright

def verify_frontend():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 1. Load the HTML content from templates.py again
        import api.templates
        html_content = api.templates.HTML_CONTENT

        with open("/home/jules/verification/temp_ui_v2.html", "w") as f:
            f.write(html_content)

        page = browser.new_page()
        page.goto("file:///home/jules/verification/temp_ui_v2.html")

        # 2. Click liquidity badge to open modal
        page.locator("#liquidity-badge").click()
        page.wait_for_selector("#chartModal")

        # 3. Check DXY Button Text
        dxy_btn = page.locator("#btn-DXY_BROAD")
        if dxy_btn.inner_text().strip() == "DXY_BROAD":
             print("DXY Button Text Correct: DXY_BROAD")
        else:
             print(f"DXY Button Text Incorrect: {dxy_btn.inner_text()}")

        # 4. Take Screenshot to check layout spacing
        page.screenshot(path="/home/jules/verification/frontend_verify_v2.png")
        print("Screenshot taken.")

        browser.close()

if __name__ == "__main__":
    verify_frontend()
