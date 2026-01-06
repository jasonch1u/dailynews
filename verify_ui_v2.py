from playwright.sync_api import Page, expect, sync_playwright

def verify_ui_updates(page: Page):
    # 1. Arrange: Go to the app
    print("Navigating to http://localhost:3000")
    page.goto("http://localhost:3000")

    # 2. Check title
    expect(page).to_have_title("每日新聞 AI 摘要")
    print("Title verified.")

    # 3. Check for checkboxes
    checkboxes = page.locator(".source-checkboxes input[type=checkbox]")
    count = checkboxes.count()
    print(f"Found {count} checkboxes.")
    if count != 3:
        raise Exception("Expected 3 checkboxes")

    # 4. Check for CSS Card (by checking class existence or layout structure)
    # Just visually checking via screenshot is enough for now.
    controls = page.locator(".controls-container")
    expect(controls).to_be_visible()

    # 5. Screenshot
    page.screenshot(path="/home/jules/verification/new_ui.png")
    print("Screenshot taken.")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_ui_updates(page)
        except Exception as e:
            print(f"Verification failed: {e}")
            page.screenshot(path="/home/jules/verification/error.png")
        finally:
            browser.close()
