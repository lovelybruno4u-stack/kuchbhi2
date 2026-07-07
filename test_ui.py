import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(record_video_dir="/home/jules/verification/")
        page = await context.new_page()

        # We need a local server running for this...
        # So we'll skip complex tests unless it's strictly required by memory (Memory says: "Frontend UI changes must be visually verified using Playwright scripts to generate WebM videos and screenshots in the /home/jules/verification/ directory.")

        await page.goto("http://localhost:5000/login", wait_until="networkidle")
        await page.screenshot(path="/home/jules/verification/login.png")

        # Click teacher role
        await page.locator('div[data-role="teacher"]').click()
        await page.fill('#username', 'admin')
        await page.fill('#password', 'admin')
        await page.click('button[type="submit"]')

        await page.wait_for_timeout(2000)

        await page.goto("http://localhost:5000/teacher/ai_tools", wait_until="networkidle")
        await page.screenshot(path="/home/jules/verification/ai_tools.png")

        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
