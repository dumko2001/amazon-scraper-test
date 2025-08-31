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
    {
        "server": "http://res.proxy-seller.com:10126",
        "username": "5d134f5a5791df73",
        "password": "54JQBCp7"
    },
    {
        "server": "http://res.proxy-seller.com:10127",
        "username": "5d134f5a5791df73",
        "password": "54JQBCp7"
    },
]

LOG_FILE = "log.json"
SCREENSHOTS_DIR = "screenshots"
SESSION_DIR = "sessions"
LOGS = []

# --- HELPER FUNCTIONS ---
def log_step(step, status, details=""):
    """Appends a new entry to the global log list."""
    log_entry = {
        "step": step,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "details": details
    }
    print(f"[{log_entry['status']}] {log_entry['step']} - {log_entry['details']}")
    LOGS.append(log_entry)

def human_like_delay(min_sec=1, max_sec=3):
    """Waits for a random duration to mimic human behavior."""
    time.sleep(random.uniform(min_sec, max_sec))

def human_like_scroll(page: Page):
    """Scrolls the page in a more human-like way."""
    for _ in range(random.randint(2, 5)):
        page.mouse.wheel(0, random.randint(300, 600))
        human_like_delay(0.5, 1.5)

def find_element_resilient(page: Page, selectors: list, timeout=5000):
    """Tries multiple selectors to find a visible element."""
    for selector in selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=timeout):
                return element
        except (PlaywrightTimeoutError, ValueError, Exception):
            continue
    return None

def wait_for_page_interactive(page: Page, timeout=30000):
    """Waits for the page to be fully interactive - critical for Amazon's dynamic content."""
    log_step("Page Loading", "info", "Waiting for page to be fully interactive...")
    
    try:
        # Wait for network to be idle (no requests for 500ms)
        page.wait_for_load_state('networkidle', timeout=timeout)
        
        # Additional wait for JavaScript to initialize
        human_like_delay(2, 4)
        
        # Verify key elements are present and clickable
        page.wait_for_selector('body', timeout=10000)
        
        log_step("Page Loading", "success", "Page is now fully interactive")
        return True
        
    except PlaywrightTimeoutError:
        log_step("Page Loading", "warning", "Page loading timeout, proceeding with caution")
        return False

def is_logged_in(page: Page):
    """Checks if user is currently logged in."""
    login_indicators = [
        '#nav-link-accountList-nav-line-1:has-text("Hallo")',
        '#nav-link-accountList:has-text("Hallo")',
        'input#twotabsearchtextbox'
    ]
    
    for indicator in login_indicators:
        if page.locator(indicator).is_visible(timeout=3000):
            return True
    return False

