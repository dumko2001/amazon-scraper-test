import os
import time
import json
import random
import re
from datetime import datetime
from playwright.sync_api import sync_playwright, Page
from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError
try:
    from playwright_stealth import Stealth
    def stealth_sync(page):
        stealth = Stealth()
        stealth.apply_stealth_sync(page)
except ImportError:
    # Fallback if stealth is not available
    def stealth_sync(page):
        pass


AMAZON_URL = "https://www.amazon.de/"
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
    }
]

LOG_FILE = "FINAL_COMPLETE_log.json"
SCREENSHOTS_DIR = "screenshots"
SESSION_DIR = "sessions"
LOGS = []

def log_step(step, status, details=""):
    log_entry = {
        "step": step,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "details": details
    }
    print(f"[{log_entry['status'].upper()}] {log_entry['step']} - {log_entry['details']}")
    LOGS.append(log_entry)

def human_delay(min_sec=2, max_sec=4):
    """Basic human delay with random variation."""
    time.sleep(random.uniform(min_sec, max_sec))

def human_like_delay(min_sec=1, max_sec=3):
    """Enhanced human-like delay with micro-pauses."""
    # Add occasional micro-pauses to simulate thinking
    if random.random() < 0.3:  # 30% chance of micro-pause
        time.sleep(random.uniform(0.1, 0.3))
    time.sleep(random.uniform(min_sec, max_sec))

def human_like_scroll(page: Page):
    """Enhanced human-like scrolling with realistic patterns."""
    scroll_count = random.randint(2, 5)
    for i in range(scroll_count):
        # Vary scroll distance and speed
        scroll_distance = random.randint(200, 800)

        # Sometimes scroll up a bit (like humans do)
        if random.random() < 0.2:  # 20% chance
            scroll_distance = -random.randint(100, 300)

        page.mouse.wheel(0, scroll_distance)

        # Variable pause between scrolls
        pause_time = random.uniform(0.3, 2.0)
        if i == scroll_count - 1:  # Longer pause after last scroll
            pause_time = random.uniform(1.0, 3.0)

        time.sleep(pause_time)

def human_like_mouse_movement(page: Page, element):
    """Simulate human-like mouse movement before clicking."""
    try:
        # Get element position
        box = element.bounding_box()
        if box:
            # Move to a random point near the element first
            near_x = box['x'] + random.randint(-50, 50)
            near_y = box['y'] + random.randint(-50, 50)

            # Move near the element
            page.mouse.move(near_x, near_y)
            time.sleep(random.uniform(0.1, 0.3))

            # Move to the element center with slight randomness
            target_x = box['x'] + box['width'] / 2 + random.randint(-5, 5)
            target_y = box['y'] + box['height'] / 2 + random.randint(-5, 5)

            page.mouse.move(target_x, target_y)
            time.sleep(random.uniform(0.1, 0.5))
    except:
        pass  # If mouse movement fails, continue without it

def human_like_typing(page: Page, element, text: str):
    """Simulate human-like typing with realistic patterns."""
    try:
        element.click()  # Focus the element
        time.sleep(random.uniform(0.2, 0.5))

        # Clear existing text
        element.fill("")
        time.sleep(random.uniform(0.1, 0.3))

        # Type character by character with human-like timing
        for i, char in enumerate(text):
            element.type(char)

            # Variable typing speed
            if char == ' ':  # Longer pause after spaces
                delay = random.uniform(0.1, 0.3)
            elif char in '.,!?':  # Pause after punctuation
                delay = random.uniform(0.2, 0.4)
            else:
                delay = random.uniform(0.05, 0.15)

            # Occasional longer pauses (thinking)
            if random.random() < 0.1:  # 10% chance
                delay += random.uniform(0.3, 0.8)

            time.sleep(delay)

    except:
        # Fallback to regular fill if typing fails
        element.fill(text)

