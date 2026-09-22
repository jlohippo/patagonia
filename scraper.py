from playwright.sync_api import sync_playwright, TimeoutError
import re
import time

def check_product(url, size=None, color=None):
    """
    Checks the product page using Playwright to get current_price, original_price, and if it's on sale.
    Handles clicking size and color variants.
    Returns a dictionary: {'current_price': float, 'original_price': float, 'is_on_sale': bool}
    or None if fetching fails.
    """
    with sync_playwright() as p:
        # Use Firefox or WebKit if Chromium is blocked, but Chromium usually works with right headers
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 720}
        )
        page = context.new_page()

        try:
            # Add a slight timeout and wait for load
            response = page.goto(url, wait_until='domcontentloaded', timeout=30000)

            # Bot check handling
            if response and response.status in (403, 429):
                print(f"Blocked by server (status {response.status}) on {url}")
                return None

            if "Access Denied" in page.title() or "Hang Tight" in page.title():
                print(f"Blocked by WAF on {url}")
                return None

            # Accept cookies if necessary to unblock UI (optional, might not be needed)
            try:
                cookie_btn = page.get_by_role("button", name=re.compile("Accept|Agree", re.I))
                if cookie_btn.is_visible():
                    cookie_btn.click()
            except:
                pass

            # Select Color
            if color:
                try:
                    # Look for color swatch or text matching the color
                    color_element = page.locator(f'[aria-label*="{color}"i], [title*="{color}"i], button:has-text("{color}")').first
                    if color_element.is_visible():
                        color_element.click()
                        time.sleep(1) # wait for DOM update
                except Exception as e:
                    print(f"Could not select color {color}: {e}")

            # Select Size
            if size:
                try:
                    # Look for size buttons
                    size_element = page.locator(f'[aria-label*="Size {size}"i], button:has-text("{size}")').first
                    if size_element.is_visible():
                        size_element.click()
                        time.sleep(1) # wait for DOM update
                except Exception as e:
                    print(f"Could not select size {size}: {e}")

            # Wait for price element to be visible
            # Try specific commerce cloud classes first
            try:
                page.wait_for_selector('.price, .sales, .product-price', timeout=10000)
            except TimeoutError:
                print("Timeout waiting for price elements.")
                pass

            html = page.content()

            # Extract prices from the DOM
            current_price = None
            original_price = None

            # Patagonia specific selectors
            sales_elem = page.locator('.sales .value').first
            if sales_elem.is_visible() and sales_elem.get_attribute('content'):
                current_price = float(sales_elem.get_attribute('content'))

            strike_elem = page.locator('.strike-through .value').first
            if strike_elem.is_visible() and strike_elem.get_attribute('content'):
                original_price = float(strike_elem.get_attribute('content'))

            # Fallback regex search on the rendered text
            if not current_price:
                # Get text of price container
                price_text = ""
                for selector in ['.price', '.product-pricing', '[data-price]']:
                    loc = page.locator(selector).first
                    if loc.is_visible():
                        price_text = loc.inner_text()
                        break

                if price_text:
                    # Find all price-like strings
                    prices = re.findall(r'\$?(\d+\.\d{2})', price_text)
                    if prices:
                        prices = [float(p) for p in prices]
                        if len(prices) > 1:
                            # Assume max is original, min is current
                            current_price = min(prices)
                            original_price = max(prices)
                        else:
                            current_price = prices[0]

            if not current_price:
                print(f"Could not extract price from {url}")
                return None

            if not original_price:
                original_price = current_price

            is_on_sale = current_price < original_price

            return {
                'current_price': current_price,
                'original_price': original_price,
                'is_on_sale': is_on_sale
            }

        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None
        finally:
            browser.close()
