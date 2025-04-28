from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
import time
import re
import requests
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logging.basicConfig(
    filename="test.log",  # Log file location
    level=logging.INFO,              # Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
)


# Define paths and credentials
CHROMEDRIVER_PATH = r"C:\Users\SelengeTulga\Documents\chromedriver64\chromedriver.exe"
LOGIN_URL = os.getenv('APPFOLIO_LOGIN_URL')
WORK_ORDER_URL = os.getenv('WORK_ORDER_URL')
LEASING_FUNNEL_URL = os.getenv('LEASING_FUNNEL_URL')
TENANT_URL = os.getenv('TENANT_URL')
PURCHASE_ORDER_URL = os.getenv('PURCHASE_ORDER_URL')
PROSPECT_SOURCE_URL = os.getenv('PROSPECT_SOURCE_URL')
BILL_URL = os.getenv('BILL_URL')
USERNAME = os.getenv('APPFOLIO_USERNAME')
PASSWORD = os.getenv('APPFOLIO_PASSWORD')

BASE_DOWNLOAD_FOLDER = r"C:\Users\SelengeTulga\Documents\GitHub\infinity_bh_appfolio\data"

# Define separate folders for each CSV type
TENANT_FOLDER = os.path.join(BASE_DOWNLOAD_FOLDER, "tenant_data")
WORK_ORDER_FOLDER = os.path.join(BASE_DOWNLOAD_FOLDER, "work_orders")
LEASING_FUNNEL_FOLDER = os.path.join(BASE_DOWNLOAD_FOLDER, "leasing_funnel")
PROSPECT_SOURCE_FOLDER = os.path.join(BASE_DOWNLOAD_FOLDER, "prospect_source")

today = datetime.today()
ninety_days_ago = today - timedelta(days=90)
first_day_of_month = today.replace(day=1)
last_day_of_prev_month = first_day_of_month - timedelta(days=1)

one_year_ago = last_day_of_prev_month - timedelta(days=365)
one_year_ago_first_day = first_day_of_month - timedelta(days=365)

formatted_today = today.strftime("%m/%d/%Y")
formatted_ninety_days_ago = ninety_days_ago.strftime("%m/%d/%Y")
formatted_first_day_of_month = first_day_of_month.strftime("%m/%d/%Y")
formatted_last_day_prev_month = last_day_of_prev_month.strftime("%m/%d/%Y")
formatted_year_ago = one_year_ago.strftime("%m/%d/%Y")
formatted_one_year_ago_first_day = one_year_ago_first_day.strftime("%m/%d/%Y")


def get_trailing_month_end_dates(today):
    trailing_months = []
    for i in range(1, 13):  # 1 to 12 months ago
        first_day = (today.replace(day=1) - relativedelta(months=i))
        last_day = (first_day + relativedelta(months=1)) - relativedelta(days=1)
        trailing_months.append(last_day.strftime("%m-%d-%Y"))
    return trailing_months

# SimpleTexting API Key
API_TOKEN = os.getenv('SIMPLE_TEXTING_API_TOKEN')
API_URL = os.getenv('SIMPLE_TEXTING_API_URL')
ACCOUNT_PHONE = os.getenv('SIMPLE_TEXTING_ACCOUNT_PHONE')


def get_latest_message():
    """Fetch the latest message from SimpleTexting API with retry on 429 error."""
    params = {"page": 0, "size": 1, "accountPhone": ACCOUNT_PHONE}
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Accept": "application/json"}
    
    for attempt in range(3):  # Retry up to 3 times
        try:
            response = requests.get(API_URL, headers=headers, params=params)
            if response.status_code == 429:
                print("Too many requests. Waiting 10 seconds before retrying...")
                logging.info("Too many requests. Waiting 10 seconds before retrying...")
                time.sleep(10)  # Wait before retrying
                continue
            response.raise_for_status()

            messages = response.json().get("content", [])
            return messages[0] if messages else None

        except requests.RequestException as e:
            print(f"API Error: {e}")
            logging.info(f"API Error: {e}")

    print("Failed to retrieve messages after multiple attempts.")
    logging.info("Failed to retrieve messages after multiple attempts.")
    return None



def wait_for_new_code(previous_message_id):
    """Wait for a new verification code that is different from the previous one."""
    max_wait_time = 30  # Maximum time to wait (in seconds)
    wait_interval = 2  # Check every 2 seconds

    for _ in range(max_wait_time // wait_interval):
        latest_message = get_latest_message()
        if latest_message and latest_message["id"] != previous_message_id:
            match = re.search(r"\b\d{6}\b", latest_message["text"])  # Extract 6-digit code
            if match:
                return match.group(0)
        time.sleep(wait_interval)

    print(" Failed to retrieve a new verification code within the time limit.")
    logging.info(" Failed to retrieve a new verification code within the time limit.")
    return None

def click_update_button(driver):
    """Click the Columns tab, check the checkboxes, and click the Update button."""
    try:
        update_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Update']"))
        )
        update_button.click()
        print("Update button clicked successfully.")
        logging.info("Update button clicked successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
        logging.info(f"An error occurred: {e}")


def open_dropdown_and_click_csv(driver):
    """Open dropdown and click the Export CSV button, and verify if it was successful."""
    try:
        # Open the dropdown menu
        dropdown_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'dropdown-div') and contains(@class, 'js-actions-dropdown')]//button"))
        )
        dropdown_button.click()
        print("Dropdown menu opened successfully.")
        
        # Click the Export CSV button
        csv_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'js-export-csv-button')]"))
        )
        csv_button.click()
        print("Export CSV button clicked successfully.")
        logging.info("Export CSV button clicked successfully.")

        # Check if the CSV file download was triggered
        # You can use specific logic to verify download completion based on your environment
        
        print("CSV export process initiated.")
        logging.info("CSV export process initiated.")

    except Exception as e:
        print(f"An error occurred: {e}")
        logging.info(f"An error occurred: {e}")

