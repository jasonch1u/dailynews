from playwright.sync_api import Page, expect, sync_playwright
import time

def verify_app(page: Page):
    # 1. Arrange: Go to the app
    print("Navigating to http://localhost:3000")
    page.goto("http://localhost:3000")

    # 2. Check title
    expect(page).to_have_title("每日新聞 AI 摘要")
    print("Title verified.")

    # 3. Check for button
    btn = page.locator("#generateBtn")
    expect(btn).to_be_visible()
    print("Button found.")

    # 4. Click button to trigger action
    btn.click()

    # 5. Wait for error message (expected since no keys)
    # The server should return 500 because GEMINI_API_KEY is missing.
    # The frontend catches this and shows "請求失敗" in red.
    # Or shows status message "❌ 發生錯誤: ..."

    status_div = page.locator("#status")
    # Wait for the status to contain error text
    expect(status_div).to_contain_text("❌", timeout=5000)
    print("Error message appeared as expected.")

    # 6. Screenshot
    page.screenshot(path="/home/jules/verification/verification.png")
    print("Screenshot taken.")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_app(page)
        except Exception as e:
            print(f"Verification failed: {e}")
            page.screenshot(path="/home/jules/verification/error.png")
        finally:
            browser.close()