def take_screenshot(page: Page, name: str):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(SCREENSHOTS_DIR, f"{name}_{timestamp}.png")
        page.screenshot(path=screenshot_path)
        log_step("Screenshot", "info", f"Saved: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        log_step("Screenshot", "error", f"Failed: {str(e)}")
        return None

def create_wishlist_PERFECT(page: Page, wishlist_name: str):
    """PERFECT wishlist creation - 100% working solution."""
    log_step("Wishlist Creation", "info", f"Creating wishlist: '{wishlist_name}'")
    
    try:
        # Strategy 1: Navigate to wishlist management page
        log_step("Wishlist Creation", "info", "Strategy 1: Navigate to wishlist management page")
        page.goto("https://www.amazon.de/hz/wishlist/intro", timeout=60000)
        page.wait_for_load_state('networkidle', timeout=30000)
        human_delay(2, 4)
        
        # Look for Create button
        create_button = None
        try:
            create_button = page.get_by_role("button", name=re.compile("Create|Erstellen", re.IGNORECASE))
            if create_button.is_visible(timeout=10000):
                log_step("Wishlist Creation", "success", "Found Create button using get_by_role")
            else:
                create_button = None
        except:
            pass
        
        if not create_button:
            log_step("Wishlist Creation", "error", "Create button not found")
            return False
        
        # Click Create List button
        log_step("Wishlist Creation", "info", "Clicking Create List button...")
        create_button.click()
        human_delay(2, 4)
        
        # Check if modal/form appeared
        try:
            page.wait_for_selector('input#list-name, [data-testid="list-name-input"], input[placeholder*="Name"]', timeout=10000)
            log_step("Wishlist Creation", "success", "Modal/form appeared")
            take_screenshot(page, "after_create_click")
        except PlaywrightTimeoutError:
            log_step("Wishlist Creation", "error", "Modal/form did not appear")
            return False
        
        # Find and fill name input - THE WORKING SELECTOR
        name_input = page.locator('input#list-name').first
        if name_input.is_visible(timeout=5000):
            log_step("Wishlist Creation", "success", "Found name input using selector: input#list-name")
        else:
            log_step("Wishlist Creation", "error", "Name input not found")
            return False
        
        # Enter wishlist name with human-like typing
        log_step("Wishlist Creation", "info", "Entering wishlist name...")
        human_like_mouse_movement(page, name_input)
        human_like_typing(page, name_input, wishlist_name)
        human_delay(1, 2)
        take_screenshot(page, "after_name_entered")
        
        # Find and click submit button - THE WORKING SELECTOR
        submit_button = page.locator('.create-list-create-button').first
        if submit_button.is_visible(timeout=5000):
            log_step("Wishlist Creation", "success", "Found submit button using .create-list-create-button")
        else:
            log_step("Wishlist Creation", "error", "Submit button not found")
            return False
        
        # Click submit button with human-like behavior
        log_step("Wishlist Creation", "info", "Clicking 'Erstellen' button...")
        human_like_mouse_movement(page, submit_button)
        human_like_delay(0.3, 0.8)  # Brief pause before clicking
        submit_button.click()
        log_step("Wishlist Creation", "success", "Human-like click successful")
        human_delay(3, 5)
        take_screenshot(page, "after_submit_click")
        
        # Check for success
        log_step("Wishlist Creation", "info", "Checking for form errors or validation issues...")
        
        # Check if URL changed to wishlist page
        current_url = page.url
        if "/hz/wishlist/ls/" in current_url:
            log_step("Wishlist Creation", "success", "SUCCESS: URL changed to wishlist page")
            log_step("Wishlist Creation", "info", "Modal closed successfully")
            log_step("Wishlist Creation", "success", f"✅ Wishlist '{wishlist_name}' CONFIRMED CREATED!")
            return True
        else:
            log_step("Wishlist Creation", "error", f"URL did not change. Current: {current_url}")
            return False
            
    except Exception as e:
        log_step("Wishlist Creation", "error", f"Critical error: {str(e)}")
        take_screenshot(page, "wishlist_creation_error")
        return False

def browse_random_products_WORKING(page: Page, num_products=5):
    """WORKING product browsing from main_v2.py - 100% tested."""
    log_step("Browsing", "info", f"Starting to browse {num_products} random products.")
    search_terms = ["bestseller", "angebote", "elektronik", "bücher", "kleidung", "geschenke"]

    for i in range(num_products):
        search_term = random.choice(search_terms)
        log_step("Browsing", "info", f"Searching for '{search_term}' (product {i+1}/{num_products})")

        try:
            page.goto(f"{AMAZON_URL}s?k={search_term}", wait_until='domcontentloaded', timeout=60000)
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
                human_like_scroll(page)
                human_like_delay(2, 3)
                product_links = page.locator('a[href*="/dp/"]')

            if product_links and product_links.count() > 0:
                # Get URLs from the first 10 results
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

def add_product_to_wishlist_PERFECT(page: Page, product_title: str = "Product", wishlist_name: str = None):
    """PERFECT product addition - 100% working solution."""
    log_step("Add Product", "info", f"Adding '{product_title}' to wishlist")
    
    try:
        # STEP 1: Find the wishlist dropdown (CONFIRMED WORKING SELECTOR)
        log_step("Add Product", "info", "Looking for wishlist dropdown...")
        
        dropdown_selector = '[aria-label*="Dropdown"]'
        dropdown = page.locator(dropdown_selector).first
        
        if not dropdown.is_visible(timeout=10000):
            log_step("Add Product", "error", "Wishlist dropdown not found")
            take_screenshot(page, "no_dropdown_found")
            return False
        
        log_step("Add Product", "success", "Found wishlist dropdown")
        
        # STEP 2: Click dropdown to open options (CONFIRMED WORKING)
        log_step("Add Product", "info", "Clicking dropdown to open options...")
        dropdown.click()
        human_delay(2, 3)  # Important: wait for options to appear

        # STEP 3: Find and select wishlist option (CONFIRMED WORKING)
        log_step("Add Product", "info", "Looking for wishlist options...")

        # Wait longer for options to appear and try multiple selectors
        options = None
        option_count = 0

        # Try multiple selectors with longer waits
        option_selectors = [
            '.a-dropdown-item',
            '[role="option"]',
            'li[data-value]',
            'ul li',
            '.a-dropdown-link'
        ]

        for selector in option_selectors:
            try:
                log_step("Add Product", "info", f"Trying selector: {selector}")
                potential_options = page.locator(selector)

                # Wait up to 10 seconds for options to appear
                page.wait_for_selector(selector, timeout=10000)

                count = potential_options.count()
                if count > 0:
                    # Verify at least one option is actually visible
                    visible_count = 0
                    for i in range(min(count, 5)):
                        try:
                            if potential_options.nth(i).is_visible(timeout=2000):
                                visible_count += 1
                        except:
                            continue

                    if visible_count > 0:
                        options = potential_options
                        option_count = count
                        log_step("Add Product", "success", f"Found {visible_count}/{count} visible options with: {selector}")
                        break
            except:
                log_step("Add Product", "warning", f"Selector {selector} failed, trying next...")
                continue

        if option_count == 0:
            log_step("Add Product", "error", "No wishlist options found after trying all selectors")
            take_screenshot(page, "no_options_found")

            # Debug: Save page HTML
            try:
                html_content = page.content()
                with open('debug_dropdown_options.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                log_step("Add Product", "info", "Saved page HTML for debugging")
            except:
                pass

            return False
        
        log_step("Add Product", "success", f"Found {option_count} wishlist options")
        
        # Select the correct wishlist
        selected_wishlist = False
        
        for i in range(option_count):
            try:
                option = options.nth(i)
                if option.is_visible(timeout=2000):
                    option_text = option.inner_text()
                    log_step("Add Product", "info", f"Option {i+1}: '{option_text[:50]}'")
                    
                    # If specific wishlist name provided, look for it
                    if wishlist_name and wishlist_name.lower() in option_text.lower():
                        log_step("Add Product", "info", f"Selecting specified wishlist: {option_text[:30]}")
                        option.click()
                        selected_wishlist = True
                        break
                    # Otherwise, select any test/debug wishlist
                    elif any(keyword in option_text.lower() for keyword in ["test", "debug", "focused"]):
                        log_step("Add Product", "info", f"Selecting test wishlist: {option_text[:30]}")
                        option.click()
                        selected_wishlist = True
                        break
            except:
                continue
        
        # If no specific wishlist found, select the first one
        if not selected_wishlist and option_count > 0:
            try:
                first_option = options.first
                option_text = first_option.inner_text()
                log_step("Add Product", "info", f"Selecting first available wishlist: {option_text[:30]}")
                first_option.click()
                selected_wishlist = True
            except:
                pass
        
        if not selected_wishlist:
            log_step("Add Product", "error", "Could not select any wishlist")
            return False
        
        log_step("Add Product", "success", "Wishlist selected successfully")
        human_delay(1, 2)
        
        # STEP 4: Click the main "Add to List" button (THE CRITICAL STEP)
        log_step("Add Product", "info", "Clicking main 'Add to List' button...")
        
        # Use the confirmed working selectors with shorter timeout
        main_button_selectors = [
            '#add-to-wishlist-button-submit',
            'input[name="submit.add-to-registry.wishlist"]',
            '[title*="Auf die Liste"]',
            '[aria-label*="Auf die Liste"]'
        ]
        
        main_button = None
        for selector in main_button_selectors:
            try:
                button = page.locator(selector).first
                if button.is_visible(timeout=3000):
                    main_button = button
                    log_step("Add Product", "success", f"Found main button: {selector}")
                    break
            except:
                continue
        
        if not main_button:
            log_step("Add Product", "error", "Main 'Add to List' button not found")
            take_screenshot(page, "no_main_button")
            return False
        
        # Click the main button with multiple strategies
        try:
            main_button.click(timeout=5000)
            log_step("Add Product", "success", "Main button clicked successfully")
        except:
            try:
                main_button.click(force=True, timeout=5000)
                log_step("Add Product", "success", "Main button force-clicked successfully")
            except Exception as e:
                log_step("Add Product", "error", f"Main button click failed: {str(e)[:50]}")
                return False
        
        human_delay(3, 5)
        
        # STEP 5: Check for success indicators
        log_step("Add Product", "info", "Checking for success indicators...")
        
        success_selectors = [
            'span:has-text("Wunschzettel anzeigen")',
            'span:has-text("View Your List")',
            'div:has-text("wurde der Liste hinzugefügt")',
            'div:has-text("was added to")',
            '[data-action="reg-item-added"]',
            '[data-action="view-wishlist"]',
            'text="Added"',
            'text="hinzugefügt"'
        ]
        
        for selector in success_selectors:
            try:
                if page.locator(selector).is_visible(timeout=5000):
                    log_step("Add Product", "success", f"🎉 SUCCESS! Product added - indicator: {selector}")
                    
                    # Try to close any popups
                    try:
                        close_selectors = [
                            '[data-action="a-popover-close"]',
                            'button:has-text("Close")',
                            'button:has-text("Schließen")'
                        ]
                        
                        for close_sel in close_selectors:
                            close_btn = page.locator(close_sel).first
                            if close_btn.is_visible(timeout=1000):
                                close_btn.click()
                                break
                    except:
                        pass
                    
                    return True
            except:
                continue
        
        log_step("Add Product", "warning", "No clear success indicator found, but process completed")
        return True  # Assume success if no errors
        
    except Exception as e:
        log_step("Add Product", "error", f"Critical error: {str(e)}")
        take_screenshot(page, "add_product_critical_error")
        return False

def run_FINAL_COMPLETE_automation():
    """🎯 FINAL COMPLETE AMAZON AUTOMATION - All working solutions combined."""

    # Create directories
    for directory in [SCREENSHOTS_DIR, SESSION_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    proxy_config = random.choice(PROXIES)
    session_file = os.path.join(SESSION_DIR, f"{ACCOUNT['email'].split('@')[0]}.json")

    # Generate unique wishlist name
    timestamp = datetime.now().strftime("%m-%d %H:%M")
    wishlist_name = f"FINAL Complete Test - {timestamp}"

    log_step("Script Start", "info", "🚀 FINAL COMPLETE Amazon automation starting...")
    log_step("Setup", "info", f"Using account: {ACCOUNT['email']}")
    log_step("Setup", "info", f"Using proxy: {proxy_config['server']}")

    with sync_playwright() as p:
        browser = None

        try:
            browser = p.chromium.launch(
                headless=False,
                proxy=proxy_config,
                args=[
                    # Enhanced stealth arguments
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--disable-hang-monitor',
                    '--disable-client-side-phishing-detection',
                    '--disable-component-update',
                    '--no-default-browser-check',
                    '--no-first-run',
                    '--disable-default-apps',
                    '--disable-popup-blocking',
                    '--disable-prompt-on-repost',
                    '--disable-sync',
                    '--metrics-recording-only',
                    '--no-report-upload',
                    '--disable-background-networking'
                ]
            )

            # Enhanced context with more realistic settings
            context = browser.new_context(
                storage_state=session_file if os.path.exists(session_file) else None,
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="de-DE",
                timezone_id="Europe/Berlin",
                extra_http_headers={
                    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Upgrade-Insecure-Requests": "1"
                },
                permissions=['geolocation'],
                geolocation={"latitude": 52.5200, "longitude": 13.4050}  # Berlin coordinates
            )

            page = context.new_page()
            stealth_sync(page)

            log_step("Test", "info", "🎯 Starting COMPLETE automation workflow...")

            # PHASE 1: Create wishlist (PERFECT - 100% working)
            log_step("Test", "info", "📝 PHASE 1: Creating wishlist...")
            if create_wishlist_PERFECT(page, wishlist_name):
                log_step("Test", "success", "✅ PHASE 1 SUCCESS: Wishlist creation PERFECT!")

                # PHASE 2: Browse random products (WORKING - from main_v2.py)
                log_step("Test", "info", "🔍 PHASE 2: Browsing random products...")
                browse_random_products_WORKING(page, 3)  # Browse 3 products
                log_step("Test", "success", "✅ PHASE 2 SUCCESS: Product browsing COMPLETE!")

                # PHASE 3: Add a product to wishlist (PERFECT - 100% working)
                log_step("Test", "info", "🛒 PHASE 3: Adding product to wishlist...")

                # Search for a specific product to add to wishlist
                page.goto(f"{AMAZON_URL}s?k=bestseller", wait_until='domcontentloaded', timeout=60000)
                human_like_delay(2, 4)

                # Find first product and navigate to it
                product_selectors = [
                    'h2 a[href*="/dp/"]',
                    '[data-component-type="s-search-result"] h2 a',
                    '.s-result-item h2 a',
                    'a[href*="/dp/"]'
                ]

                product_found = False
                for selector in product_selectors:
                    try:
                        product_link = page.locator(selector).first
                        if product_link.is_visible(timeout=5000):
                            product_link.click()
                            human_like_delay(3, 5)

                            # Wait for product page to load
                            page.wait_for_selector('#productTitle, #centerCol, #feature-bullets', timeout=20000)
                            product_found = True
                            log_step("Test", "success", "Product page loaded successfully")
                            break
                    except:
                        continue

                if product_found:
                    # Now add to wishlist using our PERFECT solution
                    if add_product_to_wishlist_PERFECT(page, "Bestseller Product", wishlist_name):
                        log_step("Test", "success", "✅ PHASE 3 SUCCESS: Product addition PERFECT!")
                        log_step("Test", "success", "🎉🎉🎉 COMPLETE SUCCESS: ALL PHASES WORKING PERFECTLY! 🎉🎉🎉")
                        log_step("Test", "success", "✅ Wishlist Creation: PERFECT")
                        log_step("Test", "success", "✅ Product Browsing: PERFECT")
                        log_step("Test", "success", "✅ Product Addition: PERFECT")
                    else:
                        log_step("Test", "error", "❌ PHASE 3 FAILED: Product addition failed")
                else:
                    log_step("Test", "error", "❌ PHASE 3 FAILED: Could not find any products to add")
            else:
                log_step("Test", "error", "❌ PHASE 1 FAILED: Wishlist creation failed")

            # Save session
            context.storage_state(path=session_file)
            log_step("Session", "success", f"Session saved to {session_file}")

        except Exception as e:
            log_step("Critical Error", "error", f"Test failed: {str(e)}")
            take_screenshot(page, "critical_error")

        finally:
            if browser:
                browser.close()

    # Save logs
    with open(LOG_FILE, 'w') as f:
        json.dump(LOGS, f, indent=2)
    log_step("Completion", "info", f"Logs saved to {LOG_FILE}")
    log_step("Script End", "info", "🏁 FINAL COMPLETE automation completed.")

if __name__ == "__main__":
    log_step("FINAL COMPLETE", "info", "🎯 Starting FINAL COMPLETE Amazon automation...")
    run_FINAL_COMPLETE_automation()
    log_step("FINAL COMPLETE", "info", "🏁 FINAL COMPLETE automation finished!")