def get_latest_csv(downloads_folder, max_wait_time=30):
    """Retrieve the latest downloaded CSV file after waiting for it."""
    print(" Waiting for CSV file to be downloaded...")
    logging.info(" Waiting for CSV file to be downloaded...")
    
    for _ in range(max_wait_time // 2):  # Check every 2 seconds, up to 30 seconds
        files = os.listdir(downloads_folder)
        csv_files = [f for f in files if f.endswith('.csv')]
        if csv_files:
            latest_file = max([os.path.join(downloads_folder, f) for f in csv_files], key=os.path.getctime)
            print(f" Latest downloaded file: {latest_file}")
            logging.info(f" Latest downloaded file: {latest_file}")
            return latest_file
        time.sleep(2)  # Wait before checking again
    
    raise FileNotFoundError(" No CSV files found in the downloads folder after waiting.")

def parse_property_name_with_string(value: str):
    text = str(value).strip()
    text = text.lstrip('->').strip()            # remove '->' and surrounding whitespace
    if ' - ' in text:
        # Split at the first " - " to separate name from address or other info
        return text.split(' - ', 1)[0].strip()
    else:
        return text
        
def parse_property_name(full_str: str) -> str:
    return full_str.split(' - ')[0].strip() if ' - ' in full_str else full_str.strip()

def is_summary_like(row):
    # Join row values into a string and check for summary patterns
    text = " ".join(str(x) for x in row if pd.notna(x)).lower()
    return (
        "units" in text or
        "occ" in text or
        "%" in text or
        len([x for x in row if pd.notna(x)]) <= 3
    )

def clean_csv(file_path,file_prefix, type):
     
    df = pd.read_csv(file_path)
    df = df.copy()
        # Add the new column for Property Name, initially empty
    df['Property Name'] = pd.NA

    if file_prefix == 'rentroll' or file_prefix == 'work_order' or file_prefix == 'purchase_order' or type == 2:
        first_col = df.columns[0]
        header_mask = df[first_col].astype(str).str.strip().str.startswith('->')

        header_indices = header_mask[header_mask].index
        # Check one row before each header to see if it’s a summary
        summary_indices = []

        for idx in header_indices:
            if idx > 0 and is_summary_like(df.iloc[idx - 1]):
                summary_indices.append(idx - 1)

        df.loc[header_mask, 'Property Name'] = df.loc[header_mask, first_col].apply(parse_property_name_with_string)
        df['Property Name'] = df['Property Name'].ffill()
         
        rows_to_drop = set(header_indices).union(summary_indices)
        df = df.drop(index=rows_to_drop).reset_index(drop=True)
        
        df = df.iloc[:-2]

    elif file_prefix == 'bill':
        first_col = df.columns[0]

        # Detect header rows that start with '->'
        header_mask = df[first_col].astype(str).str.strip().str.startswith('->')
        header_indices = header_mask[header_mask].index
        
        # Drop those header rows
        df = df.drop(index=header_indices).reset_index(drop=True)

        # Drop the last 2 rows (footer)
        df = df.iloc[:-2]

        df = df[df['Reference'].notna()].reset_index(drop=True)
        # Parse and fill 'Property Name' from header lines
        df['Property Name'] = df['Property'].apply(parse_property_name)

    elif file_prefix == 'tenant_data':
        df['Property Name'] = df['Property'].apply(parse_property_name)
        df = df.iloc[:-1]

    elif file_prefix == 'prospect':
        df = df.iloc[:-1]
    
    elif file_prefix == 'leasing':
        pass

    else:         
        print(file_prefix)
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f'C:\\Users\\SelengeTulga\\Documents\\GitHub\\infinity_bh_appfolio\\data\\{file_prefix}_cleaned_{timestamp}.csv'
    
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"CSV saved to: {output_path}")
    # logging.info(f"CSV saved to: {output_path}")

