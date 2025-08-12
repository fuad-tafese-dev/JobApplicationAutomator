import random
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
import os
import datetime


class LinkedInAutomator:
    def __init__(self, username, password, question_db):
        self.driver = self._init_stealth_driver()  # Now this will work
        self.username = username
        self.password = password
        self._setup_logging()
        self.question_db = question_db
        self.wait = WebDriverWait(self.driver, 15)


    def _init_stealth_driver(self):
        """Initialize a stealthy Chrome driver to avoid detection"""
        options = webdriver.ChromeOptions()

        # Anti-detection settings
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # If you want headless mode (optional)
        # options.add_argument("--headless=new")

        driver = webdriver.Chrome(options=options)

        # Mask Selenium detection
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            """
        })
        return driver

    def _human_interaction(self, element, text=None):
        """Simulate human-like interaction with elements"""
        try:
            element.click()  # focus the input field
            time.sleep(random.uniform(0.2, 1.5))

            if text:
                for char in text:
                    element.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))  # shorter delay for realism
            return True
        except Exception as e:
            logging.error(f"Human interaction failed: {str(e)}")
            return False

    # ... (keep existing _init_stealth_driver and _human_interaction methods) ...

    def login(self):
        """Handle LinkedIn login and reliably uncheck 'Keep me logged in'"""
        try:
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(random.uniform(1, 2))  # Wait for page to load

            # Fill in credentials
            self._human_interaction(self.driver.find_element(By.ID, "username"), self.username)
            self._human_interaction(self.driver.find_element(By.ID, "password"), self.password)

            # 1. First try: Direct JavaScript approach (most reliable)
            try:
                self.driver.execute_script("""
                    document.getElementById('rememberMeOptIn-checkbox').click();
                """)
                logging.info("Used JavaScript to uncheck checkbox")
                time.sleep(0.5)
            except Exception as js_e:
                logging.warning(f"JavaScript click failed, trying alternative methods: {str(js_e)}")

                # 2. Second try: Click the label element
                try:
                    label = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "label[for='rememberMeOptIn-checkbox']")))
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", label)
                    time.sleep(0.3)
                    label.click()
                    logging.info("Clicked the label to uncheck checkbox")
                    time.sleep(0.5)
                except Exception as label_e:
                    logging.warning(f"Label click failed: {str(label_e)}")

                    # 3. Third try: Click the checkbox using Actions
                    try:
                        checkbox = self.wait.until(
                            EC.presence_of_element_located((By.ID, "rememberMeOptIn-checkbox")))
                        actions = ActionChains(self.driver)
                        actions.move_to_element(checkbox).click().perform()
                        logging.info("Used Actions to click checkbox")
                        time.sleep(0.5)
                    except Exception as action_e:
                        logging.warning(f"All checkbox uncheck methods failed: {str(action_e)}")

                        # Click submit button
                        submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                        self._human_interaction(submit_button)
                        time.sleep(3)

                        # Check for security challenge
                        if "security check" in self.driver.title.lower() or self.driver.find_elements(By.XPATH,
                                                                                                      "//*[contains(text(),'security check')]"):
                            logging.warning("Security check detected - manual intervention required")
                            self.take_screenshot("security_check")
                            return False  # This is crucial

            # Verify if checkbox is actually unchecked (for debugging)
            try:
                checkbox = self.driver.find_element(By.ID, "rememberMeOptIn-checkbox")
                if checkbox.is_selected():
                    logging.warning("Checkbox is still checked after all attempts!")
                    self.take_screenshot("checkbox_still_checked")
                else:
                    logging.info("Successfully unchecked the checkbox")
            except:
                pass

            self.take_screenshot("after_login")
            return True

        except Exception as e:
            logging.error(f"Login failed: {str(e)}")
            self.take_screenshot("login_failed")
            return False

    def search_jobs(self, keyword, location="Remote"):
        """Search for jobs with filters"""
        try:
            url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}&location={location}&f_AL=true"
            self.driver.get(url)
            time.sleep(3)
            return True
        except Exception as e:
            logging.error(f"Job search failed: {str(e)}")
            return False

    def _close_overlays(self):
        """Close any popup overlays that might be blocking interactions"""
        try:
            # Try to close signup prompts
            close_buttons = self.driver.find_elements(By.CSS_SELECTOR,
                                                      "button[aria-label='Dismiss'], " +
                                                      "button[data-test-modal-close-btn], " +
                                                      "button.artdeco-modal__dismiss")

            for btn in close_buttons:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        time.sleep(0.5)
                except:
                    pass

        except:
            pass

    def process_applications(self, max_jobs=2):
        """Process job applications with better handling of overlays"""
        try:
            # First wait for jobs to load
            jobs = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".job-card-container--clickable"))
            )[:max_jobs]

            for job in jobs:
                try:
                    # Scroll to the job card first
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", job)
                    time.sleep(random.uniform(0.5, 1.5))

                    # Check for and close any overlays that might be blocking
                    self._close_overlays()

                    # Try to click with JavaScript as a fallback
                    try:
                        job.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", job)

                    time.sleep(random.uniform(1, 2))

                    # Apply to the job
                    self._apply_to_job()

                    # Wait a bit before next job
                    time.sleep(random.uniform(2, 4))

                except Exception as e:
                    logging.warning(f"Failed to process job: {str(e)}")
                    continue

            return True

        except Exception as e:
            logging.error(f"Application processing failed: {str(e)}")
            return False


    def _fill_all_fields(self):
        """Fill all fields in Easy Apply forms: text, dropdown, checkbox (native + custom), skipping prefilled ones."""
        try:
            # --- TEXT / NUMBER / EMAIL ---
            inputs = self.driver.find_elements(By.CSS_SELECTOR,
                                               "input[type='text'], input[type='number'], input[type='email'], input[type='tel']")
            for field in inputs:
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", field)

                    # Skip if already filled
                    if field.get_attribute("value") and field.get_attribute("value").strip():
                        continue

                    label_text = (field.get_attribute("aria-label") or "").lower()
                    value = None
                    for key, ans in self.question_db.items():
                        if key.lower() in label_text:
                            value = ans
                            break

                    if value is None:
                        if "email" in label_text:
                            value = self.username  # Use the login email
                        elif "phone" in label_text or "mobile" in label_text:
                            value = "1234567890"  # Default phone number
                        elif "year" in label_text or "experience" in label_text:
                            value = "3"  # Default experience
                        else:
                            continue

                    field.clear()
                    field.send_keys(str(value))
                    time.sleep(0.2)
                except:
                    pass

            # --- CHECKBOXES ---
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            for cb in checkboxes:
                try:
                    label_text = (cb.get_attribute("aria-label") or "").lower()

                    value = None
                    for key, ans in self.question_db.items():
                        if key.lower() in label_text:
                            value = ans
                            break

                    if value is None:
                        value = True

                    # Only click if value is True, not selected, and not disabled
                    if bool(value) and not cb.is_selected() and cb.is_enabled():
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", cb)
                        cb.click()
                        time.sleep(0.1)
                except:
                    pass

            # --- RADIO BUTTONS (including the new style from select-3.png) ---
            radio_groups = self.driver.find_elements(By.CSS_SELECTOR, "fieldset, div[role='radiogroup']")
            for group in radio_groups:
                try:
                    # Find question label - different approaches for different styles
                    question_text = ""
                    try:
                        question_text_elem = group.find_element(By.TAG_NAME, "legend")
                        question_text = question_text_elem.text.strip().lower()
                    except:
                        try:
                            question_text_elem = group.find_element(By.XPATH, "./preceding-sibling::*[1]")
                            question_text = question_text_elem.text.strip().lower()
                        except:
                            pass

                    # Skip if already answered
                    selected_radio = group.find_elements(By.CSS_SELECTOR, "input[type='radio']:checked")
                    if selected_radio:
                        continue

                    # Match from DB
                    value = None
                    for key, ans in self.question_db.items():
                        if key.lower() in question_text:
                            value = ans
                            break

                    # Default if no match (for sponsorship questions)
                    if value is None and ("sponsorship" in question_text or "visa" in question_text):
                        value = "No"

                    if value is not None:
                        # Try to click matching radio button (both traditional and new LinkedIn style)
                        radios = group.find_elements(By.CSS_SELECTOR,
                                                     "input[type='radio'], label[data-test-text-selectable-option__label]")
                        for radio in radios:
                            try:
                                label = radio.get_attribute("aria-label") or radio.get_attribute(
                                    "value") or radio.text.strip()
                                if value.lower() in label.lower():
                                    self.driver.execute_script("arguments[0].scrollIntoView(true);", radio)
                                    radio.click()
                                    time.sleep(0.1)
                                    break
                            except:
                                pass
                except:
                    pass

            # --- NATIVE SELECTS ---
            native_selects = self.driver.find_elements(By.TAG_NAME, "select")
            for sel in native_selects:
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", sel)

                    # Skip if already selected (and not the placeholder)
                    selected_value = Select(sel).first_selected_option.text.strip()
                    if selected_value and selected_value.lower() not in ["select an option", "please make a selection"]:
                        continue

                    label_text = (sel.get_attribute("aria-label") or "").lower()
                    options = [o.text.strip() for o in sel.find_elements(By.TAG_NAME, "option") if o.text.strip()]

                    value = None
                    for key, ans in self.question_db.items():
                        if key.lower() in label_text:
                            value = ans
                            break

                    if value and value in options:
                        Select(sel).select_by_visible_text(value)
                    elif options:
                        # Skip the first option if it's a placeholder
                        if options[0].lower() in ["select an option", "please make a selection"] and len(options) > 1:
                            Select(sel).select_by_visible_text(options[1])
                        else:
                            Select(sel).select_by_visible_text(options[0])

                    time.sleep(0.2)
                except:
                    pass

            # --- CUSTOM LINKEDIN DROPDOWNS ---
            custom_dropdowns = self.driver.find_elements(By.CSS_SELECTOR,
                                                         "button.artdeco-dropdown__trigger, div[role='combobox']")
            for dropdown in custom_dropdowns:
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", dropdown)

                    # Skip if already has a value (not "Select an option")
                    current_value = dropdown.text.strip()
                    if current_value and current_value.lower() not in ["select an option",
                                                                       "please enter a valid answer"]:
                        continue

                    label_text = (dropdown.get_attribute("aria-label") or "").lower()
                    value = None
                    for key, ans in self.question_db.items():
                        if key.lower() in label_text:
                            value = ans
                            break

                    dropdown.click()
                    time.sleep(0.3)

                    # Handle different dropdown styles
                    try:
                        if value:
                            # Try to find exact match
                            option = self.driver.find_element(By.XPATH, f"//span[contains(text(), '{value}')]")
                        else:
                            # Default to first option
                            option = self.driver.find_element(By.XPATH,
                                                              "//div[@role='option'][1] | //li[@role='option'][1] | //div[contains(@class, 'basic-typeahead__option')][1]")
                        option.click()
                    except:
                        # If clicking didn't work, try sending keys
                        if value:
                            input_field = self.driver.find_element(By.CSS_SELECTOR,
                                                                   "input[type='text'], input[type='search']")
                            input_field.send_keys(value)
                            time.sleep(0.5)
                            first_option = self.driver.find_element(By.XPATH, "//div[@role='option'][1]")
                            first_option.click()

                    time.sleep(0.2)
                except:
                    pass

            # --- COUNTRY CODE SELECTORS (from select-2.png) ---
            try:
                phone_fields = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Phone country code')]")
                if phone_fields:
                    country_code_dropdown = self.driver.find_element(By.XPATH, "//select[contains(@id, 'country')]")
                    Select(country_code_dropdown).select_by_value("US")  # Default to US
                    time.sleep(0.2)
            except:
                pass

        except Exception as e:
            logging.error(f"Error filling fields: {str(e)}")

    def _apply_to_job(self):
        try:
            apply_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".jobs-apply-button"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(true);", apply_button)
            apply_button.click()
            time.sleep(1)

            while True:
                self._fill_all_fields()  # << Fill whatever fields are on this step

                # Click Next, Review, or Submit
                for btn_text in ["Next", "Review", "Submit application"]:
                    try:
                        btn = self.driver.find_element(By.XPATH, f"//button[contains(., '{btn_text}')]")
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                        btn.click()
                        time.sleep(1)
                        if btn_text == "Submit application":
                            logging.info("Application submitted successfully!")
                            raise StopIteration  # Break out of both loops
                        break
                    except:
                        continue
                else:
                    break  # No matching button found → exit

        except StopIteration:
            pass
        except NoSuchElementException:
            logging.warning("Easy Apply button not found - skipping job")
        except Exception as e:
            logging.error(f"Error applying to job: {str(e)}")

        # Always close modal after submission
        try:
            close_btn = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Dismiss']"))
            )
            close_btn.click()
            time.sleep(1)
        except:
            pass

    def take_screenshot(self, filename):
        """Capture screenshots for debugging with better error handling and organization"""
        try:
            # Create screenshots directory if it doesn't exist
            os.makedirs("screenshots", exist_ok=True)

            # Add timestamp to filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename}_{timestamp}.png"
            path = os.path.join("screenshots", filename)

            # Take full page screenshot (requires Chrome 80+)
            original_size = self.driver.get_window_size()
            required_width = self.driver.execute_script('return document.body.parentNode.scrollWidth')
            required_height = self.driver.execute_script('return document.body.parentNode.scrollHeight')
            self.driver.set_window_size(required_width, required_height)
            self.driver.save_screenshot(path)  # Save screenshot
            self.driver.set_window_size(original_size['width'], original_size['height'])

            logging.info(f"Screenshot saved: {path}")
            return path
        except Exception as e:
            logging.error(f"Failed to take screenshot: {str(e)}")
            return None


    def _setup_logging(self):
        """Configure logging to both console and file"""
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)

        # Set up log filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d")
        log_file = os.path.join("logs", f"linkedin_bot_{timestamp}.log")

        # Clear previous handlers if any
        logging.getLogger().handlers = []

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )