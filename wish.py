import os
import re
import time
import json
import random
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import stealth_sync

# --- CONFIGURATION ---
AMAZON_URL = "https://www.amazon.de/"

# FIXED: Only use Niklas account
ACCOUNT = {"email": "niklasdornberger@gmail.com", "password": "zappy3r@!"}

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

def human_like_delay(min_sec=2, max_sec=4):
    """Waits for a random duration to mimic human behavior."""
    time.sleep(random.uniform(min_sec, max_sec))

def human_like_scroll(page: Page):
    """Scrolls the page in a more human-like way."""
    for _ in range(random.randint(2, 5)):
        page.mouse.wheel(0, random.randint(300, 600))
        human_like_delay(0.5, 1.5)

def find_element_resilient(page: Page, selectors: list, timeout=10000):
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
    """Waits for the page to be fully interactive."""
    log_step("Page Loading", "info", "Waiting for page to be fully interactive...")
    
    try:
        page.wait_for_load_state('networkidle', timeout=timeout)
        human_like_delay(3, 5)
        page.wait_for_selector('body', timeout=10000)
        log_step("Page Loading", "success", "Page is now fully interactive")
        return True
    except PlaywrightTimeoutError:
        log_step("Page Loading", "warning", "Page loading timeout, proceeding with caution")
        return False

def verify_real_login_status(page: Page):
    """
    CRITICAL: Clicks on the Hello/Account button to verify we're REALLY logged in.
    Sometimes it shows 'Hello' but we're not actually logged in properly.
    """
    log_step("Login Verification", "info", "Verifying real login status by clicking Hello button...")
    
    try:
        # Find and click the account/hello button
        hello_selectors = [
            '#nav-link-accountList',
            '#nav-link-accountList-nav-line-1',
            'a[data-nav-role="signin"]',
            '#navAccountListMenuHeading'
        ]
        
        hello_button = find_element_resilient(page, hello_selectors, timeout=10000)
        
        if not hello_button:
            log_step("Login Verification", "error", "Cannot find Hello/Account button")
            return False
        
        # Click the hello button
        hello_button.click()
        human_like_delay(2, 3)
        
        # Check what page we land on
        current_url = page.url.lower()
        page_content = page.content().lower()
        
        # If we're on sign-in page, we're NOT really logged in
        if 'signin' in current_url or 'login' in current_url or 'ap/signin' in current_url:
            log_step("Login Verification", "error", "FAKE LOGIN DETECTED - redirected to sign-in page")
            return False
        
        # Look for account page indicators (we should be on account dropdown or page)
        real_login_indicators = [
            'your account',
            'dein konto', 
            'meine bestellungen',
            'your orders',
            'account & login info',
            'konto- und anmeldeinformationen'
        ]
        
        indicators_found = []
        for indicator in real_login_indicators:
            if indicator in page_content:
                indicators_found.append(indicator)
        
        if indicators_found:
            log_step("Login Verification", "success", f"REAL LOGIN CONFIRMED - Found: {indicators_found}")
            
            # Navigate back to homepage
            page.goto(AMAZON_URL, timeout=30000)
            wait_for_page_interactive(page)
            return True
        else:
            log_step("Login Verification", "error", "REAL LOGIN FAILED - No account indicators found")
            return False
            
    except Exception as e:
        log_step("Login Verification", "error", f"Login verification failed: {str(e)}")
        return False