def download_csv(driver, page_url, type, file_prefix, target_date=None):
    """Navigate to a page, download CSV for a specific date, and move it to the correct folder."""
    logging.info(f"Navigating to {page_url} and downloading CSV...")
    driver.get(page_url)
    time.sleep(3)

    if target_date:
        date_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "filters_as_of_to"))
        )
        date_input.clear()
        date_input.send_keys(target_date)
        logging.info(f"Set date to {target_date}")
    
    if file_prefix == 'tenant_data':
        checkbox = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[name="filters[tenant_statuses][]"][value="all"]'))
        )
        checkbox.click()

    if file_prefix == 'work_order':
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-close"))
        )

        # Click the button to remove the selected property
        close_button.click()
        date_from_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "filters_status_date_range_from"))
        )
        date_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "filters_status_date_range_to"))
        )
        date_from_input.clear()
        date_input.clear()
        date_from_input.send_keys(formatted_ninety_days_ago) 
        date_input.send_keys(formatted_today) 


    if file_prefix == 'purchase_order':
       
        date_from_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "filters_created_date_from"))
        )
        date_from_input_to = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "filters_created_date_to"))
        )
        time.sleep(5)

        date_from_input.clear()
        date_from_input.send_keys(formatted_year_ago) 
        date_from_input_to.clear()
        date_from_input_to.send_keys(formatted_today) 

    if file_prefix == 'bill':
       
        date_from_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "filters_occurred_on_from"))
        )
        
        date_from_input_to = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "filters_occurred_on_to"))
        )
        time.sleep(5)

        date_from_input.clear()
        date_from_input.send_keys(formatted_one_year_ago_first_day) 
        date_from_input_to.clear()
        date_from_input_to.send_keys(formatted_today) 
        time.sleep(5)

    if file_prefix == 'leasing':
        date_from_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "filters_received_on_from"))
        )
        date_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "filters_received_on_to"))
        )
        date_from_input.clear()
        date_input.clear()
        date_from_input.send_keys(formatted_ninety_days_ago) 
        date_input.send_keys(formatted_today) 
    # Click update and download CSV
    click_update_button(driver)
    time.sleep(30)

    if file_prefix == 'tenant_data': 
        print('📄 Handling tenant_data columns...')

        # Wait for the search box
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Search...']"))
        )
        print('🔍 Search input found.')

        # Search for "Move-out"
        search_box.clear()
        search_box.send_keys("Move-out")
        print("🔎 Typed 'Move-out' in search box.")
        time.sleep(2)

        # Find the "Move-out" text (span)
        moveout_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[@data-ref='eLabel' and text()='Move-out']"))
        )
        print("✅ Move-out column appeared.")

        # Scroll into view and click the text directly
        driver.execute_script("arguments[0].scrollIntoView(true);", moveout_element)
        time.sleep(1)

        try:
            moveout_element.click()
            print("✅ Move-out clicked normally.")
        except Exception as e:
            print(f"⚡ Normal click failed: {e}")
            driver.execute_script("arguments[0].click();", moveout_element)
            print("✅ Move-out clicked using JavaScript fallback.")

    open_dropdown_and_click_csv(driver)
    time.sleep(30)
    
    # Retrieve latest CSV and move it to the correct folder
    latest_csv = get_latest_csv(BASE_DOWNLOAD_FOLDER)
    if latest_csv:
        print(f"[SUCCESS] CSV file ready: {latest_csv}")
        print(f"[SUCCESS] CSV URL: file://{os.path.abspath(latest_csv)}")
        logging.info(f"[SUCCESS] CSV file ready: {latest_csv}")
        logging.info(f"[SUCCESS] CSV URL: file://{os.path.abspath(latest_csv)}")
        clean_csv(latest_csv, file_prefix, type)

        if os.path.exists(latest_csv):
            os.remove(latest_csv)
            print(f"[INFO] Deleted original file: {latest_csv}")
            logging.info(f"Deleted original file: {latest_csv}")
        return True
    else:
        print("[ERROR] No CSV file was found or generated.")
        logging.info("[ERROR] No CSV file was found or generated.")
        return False

def union_rentrolls():
    today = datetime.today()
    rentroll_dfs = []

    for date_str in get_trailing_month_end_dates(today):
        prefix = f"rentroll_{date_str}_cleaned"
        
        # Find matching file (you could also use glob)
        matching_files = [f for f in os.listdir(BASE_DOWNLOAD_FOLDER) if f.startswith(prefix) and f.endswith(".csv")]

        if not matching_files:
            print(f"[SKIPPED] No file found for {prefix}")
            continue

        latest_file = max(matching_files)  # use most recent timestamped version if duplicates
        file_path = os.path.join(BASE_DOWNLOAD_FOLDER, latest_file)
        print(f"[INFO] Loading {file_path}")
        df = pd.read_csv(file_path)

        df['date_str'] = date_str
        rentroll_dfs.append(df)

    if rentroll_dfs:
        combined_df = pd.concat(rentroll_dfs, ignore_index=True)
        print(f"[SUCCESS] Combined {len(rentroll_dfs)} files, {len(combined_df)} rows total")
        return combined_df
    else:
        print("[WARNING] No rentroll files found for trailing 12 months.")
        return pd.DataFrame()

