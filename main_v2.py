# main_final.py (Production Grade, Fully Integrated Version)
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
        except (PlaywrightTimeoutError, ValueError):
            continue
    return None

def handle_popups(page: Page, action: str):
    """Handles common popups after an action (e.g., adding to wishlist)."""
    # Simple escape press is often effective for dismissing transient popups.
    page.keyboard.press("Escape")
    human_like_delay(0.5, 1)

    # Additionally, look for a persistent close button.
    close_selectors = [
        'button[aria-label="Schließen"]',
        'button[aria-label="Close"]',
        '[data-action="a-popover-close"]'
    ]
    close_button = find_element_resilient(page, close_selectors, timeout=2000)
    if close_button:
        try:
            close_button.click()
            log_step(action, "info", "Dismissed a confirmation popup.")
        except Exception:
            pass # Ignore errors if the button disappears before click

# --- CORE AUTOMATION LOGIC ---
def login_to_amazon(page: Page, email: str, password: str):
    """Robust login function with session reuse and popup handling."""
    log_step("Login", "info", f"Navigating to Amazon.de for {email}")
    page.goto(AMAZON_URL, timeout=60000, wait_until='domcontentloaded')

    # Wait for page to load and handle any initial popups
    human_like_delay(2, 4)

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

    # Check if already logged in by looking for a personalized greeting.
    login_indicators = [
        '#nav-link-accountList-nav-line-1:has-text("Hallo")',
        '#nav-link-accountList:has-text("Hallo")',
        'input#twotabsearchtextbox'  # Search box indicates we're on main page and likely logged in
    ]

    for indicator in login_indicators:
        if page.locator(indicator).is_visible(timeout=5000):
            log_step("Login", "success", "Already logged in from a previous session.")
            return

    # Click sign-in link with improved selectors
    signin_selectors = [
        'a[data-nav-role="signin"]',
        'a#nav-link-accountList',
        'a:has-text("Anmelden")',
        'a:has-text("Sign In")',
        '[data-nav-ref="nav_signin"]'
    ]
    signin_link = find_element_resilient(page, signin_selectors)
    if not signin_link:
        log_step("Login", "warning", "Sign-in link not found on homepage, navigating directly.")
        page.goto(f"{AMAZON_URL}ap/signin", timeout=60000, wait_until='domcontentloaded')
    else:
        signin_link.click()

    page.wait_for_load_state('domcontentloaded')
    human_like_delay(2, 3)

    # Fill email with improved selectors
    email_selectors = [
        'input[name="email"]',
        'input#ap_email',
        'input[type="email"]',
        'input[autocomplete="username"]'
    ]
    email_input = find_element_resilient(page, email_selectors, timeout=10000)
    if not email_input:
        log_step("Login", "error", "Could not find email input field.")
        raise Exception("Login failed: email field not found.")

    email_input.fill(email)
    human_like_delay(1, 2)

    continue_selectors = ['input#continue', 'button#continue', 'input[type="submit"]']
    continue_btn = find_element_resilient(page, continue_selectors)
    if continue_btn:
        continue_btn.click()

    page.wait_for_load_state('domcontentloaded')
    human_like_delay(2, 3)

    # Fill password with improved selectors
    password_selectors = [
        'input[name="password"]',
        'input#ap_password',
        'input[type="password"]',
        'input[autocomplete="current-password"]'
    ]
    password_input = find_element_resilient(page, password_selectors, timeout=10000)
    if not password_input:
        log_step("Login", "error", "Could not find password input field.")
        raise Exception("Login failed: password field not found.")

    password_input.fill(password)
    human_like_delay(1, 2)

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

    # Wait for a definitive element that signals a successful login.
    try:
        page.wait_for_selector('input#twotabsearchtextbox', timeout=30000)
        log_step("Login", "success", "Successfully logged in.")
    except PlaywrightTimeoutError:
        log_step("Login", "warning", "Login may have failed or a CAPTCHA is present.")
        raise Exception("Login failed: confirmation element not found after submitting credentials.")

