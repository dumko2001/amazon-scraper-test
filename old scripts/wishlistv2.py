import os
import time
import json
import random
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import stealth_sync

# --- CONFIGURATION ---
AMAZON_URL = "https://www.amazon.de/"

# Client-provided credentials and proxies
ACCOUNTS = [
    {"email": "niklasdornberger@gmail.com", "password": "zappy3r@!"},
    {"email": "tobiashenschel7@gmail.com", "password": "bouncy6#x%"},
    {"email": "marvinsiebert890@gmail.com", "password": "perky1t!"},
]

PROXIES = [
    {
        "server": "http://res.proxy-seller.com:10123",
        "username": "5d134f5a5791df73",
        "password": "54JQBCp7"
    },
    {
        "server": "http://res.proxy-seller.com:10124",
        "username": "5d134f5a5791df73",
        "password": "54JQBCp7"
    },
    {
        "server": "http://res.proxy-seller.com:10125",
        "username": "5d134f5a5791df73",
        "password": "54JQBCp7"
    },
]

LOG_FILE = "wishlist_log.json"
SCREENSHOTS_DIR = "screenshots"
SESSION_DIR = "sessions"
LOGS = []

# --- HELPER FUNCTIONS ---
def log_step(step, status, details=""):
    """Logs each step with timestamp."""
    log_entry = {
        "step": step,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "details": details
    }
    print(f"[{log_entry['status']}] {log_entry['step']} - {log_entry['details']}")
    LOGS.append(log_entry)

def human_delay(min_sec=2, max_sec=5):
    """Human-like delay."""
    time.sleep(random.uniform(min_sec, max_sec))

def wait_for_page_fully_loaded(page: Page, timeout=30000):
    """
    Waits for page to be completely loaded and interactive.
    This is CRITICAL for Amazon pages that load content dynamically.
    """
    log_step("Page Loading", "info", "Waiting for page to be fully interactive...")
    
    try:
        # 1. Wait for network to be idle (no requests for 500ms)
        page.wait_for_load_state('networkidle', timeout=timeout)
        
        # 2. Wait for DOM to be fully loaded
        page.wait_for_load_state('domcontentloaded', timeout=timeout)
        
        # 3. Additional wait for JavaScript to initialize
        human_delay(3, 6)
        
        # 4. Verify critical elements are present
        page.wait_for_selector('body', timeout=5000)
        
        log_step("Page Loading", "success", "Page is fully loaded and ready")
        return True
        
    except PlaywrightTimeoutError:
        log_step("Page Loading", "warning", "Page loading timeout - proceeding with caution")
        return False

def is_logged_in(page: Page):
    """Check if user is logged in."""
    indicators = [
        '#nav-link-accountList-nav-line-1:has-text("Hallo")',
        '#nav-link-accountList:has-text("Hallo")',
        'input#twotabsearchtextbox'
    ]
    
    for indicator in indicators:
        if page.locator(indicator).is_visible(timeout=3000):
            log_step("Login Check", "success", f"Logged in - found indicator: {indicator}")
            return True
    
    log_step("Login Check", "warning", "Not logged in")
    return False

def find_element_safe(page: Page, selectors: list, timeout=10000):
    """Safely find an element using multiple selectors."""
    for i, selector in enumerate(selectors):
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=timeout):
                log_step("Element Search", "success", f"Found element with selector {i+1}: {selector}")
                return element
        except Exception as e:
            log_step("Element Search", "info", f"Selector {i+1} failed: {selector}")
            continue
    
    log_step("Element Search", "error", "No element found with any selector")
    return None

