# main.py
import os
import time
import json
import random
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# --- CONFIGURATION ---
AMAZON_URL = "https://www.amazon.de/"
LOGIN_URL = "https://www.amazon.de/ap/signin"

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

def human_like_scroll(page):
    """Scrolls the page in a more human-like way."""
    scroll_height = page.evaluate("document.body.scrollHeight")
    for i in range(0, scroll_height, random.randint(100, 300)):
        page.mouse.wheel(0, random.randint(50, 150))
        human_like_delay(0.1, 0.3)

# --- CORE AUTOMATION LOGIC ---

def login_to_amazon(page, email, password):
    """Logs into the Amazon account."""
    log_step("Login", "info", f"Navigating to login page for {email}")

    # Try going to Amazon.de first, then to login
    page.goto(AMAZON_URL)
    human_like_delay(2, 4)

    # Look for sign-in link and click it
    try:
        signin_link_selectors = [
            'a[data-nav-role="signin"]',
            'a#nav-link-accountList',
            'a[href*="signin"]',
            '.nav-signin-tooltip a'
        ]

        signin_link = None
        for selector in signin_link_selectors:
            signin_link = page.query_selector(selector)
            if signin_link:
                break

        if signin_link:
            signin_link.click()
            human_like_delay(2, 4)
        else:
            # Fallback: go directly to login URL
            page.goto(LOGIN_URL)
            human_like_delay(2, 4)
    except:
        # Fallback: go directly to login URL
        page.goto(LOGIN_URL)
        human_like_delay(2, 4)

    # Try multiple selectors for email input
    email_selectors = [
        'input[name="email"]',
        'input#ap_email',
        'input[type="email"]',
        'input[autocomplete="username"]'
    ]

    email_input = None
    for selector in email_selectors:
        try:
            email_input = page.wait_for_selector(selector, timeout=5000)
            if email_input:
                break
        except:
            continue

    if not email_input:
        log_step("Login", "error", "Could not find email input field")
        return

    email_input.fill(email)
    human_like_delay(1, 2)

    # Try multiple selectors for continue button
    continue_selectors = [
        'input#continue',
        'button#continue',
        'input[type="submit"]',
        'button[type="submit"]'
    ]

    continue_btn = None
    for selector in continue_selectors:
        continue_btn = page.query_selector(selector)
        if continue_btn and continue_btn.is_visible():
            break

    if continue_btn:
        continue_btn.click()
        human_like_delay(2, 4)

    # Try multiple selectors for password input
    password_selectors = [
        'input[name="password"]',
        'input#ap_password',
        'input[type="password"]',
        'input[autocomplete="current-password"]'
    ]

    password_input = None
    for selector in password_selectors:
        try:
            password_input = page.wait_for_selector(selector, timeout=10000)
            if password_input:
                break
        except:
            continue

    if not password_input:
        log_step("Login", "error", "Could not find password input field")
        return

    password_input.fill(password)
    human_like_delay(1, 2)

    # Try multiple selectors for sign in button
    signin_selectors = [
        'input#signInSubmit',
        'button#signInSubmit',
        'input[type="submit"]',
        'button[type="submit"]'
    ]

    signin_btn = None
    for selector in signin_selectors:
        signin_btn = page.query_selector(selector)
        if signin_btn and signin_btn.is_visible():
            break

    if signin_btn:
        signin_btn.click()
        human_like_delay(3, 5)

    # Wait for successful login by checking for a known element
    try:
        page.wait_for_selector('input#twotabsearchtextbox', timeout=30000)
        log_step("Login", "success", "Successfully logged in.")
    except PlaywrightTimeoutError:
        # Try alternative selectors for successful login
        try:
            page.wait_for_selector('[data-nav-role="signin"]', timeout=5000)
            log_step("Login", "success", "Successfully logged in (alternative detection).")
        except PlaywrightTimeoutError:
            log_step("Login", "warning", "Login may have succeeded but couldn't confirm with standard selectors.")

