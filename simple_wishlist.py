# the_direct_url_script.py
import os
import time
import json
import random
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import stealth_sync

# --- CONFIGURATION ---
AMAZON_URL = "https://www.amazon.de/"
ACCOUNTS = [{"email": "niklasdornberger@gmail.com", "password": "zappy3r@!"}, {"email": "tobiashenschel7@gmail.com", "password": "bouncy6#x%"}, {"email": "marvinsiebert890@gmail.com", "password": "perky1t!"}]
PROXIES = [{"server": "http://res.proxy-seller.com:10123", "username": "5d134f5a5791df73", "password": "54JQBCp7"}, {"server": "http://res.proxy-seller.com:10124", "username": "5d134f5a5791df73", "password": "54JQBCp7"}, {"server": "http://res.proxy-seller.com:10125", "username": "5d134f5a5791df73", "password": "54JQBCp7"}, {"server": "http://res.proxy-seller.com:10126", "username": "5d134f5a5791df73", "password": "54JQBCp7"}, {"server": "http://res.proxy-seller.com:10127", "username": "5d134f5a5791df73", "password": "54JQBCp7"}]
LOG_FILE = "log.json"
SCREENSHOTS_DIR = "screenshots"
SESSION_DIR = "sessions"
LOGS = []

# --- HELPER FUNCTIONS ---
def log_step(step, status, details=""):
    log_entry = {"step": step, "status": status, "timestamp": datetime.now().isoformat(), "details": details}
    print(f"[{log_entry['status']}] {log_entry['step']} - {log_entry['details']}")
    LOGS.append(log_entry)

def human_like_delay(min_sec=1, max_sec=3):
    time.sleep(random.uniform(min_sec, max_sec))

def find_element_resilient(page: Page, selectors: list, timeout=5000):
    for selector in selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=timeout): return element
        except (PlaywrightTimeoutError, ValueError): continue
    return None

def failsafe_debugger(page: Page, reason: str):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    screenshot_path = os.path.join(SCREENSHOTS_DIR, f"failsafe_{reason}_{timestamp}.png")
    page.screenshot(path=screenshot_path, full_page=True)
    log_step("Failsafe", "critical", f"'{reason}' triggered. Screenshot saved for debugging.")

def is_logged_in(page: Page) -> bool:
    """Checks for a reliable element that only exists when logged in."""
    login_indicator = page.locator('#nav-link-accountList-nav-line-1:has-text("Hallo")')
    try:
        login_indicator.wait_for(timeout=3000, state='visible')
        return True
    except PlaywrightTimeoutError:
        return False

def relogin_and_return(page: Page, account: dict, target_url: str) -> bool:
    log_step("Recovery", "warning", "Session lost. Attempting to re-login...")
    try:
        page.goto(f"{AMAZON_URL}ap/signin", timeout=60000)
        email_input = find_element_resilient(page, ['input[name="email"]'], timeout=10000)
        if not email_input: return False
        email_input.fill(account['email'])
        continue_btn = find_element_resilient(page, ['input#continue'])
        if continue_btn: continue_btn.click()
        password_input = find_element_resilient(page, ['input[name="password"]'], timeout=10000)
        if not password_input: return False
        password_input.fill(account['password'])
        signin_btn = find_element_resilient(page, ['input#signInSubmit'])
        if signin_btn: signin_btn.click()
        page.wait_for_selector('input#twotabsearchtextbox', timeout=30000)
        log_step("Recovery", "success", "Re-login successful.")
        log_step("Recovery", "info", "Returning to target URL...")
        page.goto(target_url, wait_until='domcontentloaded')
        return True
    except Exception as e:
        log_step("Recovery", "CRITICAL", f"Re-login attempt failed: {str(e)}")
        return False

# --- CORE LOGIC ---
def login_to_amazon(page: Page, account: dict):
    log_step("Login", "info", f"Navigating to Amazon.de for {account['email']}")
    page.goto(AMAZON_URL, timeout=60000, wait_until='domcontentloaded')
    if is_logged_in(page):
        log_step("Login", "success", "Already logged in using a valid session.")
        return

    log_step("Login", "info", "No valid session found. Performing fresh login.")
    cookie_button = find_element_resilient(page, ['#sp-cc-accept'], timeout=3000)
    if cookie_button: cookie_button.click()
    signin_link = find_element_resilient(page, ['a[data-nav-role="signin"]', 'a#nav-link-accountList'])
    if signin_link: signin_link.click()
    else: page.goto(f"{AMAZON_URL}ap/signin", timeout=60000)
    
    email_input = find_element_resilient(page, ['input[name="email"]'], timeout=10000)
    if not email_input: raise Exception("Login failed: email field not found.")
    email_input.fill(account['email'])
    
    continue_btn = find_element_resilient(page, ['input#continue'])
    if continue_btn: continue_btn.click()
    
    password_input = find_element_resilient(page, ['input[name="password"]'], timeout=10000)
    if not password_input: raise Exception("Login failed: password field not found.")
    password_input.fill(account['password'])
    
    signin_btn = find_element_resilient(page, ['input#signInSubmit'])
    if signin_btn: signin_btn.click()
    
    try:
        page.wait_for_selector('input#twotabsearchtextbox', timeout=30000)
        log_step("Login", "success", "Fresh login successful.")
    except PlaywrightTimeoutError:
        failsafe_debugger(page, "LoginFailed")
        raise Exception("Login failed: could not confirm login after submitting credentials.")

def add_products_to_wishlist_directly(page: Page, account: dict):
    """Adds a predefined list of products to the wishlist using the 'Zero-Trust' method."""
    log_step("Wishlist", "info", "Starting direct URL wishlist task.")
    
    # Predefined list of diverse products to test different page layouts
    product_urls = [
        "https://www.amazon.de/dp/B08P265T23", # T-Shirt (has size/color options)
        "https://www.amazon.de/dp/3836294459"  # Book (simple page layout)
    ]

    added_count = 0
    for i, product_url in enumerate(product_urls):
        log_step("Wishlist", "info", f"Processing product {i+1}/{len(product_urls)}: {product_url}")
        try:
            page.goto(product_url, wait_until='domcontentloaded', timeout=60000)

            log_step("Wishlist", "info", "Waiting for page to be fully interactive...")
            page.wait_for_selector('#buybox, #rightCol', timeout=20000)

            if not is_logged_in(page):
                log_step("Wishlist", "warning", "Session was lost. Attempting recovery...")
                if not relogin_and_return(page, account, product_url):
                    failsafe_debugger(page, "ReloginFailed")
                    raise Exception("Session lost and re-login failed. Aborting.")
                log_step("Wishlist", "info", "Recovery successful. Page reloaded.")

            # Handle product variations if they exist
            option_selector = '#variation_size_name .swatch-input, #variation_color_name .swatch-input'
            option = page.locator(option_selector).first
            if option.is_visible(timeout=2000):
                log_step("Wishlist", "info", "Product option found, selecting first available choice.")
                option.click()
                human_like_delay(1, 2) # Wait for page to update after selection

            wishlist_button = find_element_resilient(page, ['#add-to-wishlist-button-submit', 'span:has-text("Auf die Liste")'])
            if not wishlist_button:
                log_step("Wishlist", "error", "Could not find the wishlist button.")
                failsafe_debugger(page, "NoWishlistButton")
                continue

            wishlist_button.click()
            
            log_step("Wishlist", "info", "Verifying that the item was added...")
            verification_selector = '#wishListMainButton-announce, span:has-text("Wunschzettel anzeigen")'
            page.wait_for_selector(verification_selector, timeout=10000)
            
            log_step("Wishlist", "SUCCESS", f"Product {i+1} was successfully added and verified.")
            added_count += 1
            
            screenshot_path = os.path.join(SCREENSHOTS_DIR, f"popup_product_{i+1}.png")
            page.screenshot(path=screenshot_path)
            log_step("Wishlist", "info", f"Screenshot of confirmation saved to {screenshot_path}")
            
            page.keyboard.press("Escape")

        except Exception as e:
            log_step("Wishlist", "error", f"Failed to add product {i+1}: {str(e)}")
            if "Aborting" in str(e): break
            else: continue
    
    log_step("Wishlist", "info", f"Finished task. Successfully added {added_count}/{len(product_urls)} products.")

# --- MAIN EXECUTION ---
def run_automation():
    for directory in [SCREENSHOTS_DIR, SESSION_DIR]:
        if not os.path.exists(directory): os.makedirs(directory)
    
    account = ACCOUNTS[0] # Use a specific account for consistency
    proxy_config = random.choice(PROXIES)
    session_file = os.path.join(SESSION_DIR, f"{account['email'].split('@')[0]}.json")
    log_step("Setup", "info", f"Using account: {account['email']}, proxy: {proxy_config['server']}")

    with sync_playwright() as p:
        browser = None
        try:
            browser = p.chromium.launch(headless=False, proxy=proxy_config, args=['--disable-blink-features=AutomationControlled'])
            context = browser.new_context(
                storage_state=session_file if os.path.exists(session_file) else None,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}, locale="de-DE", timezone_id="Europe/Berlin")
            page = context.new_page()
            stealth_sync(page)

            login_to_amazon(page, account)
            add_products_to_wishlist_directly(page, account)

            context.storage_state(path=session_file)
            log_step("Completion", "success", "Script finished.")

        except Exception as e:
            error_message = str(e).splitlines()[0]
            log_step("Error", "critical", f"A critical error stopped the script: {error_message}")
            if 'page' in locals() and page:
                failsafe_debugger(page, "CriticalError")
        finally:
            log_step("Teardown", "info", "Closing browser.")
            if browser: browser.close()
    
    with open(LOG_FILE, 'w') as f:
        json.dump(LOGS, f, indent=4)

if __name__ == "__main__":
    run_automation()