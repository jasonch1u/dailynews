from playwright.sync_api import Page, expect, sync_playwright

def verify_link_renderer(page: Page):
    # 1. Arrange: Go to the app
    print("Navigating to http://localhost:3000")
    page.goto("http://localhost:3000")

    # 2. Inject test markdown with a link to verify rendering
    # We can execute JS to simulate what marked.parse would do, or just check if marked is loaded.

    # Check if marked is loaded
    is_loaded = page.evaluate("typeof marked !== 'undefined'")
    print(f"Marked loaded: {is_loaded}")

    # Test link rendering
    test_markdown = "[Test Link](https://example.com)"
    rendered_html = page.evaluate(f"marked.parse('{test_markdown}')")
    print(f"Rendered HTML: {rendered_html}")

    # Verify target="_blank" is present
    if 'target="_blank"' not in rendered_html:
        raise Exception("Target blank missing from rendered link")

    if 'href="https://example.com"' not in rendered_html:
        raise Exception("Href is incorrect")

    print("Link rendering verified.")

    # Screenshot
    page.screenshot(path="/home/jules/verification/link_renderer.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_link_renderer(page)
        except Exception as e:
            print(f"Verification failed: {e}")
            page.screenshot(path="/home/jules/verification/error.png")
        finally:
            browser.close()