def login_to_amazon(page: Page, email: str, password: str):
    """Login with comprehensive error handling."""
    log_step("Login", "info", f"Starting login process for {email}")
    
    # Navigate to Amazon
    page.goto(AMAZON_URL, timeout=60000)
    wait_for_page_fully_loaded(page)

    # Handle cookie consent
    cookie_selectors = [
        '#sp-cc-accept',
        'button:has-text("Alle Cookies akzeptieren")',
        'button:has-text("Accept All Cookies")'
    ]
    cookie_btn = find_element_safe(page, cookie_selectors, timeout=5000)
    if cookie_btn:
        cookie_btn.click()
        human_delay(2, 3)

    # Check if already logged in
    if is_logged_in(page):
        log_step("Login", "success", "Already logged in from previous session")
        return True

    # Find and click sign-in link
    signin_selectors = [
        'a[data-nav-role="signin"]',
        'a#nav-link-accountList',
        'a:has-text("Anmelden")',
        '[data-nav-ref="nav_signin"]'
    ]
    
    signin_link = find_element_safe(page, signin_selectors)
    if not signin_link:
        log_step("Login", "warning", "Sign-in link not found, trying direct URL")
        page.goto(f"{AMAZON_URL}ap/signin", timeout=60000)
    else:
        signin_link.click()

    wait_for_page_fully_loaded(page)

    # Enter email
    email_selectors = [
        'input[name="email"]',
        'input#ap_email',
        'input[type="email"]'
    ]
    
    email_input = find_element_safe(page, email_selectors)
    if not email_input:
        raise Exception("Email input field not found")
    
    email_input.clear()
    email_input.fill(email)
    human_delay(1, 2)

    # Click continue
    continue_btn = find_element_safe(page, ['input#continue', 'button#continue'])
    if continue_btn:
        continue_btn.click()
        wait_for_page_fully_loaded(page)

    # Enter password
    password_selectors = [
        'input[name="password"]',
        'input#ap_password',
        'input[type="password"]'
    ]
    
    password_input = find_element_safe(page, password_selectors)
    if not password_input:
        raise Exception("Password input field not found")
    
    password_input.clear()
    password_input.fill(password)
    human_delay(1, 2)

    # Submit login
    submit_selectors = [
        'input#signInSubmit',
        'button#signInSubmit',
        'button:has-text("Anmelden")'
    ]
    
    submit_btn = find_element_safe(page, submit_selectors)
    if submit_btn:
        submit_btn.click()

    # Wait for login to complete
    try:
        page.wait_for_selector('input#twotabsearchtextbox', timeout=30000)
        wait_for_page_fully_loaded(page)
        log_step("Login", "success", "Login completed successfully")
        return True
    except PlaywrightTimeoutError:
        raise Exception("Login failed - home page not loaded")