def force_fresh_login(page: Page, email: str, password: str):
    """
    Forces a complete fresh login process.
    """
    log_step("Fresh Login", "info", f"Starting fresh login process for {email}")
    
    try:
        # Navigate to sign-in page directly
        page.goto(f"{AMAZON_URL}ap/signin", timeout=60000)
        wait_for_page_interactive(page)

        # Handle cookie consent if present
        cookie_selectors = [
            '#sp-cc-accept',
            'button:has-text("Alle Cookies akzeptieren")',
            'button:has-text("Accept All Cookies")'
        ]
        cookie_button = find_element_resilient(page, cookie_selectors, timeout=5000)
        if cookie_button:
            cookie_button.click()
            human_like_delay(2, 3)

        # Enter email
        email_selectors = [
            'input[name="email"]',
            'input#ap_email',
            'input[type="email"]'
        ]
        
        email_input = find_element_resilient(page, email_selectors, timeout=15000)
        if not email_input:
            raise Exception("Email input field not found")

        email_input.clear()
        email_input.fill(email)
        human_like_delay(1, 2)

        # Click continue
        continue_selectors = ['input#continue', 'button#continue', 'input[type="submit"]']
        continue_btn = find_element_resilient(page, continue_selectors)
        if continue_btn:
            continue_btn.click()
            wait_for_page_interactive(page)

        # Enter password
        password_selectors = [
            'input[name="password"]',
            'input#ap_password',
            'input[type="password"]'
        ]
        
        password_input = find_element_resilient(page, password_selectors, timeout=15000)
        if not password_input:
            raise Exception("Password input field not found")

        password_input.clear()
        password_input.fill(password)
        human_like_delay(1, 2)

        # Submit login
        signin_selectors = [
            'input#signInSubmit',
            'button#signInSubmit',
            'button:has-text("Anmelden")'
        ]
        
        signin_btn = find_element_resilient(page, signin_selectors)
        if signin_btn:
            signin_btn.click()
            wait_for_page_interactive(page)

        # Wait for homepage to load
        try:
            page.wait_for_selector('input#twotabsearchtextbox', timeout=30000)
            wait_for_page_interactive(page)
            log_step("Fresh Login", "success", "Fresh login completed successfully")
            return True
        except PlaywrightTimeoutError:
            raise Exception("Fresh login failed - homepage not loaded")
            
    except Exception as e:
        log_step("Fresh Login", "error", f"Fresh login failed: {str(e)}")
        return False

def ensure_proper_login(page: Page, email: str, password: str):
    """
    MAIN LOGIN FUNCTION: Always checks login status properly and forces login if needed.
    """
    log_step("Login Check", "info", "Starting comprehensive login verification...")
    
    # First, navigate to homepage to start fresh
    page.goto(AMAZON_URL, timeout=60000)
    wait_for_page_interactive(page)
    
    # Now verify if we're really logged in
    is_really_logged_in = verify_real_login_status(page)
    
    if is_really_logged_in:
        log_step("Login Check", "success", "Already properly logged in")
        return True
    else:
        log_step("Login Check", "warning", "Not properly logged in, forcing fresh login...")
        return force_fresh_login(page, email, password)

def browse_random_products(page: Page, num_products=5):
    """Browses products and returns list of product URLs for wishlist creation."""
    log_step("Browsing", "info", f"Starting to browse {num_products} random products")
    search_terms = ["bestseller", "angebote", "elektronik", "bücher", "kleidung", "geschenke"]
    
    collected_products = []

    for i in range(num_products):
        search_term = random.choice(search_terms)
        log_step("Browsing", "info", f"Searching for '{search_term}' (product {i+1}/{num_products})")

        try:
            page.goto(f"{AMAZON_URL}s?k={search_term}", wait_until='domcontentloaded', timeout=60000)
            wait_for_page_interactive(page)

            # Find product links
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
                    # Pick a random product and visit it
                    product_url = random.choice(valid_urls)
                    log_step("Browsing", "info", f"Navigating to product: {product_url[:50]}...")
                    page.goto(product_url, wait_until='domcontentloaded', timeout=60000)
                    wait_for_page_interactive(page)

                    # Verify we're on a product page
                    page.wait_for_selector('#productTitle, #centerCol, #feature-bullets', timeout=20000)

                    human_like_scroll(page)
                    human_like_delay(2, 4)
                    
                    # Store this product for wishlist creation
                    try:
                        product_title = page.locator('#productTitle').first.inner_text().strip()
                        collected_products.append({
                            'url': product_url,
                            'title': product_title[:50] + "..." if len(product_title) > 50 else product_title
                        })
                        log_step("Browsing", "success", f"Successfully browsed and collected product {i+1}/{num_products}")
                    except:
                        # If can't get title, still store URL
                        collected_products.append({
                            'url': product_url,
                            'title': f"Product {i+1}"
                        })
                        log_step("Browsing", "success", f"Successfully browsed product {i+1}/{num_products}")
                else:
                    log_step("Browsing", "warning", f"No valid product URLs for '{search_term}'")
            else:
                log_step("Browsing", "warning", f"No product links found for '{search_term}'")

        except Exception as e:
            log_step("Browsing", "error", f"Error browsing '{search_term}': {str(e)}")
            continue

    log_step("Browsing", "success", f"Finished browsing. Collected {len(collected_products)} products for wishlist creation")
    return collected_products

