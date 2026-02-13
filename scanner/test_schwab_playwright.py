"""
Schwab Order Entry Test - Playwright Automation
Test browser automation for placing orders in Schwab

WARNING: This is for TESTING ONLY. Browser automation for trading is:
- Slower than API (3-10 seconds vs instant)
- Less reliable (can break if Schwab changes UI)
- Requires browser to stay open
- Should only be used as backup/testing

For live trading, use:
1. Alpaca (has API)
2. QuantConnect + Schwab (when you want Schwab integration)
"""

from playwright.sync_api import sync_playwright
import time

# Schwab credentials (YOU MUST FILL THESE IN)
SCHWAB_USERNAME = "YOUR_USERNAME"
SCHWAB_PASSWORD = "YOUR_PASSWORD"

# Test order parameters
TEST_SYMBOL = "AAPL"
TEST_QUANTITY = 1
TEST_ORDER_TYPE = "market"  # or "limit"
TEST_LIMIT_PRICE = None  # Set if limit order


def login_to_schwab(page):
    """Navigate to Schwab and login"""
    print("Navigating to Schwab...")
    page.goto("https://client.schwab.com/Login/SignOn/CustomerCenterLogin.aspx")
    
    print("Waiting for login form...")
    page.wait_for_selector("#LoginId", timeout=10000)
    
    print("Entering credentials...")
    page.fill("#LoginId", SCHWAB_USERNAME)
    page.fill("#Password", SCHWAB_PASSWORD)
    
    print("Clicking login...")
    page.click("#btnLogin")
    
    # Wait for dashboard or 2FA
    print("Waiting for login to complete...")
    time.sleep(5)  # Give time for redirect
    
    # Check if 2FA is required
    if "authentication" in page.url.lower() or "verify" in page.url.lower():
        print("\n⚠️  2FA REQUIRED")
        print("Please complete 2FA in the browser window...")
        input("Press Enter after completing 2FA...")
    
    print("✅ Login successful")


def navigate_to_trade_ticket(page):
    """Navigate to trade ticket"""
    print("\nNavigating to Trade page...")
    
    # Click Trade menu
    try:
        page.click("text=Trade", timeout=5000)
        time.sleep(2)
        
        # Click Stocks & ETFs
        page.click("text=Stocks & ETFs", timeout=5000)
        time.sleep(2)
        
        print("✅ On trade ticket page")
    except Exception as e:
        print(f"❌ Error navigating to trade ticket: {e}")
        print("Current URL:", page.url)
        print("Taking screenshot...")
        page.screenshot(path="d:/cursor/screenshots/schwab_navigation_error.png")
        raise


def fill_order_form(page, symbol, quantity, order_type="market", limit_price=None):
    """Fill out the order form"""
    print(f"\nFilling order: {quantity} shares of {symbol} ({order_type})")
    
    try:
        # Find and fill symbol input
        print("Entering symbol...")
        symbol_input = page.locator("input[placeholder*='Symbol']").first
        symbol_input.clear()
        symbol_input.fill(symbol)
        time.sleep(1)
        
        # Select action (Buy)
        print("Selecting action: Buy")
        page.click("text=Buy", timeout=5000)
        time.sleep(1)
        
        # Fill quantity
        print(f"Entering quantity: {quantity}")
        qty_input = page.locator("input[placeholder*='Quantity']").first
        qty_input.clear()
        qty_input.fill(str(quantity))
        time.sleep(1)
        
        # Select order type
        print(f"Selecting order type: {order_type}")
        if order_type.lower() == "market":
            page.click("text=Market", timeout=5000)
        elif order_type.lower() == "limit":
            page.click("text=Limit", timeout=5000)
            time.sleep(1)
            
            if limit_price:
                print(f"Entering limit price: ${limit_price}")
                limit_input = page.locator("input[placeholder*='Limit Price']").first
                limit_input.clear()
                limit_input.fill(str(limit_price))
        
        time.sleep(1)
        
        # Select time in force (Day order)
        print("Selecting time in force: Day")
        page.click("text=Day", timeout=5000)
        time.sleep(1)
        
        print("✅ Order form filled")
        
    except Exception as e:
        print(f"❌ Error filling order form: {e}")
        print("Taking screenshot...")
        page.screenshot(path="d:/cursor/screenshots/schwab_form_error.png")
        raise