def browse_random_products(page: Page, num_products=5):
    """Browses products using the stable 'get URLs first' strategy with updated selectors."""
    log_step("Browsing", "info", f"Starting to browse {num_products} random products.")
    search_terms = ["bestseller", "angebote", "elektronik", "bücher", "kleidung", "geschenke"]

    for i in range(num_products):
        search_term = random.choice(search_terms)
        log_step("Browsing", "info", f"Searching for '{search_term}' (product {i+1}/{num_products})")

        try:
            page.goto(f"{AMAZON_URL}s?k={search_term}", wait_until='domcontentloaded', timeout=60000)

            # Wait for page to load and handle any popups
            human_like_delay(2, 4)

            # Updated selectors for Amazon's current structure
            product_selectors = [
                'h2 a[href*="/dp/"]',  # Most common product link selector
                '[data-component-type="s-search-result"] h2 a',
                '.s-result-item h2 a',
                'a[href*="/dp/"]',  # Fallback for any product link
                '.s-link-style a',
                '[data-cy="title-recipe-title"] a'
            ]

            # Try each selector until we find products
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

            if not product_links or product_links.count() == 0:
                log_step("Browsing", "warning", f"No product links found for '{search_term}'. Trying alternative approach.")
                # Try scrolling and waiting
                human_like_scroll(page)
                human_like_delay(2, 3)

                # Try again with a more general selector
                product_links = page.locator('a[href*="/dp/"]')

            if product_links and product_links.count() > 0:
                # Get URLs from the first 10 results
                all_hrefs = []
                for i in range(min(10, product_links.count())):
                    try:
                        href = product_links.nth(i).get_attribute('href')
                        if href and '/dp/' in href:
                            all_hrefs.append(href)
                    except Exception:
                        continue

                valid_urls = [f"{AMAZON_URL.rstrip('/')}{href}" if href.startswith('/') else href for href in all_hrefs if href]

                if valid_urls:
                    # Navigate to a random product from the collected URLs
                    product_url = random.choice(valid_urls)
                    log_step("Browsing", "info", f"Navigating to product page: {product_url[:50]}...")
                    page.goto(product_url, wait_until='domcontentloaded', timeout=60000)

                    # Wait for a key element on the product page to ensure it's loaded
                    page.wait_for_selector('#productTitle, #centerCol, #feature-bullets', timeout=20000)

                    human_like_scroll(page)
                    human_like_delay()
                    log_step("Browsing", "success", f"Successfully browsed product {i+1}/{num_products}.")
                else:
                    log_step("Browsing", "warning", f"No valid product URLs found for '{search_term}'. Skipping.")
            else:
                log_step("Browsing", "warning", f"No product links found for '{search_term}'. Skipping.")

        except Exception as e:
            log_step("Browsing", "error", f"An error occurred while browsing for '{search_term}': {str(e)}")
            continue

    log_step("Browsing", "success", "Finished browsing products.")

def add_products_to_wishlist(page: Page, num_to_add=2):
    """Adds products to wishlist using a multi-layered, highly resilient strategy with updated selectors."""
    log_step("Wishlist", "info", f"Attempting to add {num_to_add} products to wishlist.")
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

            # Wait for page to load and handle any popups
            human_like_delay(2, 4)

            # Updated selectors for Amazon's current structure
            product_selectors = [
                'h2 a[href*="/dp/"]',  # Most common product link selector
                '[data-component-type="s-search-result"] h2 a',
                '.s-result-item h2 a',
                'a[href*="/dp/"]',  # Fallback for any product link
                '.s-link-style a',
                '[data-cy="title-recipe-title"] a'
            ]

            # Try each selector until we find products
            product_links = None
            for selector in product_selectors:
                try:
                    potential_links = page.locator(selector)
                    if potential_links.count() > 0:
                        product_links = potential_links
                        log_step("Wishlist", "info", f"Found products using selector: {selector}")
                        break
                except Exception:
                    continue

            if not product_links or product_links.count() == 0:
                log_step("Wishlist", "warning", f"No product links found for '{search_term}'. Trying alternative approach.")
                # Try scrolling and waiting
                human_like_scroll(page)
                human_like_delay(2, 3)

                # Try again with a more general selector
                product_links = page.locator('a[href*="/dp/"]')

            if product_links and product_links.count() > 0:
                # Get URLs from the first 5 results
                all_hrefs = []
                for i in range(min(5, product_links.count())):
                    try:
                        href = product_links.nth(i).get_attribute('href')
                        if href and '/dp/' in href:
                            all_hrefs.append(href)
                    except Exception:
                        continue

                valid_urls = [f"{AMAZON_URL.rstrip('/')}{href}" if href.startswith('/') else href for href in all_hrefs if href]

                if valid_urls:
                    for product_url in valid_urls:
                        if added_count >= num_to_add: break

                        log_step("Wishlist", "info", f"Navigating to product page: {product_url[:50]}...")
                        page.goto(product_url, wait_until='domcontentloaded', timeout=60000)
                        page.wait_for_selector('#productTitle, #centerCol, #feature-bullets', timeout=20000)

                        # STRATEGY 1: Handle product variations (size, color, etc.)
                        variation_selectors = ['#variation_size_name .swatch-input', '#variation_color_name .swatch-input']
                        for selector in variation_selectors:
                            option = page.locator(selector).first
                            if option.is_visible(timeout=2000):
                                log_step("Wishlist", "info", "Product option found, selecting first choice.")
                                option.click()
                                human_like_delay(1, 2) # Wait for page to update after selection
                                break # Only select one type of option

                        # STRATEGY 2: Use a comprehensive list of resilient selectors for wishlist button
                        wishlist_selectors = [
                            '#add-to-wishlist-button-submit',
                            'input[name="submit.add-to-registry.wishlist"]',
                            'span:has-text("Auf die Liste")',
                            'span:has-text("Add to List")',
                            '[title="Auf die Liste"]',
                            '[aria-label*="wishlist"]',
                            '[data-action="add-to-wishlist"]'
                        ]
                        wishlist_button = find_element_resilient(page, wishlist_selectors)

                        if wishlist_button:
                            wishlist_button.click()
                            human_like_delay()
                            handle_popups(page, "Wishlist")
                            added_count += 1
                            log_step("Wishlist", "success", f"Added product {added_count}/{num_to_add} to wishlist.")
                            break # Success, move to the next search attempt if more are needed
                        else:
                            log_step("Wishlist", "warning", "No wishlist button found on this page.")
                else:
                    log_step("Wishlist", "warning", f"No valid product URLs found for '{search_term}'.")
            else:
                log_step("Wishlist", "warning", f"No product links found for '{search_term}'.")

        except Exception as e:
            log_step("Wishlist", "error", f"An error occurred during attempt {attempts}: {str(e)}")
            continue

    if added_count < num_to_add:
        log_step("Wishlist", "warning", f"Only added {added_count}/{num_to_add} products to wishlist.")
    else:
        log_step("Wishlist", "success", f"Successfully added {num_to_add} products to wishlist.")

