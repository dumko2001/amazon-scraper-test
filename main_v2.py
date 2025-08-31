# main_v2.py (Production Grade Version)
import os
import time
import json
import random
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import Stealth

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
        page.mouse.wheel(0, random.randint(200, 500))
        human_like_delay(0.5, 1.5)

def find_element_resilient(page: Page, selectors: list, timeout=10000):
    """Tries multiple selectors to find an element."""
    for selector in selectors:
        try:
            element = page.wait_for_selector(selector, timeout=timeout)
            if element and element.is_visible():
                return element
        except PlaywrightTimeoutError:
            continue
    return None

def handle_mobile_verification_popup(page: Page):
    """Handles the mobile number verification popup by clicking 'Not now'."""
    try:
        # Look for "Not now" button in various languages and formats
        not_now_selectors = [
            'button:has-text("Not now")',
            'button:has-text("Nicht jetzt")',
            'a:has-text("Not now")',
            'a:has-text("Nicht jetzt")',
            '[data-action="skip-mobile-number"]',
            'input[value="Not now"]',
            'input[value="Nicht jetzt"]'
        ]
        
        not_now_button = find_element_resilient(page, not_now_selectors, timeout=5000)
        if not_now_button:
            not_now_button.click()
            human_like_delay(1, 2)
            log_step("Mobile Verification", "info", "Clicked 'Not now' on mobile verification popup")
            return True
    except Exception as e:
        log_step("Mobile Verification", "info", f"No mobile verification popup found: {str(e)}")
    return False

# --- CORE AUTOMATION LOGIC ---
def login_to_amazon(page: Page, email: str, password: str):
    """Enhanced login function with better selectors and popup handling."""
    log_step("Login", "info", f"Navigating to Amazon.de for {email}")
    
    # Go to Amazon.de first
    page.goto(AMAZON_URL)
    human_like_delay(2, 4)
    
    # Check if already logged in
    if page.locator('span:has-text("Hallo")').first.is_visible():
        log_step("Login", "success", "Already logged in from previous session")
        return
    
    # Find and click sign-in link
    signin_selectors = [
        'a[data-nav-role="signin"]',
        'a#nav-link-accountList',
        'a:has-text("Anmelden")',
        'a:has-text("Sign in")',
        '.nav-signin-tooltip a'
    ]
    
    signin_link = find_element_resilient(page, signin_selectors)
    if signin_link:
        signin_link.click()
        human_like_delay(2, 4)
    else:
        # Fallback to direct login URL
        page.goto("https://www.amazon.de/ap/signin")
        human_like_delay(2, 4)
    
    # Fill email with multiple selector attempts
    email_selectors = [
        'input[name="email"]',
        'input#ap_email',
        'input[type="email"]',
        'input[autocomplete="username"]',
        'input[autocomplete="email"]'
    ]
    
    email_input = find_element_resilient(page, email_selectors)
    if email_input:
        email_input.fill(email)
        human_like_delay(1, 2)
        log_step("Login", "info", "Email entered successfully")
    else:
        log_step("Login", "error", "Could not find email input field")
        return
    
    # Click continue button
    continue_selectors = [
        'input#continue',
        'button#continue',
        'input[type="submit"]',
        'button[type="submit"]',
        'input[value="Continue"]',
        'input[value="Weiter"]'
    ]
    
    continue_btn = find_element_resilient(page, continue_selectors)
    if continue_btn:
        continue_btn.click()
        human_like_delay(2, 4)
    
    # Fill password
    password_selectors = [
        'input[name="password"]',
        'input#ap_password',
        'input[type="password"]',
        'input[autocomplete="current-password"]'
    ]
    
    password_input = find_element_resilient(page, password_selectors)
    if password_input:
        password_input.fill(password)
        human_like_delay(1, 2)
        log_step("Login", "info", "Password entered successfully")
    else:
        log_step("Login", "error", "Could not find password input field")
        return
    
    # Click sign in button
    signin_selectors = [
        'input#signInSubmit',
        'button#signInSubmit',
        'input[type="submit"]',
        'button[type="submit"]',
        'input[value="Sign in"]',
        'input[value="Anmelden"]'
    ]
    
    signin_btn = find_element_resilient(page, signin_selectors)
    if signin_btn:
        signin_btn.click()
        human_like_delay(3, 5)
    
    # Handle mobile verification popup if it appears
    handle_mobile_verification_popup(page)
    
    # Wait for successful login
    success_selectors = [
        'input#twotabsearchtextbox',
        '#nav-search',
        'span:has-text("Hallo")'
    ]
    
    if find_element_resilient(page, success_selectors, timeout=30000):
        log_step("Login", "success", "Successfully logged in")
    else:
        log_step("Login", "warning", "Login completed but couldn't confirm with standard selectors")