def create_new_wishlist(page: Page, wishlist_name: str):
    """
    Creates a new wishlist with proper modal handling.
    Uses the Create List modal dialog that appears after clicking the Create List button.
    """
    log_step("Create Wishlist", "info", f"Creating new wishlist: '{wishlist_name}'")
    
    try:
        # Go to the wishlist intro page first
        page.goto(f"{AMAZON_URL}hz/wishlist/intro", timeout=30000)
        wait_for_page_interactive(page)
        
        # Look for and click the Create List button
        create_button = page.get_by_role("button", name=re.compile("Create.*List|Liste erstellen", re.IGNORECASE))
        if not create_button.is_visible(timeout=10000):
            log_step("Create Wishlist", "error", "Could not find Create List button")
            return False
            
        log_step("Create Wishlist", "info", "Found Create List button, clicking...")
        create_button.click()
        
        # Wait for modal dialog with specific attributes
        try:
            page.wait_for_selector('dialog[role="dialog"], div[role="dialog"]', timeout=10000)
        except PlaywrightTimeoutError:
            log_step("Create Wishlist", "error", "Create List modal did not appear")
            return False
            
        # Short delay for animation and ensure interactive
        page.wait_for_timeout(1000)
        
        # Find and fill the name input field
        name_input = page.get_by_label("List name (required)")
        if not name_input.is_visible():
            # Try German version
            name_input = page.get_by_label(re.compile("Name.*Liste", re.IGNORECASE))
            
        if not name_input.is_visible():
            log_step("Create Wishlist", "error", "Could not find list name input field")
            return False
            
        log_step("Create Wishlist", "info", "Found name input field, entering wishlist name...")
        try:
            name_input.click()  # Ensure focus
            page.wait_for_timeout(500)  # Short delay for focus
            name_input.press_sequentially(wishlist_name, delay=100)  # Type slowly like a human
            page.wait_for_timeout(500)  # Wait after typing
        except Exception as e:
            log_step("Create Wishlist", "error", f"Error entering list name: {str(e)}")
            return False
            
        # Click the Create button in modal
        human_like_delay(1, 2)
        create_modal_button = page.get_by_role("button", name=re.compile("Create|Erstellen", re.IGNORECASE))
        if not create_modal_button.is_visible(timeout=5000):
            log_step("Create Wishlist", "error", "Could not find Create button in modal")
            return False
            
        log_step("Create Wishlist", "info", "Clicking create button...")
        create_modal_button.click()
        
        # Wait for either success indicators or URL change
        try:
            # We should be redirected to the new list
            page.wait_for_url(re.compile(r"/hz/wishlist/ls/.*"), timeout=15000)
            
            # Wait for modal to close
            try:
                page.wait_for_selector('dialog[role="dialog"], div[role="dialog"]', state="hidden", timeout=5000)
            except:
                pass  # Modal might close differently
                
            # Multiple success verification attempts
            success_found = False
            
            # Check URL
            if '/hz/wishlist/ls/' in page.url:
                success_found = True
            
            # Check for success message or list presence
            try:
                success_elements = [
                    '.a-alert-success',
                    '[data-success]',
                    '[role="alert"]:has-text("created")',
                    '[role="alert"]:has-text("erstellt")',
                    f'h2:has-text("{wishlist_name}")',
                    '.wl-list-name:has-text("' + wishlist_name + '")'
                ]
                
                for selector in success_elements:
                    if page.locator(selector).is_visible(timeout=1000):
                        success_found = True
                        break
            except:
                pass
                
            if success_found:
                log_step("Create Wishlist", "success", f"SUCCESS: Wishlist '{wishlist_name}' created!")
                return True
                
            log_step("Create Wishlist", "warning", "Could not find explicit success indicators, but URL suggests success")
            return True
            
        except PlaywrightTimeoutError:
            log_step("Create Wishlist", "error", "Timeout waiting for wishlist creation confirmation")
            return False
    except Exception as e:
        log_step("Create Wishlist", "error", f"Critical error in wishlist creation: {str(e)}")
        # Take error screenshot
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, f"error_{timestamp}.png"))
        except:
            pass
        return False
            
    finally:
        # Go back to home/lists page if we're stuck somewhere
        try:
            if not '/hz/wishlist/' in page.url:
                page.goto(f"{AMAZON_URL}hz/wishlist", timeout=30000)
                wait_for_page_interactive(page)
        except:
            pass

