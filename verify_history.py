from playwright.sync_api import Page, expect, sync_playwright

def verify_history_ui(page: Page):
    # 1. Arrange: Go to the app
    print("Navigating to http://localhost:3000")
    page.goto("http://localhost:3000")

    # 2. Check title
    expect(page).to_have_title("每日新聞 AI 摘要")
    print("Title verified.")

    # 3. Check for new UI elements
    # History Select Dropdown
    history_select = page.locator("#historySelect")
    expect(history_select).to_be_visible()
    print("History dropdown found.")

    # 4. Screenshot
    page.screenshot(path="/home/jules/verification/history_ui.png")
    print("Screenshot taken.")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_history_ui(page)
        except Exception as e:
            print(f"Verification failed: {e}")
            page.screenshot(path="/home/jules/verification/error.png")
        finally:
            browser.close()