def browse_random_products(page: Page, num_products=5):
    """Enhanced product browsing with better selectors."""
    log_step("Browsing", "info", f"Starting to browse {num_products} random products")
    
    search_terms = ["bestseller", "angebote", "elektronik", "bücher", "kleidung", "geschenke"]
    
    for i in range(num_products):
        search_term = random.choice(search_terms)
        page.goto(f"{AMAZON_URL}s?k={search_term}")
        human_like_delay(2, 4)
        
        # Enhanced product link selectors
        product_selectors = [
            '[data-component-type="s-search-result"] h2 a',
            '[data-component-type="s-search-result"] .a-link-normal',
            '.s-result-item h2 a',
            '.s-result-item .a-link-normal',
            '.s-image a',
            'h2.a-size-mini a',
            'a[data-component-type="s-product-image"]'
        ]
        
        product_links = []
        for selector in product_selectors:
            elements = page.query_selector_all(selector)
            if elements:
                product_links.extend(elements)
                break
        
        if product_links:
            # Select a random product from the first 10 results
            available_links = product_links[:min(10, len(product_links))]
            random_product_link = random.choice(available_links)
            href = random_product_link.get_attribute('href')
            
            if href:
                if href.startswith('/'):
                    product_url = f"{AMAZON_URL.rstrip('/')}{href}"
                else:
                    product_url = href
                
                log_step("Browsing", "info", f"Browsing product {i+1}/{num_products}: {search_term}")
                page.goto(product_url)
                human_like_delay(2, 4)
                human_like_scroll(page)
                human_like_delay(1, 3)
            else:
                log_step("Browsing", "warning", f"Invalid product link for product {i+1}")
        else:
            log_step("Browsing", "warning", f"No product links found for search '{search_term}'. Skipping.")
    
    log_step("Browsing", "success", "Finished browsing products")

def add_products_to_wishlist(page: Page, num_to_add=2):
    """Enhanced wishlist function with better selectors."""
    log_step("Wishlist", "info", f"Attempting to add {num_to_add} products to wishlist")

    search_terms = ["geschenke", "elektronik", "bücher", "spielzeug", "küche", "mode"]
    added_count = 0
    attempts = 0
    max_attempts = 20

    while added_count < num_to_add and attempts < max_attempts:
        attempts += 1
        search_term = random.choice(search_terms)
        page.goto(f"{AMAZON_URL}s?k={search_term}")
        human_like_delay(2, 4)

        # Enhanced product link selectors
        product_selectors = [
            '[data-component-type="s-search-result"] h2 a',
            '[data-component-type="s-search-result"] .a-link-normal',
            '.s-result-item h2 a',
            '.s-result-item .a-link-normal',
            '.s-image a',
            'h2.a-size-mini a'
        ]

        product_links = []
        for selector in product_selectors:
            elements = page.query_selector_all(selector)
            if elements:
                product_links.extend(elements)
                break

        if not product_links:
            log_step("Wishlist", "warning", f"No product links found for search '{search_term}'. Trying another search.")
            continue

        # Try first few products to find one with wishlist button
        for link in product_links[:5]:
            href = link.get_attribute('href')
            if not href:
                continue

            if href.startswith('/'):
                product_url = f"{AMAZON_URL.rstrip('/')}{href}"
            else:
                product_url = href

            page.goto(product_url)
            human_like_delay(2, 4)

            # Enhanced wishlist button selectors
            wishlist_selectors = [
                'input#add-to-wishlist-button-submit',
                'button#add-to-wishlist-button-submit',
                '[data-action="add-to-wishlist"]',
                'input[name="submit.add-to-registry.wishlist"]',
                'button:has-text("Auf die Liste")',
                'button:has-text("Add to List")',
                'span:has-text("Auf die Liste")',
                '#wishListMainButton'
            ]

            wishlist_button = find_element_resilient(page, wishlist_selectors, timeout=5000)

            if wishlist_button and wishlist_button.is_visible():
                try:
                    wishlist_button.click()
                    human_like_delay(2, 4)

                    # Handle potential popups or confirmations
                    popup_selectors = [
                        'button[aria-label="Schließen"]',
                        'button[aria-label="Close"]',
                        '.a-button-close',
                        '[data-action="a-popover-close"]',
                        'button:has-text("Schließen")',
                        'button:has-text("Close")'
                    ]

                    popup_button = find_element_resilient(page, popup_selectors, timeout=3000)
                    if popup_button:
                        popup_button.click()
                        human_like_delay(1, 2)

                    # Press Escape as backup
                    page.keyboard.press("Escape")
                    human_like_delay(1, 2)

                    added_count += 1
                    log_step("Wishlist", "success", f"Added product {added_count}/{num_to_add} to wishlist")
                    break

                except Exception as e:
                    log_step("Wishlist", "warning", f"Failed to click wishlist button: {str(e)}")
            else:
                log_step("Wishlist", "info", "No wishlist button found on this page, trying another product")

    if added_count < num_to_add:
        log_step("Wishlist", "warning", f"Only added {added_count}/{num_to_add} products to wishlist after {attempts} attempts")
    else:
        log_step("Wishlist", "success", f"Successfully added {added_count} products to wishlist")

