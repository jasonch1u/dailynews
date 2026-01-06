from playwright.sync_api import Page, expect, sync_playwright

def verify_article_list_ui(page: Page):
    # 1. Arrange: Go to the app
    print("Navigating to http://localhost:3000")
    page.goto("http://localhost:3000")

    # 2. Check title
    expect(page).to_have_title("每日新聞 AI 摘要")

    # 3. Check for Article List sidebar
    article_list = page.locator("#articleList")
    expect(article_list).to_be_visible()

    # 4. Check for List Content container
    list_content = page.locator("#articleListContent")
    expect(list_content).to_be_visible()

    # 5. Check "Layout" (two columns) by ensuring both Content and ArticleList are visible
    content_area = page.locator("#content")
    expect(content_area).to_be_visible()

    # 6. Screenshot
    page.screenshot(path="/home/jules/verification/article_list_ui.png")
    print("Screenshot taken.")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_article_list_ui(page)
        except Exception as e:
            print(f"Verification failed: {e}")
            page.screenshot(path="/home/jules/verification/error.png")
        finally:
            browser.close()