def preview_order(page):
    """Click preview/review order button"""
    print("\nPreviewing order...")
    
    try:
        # Look for Preview/Review Order button
        preview_button = page.locator("button:has-text('Preview Order'), button:has-text('Review Order')").first
        preview_button.click()
        
        print("Waiting for preview screen...")
        time.sleep(3)
        
        print("✅ Order preview loaded")
        
        # Take screenshot of preview
        page.screenshot(path="d:/cursor/screenshots/schwab_order_preview.png")
        print("📸 Screenshot saved: schwab_order_preview.png")
        
    except Exception as e:
        print(f"❌ Error previewing order: {e}")
        page.screenshot(path="d:/cursor/screenshots/schwab_preview_error.png")
        raise


def submit_order(page, actually_submit=False):
    """Submit the order (with safety confirmation)"""
    print("\nOrder ready to submit...")
    
    if not actually_submit:
        print("⚠️  DRY RUN - Not actually submitting")
        print("Set actually_submit=True to place real order")
        return
    
    print("⚠️  SUBMITTING REAL ORDER")
    input("Press Enter to confirm submission (Ctrl+C to cancel)...")
    
    try:
        # Click Place Order / Submit button
        submit_button = page.locator("button:has-text('Place Order'), button:has-text('Submit')").first
        submit_button.click()
        
        print("Waiting for confirmation...")
        time.sleep(3)
        
        # Take screenshot of confirmation
        page.screenshot(path="d:/cursor/screenshots/schwab_order_confirmation.png")
        print("📸 Screenshot saved: schwab_order_confirmation.png")
        
        print("✅ Order submitted!")
        
    except Exception as e:
        print(f"❌ Error submitting order: {e}")
        page.screenshot(path="d:/cursor/screenshots/schwab_submit_error.png")
        raise


def test_schwab_order_entry(actually_submit=False):
    """
    Full test of Schwab order entry via Playwright
    
    Args:
        actually_submit: Set to True to actually place the order (default: False for dry run)
    """
    print("="*60)
    print("SCHWAB ORDER ENTRY TEST - PLAYWRIGHT")
    print("="*60)
    print(f"Mode: {'REAL ORDER' if actually_submit else 'DRY RUN (preview only)'}")
    print(f"Symbol: {TEST_SYMBOL}")
    print(f"Quantity: {TEST_QUANTITY}")
    print(f"Order Type: {TEST_ORDER_TYPE}")
    if TEST_LIMIT_PRICE:
        print(f"Limit Price: ${TEST_LIMIT_PRICE}")
    print("="*60)
    print()
    
    # Check credentials
    if SCHWAB_USERNAME == "YOUR_USERNAME":
        print("❌ ERROR: You must set SCHWAB_USERNAME and SCHWAB_PASSWORD in the script")
        return
    
    with sync_playwright() as p:
        # Launch browser (headless=False to see it work)
        print("Launching browser...")
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        try:
            # Step 1: Login
            login_to_schwab(page)
            
            # Step 2: Navigate to trade ticket
            navigate_to_trade_ticket(page)
            
            # Step 3: Fill order form
            fill_order_form(page, TEST_SYMBOL, TEST_QUANTITY, TEST_ORDER_TYPE, TEST_LIMIT_PRICE)
            
            # Step 4: Preview order
            preview_order(page)
            
            # Step 5: Submit order (if requested)
            submit_order(page, actually_submit)
            
            print("\n" + "="*60)
            print("TEST COMPLETE")
            print("="*60)
            
            # Keep browser open for inspection
            print("\nBrowser will stay open for 30 seconds...")
            print("Check the order status in Schwab")
            time.sleep(30)
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            print("Browser will stay open for inspection...")
            time.sleep(60)
            
        finally:
            browser.close()
            print("Browser closed")


if __name__ == "__main__":
    # DRY RUN - just preview, don't submit
    test_schwab_order_entry(actually_submit=False)
    
    # To actually place orders, use:
    # test_schwab_order_entry(actually_submit=True)