def cancel_prime_if_active(page: Page):
    """Enhanced Prime cancellation with better selectors."""
    log_step("Prime Cancellation", "info", "Checking for active Prime membership")

    prime_urls = [
        "https://www.amazon.de/gp/primecentral",
        "https://www.amazon.de/gp/prime/pipeline/membersignup",
        "https://www.amazon.de/amazonprime"
    ]

    for prime_url in prime_urls:
        try:
            page.goto(prime_url)
            human_like_delay(3, 5)

            # Enhanced Prime cancellation selectors
            cancel_selectors = [
                'a[href*="cancel"]',
                'a[href*="end"]',
                'a[href*="beenden"]',
                'button:has-text("Mitgliedschaft beenden")',
                'a:has-text("Mitgliedschaft beenden")',
                'button:has-text("End membership")',
                'a:has-text("End membership")',
                '[data-testid="end-membership"]',
                '.prime-cancel-button',
                'a:has-text("Kündigen")',
                'button:has-text("Kündigen")'
            ]

            cancel_button = find_element_resilient(page, cancel_selectors, timeout=5000)

            if cancel_button and cancel_button.is_visible():
                log_step("Prime Cancellation", "info", "Active Prime membership found. Attempting to cancel")
                try:
                    cancel_button.click()
                    page.wait_for_load_state('domcontentloaded')
                    human_like_delay(3, 5)
                    log_step("Prime Cancellation", "success", "Clicked the cancel Prime button. Process initiated")
                    return
                except Exception as e:
                    log_step("Prime Cancellation", "warning", f"Failed to click cancel button: {str(e)}")
            else:
                log_step("Prime Cancellation", "info", f"No cancellation button found on {prime_url}")

        except Exception as e:
            log_step("Prime Cancellation", "warning", f"Error accessing {prime_url}: {str(e)}")

    log_step("Prime Cancellation", "info", "No active Prime membership or cancellation option found after checking all URLs")

def run_automation():
    """Main automation function with enhanced error handling and session management."""
    # Create necessary directories
    for directory in [SCREENSHOTS_DIR, SESSION_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    # Select random account and proxy
    account = random.choice(ACCOUNTS)
    proxy_config = random.choice(PROXIES)
    session_file = os.path.join(SESSION_DIR, f"{account['email'].split('@')[0]}.json")

    log_step("Setup", "info", f"Using account: {account['email']} and proxy: {proxy_config['server']}")

    with sync_playwright() as p:
        browser = None
        retry_count = 0
        max_retries = 1

        while retry_count <= max_retries:
            try:
                # Launch browser with stealth mode and proxy
                browser = p.chromium.launch(
                    headless=False,
                    proxy=proxy_config,
                    args=[
                        '--no-first-run',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )

                # Create context with session persistence
                context = browser.new_context(
                    storage_state=session_file if os.path.exists(session_file) else None,
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    locale="de-DE",
                    timezone_id="Europe/Berlin"
                )

                page = context.new_page()

                # Apply stealth mode
                stealth_config = Stealth()
                stealth_config.apply_stealth_sync(page)

                # Execute automation tasks
                login_to_amazon(page, account['email'], account['password'])
                browse_random_products(page, 5)
                add_products_to_wishlist(page, 2)
                cancel_prime_if_active(page)

                # Save session state on success
                context.storage_state(path=session_file)
                log_step("Session", "success", f"Session state saved to {session_file}")

                log_step("Completion", "success", "Automation script finished successfully")
                break

            except Exception as e:
                error_message = str(e).splitlines()[0]
                log_step("Error", "critical", f"An error occurred: {error_message}")

                if browser and 'page' in locals():
                    screenshot_path = os.path.join(SCREENSHOTS_DIR, f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                    page.screenshot(path=screenshot_path)
                    log_step("Error Handling", "info", f"Screenshot saved to {screenshot_path}")

                if retry_count < max_retries:
                    retry_count += 1
                    log_step("Error Handling", "warning", f"Retrying... (Attempt {retry_count}/{max_retries})")
                    if browser:
                        browser.close()
                    human_like_delay(5, 10)
                else:
                    log_step("Error Handling", "critical", "Maximum retries reached. Aborting.")
                    break
            finally:
                if browser:
                    browser.close()

    # Write the final log file
    with open(LOG_FILE, 'w') as f:
        json.dump(LOGS, f, indent=4)

if __name__ == "__main__":
    run_automation()