def handle_wishlist_popup(page: Page, wishlist_name: str, attempt: int):
    """
    CRITICAL: Handles the popup/modal that appears after entering wishlist name.
    This is the key function that was missing in your original code.
    """
    log_step("Wishlist Popup", "info", "Checking for wishlist creation popup/modal...")
    
    try:
        # Wait a moment for popup to appear
        human_like_delay(2, 3)
        
        # Look for various popup/modal indicators
        popup_selectors = [
            # Standard Amazon popups/modals
            'div[role="dialog"]',
            'div.a-popover-wrapper',
            'div[data-testid*="modal"]',
            'div[data-testid*="popup"]',
            '.a-modal-scroller',
            '[role="dialog"]',
            # Specific wishlist popups
            'div:has-text("Liste erstellen")',
            'div:has-text("Create List")',
            'form[method="post"]'
        ]
        
        popup_element = None
        for selector in popup_selectors:
            try:
                potential_popup = page.locator(selector).first
                if potential_popup.is_visible(timeout=5000):
                    popup_element = potential_popup
                    log_step("Wishlist Popup", "success", f"Found popup with selector: {selector}")
                    break
            except:
                continue
        
        if not popup_element:
            # Sometimes the popup is the entire page content, check for confirm buttons directly
            log_step("Wishlist Popup", "info", "No specific popup found, checking for confirmation buttons on page...")
        
        # Take screenshot of current state
        popup_screenshot = os.path.join(SCREENSHOTS_DIR, f"popup_state_{attempt}_{datetime.now().strftime('%H%M%S')}.png")
        page.screenshot(path=popup_screenshot)
        log_step("Wishlist Popup", "info", f"Popup state screenshot: {popup_screenshot}")
        
        # Look for confirmation buttons (both in popup and on page)
        confirm_button_selectors = [
            # German Amazon
            'button:has-text("Liste erstellen")',
            'button:has-text("Erstellen")',
            'button:has-text("Bestätigen")',
            'button:has-text("OK")',
            'input[value="Liste erstellen"]',
            'input[value="Erstellen"]',
            
            # English Amazon (fallback)
            'button:has-text("Create List")',
            'button:has-text("Create")',
            'button:has-text("Confirm")',
            'button:has-text("OK")',
            'input[value="Create List"]',
            'input[value="Create"]',
            
            # Generic form submissions
            'button[type="submit"]',
            'input[type="submit"]',
            
            # By data attributes or IDs
            '[data-testid*="confirm"]',
            '[data-testid*="create"]',
            '#confirm-button',
            '#create-button'
        ]
        
        confirm_button = None
        for selector in confirm_button_selectors:
            try:
                if popup_element:
                    # Look inside the popup first
                    potential_btn = popup_element.locator(selector).first
                else:
                    # Look on the entire page
                    potential_btn = page.locator(selector).first
                
                if potential_btn.is_visible(timeout=3000):
                    # Additional validation - make sure it's not a search or navigation button
                    btn_text = potential_btn.inner_text().lower()
                    btn_class = potential_btn.get_attribute('class') or ""
                    btn_id = potential_btn.get_attribute('id') or ""
                    
                    # Skip obvious non-wishlist buttons
                    skip_indicators = ['search', 'suchen', 'navigation', 'nav', 'menu']
                    should_skip = any(indicator in f"{btn_text} {btn_class} {btn_id}".lower() 
                                    for indicator in skip_indicators)
                    
                    if not should_skip:
                        confirm_button = potential_btn
                        log_step("Wishlist Popup", "success", f"Found confirm button: {selector} (text: '{btn_text}')")
                        break
                    else:
                        log_step("Wishlist Popup", "info", f"Skipping non-relevant button: {btn_text}")
                        
            except Exception as e:
                log_step("Wishlist Popup", "info", f"Button check failed for {selector}: {str(e)}")
                continue
        
        if not confirm_button:
            log_step("Wishlist Popup", "warning", "No confirmation button found in popup")
            return False
        
        # Click the confirmation button
        log_step("Wishlist Popup", "info", f"Clicking confirmation button...")
        confirm_button.click()
        human_like_delay(3, 5)  # Wait for the action to complete
        
        # Take screenshot after clicking confirm
        after_confirm_screenshot = os.path.join(SCREENSHOTS_DIR, f"after_confirm_{attempt}_{datetime.now().strftime('%H%M%S')}.png")
        page.screenshot(path=after_confirm_screenshot)
        log_step("Wishlist Popup", "info", f"After confirm click screenshot: {after_confirm_screenshot}")
        
        # After clicking Create List button, we need to wait for redirection or dialog close
        human_like_delay(3, 5)
        
        # First, look for typical error indicators that would show if creation failed
        error_indicators = [
            ".error",
            "[data-error]",
            "error-message",
            ".a-alert-error"
        ]
        
        for error_selector in error_indicators:
            try:
                error_element = page.locator(error_selector).first
                if error_element.is_visible(timeout=2000):
                    log_step("Wishlist Popup", "error", f"Error creating wishlist: {error_element.inner_text()}")
                    return False
            except:
                continue

        # Look for the created list in the page
        # We'll try multiple locator strategies
        list_found = False
        try:
            # Strategy 1: Look for list name in a visible element 
            list_link = page.get_by_text(wishlist_name, exact=True).first
            if list_link.is_visible(timeout=5000):
                list_found = True
            
            # Strategy 2: Check if we were redirected to the new list's page
            # The URL pattern is usually something like: /hz/wishlist/ls/XXXXX
            current_url = page.url.lower()
            if "/hz/wishlist/ls/" in current_url:
                list_found = True
            
            # Strategy 3: Look for elements that indicate we're on a wishlist page
            list_indicators = [
                '[role="tabpanel"]',  # The main wishlist panel
                '[data-action="list-header"]',  # List header area
                '[data-action="list-header"] span:has-text("Private")',  # Privacy indicator
                '[data-test-id="list-header"]'  # Another common test ID
            ]
            
            for selector in list_indicators:
                element = page.locator(selector).first
                if element.is_visible(timeout=2000):
                    list_found = True
                    break
            
            if list_found:
                log_step("Wishlist Popup", "success", f"SUCCESS: Wishlist '{wishlist_name}' created and verified! URL: {page.url}")
                return True
        except Exception as e:
            log_step("Wishlist Popup", "warning", f"Error while verifying list creation: {str(e)}")
        
        log_step("Wishlist Popup", "warning", "Could not verify list creation through UI elements. Will check alternate methods.")
        return False
        
    except Exception as e:
        log_step("Wishlist Popup", "error", f"Error handling wishlist popup: {str(e)}")
        return False

def create_wishlist_alternative_method(page: Page, wishlist_name: str):
    """
    Alternative method: Navigate through account menu to find wishlist creation.
    """
    log_step("Create Wishlist Alt", "info", "Trying alternative wishlist creation method...")
    
    try:
        page.goto(AMAZON_URL, timeout=30000)
        wait_for_page_interactive(page)
        
        account_selectors = ['#nav-link-accountList', 'a[data-nav-role="signin"]']
        account_btn = find_element_resilient(page, account_selectors, timeout=10000)
        
        if not account_btn:
             log_step("Create Wishlist Alt", "error", "Could not find account menu button.")
             return False

        account_btn.hover()
        human_like_delay(1, 2)
        
        wishlist_link_selectors = ['a:has-text("Wunschzettel")', 'a:has-text("Wish List")']
        wishlist_link = find_element_resilient(page, wishlist_link_selectors, timeout=10000)
        
        if wishlist_link:
            log_step("Create Wishlist Alt", "info", "Found wishlist link in account dropdown, clicking...")
            wishlist_link.click()
            wait_for_page_interactive(page)
            # Now that we're on a wishlist page, the main function's logic might work
            return create_new_wishlist(page, wishlist_name) 

        log_step("Create Wishlist Alt", "error", "Alternative method also failed to find wishlist link.")
        return False
        
    except Exception as e:
        log_step("Create Wishlist Alt", "error", f"Alternative method error: {str(e)}")
        return False


