import os
import time
import undetected_chromedriver as uc
import datetime
import base64
import cv2
import numpy as np
import pytesseract
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from selenium.webdriver.common.keys import Keys

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

load_dotenv()


def main():
    print("Launching Undetected Chromedriver...")
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--incognito")
    options.add_experimental_option(
        "prefs", {"profile.default_content_setting_values.popups": 1}
    )

    driver = uc.Chrome(options=options, version_main=148)
    wait = WebDriverWait(driver, 30)

    # --- TATKAL TIMING LOGIC ---
    is_tatkal = os.getenv("JOURNEY_QUOTA", "").upper() in ["TATKAL", "PREMIUM TATKAL"]
    target_booking_time = None

    if is_tatkal:
        print("TATKAL MODE DETECTED! Activating precision scheduling...")
        # All AC classes book at 10 AM, everything else at 11 AM
        ac_classes = ["1A", "2A", "3A", "3E", "CC", "EC", "EA", "VC"]
        target_hour = 10 if os.getenv("CLASS", "").upper() in ac_classes else 11

        now = datetime.datetime.now()
        target_booking_time = now.replace(
            hour=target_hour, minute=0, second=0, microsecond=0
        )

        # If it's already past the booking time today, assume we are testing for tomorrow
        if now > target_booking_time:
            target_booking_time += datetime.timedelta(days=1)

        print(
            f"Target Booking Time: {target_booking_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # # --- TEST OVERRIDE: Set target time to 2 minutes from right now ---
        # target_booking_time = datetime.datetime.now() + datetime.timedelta(minutes=2)

        # T - 90 Seconds Wait (Navigate to Site)
        nav_time = target_booking_time - datetime.timedelta(seconds=90)
        print(f"Waiting until {nav_time.strftime('%H:%M:%S')} to launch IRCTC...")
        while datetime.datetime.now() < nav_time:
            time.sleep(0.5)

    try:
        print("Opening IRCTC Website...")
        driver.get("https://www.irctc.co.in/nget/train-search")

        print("Checking for alert popups...")
        try:
            popup_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'OK')]")
                )
            )
            popup_btn.click()
            print("Popup closed.")
        except Exception:
            print("No popup found, continuing...")

        print("Clicking the Login button...")
        login_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'LOGIN')]"))
        )
        login_btn.click()

        print("Waiting for the login modal to appear...")
        username_field = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[contains(@placeholder, 'User Name')]")
            )
        )
        password_field = driver.find_element(
            By.XPATH, "//input[contains(@placeholder, 'Password')]"
        )

        print("Entering Credentials...")
        username_field.send_keys(os.getenv("IRCTC_USERNAME"))
        password_field.send_keys(os.getenv("IRCTC_PASSWORD"))

        print("Clicking the SIGN IN button...")
        signin_btn = driver.find_element(
            By.XPATH, "//button[contains(text(), 'SIGN IN')]"
        )
        signin_btn.click()

        print("Waiting for Login to complete...")
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[contains(text(), 'MY ACCOUNT')]")
            )
        )
        print("Login Successful! Bot is resuming control.")

        print("Checking for 'Last Transaction' popup...")
        try:
            # We wait up to 3 seconds for the dialog box to render
            close_btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[contains(text(), 'Close') or contains(text(), 'CLOSE')]",
                    )
                )
            )
            # Use Javascript click to perfectly bypass any invisible overlays
            driver.execute_script("arguments[0].click();", close_btn)
            print("Closed recent booking popup.")
        except Exception:
            print("No recent booking popup found.")

        print("\nSEARCHING TRAINS...")
        from_field = driver.find_element(
            By.XPATH, "//p-autocomplete[@id='origin']//input"
        )
        to_field = driver.find_element(
            By.XPATH, "//p-autocomplete[@id='destination']//input"
        )

        print(f"Entering Source Station: {os.getenv('SOURCE_STATION')}")
        from_field.click()
        for char in os.getenv("SOURCE_STATION"):
            from_field.send_keys(char)
            time.sleep(0.1)

        from_option = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//li[@role='option']"))
        )
        from_option.click()
        time.sleep(0.2)

        print(f"Entering Destination Station: {os.getenv('DESTINATION_STATION')}")
        to_field.click()
        for char in os.getenv("DESTINATION_STATION"):
            to_field.send_keys(char)
            time.sleep(0.1)

        to_option = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//li[@role='option']"))
        )
        to_option.click()
        time.sleep(0.2)

        print(f"Entering Date: {os.getenv('JOURNEY_DATE')}")
        date_field = driver.find_element(By.XPATH, "//p-calendar//input")
        date_field.click()
        for _ in range(15):
            date_field.send_keys(Keys.BACKSPACE)
        for char in os.getenv("JOURNEY_DATE"):
            date_field.send_keys(char)
            time.sleep(0.1)
        date_field.send_keys(Keys.ESCAPE)
        time.sleep(0.5)

        print(f"Selecting Quota: {os.getenv('JOURNEY_QUOTA')}")
        quota_dropdown = driver.find_element(
            By.XPATH, "//p-dropdown[@id='journeyQuota']"
        )
        quota_dropdown.click()
        quota_option = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    f"//li[@role='option']//span[contains(text(), '{os.getenv('JOURNEY_QUOTA')}')]",
                )
            )
        )
        quota_option.click()

        # T - 50 Seconds Wait (Search Phase)
        if is_tatkal and target_booking_time:
            search_time = target_booking_time - datetime.timedelta(seconds=50)
            print(
                f"TATKAL HOLD: Waiting until {search_time.strftime('%H:%M:%S')} to click Search..."
            )
            while datetime.datetime.now() < search_time:
                time.sleep(0.1)

        print("Clicking Search...")
        search_btn = driver.find_element(
            By.XPATH, "//button[contains(text(), 'Search')]"
        )
        driver.execute_script("arguments[0].click();", search_btn)

        print("Waiting for results page to load...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//app-train-list")))

        print("Search successful! Results loaded.")

        # --- PHASE 3B: TRAIN SELECTION & TATKAL EXECUTION ---
        date_obj = datetime.datetime.strptime(os.getenv("JOURNEY_DATE"), "%d/%m/%Y")
        short_date = date_obj.strftime("%d %b")
        print(f"\nLooking for Train: {os.getenv('TRAIN_NUMBER')}")
        train_card_xpath = f"//div[contains(@class, 'form-group') and contains(., '{os.getenv('TRAIN_NUMBER')}')]"
        train_card = wait.until(
            EC.presence_of_element_located((By.XPATH, train_card_xpath))
        )
        # T - 0 Seconds Wait (Booking Phase)
        if is_tatkal and target_booking_time:
            print(
                f"TATKAL HOLD: Waiting for exactly {target_booking_time.strftime('%H:%M:%S')} to strike..."
            )
            while datetime.datetime.now() < target_booking_time:
                time.sleep(0.01)  # Ultra precision check!

        print(f"Clicking on Class: {os.getenv('CLASS')}...")
        class_tab = train_card.find_element(
            By.XPATH, f".//strong[contains(text(), '{os.getenv('CLASS')}')]"
        )

        # Aggressive Retry Loop for Tatkal Class Selection
        booking_success = False
        while not booking_success:
            try:
                class_tab.click()
                print("Checking for availability data...")

                # FORCE ACTIVATE THE AVAILABILITY PANEL
                try:
                    # We look for the first availability panel (it usually contains a strong tag with the date/status)
                    first_avl_panel = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located(
                            (
                                By.XPATH,
                                "//div[contains(@class, 'pre-avl') or contains(@class, 'wl')]",
                            )
                        )
                    )
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});",
                        first_avl_panel,
                    )
                    time.sleep(0.2)
                    # Use JS click to bypass overlapping UI
                    driver.execute_script("arguments[0].click();", first_avl_panel)
                    print(
                        "Successfully clicked the availability panel to activate Book Now!"
                    )
                except Exception:
                    print(
                        "No clickable availability panel found, assuming Book Now is already active."
                    )

                # We use a short 1.5s wait so it retries instantly if data doesn't load!
                availability_box = WebDriverWait(driver, 1.5).until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            f"{train_card_xpath}//td[contains(., '{short_date}')]",
                        )
                    )
                )
                availability_box.click()

                print("Clicking Book Now...")
                book_now_btn = train_card.find_element(
                    By.XPATH, ".//button[contains(text(), 'Book Now')]"
                )
                book_now_btn.click()

                booking_success = True  # Broke through the server lag!

            except Exception:
                print(
                    "Server lagged or threw a popup. Dismissing popups and retrying in 1.5s..."
                )
                try:
                    # Clear any "Please try later" popups blocking the screen
                    error_ok = driver.find_element(
                        By.XPATH,
                        "//button[contains(text(), 'OK') or contains(text(), 'OKAY')]",
                    )
                    driver.execute_script("arguments[0].click();", error_ok)
                except Exception:
                    pass
                time.sleep(1.5)
        print("Checking for confirmation popups...")
        try:
            i_agree_btn = WebDriverWait(driver, 0.5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//span[contains(text(), 'I Agree')]")
                )
            )
            i_agree_btn.click()
            print("Accepted 'I Agree' popup.")
        except Exception:
            pass
        try:
            yes_btn = WebDriverWait(driver, 0.5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Yes')]")
                )
            )
            yes_btn.click()
            print("Accepted 'Yes' confirmation popup.")
        except Exception:
            pass
        print("Booking initiated! Waiting for Passenger Details page...")
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//span[contains(text(), 'Passenger Details')]")
            )
        )

        # --- PHASE 4: PASSENGER DETAILS ---
        print("\n--- PHASE 4: PASSENGER DETAILS ---")
        passengers_str = os.getenv("PASSENGERS", "")
        passengers = [
            p.strip().split("|") for p in passengers_str.split(",") if p.strip()
        ]

        for index, p_data in enumerate(passengers):
            name, age, gender, berth = p_data
            print(
                f"Entering Passenger {index+1}: {name}, Age: {age}, Gender: {gender}, Berth: {berth}"
            )
            if index > 0:
                print("Clicking '+ Add Passenger'...")
                add_btn = driver.find_element(
                    By.XPATH, "//span[contains(text(), '+ Add Passenger')]"
                )
                # Safely center the Add button on the screen
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", add_btn
                )
                time.sleep(0.5)
                add_btn.click()
                time.sleep(0.5)
            # Name Field
            name_fields = driver.find_elements(
                By.XPATH, "//p-autocomplete[@formcontrolname='passengerName']//input"
            )

            # Safely scroll the name box to the CENTER of the screen to avoid the fixed top header!
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", name_fields[index]
            )
            time.sleep(0.5)

            name_fields[index].click()
            for char in name:
                name_fields[index].send_keys(char)
                time.sleep(0.1)
            name_fields[index].send_keys(Keys.ESCAPE)
            # Age Field
            age_fields = driver.find_elements(
                By.XPATH, "//input[@formcontrolname='passengerAge']"
            )
            age_fields[index].click()
            for char in age:
                age_fields[index].send_keys(char)
                time.sleep(0.1)
            # Gender and Berth Dropdowns
            gender_dropdowns = driver.find_elements(
                By.XPATH, "//select[@formcontrolname='passengerGender']"
            )
            Select(gender_dropdowns[index]).select_by_value(gender)
            if berth.upper() != "NO PREFERENCE":
                berth_dropdowns = driver.find_elements(
                    By.XPATH, "//select[@formcontrolname='passengerBerthChoice']"
                )
                Select(berth_dropdowns[index]).select_by_visible_text(berth)

        print("Selecting Reservation Choice (Same Coach)...")
        try:
            # 1. Click the PrimeNG dropdown to open it
            res_dropdown = driver.find_element(
                By.XPATH,
                "//*[contains(text(), 'Reservation Choice')]/following-sibling::p-dropdown",
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", res_dropdown
            )
            res_dropdown.click()
            time.sleep(0.5)  # Wait for the dropdown menu to animate open

            # 2. Click the 'Same coach' option from the list
            same_coach_opt = driver.find_element(
                By.XPATH, "//li//span[contains(text(), 'allotted in same coach')]"
            )
            same_coach_opt.click()
            print("Successfully locked in Same Coach preference!")
        except Exception as e:
            print(f"Failed to select Reservation Choice: {e}")

        print("Selecting Payment Category...")
        try:
            payment_method = os.getenv("PAYMENT_METHOD", "UPI").upper()

            # Grab every single radio button box on the entire webpage
            all_radio_boxes = driver.find_elements(
                By.XPATH, "//div[contains(@class, 'ui-radiobutton-box')]"
            )

            if payment_method == "E-WALLET":
                # E-Wallet is always the second-to-last radio button on the page
                radio_box = all_radio_boxes[-2]
            else:
                # BHIM/UPI is always the absolute LAST radio button on the page!
                radio_box = all_radio_boxes[-1]

            # Safely scroll it to the center
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", radio_box
            )
            time.sleep(0.5)

            # Physically click it!
            radio_box.click()

            print(f"Successfully selected {payment_method} category!")

        except Exception as e:
            print(f"Failed to select payment category: {e}")

        print("Clicking Continue...")
        continue_btn = driver.find_element(
            By.XPATH, "//button[contains(text(), 'Continue')]"
        )
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", continue_btn
        )

        continue_success = False
        while not continue_success:
            try:
                # We use a physical click!
                # If the loading spinner is on screen, this click is blocked by the spinner, safely preventing double-submissions!
                continue_btn.click()
            except Exception:
                # The click was intercepted by the loading spinner. It is currently processing!
                pass

            try:
                # Check if the Review Page has loaded
                WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//input[@formcontrolname='captcha']")
                    )
                )
                continue_success = True
                print("WE BEAT AKAMAI! Review Page loaded successfully!")
            except Exception:
                # If it hasn't loaded, check for error popups
                try:
                    error_ok = driver.find_element(
                        By.XPATH,
                        "//button[contains(text(), 'OK') or contains(text(), 'OKAY')]",
                    )
                    driver.execute_script("arguments[0].click();", error_ok)
                    print("Dismissed popup! Retrying Continue...")
                except Exception:
                    pass
                time.sleep(1.5)

        print("\n*** THE ULTIMATE TEST ***")
        print("Waiting for Review Page to load...")

        # If the bot detects the captcha input, it successfully bypassed the error page!
        long_wait = WebDriverWait(driver, 120)

        # If the bot detects the captcha input, it successfully bypassed the error page!
        long_wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@formcontrolname='captcha']")
            )
        )
        print("WE BEAT AKAMAI! Review Page loaded successfully!")

        # --- PHASE 5: REVIEW & PAYMENT (AUTOMATED OCR) ---
        print("\n--- PHASE 5: REVIEW CAPTCHA SOLVER ---")

        # We loop endlessly until we successfully reach the Payment Page!
        payment_page_loaded = False
        while not payment_page_loaded:
            try:
                # 1. Focus the captcha input box
                captcha_input = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//input[@formcontrolname='captcha']")
                    )
                )
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", captcha_input
                )

                # Clear any text from previous failed attempts
                captcha_input.clear()
                time.sleep(0.5)

                # 2. Grab the captcha image from the screen
                print("Capturing Captcha image...")
                captcha_img = driver.find_element(
                    By.XPATH,
                    "//img[contains(@class, 'captcha-img') or contains(@src, 'captcha')]",
                )
                captcha_img.screenshot("solve_captcha.png")

                # 3. OpenCV Pipeline (Noise Removal)
                img = cv2.imread("solve_captcha.png")
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY_INV)
                kernel = np.ones((2, 2), np.uint8)
                processed = cv2.erode(thresh, kernel, iterations=1)
                processed = cv2.dilate(processed, kernel, iterations=1)

                # 4. Tesseract Engine (Text Extraction)
                text = pytesseract.image_to_string(processed, config="--psm 7").strip()
                # Strip out any spaces or special characters Tesseract might hallucinate
                text = "".join(e for e in text if e.isalnum() or e in ["=", "-", "+"])

                print(f"🤖 OCR Guessed: '{text}'")

                # 5. Type it into the website
                for char in text:
                    captcha_input.send_keys(char)
                    time.sleep(0.05)  # Type it slightly naturally to appease Angular

                time.sleep(0.5)

                # 6. Click Continue
                print("Clicking Continue...")
                continue_btn = driver.find_element(
                    By.XPATH, "//button[contains(text(), 'Continue')]"
                )
                # We use Javascript click because it's a one-off navigation
                driver.execute_script("arguments[0].click();", continue_btn)

                # 7. Check if we broke through to the Payment Page!
                try:
                    # Wait 3 seconds to see if the "Pay & Book" button appears on the next page
                    pay_book_btn = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//button[contains(text(), 'Pay & Book')]")
                        )
                    )
                    payment_page_loaded = True
                    print("✅ Captcha Solved Successfully! Payment Page loaded!")
                except Exception:
                    # If "Pay & Book" didn't appear, the Captcha was wrong (or the server lagged).
                    print(
                        "❌ OCR Failed or Page Loading. Refreshing captcha and retrying..."
                    )
                    try:
                        # Click the little refresh circle icon to force a new captcha image
                        refresh_btn = driver.find_element(
                            By.XPATH,
                            "//*[contains(@class, 'fa-refresh') or contains(@class, 'refresh')]",
                        )
                        driver.execute_script("arguments[0].click();", refresh_btn)
                        time.sleep(1.5)  # Wait for the new image to render
                    except Exception:
                        pass

            except Exception as e:
                # Failsafe: if the loop crashes, it might mean the page transitioned while we were looking for the image!
                try:
                    pay_book_btn = driver.find_element(
                        By.XPATH, "//button[contains(text(), 'Pay & Book')]"
                    )
                    payment_page_loaded = True
                except Exception:
                    print("Error during OCR loop, retrying in 1 second...")
                    time.sleep(1)
        print("\nPayment Page detected! Bot is resuming control...")
        time.sleep(2)

        payment_method = os.getenv("PAYMENT_METHOD", "UPI").upper()

        if payment_method == "E-WALLET":
            print("Selecting 'E-Wallet' tab...")
            ewallet_tab = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(text(), 'Instant Payment')]")
                )
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", ewallet_tab
            )
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", ewallet_tab)
            time.sleep(2)
        else:
            print("Selecting 'BHIM/UPI' tab...")
            # We split the search into 'BHIM' and 'UPI' so spaces or slashes don't break it!
            upi_tab = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//*[contains(text(), 'BHIM') and contains(text(), 'UPI')]",
                    )
                )
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", upi_tab
            )
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", upi_tab)
            time.sleep(1.5)

            print("Selecting 'PAYTM UPI'...")
            # We look for the word Paytm in either the text or the Image ALT tag, completely case-insensitive
            paytm_upi = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'paytm') or contains(translate(@alt, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'paytm')]",
                    )
                )
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", paytm_upi
            )
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", paytm_upi)
            time.sleep(1)

        print("Clicking 'Pay & Book'...")
        # We re-fetch the button just in case the DOM refreshed when we clicked the left sidebar
        final_pay_btn = driver.find_element(
            By.XPATH, "//button[contains(text(), 'Pay & Book')]"
        )
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", final_pay_btn
        )
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", final_pay_btn)

        # 1. Check if it's a browser-level popup alert
        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.accept()
            print("Accepted browser alert confirmation.")
        except Exception:
            pass

        # 2. Wait for the new CONFIRM page to load (up to 30 seconds)
        try:
            # We look for both 'Confirm' and 'CONFIRM' to beat the case-sensitivity!
            confirm_btn = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[contains(text(), 'Confirm') or contains(text(), 'CONFIRM')]",
                    )
                )
            )
            # Scroll it into view just in case it's off-screen
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", confirm_btn
            )
            time.sleep(1)
            driver.execute_script("arguments[0].click();", confirm_btn)
            print("Successfully clicked the final CONFIRM button.")
        except Exception:
            print("Failed to find the final CONFIRM button.")

        print("\nWaiting for success page... (This can take up to 5 minutes)")
        # 5-minute wait for IRCTC's slow ticketing queue
        success_wait = WebDriverWait(driver, 300)

        # 1. Click Skip on the Review Dialog (if it appears)
        try:
            skip_btn = success_wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Skip')]")
                )
            )
            print("Success page loaded! Clicking Skip on review popup...")
            driver.execute_script("arguments[0].click();", skip_btn)
            time.sleep(2)
        except Exception:
            print("No Skip button found or success page took too long.")

        # Save the main window ID so we can come back to it
        main_window = driver.current_window_handle

        # 2. Click Print Ticket on the success page
        print("Clicking 'Print Ticket'...")
        try:
            # Look for the actual Print Ticket button
            print_btn = driver.find_element(
                By.XPATH,
                "//*[contains(text(), 'Print Ticket') or contains(text(), 'Print E-Ticket')]",
            )
            driver.execute_script("arguments[0].click();", print_btn)

            # Wait for the popup window to open and switch to it
            print("Waiting for ticket popup window...")
            WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
            window_2 = [h for h in driver.window_handles if h != main_window][0]
            driver.switch_to.window(window_2)

            time.sleep(4)  # Let the ticket fully render its HTML

            print("Generating beautifully formatted PDF via Chrome DevTools...")
            import base64

            pdf = driver.execute_cdp_cmd(
                "Page.printToPDF",
                {
                    "landscape": False,
                    "displayHeaderFooter": False,
                    "printBackground": True,
                    "preferCSSPageSize": True,
                    "paperWidth": 8.27,
                    "paperHeight": 11.69,
                    "marginTop": 0.3,
                    "marginBottom": 0.3,
                    "marginLeft": 0.3,
                    "marginRight": 0.3,
                    "scale": 0.8,
                },
            )

            # Format the filename
            date_obj = datetime.datetime.strptime(os.getenv("JOURNEY_DATE"), "%d/%m/%Y")
            file_name = date_obj.strftime("%d %B") + " - Ticket.pdf"

            print(f"Saving file directly to hard drive as '{file_name}'...")
            with open(file_name, "wb") as f:
                f.write(base64.b64decode(pdf["data"]))

            print("File saved perfectly!")
            time.sleep(2)

            # Close popup and switch back
            driver.close()
            driver.switch_to.window(main_window)

        except Exception as e:
            print(f"Failed to download PDF: {e}")

        time.sleep(1)

        # 3. Log Out
        print("Logging out...")
        try:
            my_account = driver.find_element(
                By.XPATH, "//a[contains(text(), 'MY ACCOUNT')]"
            )
            driver.execute_script("arguments[0].click();", my_account)
            time.sleep(1)

            logout_btn = driver.find_element(
                By.XPATH,
                "//a[contains(text(), 'Logout') or contains(text(), 'Log Out')]",
            )
            driver.execute_script("arguments[0].click();", logout_btn)
            print("Logged out successfully!")
        except Exception:
            print("Failed to logout.")

        print("\n🎉 MISSION ACCOMPLISHED! ALL TASKS COMPLETED! 🎉")
        time.sleep(10)

    finally:
        print("Closing browser...")
        driver.quit()


if __name__ == "__main__":
    main()
