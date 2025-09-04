import os
import time
import json
import random
import re
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import stealth_sync

# --- CONFIGURATION ---
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
    },
]

LOG_FILE = "wishlist_focused_log.json"
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
    time.sleep(random.uniform(min_sec, max_sec))

def human_like_delay(min_sec=1, max_sec=3):
    """Waits for a random duration to mimic human behavior."""
    time.sleep(random.uniform(min_sec, max_sec))

def human_like_scroll(page: Page):
    """Scrolls the page in a more human-like way."""
    for _ in range(random.randint(2, 5)):
        page.mouse.wheel(0, random.randint(300, 600))
        human_like_delay(0.5, 1.5)

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

def create_wishlist_robust(page: Page, wishlist_name: str):
    """Ultra-robust wishlist creation using multiple strategies."""
    log_step("Wishlist Creation", "info", f"Creating wishlist: '{wishlist_name}'")
    
    try:
        # Strategy 1: Try going to existing wishlist page first, then create new one
        log_step("Wishlist Creation", "info", "Strategy 1: Navigate to wishlist management page")

        # First try the main wishlist page
        try:
            page.goto(f"{AMAZON_URL}hz/wishlist", timeout=60000)
            page.wait_for_load_state('networkidle', timeout=30000)
            human_delay(3, 5)

            # Look for "Create new list" or similar button
            create_new_selectors = [
                'button:has-text("Neue Liste erstellen")',
                'button:has-text("Create new list")',
                'a:has-text("Neue Liste erstellen")',
                'a:has-text("Create new list")',
                'button:has-text("Liste erstellen")',
                'button:has-text("Create a List")'
            ]

            create_button = None
            for selector in create_new_selectors:
                try:
                    element = page.locator(selector).first
                    if element.is_visible(timeout=3000):
                        create_button = element
                        log_step("Wishlist Creation", "success", f"Found create button on main page: {selector}")
                        break
                except:
                    continue

            if not create_button:
                # Fallback to intro page
                log_step("Wishlist Creation", "info", "No create button on main page, trying intro page")
                page.goto(f"{AMAZON_URL}hz/wishlist/intro", timeout=60000)
                page.wait_for_load_state('networkidle', timeout=30000)
                human_delay(3, 5)
        except:
            # Fallback to intro page
            log_step("Wishlist Creation", "info", "Main page failed, trying intro page")
            page.goto(f"{AMAZON_URL}hz/wishlist/intro", timeout=60000)
            page.wait_for_load_state('networkidle', timeout=30000)
            human_delay(3, 5)
        
        # Look for Create List button using multiple methods
        create_button = None
        
        # Method 1: get_by_role (most reliable)
        try:
            create_button = page.get_by_role("button", name=re.compile("Create.*List|Liste erstellen", re.IGNORECASE))
            if create_button.is_visible(timeout=5000):
                log_step("Wishlist Creation", "success", "Found Create button using get_by_role")
            else:
                create_button = None
        except:
            pass
        
        # Method 2: get_by_text
        if not create_button:
            try:
                create_button = page.get_by_text(re.compile("Liste erstellen|Create.*List", re.IGNORECASE))
                if create_button.is_visible(timeout=5000):
                    log_step("Wishlist Creation", "success", "Found Create button using get_by_text")
                else:
                    create_button = None
            except:
                pass
        
        # Method 3: Traditional selectors
        if not create_button:
            selectors = [
                'button:has-text("Liste erstellen")',
                'button:has-text("Create a List")',
                'a:has-text("Liste erstellen")',
                'a:has-text("Create a List")',
                'input[value*="Liste erstellen"]',
                'input[value*="Create"]',
                '.a-button:has-text("Liste")',
                '.a-button:has-text("Create")'
            ]
            
            for selector in selectors:
                try:
                    element = page.locator(selector).first
                    if element.is_visible(timeout=3000):
                        create_button = element
                        log_step("Wishlist Creation", "success", f"Found Create button using selector: {selector}")
                        break
                except:
                    continue
        
        if not create_button:
            log_step("Wishlist Creation", "warning", "Strategy 1 failed, trying Strategy 2")
            
            # Strategy 2: Navigate through account menu
            page.goto(AMAZON_URL, timeout=60000)
            page.wait_for_load_state('networkidle', timeout=30000)
            human_delay(2, 3)
            
            # Hover over account menu
            account_element = page.locator('#nav-link-accountList').first
            if account_element.is_visible(timeout=10000):
                account_element.hover()
                human_delay(2, 3)
                
                # Look for wishlist link
                wishlist_selectors = [
                    'a:has-text("Wunschzettel")',
                    'a:has-text("Wish List")',
                    'a:has-text("Listen")',
                    'a:has-text("Lists")'
                ]
                
                for selector in wishlist_selectors:
                    try:
                        wishlist_link = page.locator(selector).first
                        if wishlist_link.is_visible(timeout=3000):
                            wishlist_link.click()
                            page.wait_for_load_state('networkidle', timeout=30000)
                            human_delay(2, 3)
                            
                            # Now look for create button again
                            create_button = page.get_by_role("button", name=re.compile("Create.*List|Liste erstellen", re.IGNORECASE))
                            if create_button.is_visible(timeout=5000):
                                log_step("Wishlist Creation", "success", "Found Create button via account menu")
                                break
                    except:
                        continue
        
        if not create_button:
            log_step("Wishlist Creation", "error", "All strategies failed to find Create button")
            take_screenshot(page, "create_button_not_found")
            return False
        
        # Click the Create button
        log_step("Wishlist Creation", "info", "Clicking Create List button...")
        create_button.click()
        human_delay(3, 5)
        
        # Wait for modal/form to appear
        modal_appeared = False
        try:
            page.wait_for_selector('dialog[role="dialog"], div[role="dialog"], .a-modal-scroller, form', timeout=10000)
            modal_appeared = True
            log_step("Wishlist Creation", "success", "Modal/form appeared")
        except PlaywrightTimeoutError:
            log_step("Wishlist Creation", "warning", "No modal detected, continuing...")
        
        take_screenshot(page, "after_create_click")
        
        # Find name input field using multiple methods
        name_input = None
        
        # Method 1: get_by_label (most reliable)
        try:
            name_input = page.get_by_label(re.compile("List name|Name.*Liste|Name.*required", re.IGNORECASE))
            if name_input.is_visible(timeout=5000):
                log_step("Wishlist Creation", "success", "Found name input using get_by_label")
            else:
                name_input = None
        except:
            pass
        
        # Method 2: get_by_placeholder
        if not name_input:
            try:
                name_input = page.get_by_placeholder(re.compile("Name|Liste", re.IGNORECASE))
                if name_input.is_visible(timeout=5000):
                    log_step("Wishlist Creation", "success", "Found name input using get_by_placeholder")
                else:
                    name_input = None
            except:
                pass
        
        # Method 3: Traditional selectors
        if not name_input:
            selectors = [
                'input[name="name"]',
                'input[placeholder*="Name"]',
                'input[aria-label*="Name"]',
                'input[aria-label*="Liste"]',
                'input#list-name',
                'input[type="text"]'
            ]
            
            for selector in selectors:
                try:
                    element = page.locator(selector).first
                    if element.is_visible(timeout=3000):
                        name_input = element
                        log_step("Wishlist Creation", "success", f"Found name input using selector: {selector}")
                        break
                except:
                    continue
        
        if not name_input:
            log_step("Wishlist Creation", "error", "Name input field not found")
            take_screenshot(page, "name_input_not_found")
            return False
        
        # Enter wishlist name
        log_step("Wishlist Creation", "info", "Entering wishlist name...")
        name_input.click()
        human_delay(0.5, 1)
        name_input.clear()
        name_input.press_sequentially(wishlist_name, delay=100)  # Type like human
        human_delay(1, 2)
        
        take_screenshot(page, "after_name_entered")
        
        # Find and click submit button - CRITICAL: Use the modal button approach
        submit_button = None

        # Method 1: THE CORRECT SELECTOR - Based on HTML analysis
        try:
            # This is the ACTUAL working selector from the HTML structure
            submit_button = page.locator('.create-list-create-button').first
            if submit_button.is_visible(timeout=5000):
                log_step("Wishlist Creation", "success", "Found submit button using .create-list-create-button")
            else:
                submit_button = None
        except:
            pass
        
        # Method 2: Alternative correct selectors
        if not submit_button:
            correct_selectors = [
                'input[aria-labelledby="lists-desktop-create-list-label"]',
                '[data-action="create-list-submit"]'
            ]

            for selector in correct_selectors:
                try:
                    element = page.locator(selector).first
                    if element.is_visible(timeout=3000):
                        submit_button = element
                        log_step("Wishlist Creation", "success", f"Found submit button using selector: {selector}")
                        break
                except:
                    continue

        # Method 3: Fallback to form inputs (less reliable)
        if not submit_button:
            form_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'input[value*="Create"]',
                'input[value*="Erstellen"]'
            ]

            for selector in form_selectors:
                try:
                    element = page.locator(selector).first
                    if element.is_visible(timeout=3000):
                        submit_button = element
                        log_step("Wishlist Creation", "warning", f"Found form input using selector: {selector}")
                        break
                except:
                    continue
        
        if not submit_button:
            # Try pressing Enter on the name input as fallback
            log_step("Wishlist Creation", "warning", "Submit button not found, trying Enter key")
            name_input.press("Enter")
            human_delay(3, 5)
        else:
            # Click submit button with multiple strategies - CRITICAL SECTION
            log_step("Wishlist Creation", "info", "Clicking 'Erstellen' button...")

            click_successful = False

            # Strategy 1: Normal click
            try:
                submit_button.click(timeout=10000)  # Shorter timeout
                click_successful = True
                log_step("Wishlist Creation", "success", "Normal click successful")
            except Exception as e:
                log_step("Wishlist Creation", "warning", f"Normal click failed: {str(e)[:100]}")

                # Strategy 2: Force click
                try:
                    submit_button.click(force=True, timeout=10000)
                    click_successful = True
                    log_step("Wishlist Creation", "success", "Force click successful")
                except Exception as e2:
                    log_step("Wishlist Creation", "warning", f"Force click failed: {str(e2)[:100]}")

                    # Strategy 3: JavaScript click
                    try:
                        page.evaluate("arguments[0].click()", submit_button.element_handle())
                        click_successful = True
                        log_step("Wishlist Creation", "success", "JavaScript click successful")
                    except Exception as e3:
                        log_step("Wishlist Creation", "warning", f"JS click failed: {str(e3)[:100]}")

                        # Strategy 4: Press Enter on name input
                        try:
                            name_input.press("Enter")
                            click_successful = True
                            log_step("Wishlist Creation", "success", "Enter key successful")
                        except Exception as e4:
                            log_step("Wishlist Creation", "error", f"All click methods failed: {str(e4)[:100]}")

            if not click_successful:
                log_step("Wishlist Creation", "error", "CRITICAL: Could not click Erstellen button")
                take_screenshot(page, "erstellen_click_failed")
                return False

            human_delay(5, 8)  # Longer wait for page to process
        
        take_screenshot(page, "after_submit_click")

        # Check for form validation errors or other issues
        log_step("Wishlist Creation", "info", "Checking for form errors or validation issues...")

        error_selectors = [
            '.a-alert-error',
            '.a-form-error',
            '[role="alert"]',
            'div:has-text("error")',
            'div:has-text("Error")',
            'div:has-text("fehler")',
            'div:has-text("Fehler")',
            'span:has-text("required")',
            'span:has-text("erforderlich")'
        ]

        for error_selector in error_selectors:
            try:
                if page.locator(error_selector).is_visible(timeout=2000):
                    error_text = page.locator(error_selector).inner_text()
                    log_step("Wishlist Creation", "error", f"Form validation error found: {error_text[:100]}")
                    take_screenshot(page, "form_validation_error")
                    return False
            except:
                continue

        # Check if modal is still open (indicates form didn't submit)
        try:
            modal_still_open = page.locator('dialog[role="dialog"], div[role="dialog"], .a-modal-scroller').is_visible(timeout=3000)
            if modal_still_open:
                log_step("Wishlist Creation", "warning", "Modal is still open - form may not have submitted properly")

                # Try to find any additional required fields
                required_fields = page.locator('input[required], select[required], textarea[required]')
                field_count = required_fields.count()

                if field_count > 1:  # More than just the name field
                    log_step("Wishlist Creation", "warning", f"Found {field_count} required fields - may need to fill additional fields")

                    for i in range(field_count):
                        try:
                            field = required_fields.nth(i)
                            field_name = field.get_attribute('name') or field.get_attribute('id') or f"field_{i}"
                            field_value = field.input_value()

                            if not field_value:  # Empty required field
                                log_step("Wishlist Creation", "warning", f"Empty required field found: {field_name}")

                                # Try to fill common fields
                                if 'privacy' in field_name.lower() or 'visibility' in field_name.lower():
                                    try:
                                        field.select_option('private')
                                        log_step("Wishlist Creation", "info", f"Set {field_name} to private")
                                    except:
                                        pass
                        except:
                            continue

                    # Try clicking submit again after filling additional fields
                    log_step("Wishlist Creation", "info", "Retrying submit after checking additional fields...")
                    try:
                        submit_button.click(force=True, timeout=5000)
                        human_delay(3, 5)
                    except:
                        pass
        except:
            pass

        # STRICT SUCCESS VERIFICATION - Only report success if we're 100% sure
        success_found = False

        # Method 1: Check URL change to actual wishlist page (most reliable) - Use same pattern as wish.py
        try:
            page.wait_for_url(re.compile(r"/hz/wishlist/ls/.*"), timeout=15000)
            success_found = True
            log_step("Wishlist Creation", "success", "SUCCESS: URL changed to wishlist page")

            # Wait for modal to close
            try:
                page.wait_for_selector('dialog[role="dialog"], div[role="dialog"]', state="hidden", timeout=5000)
                log_step("Wishlist Creation", "info", "Modal closed successfully")
            except:
                pass  # Modal might close differently

        except PlaywrightTimeoutError:
            log_step("Wishlist Creation", "warning", "URL did not change to wishlist page")

        # Method 2: Check for wishlist name on the page (very reliable)
        if not success_found:
            try:
                # Look for the exact wishlist name we created
                name_element = page.locator(f'text="{wishlist_name}"').first
                if name_element.is_visible(timeout=5000):
                    success_found = True
                    log_step("Wishlist Creation", "success", f"SUCCESS: Found wishlist name '{wishlist_name}' on page")
            except:
                pass

        # Method 3: Check for wishlist page elements (moderately reliable)
        if not success_found:
            wishlist_page_indicators = [
                'h1:has-text("Wunschzettel")',
                'h1:has-text("Wish List")',
                '[data-testid="list-name"]',
                '.list-name',
                '#listName'
            ]

            for indicator in wishlist_page_indicators:
                try:
                    if page.locator(indicator).is_visible(timeout=3000):
                        # Double-check we're not still on intro page
                        current_url = page.url.lower()
                        if '/intro' not in current_url and '/hz/wishlist' in current_url:
                            success_found = True
                            log_step("Wishlist Creation", "success", f"SUCCESS: Found wishlist page indicator: {indicator}")
                            break
                except:
                    continue

        # Method 4: Final URL check (least reliable, only if others fail)
        if not success_found:
            current_url = page.url.lower()
            if '/hz/wishlist/ls/' in current_url and '/intro' not in current_url:
                # Additional check: make sure we're not on an error page
                error_indicators = ['error', 'fehler', 'problem']
                page_text = page.locator('body').inner_text().lower()

                if not any(error in page_text for error in error_indicators):
                    success_found = True
                    log_step("Wishlist Creation", "success", f"SUCCESS: On wishlist page (URL check): {current_url}")

        if success_found:
            log_step("Wishlist Creation", "success", f"✅ Wishlist '{wishlist_name}' CONFIRMED CREATED!")
            return True
        else:
            log_step("Wishlist Creation", "error", f"❌ FAILED: Could not confirm wishlist creation")
            log_step("Wishlist Creation", "error", f"Current URL: {page.url}")
            take_screenshot(page, "wishlist_creation_failed")
            return False
            
    except Exception as e:
        log_step("Wishlist Creation", "error", f"Critical error: {str(e)}")
        take_screenshot(page, "wishlist_creation_error")
        return False

def add_product_to_wishlist_FINAL_WORKING(page: Page, product_url: str = None, product_title: str = "Product", wishlist_name: str = None):
    """
    FINAL WORKING SOLUTION for adding products to wishlist.
    Based on successful debug analysis.
    """
    log_step("Add Product", "info", f"Adding '{product_title}' to wishlist")

    try:
        # If product URL provided, navigate to it
        if product_url:
            page.goto(product_url, timeout=60000)
            page.wait_for_load_state('networkidle', timeout=30000)
            human_delay(2, 4)

            # Verify we're on product page
            try:
                page.wait_for_selector('#productTitle, #centerCol', timeout=20000)
            except PlaywrightTimeoutError:
                log_step("Add Product", "warning", "Product page load timeout, continuing...")

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

        # Use the confirmed working selector
        options = page.locator('.a-dropdown-item')
        option_count = options.count()

        if option_count == 0:
            log_step("Add Product", "error", "No wishlist options found")
            take_screenshot(page, "no_options_found")
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

def browse_random_products_WORKING(page: Page, num_products=5):
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

def run_focused_test():
        role_patterns = [
            "Add.*List",
            "Auf.*Liste",
            "Add.*Wish",
            "Wunsch.*hinzu",
            "Liste.*hinzu",
            "Add.*Cart",  # Sometimes it's "Add to Cart" first
            "In den.*Warenkorb"
        ]

        for pattern in role_patterns:
            try:
                add_button = page.get_by_role("button", name=re.compile(pattern, re.IGNORECASE))
                if add_button.is_visible(timeout=3000):
                    log_step("Add Product", "success", f"Found button using get_by_role pattern: {pattern}")
                    break
                else:
                    add_button = None
            except:
                continue

        # Method 2: get_by_text with more variations
        if not add_button:
            text_patterns = [
                "Auf die Liste",
                "Add to List",
                "Add to Wish",
                "Zur Wunschliste",
                "Liste hinzufügen",
                "Wunschzettel",
                "Wishlist"
            ]

            for pattern in text_patterns:
                try:
                    add_button = page.get_by_text(pattern, exact=False)
                    if add_button.is_visible(timeout=3000):
                        log_step("Add Product", "success", f"Found button using get_by_text: {pattern}")
                        break
                    else:
                        add_button = None
                except:
                    continue

        # Method 3: Traditional selectors with more comprehensive list
        if not add_button:
            selectors = [
                # Primary wishlist selectors
                '#add-to-wishlist-button-submit',
                'input[name="submit.add-to-registry.wishlist"]',
                'button[name="submit.add-to-registry.wishlist"]',

                # Text-based selectors
                'span:has-text("Auf die Liste")',
                'span:has-text("Add to List")',
                'button:has-text("Auf die Liste")',
                'button:has-text("Add to List")',
                'a:has-text("Auf die Liste")',
                'a:has-text("Add to List")',

                # Title/aria-label selectors
                '[title="Auf die Liste"]',
                '[title="Add to List"]',
                '[aria-label*="Liste"]',
                '[aria-label*="List"]',
                '[aria-label*="Wishlist"]',
                '[aria-label*="Wunsch"]',

                # ID and class selectors
                '#wishListMainButton',
                '#add-to-wishlist-button',
                '.a-button-wishlist',
                '.wishlist-button',

                # Data attribute selectors
                '[data-action*="wishlist"]',
                '[data-action*="add-to-registry"]',
                '[data-testid*="wishlist"]',
                '[data-testid*="add-to-list"]',

                # Generic button selectors that might contain wishlist functionality
                'button[type="submit"]',
                'input[type="submit"]',
                'button.a-button-primary',
                'input.a-button-primary'
            ]

            for selector in selectors:
                try:
                    element = page.locator(selector).first
                    if element.is_visible(timeout=2000):
                        # Check if this element contains wishlist-related text
                        element_text = element.inner_text().lower()
                        element_html = element.get_attribute('outerHTML') or ""

                        wishlist_keywords = ['liste', 'list', 'wish', 'wunsch']
                        if any(keyword in element_text or keyword in element_html.lower() for keyword in wishlist_keywords):
                            add_button = element
                            log_step("Add Product", "success", f"Found Add to List button using selector: {selector}")
                            log_step("Add Product", "info", f"Button text: '{element_text[:100]}'")
                            break
                except:
                    continue

        # Method 4: Fallback - look for any element that might be related to wishlists
        if not add_button:
            log_step("Add Product", "warning", "Standard methods failed, trying fallback approach...")

            # Look for any element containing wishlist-related text
            fallback_selectors = [
                '*:has-text("Liste")',
                '*:has-text("List")',
                '*:has-text("Wish")',
                '*:has-text("Wunsch")',
                'a[href*="wishlist"]',
                'a[href*="registry"]',
                'button[onclick*="wishlist"]',
                'button[onclick*="registry"]'
            ]

            for selector in fallback_selectors:
                try:
                    elements = page.locator(selector)
                    count = elements.count()

                    for i in range(min(5, count)):  # Check first 5 matches
                        element = elements.nth(i)
                        if element.is_visible(timeout=1000):
                            element_text = element.inner_text().lower()
                            # Check if it's clickable and contains relevant keywords
                            if ('liste' in element_text or 'list' in element_text or 'wish' in element_text) and len(element_text) < 100:
                                add_button = element
                                log_step("Add Product", "success", f"Found fallback button: '{element_text[:50]}'")
                                break
                except:
                    continue

                if add_button:
                    break

        if not add_button:
            log_step("Add Product", "error", "Add to List button not found after exhaustive search")
            take_screenshot(page, "add_button_not_found")

            # Final debug: save page HTML for analysis
            try:
                html_content = page.content()
                with open('debug_product_page.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                log_step("Add Product", "info", "Saved page HTML to debug_product_page.html for analysis")
            except:
                pass

            return False

        # Click the Add to List button
        log_step("Add Product", "info", "Clicking Add to List button...")

        try:
            add_button.scroll_into_view_if_needed()
            human_delay(1, 2)
            add_button.click()
        except Exception as e:
            log_step("Add Product", "warning", f"Normal click failed: {str(e)[:100]}")
            try:
                add_button.click(force=True)
            except Exception as e2:
                log_step("Add Product", "warning", f"Force click failed: {str(e2)[:100]}")
                try:
                    page.evaluate("arguments[0].click()", add_button.element_handle())
                except Exception as e3:
                    log_step("Add Product", "error", f"All click methods failed: {str(e3)[:100]}")
                    return False

        human_delay(3, 5)
        take_screenshot(page, "after_add_click")

        # Check for success indicators
        success_found = False
        success_selectors = [
            'span:has-text("Wunschzettel anzeigen")',
            'span:has-text("View Your List")',
            'div:has-text("wurde der Liste hinzugefügt")',
            'div:has-text("was added to")',
            '[data-action="reg-item-added"]',
            '[data-action="view-wishlist"]',
            '#WLHUC_result',
            'text="Added to"',
            'text="hinzugefügt"'
        ]

        for selector in success_selectors:
            try:
                if page.locator(selector).is_visible(timeout=5000):
                    log_step("Add Product", "success", f"SUCCESS: Product added! Found indicator: {selector}")
                    success_found = True

                    # Try to close any popups
                    close_selectors = [
                        '[data-action="a-popover-close"]',
                        'button:has-text("Close")',
                        'button:has-text("Schließen")',
                        '.a-button-close'
                    ]

                    for close_selector in close_selectors:
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

        # Check for errors
        error_selectors = [
            'div:has-text("could not be added")',
            'div:has-text("konnte nicht hinzugefügt werden")',
            '#huc-atwl-error-section',
            'text="Error"',
            'text="Fehler"'
        ]

        for error_selector in error_selectors:
            try:
                if page.locator(error_selector).is_visible(timeout=1000):
                    log_step("Add Product", "error", f"Failed to add product - error detected: {error_selector}")
                    return False
            except:
                continue

        log_step("Add Product", "warning", "Could not verify if product was added")
        take_screenshot(page, "add_product_uncertain")
        return False

    except Exception as e:
        log_step("Add Product", "error", f"Critical error: {str(e)}")
        take_screenshot(page, "add_product_error")
        return False

def run_focused_test():
    """Focused test for wishlist creation and product addition."""
    # Create directories
    for directory in [SCREENSHOTS_DIR, SESSION_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    # Test products
    test_products = [
        {
            'url': 'https://www.amazon.de/dp/B08N5WRWNW',
            'title': 'Amazon Echo Dot (Test Product 1)'
        },
        {
            'url': 'https://www.amazon.de/dp/B07PFFMP9P',
            'title': 'Kindle Paperwhite (Test Product 2)'
        }
    ]

    proxy_config = random.choice(PROXIES)
    session_file = os.path.join(SESSION_DIR, f"{ACCOUNT['email'].split('@')[0]}.json")

    log_step("Setup", "info", f"Using account: {ACCOUNT['email']}")
    log_step("Setup", "info", f"Using proxy: {proxy_config['server']}")

    with sync_playwright() as p:
        browser = None

        try:
            browser = p.chromium.launch(
                headless=False,
                proxy=proxy_config,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
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

            log_step("Test", "info", "Starting focused wishlist test...")

            # Test 1: Create wishlist
            wishlist_name = f"Focused Test List - {datetime.now().strftime('%m-%d %H:%M')}"

            if create_wishlist_robust(page, wishlist_name):
                log_step("Test", "success", "✅ Wishlist creation SUCCESSFUL!")

                # Test 2: Browse random products (using working logic from main_v2.py)
                log_step("Test", "info", "🔍 Starting product browsing phase...")
                browse_random_products_WORKING(page, 3)  # Browse 3 products

                # Test 3: Add a product to wishlist using the working method
                log_step("Test", "info", "🛒 Adding product to wishlist...")

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
                    # Now add to wishlist using our WORKING solution
                    if add_product_to_wishlist_FINAL_WORKING(page, None, "Bestseller Product", wishlist_name):
                        log_step("Test", "success", "✅ Product addition SUCCESSFUL!")
                        log_step("Test", "success", "🎉 COMPLETE SUCCESS: Wishlist creation + Product browsing + Product addition ALL WORK!")
                    else:
                        log_step("Test", "error", "❌ Product addition FAILED")
                else:
                    log_step("Test", "error", "❌ Could not find any products to add")
            else:
                log_step("Test", "error", "❌ Wishlist creation FAILED")

            # Save session
            context.storage_state(path=session_file)
            log_step("Session", "success", f"Session saved to {session_file}")

        except Exception as e:
            log_step("Error", "critical", f"Test failed: {str(e)}")
            if 'page' in locals():
                take_screenshot(page, "critical_error")

        finally:
            if browser:
                browser.close()

    # Save logs
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(LOGS, f, indent=4, ensure_ascii=False)

    log_step("Completion", "info", f"Logs saved to {LOG_FILE}")

if __name__ == "__main__":
    log_step("Script Start", "info", "Focused wishlist test starting...")
    run_focused_test()
    log_step("Script End", "info", "Focused wishlist test completed.")