def add_product_to_current_wishlist(page: Page, product_url: str, product_title: str, wishlist_name: str = None):
    """
    Adds a specific product to a specific wishlist.
    If wishlist_name is provided, it will select that wishlist from the dropdown.
    Returns True if successful, False if failed.
    """
    log_step("Add to Wishlist", "info", f"Adding product to wishlist: {product_title}")
    
    try:
        page.goto(product_url, timeout=60000)
        wait_for_page_interactive(page)
        
        page.wait_for_selector('#productTitle, #centerCol', timeout=20000)
        
        # First check if we need to handle any variation popups
        variation_selectors = [
            '#variation_select',
            '#variation-selector',
            'select.a-native-dropdown'
        ]
        
        for selector in variation_selectors:
            try:
                variation = page.locator(selector).first
                if variation.is_visible(timeout=2000):
                    # Select first available option
                    options = page.locator(f"{selector} option").all()
                    for option in options:
                        if not option.get_attribute('disabled'):
                            option.click()
                            human_like_delay(1, 2)
                            break
            except:
                continue
                
        # First look for the dropdown arrow next to "Add to List"
        dropdown_selectors = [
            '[aria-label*="Dropdown"][aria-label*="List"]',  # Generic dropdown for list
            '[aria-label="Dropdown auswählen, Auf die Liste"]',  # German
            '[aria-label="Dropdown select, Add to List"]',  # English
            '#wishlistButtonStack span[role="button"]',  # Generic dropdown button
            '#wishlistButtonStack button:not([id="add-to-wishlist-button-submit"])',
            '[data-action="a-dropdown-button"]',
            '#add-to-wishlist-button-dropdown',
            '#add-to-wishlist-button'
        ]
        
        dropdown_button = None
        for selector in dropdown_selectors:
            try:
                element = page.locator(selector).first
                if element.is_visible(timeout=2000):
                    dropdown_button = element
                    break
            except:
                continue
        
        if dropdown_button:
            log_step("Add to Wishlist", "info", "Found wishlist dropdown, clicking to reveal options...")
            dropdown_button.click()
            human_like_delay(1, 2)
            
            if wishlist_name:
                # Look for the specific wishlist in the dropdown
                wishlist_option_selectors = [
                    f'[role="option"]:has-text("{wishlist_name}")',
                    f'#atwl-dd-ul li:has-text("{wishlist_name}")',
                    f'[data-value*="{wishlist_name}"]',
                    f'[aria-label*="{wishlist_name}"]',
                    f'a:has-text("{wishlist_name}")',
                    f'li:has-text("{wishlist_name}")'
                ]
                
                wishlist_option = None
                for selector in wishlist_option_selectors:
                    try:
                        element = page.locator(selector).first
                        if element.is_visible(timeout=2000):
                            wishlist_option = element
                            break
                    except:
                        continue
                
                if wishlist_option:
                    log_step("Add to Wishlist", "info", f"Found and selecting wishlist: {wishlist_name}")
                    wishlist_option.click()
                    human_like_delay(2, 3)
                else:
                    log_step("Add to Wishlist", "warning", f"Could not find wishlist: {wishlist_name}")
                    # Close dropdown by clicking outside
                    page.locator('body').click()
        
        # Now click the main "Add to List" button
        wishlist_selectors = [
            '#add-to-wishlist-button-submit',
            'input[name="submit.add-to-registry.wishlist"]',
            'button[name="submit.add-to-registry.wishlist"]',
            '#add-to-list-button',
            'input[aria-labelledby="wishListMainButton-announce"]',
            'button[aria-labelledby="wishListMainButton-announce"]',
            'span:has-text("Auf die Liste") >> xpath=..',
            'span:has-text("Add to List") >> xpath=..',
            '[title="Auf die Liste"]',
            '[title="Add to List"]',
            '#add-to-wishlist-button'
        ]
        
        # Try multiple times as sometimes the button needs time to be really clickable
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                wishlist_button = None
                for selector in wishlist_selectors:
                    try:
                        element = page.locator(selector).first
                        if element.is_visible(timeout=5000):
                            wishlist_button = element
                            break
                    except:
                        continue
                
                if not wishlist_button:
                    if attempt == max_attempts - 1:
                        log_step("Add to Wishlist", "error", "Wishlist button not found")
                        return False
                    continue
                
                wishlist_button.scroll_into_view_if_needed()
                human_like_delay(1, 2)
                
                log_step("Add to Wishlist", "info", f"Clicking wishlist button (attempt {attempt + 1})...")
                wishlist_button.click()
                
                # Wait for button state change or success indicators
                success_change = page.wait_for_selector('[data-action="reg-item-added"], [data-action="view-wishlist"]', timeout=5000)
                if success_change:
                    break
                    
            except Exception as click_error:
                log_step("Add to Wishlist", "warning", f"Click attempt {attempt + 1} failed: {str(click_error)}")
                if attempt == max_attempts - 1:
                    raise
                human_like_delay(2, 3)
                continue
                
        human_like_delay(3, 5)
        
        # Check for and dismiss any post-add popups
        popup_close_selectors = [
            '[data-action="reg-close-button"]',
            '[data-action="a-popover-close"]',
            'button:has-text("Close")',
            'button:has-text("Schließen")'
        ]
        
        # Look for success indicators
        success_indicators = [
            'span:has-text("Wunschzettel anzeigen")',
            'span:has-text("View Your List")',
            'span:has-text("View Wish List")',
            'div:has-text("wurde der Liste hinzugefügt")',
            'div:has-text("was added to")',
            '[data-action="reg-item-added"]',
            '[data-action="view-wishlist"]',
            '#WLHUC_result',  # Wishlist add confirmation section
            '#huc-atwl-header-section'  # Header of add confirmation
        ]
        
        success_found = False
        
        # First check if add was successful
        for indicator in success_indicators:
            try:
                if page.locator(indicator).is_visible(timeout=5000):
                    log_step("Add to Wishlist", "success", f"SUCCESS: Product added to wishlist - Found indicator: {indicator}")
                    success_found = True
                    
                    # Try to close any popups
                    for close_selector in popup_close_selectors:
                        try:
                            close_btn = page.locator(close_selector).first
                            if close_btn.is_visible(timeout=1000):
                                close_btn.click()
                                break
                        except:
                            continue
                            
                    break
            except:
                continue
                
        if success_found:
            return True
            
        # If no success indicators, check for errors
        error_indicators = [
            'div:has-text("could not be added")',
            'div:has-text("konnte nicht hinzugefügt werden")',
            '#huc-atwl-error-section'
        ]
        
        for error in error_indicators:
            try:
                if page.locator(error).is_visible(timeout=1000):
                    log_step("Add to Wishlist", "error", f"Failed to add item - Error found: {error}")
                    return False
            except:
                continue
                
        log_step("Add to Wishlist", "warning", "Could not verify if product was added successfully")
        # Take screenshot for debugging
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, f"add_wishlist_{timestamp}.png"))
        except:
            pass
            
        return False  # Be conservative - if we can't verify success, assume failure
        
    except Exception as e:
        log_step("Add to Wishlist", "error", f"Error adding product to wishlist: {str(e)}")
        return False