def handle_wishlist_popup(page: Page):
    """
    Handles various types of popups that appear after adding to wishlist.
    Returns True if popup was handled, False if no popup found.
    """
    log_step("Popup Handler", "info", "Checking for wishlist popups...")
    
    # Wait a moment for popup to appear
    human_delay(1, 2)
    
    # Common popup selectors
    popup_selectors = [
        'div.a-popover-wrapper[style*="display: block"]',
        'div[role="dialog"]',
        '.a-modal-scroller',
        '#attach-sims-popover',
        '[data-testid="add-to-list-popover"]'
    ]
    
    popup_found = False
    popup_element = None
    
    # Check for popup presence
    for selector in popup_selectors:
        try:
            popup = page.locator(selector).first
            if popup.is_visible(timeout=3000):
                popup_element = popup
                popup_found = True
                log_step("Popup Handler", "success", f"Found popup: {selector}")
                break
        except:
            continue
    
    if popup_found and popup_element:
        # Take screenshot of popup
        screenshot_path = os.path.join(SCREENSHOTS_DIR, f"popup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        page.screenshot(path=screenshot_path)
        log_step("Popup Handler", "info", f"Popup screenshot saved: {screenshot_path}")
        
        # Try to find and log popup buttons
        try:
            buttons = popup_element.locator('button, a, input[type="submit"]')
            button_texts = []
            for i in range(buttons.count()):
                try:
                    text = buttons.nth(i).inner_text().strip()
                    if text:
                        button_texts.append(text)
                except:
                    continue
            
            if button_texts:
                log_step("Popup Handler", "info", f"Popup buttons found: {button_texts}")
            
            # Try to find "Create new list" or similar buttons and click them
            new_list_selectors = [
                'button:has-text("Neue Liste erstellen")',
                'button:has-text("Create new list")',
                'a:has-text("Neue Liste erstellen")',
                'a:has-text("Create new list")'
            ]
            
            new_list_btn = None
            for selector in new_list_selectors:
                try:
                    btn = popup_element.locator(selector).first
                    if btn.is_visible(timeout=2000):
                        new_list_btn = btn
                        break
                except:
                    continue
            
            if new_list_btn:
                log_step("Popup Handler", "info", "Clicking 'Create new list' button")
                new_list_btn.click()
                human_delay(2, 3)
                
                # After creating new list, there might be another confirmation
                page.keyboard.press("Escape")
                human_delay(1, 2)
            else:
                # No specific button found, just close with escape
                log_step("Popup Handler", "info", "No specific action button found, closing with Escape")
                page.keyboard.press("Escape")
                human_delay(1, 2)
                
        except Exception as e:
            log_step("Popup Handler", "warning", f"Error handling popup content: {str(e)}")
            page.keyboard.press("Escape")
            human_delay(1, 2)
    else:
        log_step("Popup Handler", "info", "No popup detected")
    
    return popup_found

def verify_wishlist_addition(page: Page, max_wait_seconds=15):
    """
    Verifies that item was actually added to wishlist.
    Looks for button text changes or confirmation messages.
    """
    log_step("Wishlist Verification", "info", "Verifying item was added to wishlist...")
    
    # Success indicators - button text changes or confirmation messages
    success_indicators = [
        # Button text changes
        '#wishListMainButton-announce',
        'span:has-text("Wunschzettel anzeigen")',
        'span:has-text("View Your List")',
        'span:has-text("Zur Liste")',
        'button:has-text("View Your List")',
        
        # Confirmation messages
        'div:has-text("wurde der Liste hinzugefügt")',
        'div:has-text("was added to your list")',
        'div:has-text("Added to")',
        'span:has-text("Hinzugefügt")',
        
        # Alternative success indicators
        '[data-action="view-list-redirect"]'
    ]
    
    start_time = time.time()
    while (time.time() - start_time) < max_wait_seconds:
        for indicator in success_indicators:
            try:
                element = page.locator(indicator).first
                if element.is_visible(timeout=1000):
                    log_step("Wishlist Verification", "success", f"VERIFIED: Found success indicator: {indicator}")
                    return True
            except:
                continue
        
        # Short wait before checking again
        time.sleep(0.5)
    
    # If we get here, verification failed
    log_step("Wishlist Verification", "error", "VERIFICATION FAILED: No success indicators found")
    return False

def add_single_product_to_wishlist(page: Page, product_url: str, attempt_num: int):
    """
    Attempts to add a single product to wishlist with full verification.
    Returns True if successful, False if failed.
    """
    log_step("Single Product", "info", f"Attempt {attempt_num}: Adding product to wishlist")
    log_step("Single Product", "info", f"URL: {product_url[:80]}...")
    
    try:
        # Navigate to product page
        page.goto(product_url, timeout=60000)
        wait_for_page_fully_loaded(page)
        
        # Verify we're on a product page
        product_indicators = ['#productTitle', '#centerCol', '#feature-bullets', '#buybox']
        product_page_loaded = False
        
        for indicator in product_indicators:
            if page.locator(indicator).is_visible(timeout=10000):
                product_page_loaded = True
                log_step("Single Product", "success", f"Product page loaded - found: {indicator}")
                break
        
        if not product_page_loaded:
            log_step("Single Product", "error", "Product page not properly loaded")
            return False
        
        # Check if still logged in
        if not is_logged_in(page):
            log_step("Single Product", "error", "Lost login session")
            return False
        
        # Wait extra time for buy box to be interactive
        buy_box_selectors = ['#rightCol', '#apex_desktop', '#buybox', '#desktop_buybox']
        buy_box_found = False
        
        for selector in buy_box_selectors:
            if page.locator(selector).is_visible(timeout=10000):
                buy_box_found = True
                log_step("Single Product", "success", f"Buy box area found: {selector}")
                break
        
        if not buy_box_found:
            log_step("Single Product", "warning", "Buy box not found - page may not be interactive")
        
        # CRITICAL: Extra wait for JavaScript to fully initialize
        log_step("Single Product", "info", "Waiting for page to be fully interactive...")
        human_delay(5, 8)  # Longer wait to ensure everything is ready
        
        # Handle product variations if present
        variation_selectors = [
            '#variation_size_name .swatch-input:not([disabled])',
            '#variation_color_name .swatch-input:not([disabled])'
        ]
        
        for selector in variation_selectors:
            try:
                option = page.locator(selector).first
                if option.is_visible(timeout=3000):
                    log_step("Single Product", "info", "Selecting product variation")
                    option.click()
                    human_delay(2, 4)  # Wait for page to update
                    break
            except:
                continue
        
        # Find wishlist button with comprehensive selectors
        wishlist_selectors = [
            '#add-to-wishlist-button-submit',
            'input[name="submit.add-to-registry.wishlist"]',
            'span:has-text("Auf die Liste") >> xpath=..',  # Get parent button
            'button:has(span:has-text("Auf die Liste"))',
            'span:has-text("Add to List") >> xpath=..',
            '[title="Auf die Liste"]',
            '[aria-label*="wishlist"]',
            '[data-action="add-to-wishlist"]',
            'button:has-text("Liste")'
        ]
        
        wishlist_button = find_element_safe(page, wishlist_selectors, timeout=15000)
        
        if not wishlist_button:
            log_step("Single Product", "error", "Wishlist button not found on this product")
            return False
        
        # Ensure button is fully interactive
        try:
            # Wait for button to be stable
            wishlist_button.wait_for(state='visible', timeout=10000)
            wishlist_button.wait_for(state='stable', timeout=5000)
            
            # Scroll button into view
            wishlist_button.scroll_into_view_if_needed()
            human_delay(1, 2)
            
            log_step("Single Product", "info", "Clicking wishlist button...")
            wishlist_button.click()
            
            # CRITICAL: Verify the action was successful
            verification_successful = verify_wishlist_addition(page, max_wait_seconds=15)
            
            if verification_successful:
                log_step("Single Product", "success", "VERIFIED: Product added to wishlist successfully")
                
                # Handle any popup that appeared
                handle_wishlist_popup(page)
                
                return True
            else:
                log_step("Single Product", "error", "FAILED: Product was NOT added to wishlist")
                
                # Take debug screenshot
                screenshot_path = os.path.join(SCREENSHOTS_DIR, f"failed_add_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                page.screenshot(path=screenshot_path)
                log_step("Single Product", "info", f"Debug screenshot: {screenshot_path}")
                
                return False
                
        except Exception as click_error:
            log_step("Single Product", "error", f"Error clicking wishlist button: {str(click_error)}")
            return False
    
    except Exception as e:
        log_step("Single Product", "error", f"General error: {str(e)}")
        return False

def get_product_urls_from_search(page: Page, search_term: str, num_products=10):
    """
    Searches for products and returns a list of product URLs.
    This separates URL collection from the actual wishlist adding process.
    """
    log_step("Product Search", "info", f"Searching for '{search_term}'")
    
    try:
        # Navigate to search results
        search_url = f"{AMAZON_URL}s?k={search_term}"
        page.goto(search_url, timeout=60000)
        wait_for_page_fully_loaded(page)
        
        # Find product links
        product_link_selectors = [
            'h2 a[href*="/dp/"]',
            '[data-component-type="s-search-result"] h2 a',
            '.s-result-item h2 a',
            'a[href*="/dp/"]'
        ]
        
        all_product_urls = []
        
        for selector in product_link_selectors:
            try:
                links = page.locator(selector)
                if links.count() > 0:
                    log_step("Product Search", "success", f"Found products with: {selector}")
                    
                    # Collect URLs
                    for i in range(min(num_products, links.count())):
                        try:
                            href = links.nth(i).get_attribute('href')
                            if href and '/dp/' in href:
                                full_url = f"{AMAZON_URL.rstrip('/')}{href}" if href.startswith('/') else href
                                all_product_urls.append(full_url)
                        except:
                            continue
                    
                    break  # Found products with this selector, no need to try others
                    
            except Exception:
                continue
        
        if all_product_urls:
            log_step("Product Search", "success", f"Collected {len(all_product_urls)} product URLs")
            return all_product_urls
        else:
            log_step("Product Search", "error", f"No products found for '{search_term}'")
            return []
            
    except Exception as e:
        log_step("Product Search", "error", f"Search failed: {str(e)}")
        return []

def add_products_to_wishlist_main(page: Page, target_count=2):
    """
    Main function to add products to wishlist.
    Uses a systematic approach: get URLs first, then process them.
    """
    log_step("Wishlist Main", "info", f"Starting to add {target_count} products to wishlist")
    
    search_terms = ["geschenke", "elektronik", "bücher", "spielzeug", "küche", "mode", "garten"]
    added_count = 0
    total_attempts = 0
    max_total_attempts = 20
    
    while added_count < target_count and total_attempts < max_total_attempts:
        search_term = random.choice(search_terms)
        
        # Get product URLs from search
        product_urls = get_product_urls_from_search(page, search_term, num_products=5)
        
        if not product_urls:
            total_attempts += 1
            continue
        
        # Try each product URL
        for product_url in product_urls:
            if added_count >= target_count:
                break
            
            total_attempts += 1
            
            # Try to add this product (with one retry if it fails)
            success = False
            for retry in range(2):  # Try twice per product
                attempt_num = f"{total_attempts}.{retry + 1}"
                success = add_single_product_to_wishlist(page, product_url, attempt_num)
                
                if success:
                    added_count += 1
                    log_step("Wishlist Main", "success", f"Progress: {added_count}/{target_count} products added")
                    break
                else:
                    if retry == 0:
                        log_step("Wishlist Main", "warning", "First attempt failed, retrying...")
                        human_delay(3, 5)  # Wait before retry
            
            if success:
                break  # Move to next search term
            
            if total_attempts >= max_total_attempts:
                break
    
    # Final results
    if added_count >= target_count:
        log_step("Wishlist Main", "success", f"SUCCESS: Added {added_count}/{target_count} products to wishlist")
    else:
        log_step("Wishlist Main", "warning", f"PARTIAL SUCCESS: Added {added_count}/{target_count} products after {total_attempts} attempts")
    
    return added_count

def run_wishlist_script():
    """Main execution function."""
    # Setup directories
    for directory in [SCREENSHOTS_DIR, SESSION_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    # Select account and proxy
    account = random.choice(ACCOUNTS)
    proxy_config = random.choice(PROXIES)
    session_file = os.path.join(SESSION_DIR, f"{account['email'].split('@')[0]}.json")
    
    log_step("Setup", "info", f"Account: {account['email']}")
    log_step("Setup", "info", f"Proxy: {proxy_config['server']}")
    
    with sync_playwright() as p:
        browser = None
        
        try:
            # Launch browser
            log_step("Browser", "info", "Launching browser...")
            
            browser = p.chromium.launch(
                headless=False,
                proxy=proxy_config,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-first-run',
                    '--disable-dev-shm-usage',
                    '--disable-background-timer-throttling'
                ]
            )
            
            context = browser.new_context(
                storage_state=session_file if os.path.exists(session_file) else None,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="de-DE",
                timezone_id="Europe/Berlin"
            )
            
            page = context.new_page()
            stealth_sync(page)
            
            # Execute main tasks
            log_step("Execution", "info", "Starting wishlist automation...")
            
            # 1. Login
            login_success = login_to_amazon(page, account['email'], account['password'])
            if not login_success:
                raise Exception("Login failed")
            
            # 2. Add products to wishlist
            products_added = add_products_to_wishlist_main(page, target_count=2)
            
            # 3. Save session
            context.storage_state(path=session_file)
            log_step("Session", "success", f"Session saved: {session_file}")
            
            # Final status
            if products_added >= 2:
                log_step("Final Result", "success", f"Wishlist script completed successfully! Added {products_added} products.")
            else:
                log_step("Final Result", "warning", f"Wishlist script completed with partial success. Added {products_added}/2 products.")
        
        except Exception as e:
            log_step("Critical Error", "error", f"Script failed: {str(e)}")
            
            # Take error screenshot
            if 'page' in locals():
                try:
                    screenshot_path = os.path.join(SCREENSHOTS_DIR, f"critical_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                    page.screenshot(path=screenshot_path)
                    log_step("Error Screenshot", "info", f"Screenshot saved: {screenshot_path}")
                except:
                    pass
        
        finally:
            if browser:
                browser.close()
    
    # Save logs
    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(LOGS, f, indent=4, ensure_ascii=False)
        print(f"Logs saved to {LOG_FILE}")
    except Exception as e:
        print(f"Failed to save logs: {e}")

if __name__ == "__main__":
    start_time = datetime.now()
    log_step("Script Start", "info", f"Wishlist script started at {start_time}")
    
    try:
        run_wishlist_script()
    except KeyboardInterrupt:
        log_step("Interrupted", "warning", "Script interrupted by user")
    except Exception as e:
        log_step("Unexpected Error", "error", f"Unexpected error: {str(e)}")
    
    end_time = datetime.now()
    duration = end_time - start_time
    log_step("Script End", "info", f"Script completed in {duration.total_seconds():.1f} seconds")