def cancel_prime_if_active(page: Page):
    """Navigates to Prime management page and cancels if option is present."""
    log_step("Prime Cancellation", "info", "Checking for active Prime membership.")
    prime_url = f"{AMAZON_URL}gp/primecentral"
    
    try:
        page.goto(prime_url, wait_until='domcontentloaded', timeout=60000)
        
        cancel_selectors = [
            'a[href*="cancel"]',
            'a:has-text("Mitgliedschaft beenden")',
            'button:has-text("Mitgliedschaft beenden")'
        ]
        
        cancel_button = find_element_resilient(page, cancel_selectors)
        
        if cancel_button:
            log_step("Prime Cancellation", "info", "Active Prime membership found. Attempting to cancel.")
            cancel_button.click()
            page.wait_for_load_state('domcontentloaded')
            log_step("Prime Cancellation", "success", "Clicked the cancel Prime button. Process initiated.")
        else:
            log_step("Prime Cancellation", "info", "No active Prime membership or cancellation option found.")
    except Exception as e:
        log_step("Prime Cancellation", "error", f"An error occurred while checking Prime status: {str(e)}")

def run_automation():
    """Main function to orchestrate the automation with stealth and robust error handling."""
    for directory in [SCREENSHOTS_DIR, SESSION_DIR]:
        if not os.path.exists(directory): os.makedirs(directory)

    account = random.choice(ACCOUNTS)
    proxy_config = random.choice(PROXIES)
    session_file = os.path.join(SESSION_DIR, f"{account['email'].split('@')[0]}.json")
    log_step("Setup", "info", f"Using account: {account['email']}, proxy: {proxy_config['server']}")

    with sync_playwright() as p:
        browser = None
        for attempt in range(2): # Retry logic: 0 for first try, 1 for retry
            try:
                browser = p.chromium.launch(
                    headless=False,
                    proxy=proxy_config,
                    args=['--disable-blink-features=AutomationControlled']
                )
                context = browser.new_context(
                    storage_state=session_file if os.path.exists(session_file) else None,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    locale="de-DE",
                    timezone_id="Europe/Berlin"
                )
                page = context.new_page()
                stealth_sync(page) # Apply stealth measures

                # --- EXECUTE TASKS ---
                login_to_amazon(page, account['email'], account['password'])
                browse_random_products(page, 5)
                add_products_to_wishlist(page, 2)
                cancel_prime_if_active(page)

                context.storage_state(path=session_file) # Save session on success
                log_step("Session", "success", f"Session state saved to {session_file}")
                log_step("Completion", "success", "Automation script finished successfully.")
                break # Exit retry loop on success

            except Exception as e:
                error_message = str(e).splitlines()[0]
                log_step("Error", "critical", f"An error occurred: {error_message}")
                
                if 'page' in locals() and page:
                    screenshot_path = os.path.join(SCREENSHOTS_DIR, f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                    page.screenshot(path=screenshot_path)
                    log_step("Error Handling", "info", f"Screenshot saved to {screenshot_path}")

                if attempt == 0:
                    log_step("Error Handling", "warning", "Retrying... (Attempt 1/1)")
                    if browser: browser.close()
                    human_like_delay(5, 10)
                else:
                    log_step("Error Handling", "critical", "Maximum retries reached. Aborting.")
            finally:
                if browser: browser.close()
    
    with open(LOG_FILE, 'w') as f:
        json.dump(LOGS, f, indent=4)

if __name__ == "__main__":
    run_automation()