def create_wishlists_and_add_products(page: Page, products: list, target_count=2):
    """
    Creates separate wishlists for products and adds them.
    """
    log_step("Wishlist Creation", "info", f"Creating {target_count} wishlists and adding products")
    
    successful_additions = 0
    
    if not products:
        log_step("Wishlist Creation", "error", "No products were collected to add to wishlists.")
        return 0

    for i in range(min(target_count, len(products))):
        product = products[i]
        wishlist_name = f"My Automation List {i+1} - {datetime.now().strftime('%m-%d %H:%M')}"
        
        log_step("Wishlist Creation", "info", f"=== Processing product {i+1}/{target_count}: {product['title']} ===")
        
        wishlist_created = create_new_wishlist(page, wishlist_name)
        
        if wishlist_created:
            product_added = add_product_to_current_wishlist(page, product['url'], product['title'], wishlist_name)
            if product_added:
                successful_additions += 1
                log_step("Wishlist Creation", "success", f"Successfully created wishlist and added product {i+1}")
            else:
                log_step("Wishlist Creation", "error", f"Created wishlist but FAILED to add product {i+1}")
        else:
            log_step("Wishlist Creation", "error", f"FAILED to create wishlist for product {i+1}")
        
        human_like_delay(3, 5)
    
    log_step("Wishlist Creation", "success", f"Completed. Successfully added {successful_additions}/{target_count} products to new wishlists.")
    return successful_additions


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
            'button:has-text("Mitgliedschaft beenden")'
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
    """Main function with enhanced login verification and wishlist creation."""
    for directory in [SCREENSHOTS_DIR, SESSION_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    proxy_config = random.choice(PROXIES)
    session_file = os.path.join(SESSION_DIR, f"{ACCOUNT['email'].split('@')[0]}.json")
    
    log_step("Setup", "info", f"Using account: {ACCOUNT['email']}, proxy: {proxy_config['server']}")

    with sync_playwright() as p:
        browser = None
        
        for attempt in range(2):
            page = None # Ensure page is defined for error handling
            try:
                log_step("Browser Setup", "info", f"Starting browser (attempt {attempt + 1}/2)")
                
                browser = p.chromium.launch(
                    headless=False,
                    proxy=proxy_config,
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                context = browser.new_context(
                    storage_state=session_file if os.path.exists(session_file) else None,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    locale="de-DE"
                )
                
                page = context.new_page()
                stealth_sync(page)

                log_step("Task Execution", "info", "Starting automation tasks...")
                
                login_success = ensure_proper_login(page, ACCOUNT['email'], ACCOUNT['password'])
                if not login_success:
                    raise Exception("Failed to establish proper login")
                
                collected_products = browse_random_products(page, 5)
                if not collected_products:
                    raise Exception("No products collected during browsing")
                
                products_added = create_wishlists_and_add_products(page, collected_products, target_count=2)
                
                cancel_prime_if_active(page)

                context.storage_state(path=session_file)
                log_step("Session", "success", f"Session state saved to {session_file}")
                
                if products_added >= 2:
                    log_step("Completion", "success", f"Automation completed successfully! Added {products_added} products to new wishlists.")
                else:
                    log_step("Completion", "warning", f"Automation completed with partial success. Added {products_added}/2 products.")
                
                break

            except Exception as e:
                error_message = str(e).splitlines()[0]
                log_step("Error", "critical", f"Automation failed: {error_message}")
                
                if page:
                    try:
                        screenshot_path = os.path.join(SCREENSHOTS_DIR, f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                        page.screenshot(path=screenshot_path)
                        log_step("Error Handling", "info", f"Error screenshot saved to {screenshot_path}")
                    except Exception as se:
                        log_step("Error Handling", "error", f"Could not save screenshot: {se}")

                if attempt == 0:
                    log_step("Error Handling", "warning", "Retrying automation (1/1 retry attempts)")
                    if browser:
                        browser.close()
                    human_like_delay(5, 10)
                else:
                    log_step("Error Handling", "critical", "Maximum retries reached. Automation failed.")
                    
            finally:
                if browser:
                    try:
                        browser.close()
                    except:
                        pass
    
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(LOGS, f, indent=4, ensure_ascii=False)
    print(f"Final logs saved to {LOG_FILE}")


if __name__ == "__main__":
    start_time = datetime.now()
    log_step("Script Start", "info", f"Amazon automation script started at {start_time}")
    
    try:
        run_automation()
    except KeyboardInterrupt:
        log_step("Script Interrupted", "warning", "Script was interrupted by user")
    except Exception as e:
        log_step("Script Error", "critical", f"Unexpected script error occurred: {str(e)}")
    finally:
        end_time = datetime.now()
        duration = end_time - start_time
        log_step("Script End", "info", f"Script completed in {duration.total_seconds():.1f} seconds")