def analyze_and_handle_wishlist_popup(page: Page):
    """
    Analyzes the content of the wishlist confirmation popup, logs it,
    takes a screenshot, and then closes it.
    """
    log_step("Popup Analysis", "info", "Wishlist action successful. Analyzing confirmation popup...")
    try:
        # Define selectors for various popup types
        popup_selectors = [
            'div.a-popover-wrapper',
            'div[role="dialog"]',
            '.a-modal-scroller',
            '#attach-sims-popover'
        ]
        
        popup_found = False
        for selector in popup_selectors:
            popup = page.locator(selector).first
            if popup.is_visible(timeout=3000):
                popup_found = True
                log_step("Popup Analysis", "info", f"Found popup with selector: {selector}")
                
                # Take a screenshot for visual proof
                screenshot_path = os.path.join(SCREENSHOTS_DIR, f"wishlist_popup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                page.screenshot(path=screenshot_path)
                log_step("Popup Analysis", "info", f"Screenshot of popup saved to {screenshot_path}")

                # Find all buttons and links within the popup
                buttons = popup.locator('button, a, input[type="submit"]')
                
                if buttons.count() > 0:
                    button_texts = []
                    for i in range(buttons.count()):
                        try:
                            text = buttons.nth(i).inner_text().strip()
                            if text:
                                button_texts.append(text)
                        except:
                            continue
                    
                    if button_texts:
                        log_step("Popup Analysis", "info", f"Found buttons/links in popup: {button_texts}")
                    else:
                        log_step("Popup Analysis", "warning", "Popup found but no readable button text")
                else:
                    log_step("Popup Analysis", "warning", "Could not find any buttons or links in the popup.")
                break
        
        if not popup_found:
            log_step("Popup Analysis", "info", "No popup appeared - item may have been added directly")

        # The most reliable way to close any popup is to press Escape
        page.keyboard.press("Escape")
        human_like_delay(0.5, 1)
        log_step("Popup Analysis", "info", "Pressed Escape to close any popups")

    except Exception as e:
        log_step("Popup Analysis", "error", f"An error occurred during popup analysis: {str(e)}")

def verify_wishlist_success(page: Page, timeout=10000):
    """
    Verifies that the wishlist action was successful by looking for confirmation indicators.
    Returns True if verified, False if not.
    """
    log_step("Wishlist Verification", "info", "Verifying wishlist action success...")
    
    # Multiple indicators that show the item was added successfully
    success_indicators = [
        # Button text changes to "View Your List" or similar
        '#wishListMainButton-announce',
        'span:has-text("Wunschzettel anzeigen")',
        'span:has-text("View Your List")',
        'span:has-text("Zur Liste")',
        
        # Alternative confirmation messages
        '[data-action="view-list-redirect"]',
        'span:has-text("Hinzugefügt")',
        'span:has-text("Added")',
        
        # Popup confirmation elements
        'div:has-text("wurde der Liste hinzugefügt")',
        'div:has-text("was added to your list")'
    ]
    
    start_time = time.time()
    while (time.time() - start_time) < (timeout / 1000):
        for indicator in success_indicators:
            try:
                if page.locator(indicator).is_visible(timeout=1000):
                    log_step("Wishlist Verification", "success", f"SUCCESS CONFIRMED: Found indicator '{indicator}'")
                    return True
            except:
                continue
        
        # Short wait before trying again
        time.sleep(0.5)
    
    log_step("Wishlist Verification", "error", "VERIFICATION FAILED: No success indicators found")
    return False

# --- CORE AUTOMATION LOGIC ---
def login_to_amazon(page: Page, email: str, password: str):
    """Robust login function with session reuse and popup handling."""
    log_step("Login", "info", f"Navigating to Amazon.de for {email}")
    page.goto(AMAZON_URL, timeout=60000, wait_until='domcontentloaded')

    # Wait for page to be interactive
    wait_for_page_interactive(page)

    # Handle cookie consent if present
    cookie_selectors = [
        '#sp-cc-accept',
        'button:has-text("Alle Cookies akzeptieren")',
        'button:has-text("Accept All Cookies")',
        '[data-cy="accept-all-cookies"]'
    ]
    cookie_button = find_element_resilient(page, cookie_selectors, timeout=3000)
    if cookie_button:
        cookie_button.click()
        human_like_delay(1, 2)

    # Check if already logged in
    if is_logged_in(page):
        log_step("Login", "success", "Already logged in from previous session")
        return

    # Navigate to sign-in
    signin_selectors = [
        'a[data-nav-role="signin"]',
        'a#nav-link-accountList',
        'a:has-text("Anmelden")',
        'a:has-text("Sign In")',
        '[data-nav-ref="nav_signin"]'
    ]
    signin_link = find_element_resilient(page, signin_selectors)
    if not signin_link:
        log_step("Login", "warning", "Sign-in link not found, navigating directly")
        page.goto(f"{AMAZON_URL}ap/signin", timeout=60000)
    else:
        signin_link.click()

    wait_for_page_interactive(page)

    # Fill email
    email_selectors = [
        'input[name="email"]',
        'input#ap_email',
        'input[type="email"]',
        'input[autocomplete="username"]'
    ]
    email_input = find_element_resilient(page, email_selectors, timeout=10000)
    if not email_input:
        raise Exception("Login failed: email field not found")

    email_input.fill(email)
    human_like_delay(1, 2)

    # Click continue
    continue_selectors = ['input#continue', 'button#continue', 'input[type="submit"]']
    continue_btn = find_element_resilient(page, continue_selectors)
    if continue_btn:
        continue_btn.click()

    wait_for_page_interactive(page)

    # Fill password
    password_selectors = [
        'input[name="password"]',
        'input#ap_password',
        'input[type="password"]',
        'input[autocomplete="current-password"]'
    ]
    password_input = find_element_resilient(page, password_selectors, timeout=10000)
    if not password_input:
        raise Exception("Login failed: password field not found")

    password_input.fill(password)
    human_like_delay(1, 2)

    # Submit login
    signin_selectors = [
        'input#signInSubmit',
        'button#signInSubmit',
        'input[type="submit"]',
        'button:has-text("Anmelden")',
        'button:has-text("Sign In")'
    ]
    signin_btn = find_element_resilient(page, signin_selectors)
    if signin_btn:
        signin_btn.click()

    # Wait for login confirmation
    try:
        page.wait_for_selector('input#twotabsearchtextbox', timeout=30000)
        log_step("Login", "success", "Successfully logged in")
    except PlaywrightTimeoutError:
        raise Exception("Login failed: confirmation element not found")

def browse_random_products(page: Page, num_products=5):
    """Browses products with proper page loading waits."""
    log_step("Browsing", "info", f"Starting to browse {num_products} random products")
    search_terms = ["bestseller", "angebote", "elektronik", "bücher", "kleidung", "geschenke"]

    for i in range(num_products):
        search_term = random.choice(search_terms)
        log_step("Browsing", "info", f"Searching for '{search_term}' (product {i+1}/{num_products})")

        try:
            page.goto(f"{AMAZON_URL}s?k={search_term}", wait_until='domcontentloaded', timeout=60000)
            wait_for_page_interactive(page)

            # Find product links with better selectors
            product_selectors = [
                'h2 a[href*="/dp/"]',
                '[data-component-type="s-search-result"] h2 a',
                '.s-result-item h2 a',
                'a[href*="/dp/"]'
            ]

            product_links = None
            for selector in product_selectors:
                try:
                    potential_links = page.locator(selector)
                    if potential_links.count() > 0:
                        product_links = potential_links
                        log_step("Browsing", "info", f"Found products using selector: {selector}")
                        break
                except Exception:
                    continue

            if product_links and product_links.count() > 0:
                # Get URLs from first 10 results
                all_hrefs = []
                for j in range(min(10, product_links.count())):
                    try:
                        href = product_links.nth(j).get_attribute('href')
                        if href and '/dp/' in href:
                            all_hrefs.append(href)
                    except Exception:
                        continue

                valid_urls = [f"{AMAZON_URL.rstrip('/')}{href}" if href.startswith('/') else href for href in all_hrefs if href]

                if valid_urls:
                    product_url = random.choice(valid_urls)
                    log_step("Browsing", "info", f"Navigating to product: {product_url[:50]}...")
                    page.goto(product_url, wait_until='domcontentloaded', timeout=60000)
                    wait_for_page_interactive(page)

                    # Verify we're on a product page
                    page.wait_for_selector('#productTitle, #centerCol, #feature-bullets', timeout=20000)

                    human_like_scroll(page)
                    human_like_delay(2, 4)
                    log_step("Browsing", "success", f"Successfully browsed product {i+1}/{num_products}")
                else:
                    log_step("Browsing", "warning", f"No valid product URLs for '{search_term}'")
            else:
                log_step("Browsing", "warning", f"No product links found for '{search_term}'")

        except Exception as e:
            log_step("Browsing", "error", f"Error browsing '{search_term}': {str(e)}")
            continue

    log_step("Browsing", "success", "Finished browsing products")

def add_products_to_wishlist(page: Page, account: dict, num_to_add=2):
    """
    Adds products to wishlist with robust "Click, Verify, Recover, Analyze" strategy.
    """
    log_step("Wishlist", "info", f"Attempting to add {num_to_add} products to wishlist")
    search_terms = ["geschenke", "elektronik", "bücher", "spielzeug", "küche", "mode"]
    added_count = 0
    attempts = 0
    max_attempts = 15

    while added_count < num_to_add and attempts < max_attempts:
        attempts += 1
        search_term = random.choice(search_terms)
        log_step("Wishlist", "info", f"Searching for '{search_term}' (attempt {attempts})")
        
        try:
            page.goto(f"{AMAZON_URL}s?k={search_term}", wait_until='domcontentloaded', timeout=60000)
            wait_for_page_interactive(page)
            
            # Find product links
            product_links = page.locator('h2 a[href*="/dp/"]')
            
            # Wait for at least one product link to be visible
            try:
                product_links.first.wait_for(timeout=10000, state='visible')
            except PlaywrightTimeoutError:
                log_step("Wishlist", "warning", f"No products found for '{search_term}'")
                continue
            
            # Get first 5 product URLs
            all_hrefs = []
            for j in range(min(5, product_links.count())):
                try:
                    href = product_links.nth(j).get_attribute('href')
                    if href and '/dp/' in href:
                        all_hrefs.append(href)
                except Exception:
                    continue

            valid_urls = [f"{AMAZON_URL.rstrip('/')}{href}" if href.startswith('/') else href for href in all_hrefs if href]

            if not valid_urls:
                log_step("Wishlist", "warning", f"No valid product URLs found for '{search_term}'")
                continue

            for product_url in valid_urls:
                if added_count >= num_to_add:
                    break

                item_added_successfully = False
                
                # Try up to 2 times per product
                for retry_attempt in range(2):
                    try:
                        log_step("Wishlist", "info", f"Navigating to product page (attempt {retry_attempt + 1}/2)...")
                        page.goto(product_url, wait_until='domcontentloaded', timeout=60000)
                        wait_for_page_interactive(page)
                        
                        # Verify we're on a product page and it's loaded
                        page.wait_for_selector('#productTitle, #centerCol', timeout=20000)
                        
                        # Check if still logged in
                        if not is_logged_in(page):
                            log_step("Wishlist", "warning", "Session lost, need to re-login")
                            raise Exception("Session lost during wishlist operation")
                        
                        # Wait for the buy box area to be fully loaded
                        buy_box_selectors = [
                            '#rightCol',
                            '#apex_desktop',
                            '#buybox',
                            '#desktop_buybox'
                        ]
                        
                        buy_box_found = False
                        for selector in buy_box_selectors:
                            if page.locator(selector).is_visible(timeout=5000):
                                buy_box_found = True
                                log_step("Wishlist", "info", f"Buy box area loaded: {selector}")
                                break
                        
                        if not buy_box_found:
                            log_step("Wishlist", "warning", "Buy box area not found, page may not be fully loaded")
                        
                        # Additional wait for JavaScript to initialize buttons
                        human_like_delay(3, 5)
                        
                        # Handle product variations (size, color, etc.) if present
                        variation_selectors = [
                            '#variation_size_name .swatch-input:not([disabled])',
                            '#variation_color_name .swatch-input:not([disabled])'
                        ]
                        for selector in variation_selectors:
                            option = page.locator(selector).first
                            if option.is_visible(timeout=2000):
                                log_step("Wishlist", "info", "Selecting product variation")
                                option.click()
                                human_like_delay(2, 3)  # Wait for page to update
                                break
                        
                        # Find wishlist button with comprehensive selectors
                        wishlist_selectors = [
                            '#add-to-wishlist-button-submit',
                            'input[name="submit.add-to-registry.wishlist"]',
                            'span:has-text("Auf die Liste")',
                            'span:has-text("Add to List")',
                            '[title="Auf die Liste"]',
                            '[aria-label*="wishlist"]',
                            '[data-action="add-to-wishlist"]',
                            'button:has-text("Liste")'
                        ]
                        
                        wishlist_button = find_element_resilient(page, wishlist_selectors, timeout=10000)
                        
                        if not wishlist_button:
                            log_step("Wishlist", "warning", "Wishlist button not found on this product")
                            if retry_attempt == 0:
                                # Try refreshing the page once
                                log_step("Wishlist", "info", "Refreshing page and retrying...")
                                continue
                            else:
                                break  # Give up on this product
                        
                        # CRITICAL: Ensure button is clickable
                        try:
                            wishlist_button.wait_for(state='visible', timeout=5000)
                            page.wait_for_timeout(1000)  # Additional safety wait
                            
                            log_step("Wishlist", "info", f"Clicking wishlist button (attempt {retry_attempt + 1}/2)")
                            wishlist_button.click()
                            
                            # VERIFICATION STEP - This is the key fix
                            verification_successful = verify_wishlist_success(page, timeout=10000)
                            
                            if verification_successful:
                                log_step("Wishlist", "success", "VERIFIED: Item successfully added to wishlist")
                                
                                # ANALYSIS STEP
                                analyze_and_handle_wishlist_popup(page)
                                
                                added_count += 1
                                item_added_successfully = True
                                break  # Success! Exit retry loop
                            else:
                                # Verification failed - the click didn't work
                                log_step("Wishlist", "error", f"VERIFICATION FAILED: Click did not add item to wishlist")
                                
                                # Take screenshot for debugging
                                screenshot_path = os.path.join(SCREENSHOTS_DIR, f"wishlist_failed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                                page.screenshot(path=screenshot_path)
                                log_step("Wishlist", "info", f"Debug screenshot saved: {screenshot_path}")
                                
                                if retry_attempt == 0:
                                    log_step("Wishlist", "info", "Retrying with page refresh...")
                                    continue
                                else:
                                    log_step("Wishlist", "error", "Final retry failed, moving to next product")
                                    break
                        
                        except Exception as click_error:
                            log_step("Wishlist", "error", f"Click attempt {retry_attempt + 1} failed: {str(click_error)}")
                            if retry_attempt == 1:
                                # Final attempt failed, take screenshot
                                screenshot_path = os.path.join(SCREENSHOTS_DIR, f"wishlist_click_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                                page.screenshot(path=screenshot_path)
                                log_step("Wishlist", "error", f"Error screenshot saved: {screenshot_path}")

                    except Exception as e:
                        log_step("Wishlist", "warning", f"Product attempt {retry_attempt + 1} failed: {str(e)}")
                        if retry_attempt == 1:
                            log_step("Wishlist", "error", "Final retry failed for this product")
                
                if item_added_successfully:
                    break  # Move to next search term
        
        except Exception as e:
            log_step("Wishlist", "error", f"Search attempt {attempts} failed: {str(e)}")
            continue

    # Final status
    if added_count < num_to_add:
        log_step("Wishlist", "warning", f"Only managed to add {added_count}/{num_to_add} products to wishlist")
    else:
        log_step("Wishlist", "success", f"Successfully added {num_to_add} products to wishlist")

def cancel_prime_if_active(page: Page):
    """Navigates to Prime management page and cancels if option is present."""
    log_step("Prime Cancellation", "info", "Checking for active Prime membership")
    prime_url = f"{AMAZON_URL}gp/primecentral"
    
    try:
        page.goto(prime_url, wait_until='domcontentloaded', timeout=60000)
        wait_for_page_interactive(page)
        
        cancel_selectors = [
            'a[href*="cancel"]',
            'a:has-text("Mitgliedschaft beenden")',
            'button:has-text("Mitgliedschaft beenden")',
            'a:has-text("Cancel")',
            'button:has-text("Cancel")'
        ]
        
        cancel_button = find_element_resilient(page, cancel_selectors, timeout=10000)
        
        if cancel_button:
            log_step("Prime Cancellation", "info", "Active Prime membership found. Attempting to cancel")
            cancel_button.click()
            wait_for_page_interactive(page)
            log_step("Prime Cancellation", "success", "Clicked cancel Prime button. Process initiated")
        else:
            log_step("Prime Cancellation", "info", "No active Prime membership or cancellation option found")
    except Exception as e:
        log_step("Prime Cancellation", "error", f"Error checking Prime status: {str(e)}")

def run_automation():
    """Main function with robust error handling and retry logic."""
    for directory in [SCREENSHOTS_DIR, SESSION_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    account = random.choice(ACCOUNTS)
    proxy_config = random.choice(PROXIES)
    session_file = os.path.join(SESSION_DIR, f"{account['email'].split('@')[0]}.json")
    
    log_step("Setup", "info", f"Using account: {account['email']}, proxy: {proxy_config['server']}")

    with sync_playwright() as p:
        browser = None
        
        # Retry logic: attempt twice
        for attempt in range(2):
            try:
                log_step("Browser Setup", "info", f"Starting browser (attempt {attempt + 1}/2)")
                
                browser = p.chromium.launch(
                    headless=False,
                    proxy=proxy_config,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-first-run',
                        '--disable-background-timer-throttling',
                        '--disable-renderer-backgrounding',
                        '--disable-backgrounding-occluded-windows'
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
                stealth_sync(page)  # Apply stealth measures

                # --- EXECUTE TASKS ---
                log_step("Task Execution", "info", "Starting automation tasks...")
                
                login_to_amazon(page, account['email'], account['password'])
                browse_random_products(page, 5)
                add_products_to_wishlist(page, account, 2)
                cancel_prime_if_active(page)

                # Save session on success
                context.storage_state(path=session_file)
                log_step("Session", "success", f"Session state saved to {session_file}")
                log_step("Completion", "success", "Automation script finished successfully")
                break  # Exit retry loop on success

            except Exception as e:
                error_message = str(e).splitlines()[0]  # First line only
                log_step("Error", "critical", f"Automation failed: {error_message}")
                
                # Take screenshot if page exists
                if 'page' in locals() and page:
                    try:
                        screenshot_path = os.path.join(SCREENSHOTS_DIR, f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                        page.screenshot(path=screenshot_path)
                        log_step("Error Handling", "info", f"Error screenshot saved to {screenshot_path}")
                    except:
                        pass

                if attempt == 0:
                    log_step("Error Handling", "warning", "Retrying automation (1/1 retry attempts)")
                    if browser:
                        browser.close()
                    human_like_delay(5, 10)  # Wait before retry
                else:
                    log_step("Error Handling", "critical", "Maximum retries reached. Automation failed.")
                    
            finally:
                if browser:
                    try:
                        browser.close()
                    except:
                        pass
    
    # Save logs to file
    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(LOGS, f, indent=4, ensure_ascii=False)
        log_step("Logs", "success", f"Logs saved to {LOG_FILE}")
    except Exception as e:
        print(f"Failed to save logs: {e}")

if __name__ == "__main__":
    start_time = datetime.now()
    log_step("Script Start", "info", f"Amazon automation script started at {start_time}")
    
    try:
        run_automation()
    except KeyboardInterrupt:
        log_step("Script Interrupted", "warning", "Script was interrupted by user")
    except Exception as e:
        log_step("Script Error", "critical", f"Unexpected script error: {str(e)}")
    finally:
        end_time = datetime.now()