def get_data_from_appfolio():
    logging.info("Started Appfolio data process")
    """Check if ChromeDriver is set up correctly and perform login."""
    success = False  # Initialize success flag
    # Set up Chrome options
    options = Options()
    options.add_experimental_option("prefs", {"download.default_directory": BASE_DOWNLOAD_FOLDER})  # Set default download folder
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    # Open login page
    print("[INFO] Opening login page...")
    logging.info("[INFO] Opening login page...")
    driver.get(LOGIN_URL)

    try:
        # Wait for username field and enter credentials
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "user_email"))).send_keys(USERNAME)
        print("[INFO] Entered username")
        logging.info("[INFO] Entered username")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "user_password"))).send_keys(PASSWORD)
        print("[INFO] Entered password")
        logging.info("[INFO] Entered password")
        # Click login button
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "commit"))).click()
        print("[INFO] Clicked login button")
        logging.info("[INFO] Clicked login button")
        time.sleep(3)  # Wait for 2FA screen to load

        # Detect if 2FA is required
        if "verification_code" in driver.page_source:
            print("[INFO] 2-Step Verification detected. Retrieving verification code...")
            logging.info("[INFO] 2-Step Verification detected. Retrieving verification code...")
            # Get the latest message ID **before** requesting a new code
            previous_message = get_latest_message()
            previous_message_id = previous_message["id"] if previous_message else None

            # Click "Send Verification Code" button
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@value='Send Verification Code']"))
            ).click()
            print("[INFO] Requested verification code.")
            logging.info("[INFO] Requested verification code.")
            # Wait for a new code that is different from the previous one
            verification_code = wait_for_new_code(previous_message_id)

            if not verification_code:
                print(" No new verification code received.")
                logging.info("No new verification code received.")
                driver.quit()
                exit()

            # Enter verification code
            verification_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "user_verification_code"))
            )
            verification_input.click()
            time.sleep(1)
            verification_input.send_keys(verification_code)
            print(f"Entered verification code: {verification_code}")
            logging.info(f"Entered verification code: {verification_code}")
            
            # Click "Sign In" Button
            sign_in_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "sign_in_button"))
            )
            sign_in_button.click()
            print("Successfully submitted the verification code!")
            logging.info("Successfully submitted the verification code!")

        else:
            print("[SUCCESS] Login successful (No 2FA required).")
            logging.info("[SUCCESS] Login successful (No 2FA required).")
        
        time.sleep(3)  # Allow page to load

        # rentroll = download_csv(driver, LOGIN_URL, 1, 'rentroll', None)
        tenant = download_csv(driver, TENANT_URL, 1, 'tenant_data',None)
        # work_order = download_csv(driver, WORK_ORDER_URL, 1, 'work_order',None)
        # leasing = download_csv(driver, LEASING_FUNNEL_URL, 1, 'leasing',None) 
        # prospect = download_csv(driver, PROSPECT_SOURCE_URL,1, 'prospect',None)
        # bill = download_csv(driver, BILL_URL, 1,'bill',None)
        month_end_dates = get_trailing_month_end_dates(today)

        for date_str in month_end_dates:
            prefix = f"rentroll_{date_str.replace('/', '-')}_cleaned_"
            if any(fname.startswith(prefix) for fname in os.listdir(BASE_DOWNLOAD_FOLDER)):
                print(f"[SKIPPED] Found existing file for {date_str}")
                continue

            success = download_csv(driver, LOGIN_URL, 2,  f"rentroll_{date_str.replace('/', '-')}", target_date=date_str)
            if not success:
                logging.warning(f"Download failed for {date_str}")

        df_all_rentrolls = union_rentrolls()
        output_path = os.path.join(BASE_DOWNLOAD_FOLDER, f"rentroll_12_months_combined_{datetime.today().strftime('%Y%m%d')}.csv")
        df_all_rentrolls.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"[DONE] Saved combined file to: {output_path}")
        success = True  # Mark as successful
    except Exception as e:
        print(f" An error occurred: {e}")
        logging.info(f" An error occurred: {e}")

    finally:
        driver.quit()
        if success:
            logging.info("[SUCCESS] The entire process completed successfully.")
            print("[SUCCESS] The entire process completed successfully.")
        else:
            logging.info("[ERROR] The process encountered an error.")
            print("[ERROR] The process encountered an error.")
        time.sleep(3)


if __name__ == "__main__":
    # filepath = r"C:\Users\SelengeTulga\Documents\GitHub\infinity_bh_appfolio\rent_roll-20250418.csv"
    # clean_csv(filepath, 'rentroll')
    get_data_from_appfolio()

