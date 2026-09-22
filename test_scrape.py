from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.patagonia.com/shop/web-specials/')
    time.sleep(2)
    print(page.title())
    print(page.content()[:200])
    browser.close()
