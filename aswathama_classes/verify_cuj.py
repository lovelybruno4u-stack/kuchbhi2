from playwright.sync_api import sync_playwright

def run_cuj(page):
    # Go to root -> redirects to login
    page.goto("http://127.0.0.1:8000")
    page.wait_for_timeout(1000)

    # Login as Teacher
    page.get_by_role("button", name="Teacher").click()
    page.wait_for_timeout(500)
    page.get_by_placeholder("Enter Admin Password").fill("admin123")
    page.wait_for_timeout(500)
    page.get_by_role("button", name="Login as Teacher").click()
    page.wait_for_timeout(1000)

    # Take screenshot of Teacher Dashboard
    page.screenshot(path="/home/jules/verification/screenshots/teacher_dashboard.png")
    page.wait_for_timeout(1000)

    # Go to Announcements and post something
    page.get_by_role("link", name="Announcements").click()
    page.wait_for_timeout(1000)
    page.get_by_placeholder("Enter announcement text here...").fill("Welcome to ASWATHAMA CLASSES! Enjoy the new AI platform.")
    page.wait_for_timeout(500)
    page.get_by_role("button", name="Post Announcement").click()
    page.wait_for_timeout(1000)

    # Logout
    page.get_by_role("link", name="Logout").click()
    page.wait_for_timeout(1000)

    # Login as Student (Using a known ID from our previous tests or just dummy)
    # We'll just screenshot the login page one more time to capture final state
    page.screenshot(path="/home/jules/verification/screenshots/verification.png")
    page.wait_for_timeout(1000)

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/home/jules/verification/videos"
        )
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