def browse_random_products(page, num_products=5):
    """Browses a specified number of random product pages."""
    log_step("Browsing", "info", f"Starting to browse {num_products} random products.")

    search_terms = ["bestseller", "angebote", "elektronik", "bücher", "kleidung"]

    for i in range(num_products):
        search_term = random.choice(search_terms)
        page.goto(f"{AMAZON_URL}s?k={search_term}")
        human_like_delay(2, 4)

        # Try multiple selectors for product links
        product_selectors = [
            '[data-component-type="s-search-result"] h2 a',
            '[data-component-type="s-search-result"] .a-link-normal',
            '.s-result-item h2 a',
            '.s-result-item .a-link-normal',
            'h2.a-size-mini a',
            'a[data-component-type="s-product-image"]',
            '.s-image a',
            '[data-cy="title-recipe-link"]'
        ]

        product_links = []
        for selector in product_selectors:
            product_links = page.query_selector_all(selector)
            if product_links:
                break

        if not product_links:
            log_step("Browsing", "warning", f"No product links found for search '{search_term}'. Skipping.")
            continue

        # Select a random product from the first 10 results to avoid sponsored content
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
            log_step("Browsing", "warning", f"Invalid product link for product {i+1}. Skipping.")

    log_step("Browsing", "success", "Finished browsing products.")

def add_products_to_wishlist(page, num_to_add=2):
    """Adds a specified number of products to the wishlist."""
    log_step("Wishlist", "info", f"Attempting to add {num_to_add} products to wishlist.")

    search_terms = ["geschenke", "elektronik", "bücher", "spielzeug", "küche"]
    added_count = 0
    attempts = 0
    max_attempts = 20  # Prevent infinite loops

    while added_count < num_to_add and attempts < max_attempts:
        attempts += 1
        search_term = random.choice(search_terms)
        page.goto(f"{AMAZON_URL}s?k={search_term}")
        human_like_delay(2, 4)

        # Try multiple selectors for product links
        product_selectors = [
            '[data-component-type="s-search-result"] h2 a',
            '[data-component-type="s-search-result"] .a-link-normal',
            '.s-result-item h2 a',
            '.s-result-item .a-link-normal',
            'h2.a-size-mini a',
            'a[data-component-type="s-product-image"]',
            '.s-image a',
            '[data-cy="title-recipe-link"]'
        ]

        product_links = []
        for selector in product_selectors:
            product_links = page.query_selector_all(selector)
            if product_links:
                break

        if not product_links:
            log_step("Wishlist", "warning", f"No product links found for search '{search_term}'. Trying another search.")
            continue

        # Try first few products to find one with wishlist button
        for link in product_links[:5]:  # Only try first 5 to avoid sponsored content
            href = link.get_attribute('href')
            if not href:
                continue

            if href.startswith('/'):
                product_url = f"{AMAZON_URL.rstrip('/')}{href}"
            else:
                product_url = href

            page.goto(product_url)
            human_like_delay(2, 4)

            # Try multiple selectors for wishlist button
            wishlist_selectors = [
                'input#add-to-wishlist-button-submit',
                'button#add-to-wishlist-button-submit',
                '[data-action="add-to-wishlist"]',
                'input[name="submit.add-to-registry.wishlist"]'
            ]

            wishlist_button = None
            for selector in wishlist_selectors:
                wishlist_button = page.query_selector(selector)
                if wishlist_button and wishlist_button.is_visible():
                    break

            if wishlist_button and wishlist_button.is_visible():
                try:
                    wishlist_button.click()
                    human_like_delay(2, 4)

                    # Handle potential popups or confirmations
                    popup_selectors = [
                        'button[aria-label="Schließen"]',
                        'button[aria-label="Close"]',
                        '.a-button-close',
                        '[data-action="a-popover-close"]'
                    ]

                    for popup_selector in popup_selectors:
                        popup_button = page.query_selector(popup_selector)
                        if popup_button and popup_button.is_visible():
                            popup_button.click()
                            human_like_delay(1, 2)
                            break

                    added_count += 1
                    log_step("Wishlist", "success", f"Added product {added_count}/{num_to_add} to wishlist.")
                    break

                except Exception as e:
                    log_step("Wishlist", "warning", f"Failed to click wishlist button: {str(e)}")
            else:
                log_step("Wishlist", "info", "No wishlist button found on this page, trying another product.")

    if added_count < num_to_add:
        log_step("Wishlist", "warning", f"Only added {added_count}/{num_to_add} products to wishlist after {attempts} attempts.")
    else:
        log_step("Wishlist", "success", f"Successfully added {added_count} products to wishlist.")

