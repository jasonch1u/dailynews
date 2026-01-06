from playwright.sync_api import Page, expect, sync_playwright

def verify_sticky_header_ui(page: Page):
    # 1. Arrange: Go to the app
    print("Navigating to http://localhost:3000")
    page.goto("http://localhost:3000")

    # 2. Check title
    expect(page).to_have_title("每日新聞 AI 摘要")

    # 3. Check Header existence and sticky property (via computed style, or just visual presence at top)
    header = page.locator("header")
    expect(header).to_be_visible()

    # 4. Check controls inside header
    header_controls = header.locator(".header-controls")
    expect(header_controls).to_be_visible()

    # Check Dropdown source button
    source_btn = header_controls.locator(".source-btn")
    expect(source_btn).to_contain_text("來源篩選")

    # Check Date Select
    date_select = header_controls.locator("#historySelect")
    expect(date_select).to_be_visible()

    # 5. Check Layout Grid
    main_container = page.locator(".main-container")
    expect(main_container).to_be_visible()

    # 6. Screenshot
    page.screenshot(path="/home/jules/verification/sticky_header_ui.png")
    print("Screenshot taken.")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_sticky_header_ui(page)
        except Exception as e:
            print(f"Verification failed: {e}")
            page.screenshot(path="/home/jules/verification/error.png")
        finally:
            browser.close()