def cancel_prime_if_active(page):
    """Navigates to the Prime management page and cancels if the option is present."""
    log_step("Prime Cancellation", "info", "Checking for active Prime membership.")

    # Try multiple Prime management URLs
    prime_urls = [
        "https://www.amazon.de/gp/primecentral",
        "https://www.amazon.de/gp/prime/pipeline/membersignup",
        "https://www.amazon.de/amazonprime"
    ]

    for prime_url in prime_urls:
        try:
            page.goto(prime_url)
            human_like_delay(3, 5)

            # Multiple selectors for Prime cancellation
            cancel_selectors = [
                'a[href*="cancel"]',
                'a[href*="end"]',
                'a[href*="beenden"]',
                'button:has-text("Mitgliedschaft beenden")',
                'a:has-text("Mitgliedschaft beenden")',
                'button:has-text("End membership")',
                'a:has-text("End membership")',
                '[data-testid="end-membership"]',
                '.prime-cancel-button'
            ]

            cancel_button = None
            for selector in cancel_selectors:
                try:
                    cancel_button = page.query_selector(selector)
                    if cancel_button and cancel_button.is_visible():
                        break
                except:
                    continue

            if cancel_button and cancel_button.is_visible():
                log_step("Prime Cancellation", "info", "Active Prime membership found. Attempting to cancel.")
                try:
                    cancel_button.click()
                    page.wait_for_load_state('domcontentloaded')
                    human_like_delay(3, 5)
                    log_step("Prime Cancellation", "success", "Clicked the cancel Prime button. Process initiated.")
                    return
                except Exception as e:
                    log_step("Prime Cancellation", "warning", f"Failed to click cancel button: {str(e)}")
            else:
                log_step("Prime Cancellation", "info", f"No cancellation button found on {prime_url}")

        except Exception as e:
            log_step("Prime Cancellation", "warning", f"Error accessing {prime_url}: {str(e)}")

    log_step("Prime Cancellation", "info", "No active Prime membership or cancellation option found after checking all URLs.")


def run_automation():
    """Main function to orchestrate the automation task."""
    if not os.path.exists(SCREENSHOTS_DIR):
        os.makedirs(SCREENSHOTS_DIR)

    # Select random account and proxy
    account = random.choice(ACCOUNTS)
    proxy_config = random.choice(PROXIES)

    log_step("Setup", "info", f"Using account: {account['email']} and proxy: {proxy_config['server']}")

    with sync_playwright() as p:
        browser = None
        retry_count = 0
        max_retries = 1

        while retry_count <= max_retries:
            try:
                browser = p.chromium.launch(
                    headless=False,
                    proxy=proxy_config
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
                )
                page = context.new_page()

                login_to_amazon(page, account['email'], account['password'])
                browse_random_products(page, 5)
                add_products_to_wishlist(page, 2)
                cancel_prime_if_active(page)

                log_step("Completion", "success", "Automation script finished successfully.")
                break # Success, exit loop

            except Exception as e:
                error_message = str(e).splitlines()[0]
                log_step("Error", "critical", f"An error occurred: {error_message}")
                
                if browser:
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