from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import os
import shutil
import time
import glob
import requests
import json
import sys
from typing import Any, Iterable
import re
import subprocess
import argparse

# --- Helpers for robust date extraction ---
def _first_item(value: Any) -> Any:
    """Return the first item if value is a list, else the value itself."""
    if isinstance(value, list):
        return value[0] if value else None
    return value

def _to_epoch_ms(value: Any) -> int:
    """Try to normalize various representations (str/int/float/list) to epoch ms; 0 if unknown."""
    v = _first_item(value)
    if v is None:
        return 0
    # Strings: digits only
    if isinstance(v, str):
        vs = v.strip()
        if vs.isdigit():
            try:
                v = int(vs)
            except Exception:
                return 0
        else:
            return 0  # non-numeric strings are not epoch values
    # Numbers
    if isinstance(v, (int, float)):
        vi = int(v)
        # Heuristic: if it's in seconds, convert to ms
        if vi < 10_000_000_000:  # < ~Sat Nov 20 2286 in seconds
            # could be seconds
            if vi > 0 and vi < 10_000_000_000:  # seconds
                return vi * 1000
        return vi  # assume already ms
    return 0

def _format_epoch_ms(epoch_ms: int) -> str:
    try:
        return time.strftime('%d-%m-%Y %I:%M %p', time.gmtime(epoch_ms / 1000)) if epoch_ms else ''
    except Exception:
        return ''

def extract_date_string(doc: dict, preferred_numeric_keys: Iterable[str], preferred_string_keys: Iterable[str]) -> str:
    """
    Best-effort extraction of a human-readable date string.
    1) Try preferred numeric keys as epoch (ms or s), format to string.
    2) If none, try preferred string keys and return first non-empty string.
    3) As a last resort, scan all keys for something containing 'date' and 'start'/'end'.
    """
    # 1) numeric-first
    for k in preferred_numeric_keys:
        if k in doc:
            ms = _to_epoch_ms(doc.get(k))
            if ms:
                s = _format_epoch_ms(ms)
                if s:
                    return s
    # 2) preferred string keys
    for k in preferred_string_keys:
        if k in doc:
            v = _first_item(doc.get(k))
            if isinstance(v, str) and v.strip():
                return v.strip()
    # 3) heuristic scan
    try:
        for k, v in doc.items():
            lk = k.lower()
            if 'date' in lk and (('start' in lk) or ('end' in lk) or ('bid' in lk)):
                ms = _to_epoch_ms(v)
                if ms:
                    s = _format_epoch_ms(ms)
                    if s:
                        return s
                vv = _first_item(v)
                if isinstance(vv, str) and vv.strip():
                    return vv.strip()
    except Exception:
        pass
    return ''

# --- Helpers for safe CSV filenames ---
INVALID_WIN_CHARS = r'[\\/:*?"<>|]'

def sanitize_for_filename(text: str | None) -> str:
    if not text:
        return 'ALL'
    s = text.strip()
    s = re.sub(INVALID_WIN_CHARS, '_', s)
    s = re.sub(r'\s+', '_', s)
    s = s.strip('_') or 'ALL'
    return s

def build_csv_filename(state: str | None, city: str | None, label: str | None = None) -> str:
    ts = time.strftime('%Y%m%d_%H%M%S', time.localtime())
    if label:
        base = sanitize_for_filename(label)
        return f"{base}_{ts}.csv"

    parts = ['bids']
    state_part = sanitize_for_filename(state)
    city_part = sanitize_for_filename(city) if city else ''
    # Include state if provided (not ALL), include city if provided
    if state and state_part != 'ALL':
        parts.append(state_part)
    if city and city_part:
        parts.append(city_part)
    if len(parts) == 1:  # nothing added
        parts.append('ALL')
    parts.append(ts)
    return '_'.join(parts) + '.csv'


DATE_DEBUG_PRINTED = False


def build_ra_destination(state: str | None, city: str | None) -> str:
    state_part = sanitize_for_filename(state) if state else 'ALL'
    city_part = sanitize_for_filename(city) if city else 'ALL'
    dest = os.path.join(os.getcwd(), "RAs", state_part, city_part)
    os.makedirs(dest, exist_ok=True)
    return dest


def click_view_all_button(driver) -> bool:
    """Attempt to click the 'View All RAs/Bids' button; return True on success."""
    selectors = [
        (By.LINK_TEXT, "View All RAs/Bids"),
        (By.LINK_TEXT, "View All RA/Bids"),
        (By.PARTIAL_LINK_TEXT, "View All RA"),
        (By.XPATH, "//a[contains(., 'View All RA')]")
    ]
    for by, value in selectors:
        try:
            element = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((by, value)))
            try:
                driver.execute_script("arguments[0].click();", element)
            except Exception:
                element.click()
            time.sleep(2)
            return True
        except Exception:
            continue
    return False


def transform_doc(doc: dict) -> dict:
    """Normalize a single search result document into the expected record structure."""
    global DATE_DEBUG_PRINTED

    bid_no = _first_item(doc.get('b_bid_number'))
    bid_no = str(bid_no or '')

    category = _first_item(doc.get('b_category_name'))
    items = str(category or '')

    quantity = _first_item(doc.get('b_total_quantity'))
    quantity = str(quantity or '')

    min_name = _first_item(doc.get('ba_official_details_minName'))
    min_name = str(min_name or '')

    dept_name = _first_item(doc.get('ba_official_details_deptName'))
    dept_name = str(dept_name or '')

    dept_addr = (min_name + ' ' + dept_name).strip()

    start_date = extract_date_string(
        doc,
        preferred_numeric_keys=[
            'final_start_date_sort',
            'final_bid_start_date_sort',
            'b_bid_start_date_js',
            'b_start_date_js'
        ],
        preferred_string_keys=[
            'b_bid_start_date',
            'start_date',
            'b_start_date'
        ]
    )

    end_date = extract_date_string(
        doc,
        preferred_numeric_keys=[
            'final_end_date_sort',
            'final_bid_end_date_sort',
            'b_bid_end_date_js',
            'b_end_date_js'
        ],
        preferred_string_keys=[
            'b_bid_end_date',
            'end_date',
            'b_end_date'
        ]
    )

    if (not start_date or not end_date) and not DATE_DEBUG_PRINTED:
        try:
            print("[DEBUG] Date fields missing. Available keys in first problematic doc:")
            print(sorted(list(doc.keys())))
        finally:
            DATE_DEBUG_PRINTED = True

    bid_type = _first_item(doc.get('b_bid_type'))
    eval_type = _first_item(doc.get('b_eval_type'))
    ra_available = 'Yes' if str(bid_type) == '2' and str(eval_type) != '0' else 'No'

    b_id_value = _first_item(doc.get('b_id'))

    return {
        'Bid No': bid_no,
        'Items': items,
        'Quantity': quantity,
        'Department Name And Address': dept_addr,
        'Start Date': start_date,
        'End Date': end_date,
        'RA available': ra_available,
        'Bid Doc': 'No',
        'b_id': b_id_value
    }


def fetch_bids(session: requests.Session, csrf_token: str, user_agent: str, payload: dict, data_store: list) -> int:
    """Fetch bid pages via API, populating data_store. Returns total records fetched."""
    payload_local = payload.copy()
    page = 1
    total = 0
    try:
        while True:
            payload_local['page'] = page
            response = session.post(
                'https://bidplus.gem.gov.in/search-bids',
                data={'payload': json.dumps(payload_local), 'csrf_bd_gem_nk': csrf_token},
                headers={'User-Agent': user_agent}
            )
            if response.status_code != 200:
                print(f"Stopping at page {page}: HTTP {response.status_code}")
                break
            try:
                json_data = response.json()
            except Exception as exc:
                print(f"Failed to decode JSON on page {page}: {exc}")
                break

            response_section = json_data.get('response', {}).get('response', {})
            docs = response_section.get('docs', [])
            num_found = response_section.get('numFound')
            if not docs:
                break

            for doc in docs:
                record = transform_doc(doc)
                data_store.append(record)
                total += 1

            print(f"Page {page}: {len(docs)} docs, added {len(docs)} new records")
            page += 1
            if isinstance(num_found, int) and num_found > 0 and total >= num_found:
                print(f"Reached reported total ({num_found}) records.")
                break
    except KeyboardInterrupt:
        raise

    return total


def download_bid_documents(session: requests.Session, user_agent: str, records: list[dict], dest_folder: str) -> None:
    """Download bid documents linked via showbidDocument for each record."""
    for record in records:
        b_id = record.get('b_id')
        bid_no = record.get('Bid No') or ''
        if not b_id or not bid_no:
            continue

        safe_bid_no = sanitize_for_filename(bid_no)
        dest_path = os.path.join(dest_folder, f"{safe_bid_no}.pdf")
        if os.path.exists(dest_path):
            record['Bid Doc'] = 'Yes'
            continue

        url = f"https://bidplus.gem.gov.in/showbidDocument/{b_id}"
        try:
            response = session.get(
                url,
                headers={
                    'User-Agent': user_agent,
                    'Referer': 'https://bidplus.gem.gov.in/advance-search'
                },
                stream=False,
                timeout=60
            )
            if response.status_code == 200:
                content = response.content or b''
                header = response.headers.get('Content-Type', '').lower()
                is_pdf_header = 'pdf' in header or 'octet-stream' in header or 'application/download' in header
                is_pdf_body = content.lstrip().startswith(b'%PDF') if content else False

                if content and (is_pdf_header or is_pdf_body):
                    with open(dest_path, 'wb') as fh:
                        fh.write(content)
                    record['Bid Doc'] = 'Yes'
                    print(f"Saved bid PDF for {bid_no}")
                else:
                    record['Bid Doc'] = 'No'
                    print(f"Bid PDF unavailable or not a PDF for {bid_no} (Content-Type: {response.headers.get('Content-Type')})")
            else:
                record['Bid Doc'] = 'No'
                print(f"Failed to download bid PDF for {bid_no}: HTTP {response.status_code}")
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            print(f"Error downloading bid PDF for {bid_no}: {exc}")
            record['Bid Doc'] = 'No'


def download_ra_documents(driver, ra_records: list) -> None:
    """Trigger download of RA documents for the provided records."""
    for record in ra_records:
        b_id = record.get('b_id')
        if not b_id:
            continue
        ra_url = f"https://bidplus.gem.gov.in/list-ra-schedules/{b_id}"
        try:
            driver.get(ra_url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            links = driver.find_elements(By.PARTIAL_LINK_TEXT, "RA document")
            if not links:
                print(f"No RA document links found for {record['Bid No']}")
            for link in links:
                try:
                    driver.execute_script("arguments[0].click();", link)
                except Exception:
                    link.click()
                time.sleep(1)
            print(f"Requested RA download for {record['Bid No']}")
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            print(f"Error downloading RA for {record['Bid No']}: {exc}")


def move_ra_pdfs(download_dir: str, ra_folder: str, ra_records: list, existing_before: set[str]) -> None:
    """Move newly downloaded RA PDFs into the RAs folder with sanitized names."""
    if not ra_records:
        return

    time.sleep(10)
    current_files = sorted(glob.glob(os.path.join(download_dir, "*.pdf")), key=os.path.getmtime)
    new_files = [f for f in current_files if f not in existing_before]

    if not new_files:
        print("No new RA documents detected after download attempts.")
        return

    move_count = min(len(new_files), len(ra_records))
    for idx in range(move_count):
        record = ra_records[idx]
        file_path = new_files[idx]
        bid_no = record.get('Bid No', 'UNKNOWN')
        safe_bid_no = sanitize_for_filename(bid_no)
        tentative = os.path.join(ra_folder, f"{safe_bid_no}_RA.pdf")
        if os.path.exists(tentative):
            suffix = 1
            while True:
                candidate = os.path.join(ra_folder, f"{safe_bid_no}_RA_{suffix}.pdf")
                if not os.path.exists(candidate):
                    tentative = candidate
                    break
                suffix += 1
        dest_path = tentative
        try:
            shutil.move(file_path, dest_path)
            print(f"Moved to RAs/{os.path.basename(dest_path)}")
        except Exception as exc:
            print(f"Error moving file '{file_path}': {exc}")

    if len(new_files) < len(ra_records):
        print(f"Warning: Expected {len(ra_records)} RA documents but found {len(new_files)} download(s).")


def save_csv(data: list, state: str, city: str, label_override: str | None = None) -> str | None:
    """Persist scraped data into the Data/ folder and return the CSV path."""
    if not data:
        return None

    data_folder = os.path.join(os.getcwd(), "Data")
    os.makedirs(data_folder, exist_ok=True)

    df = pd.DataFrame(data)
    if 'b_id' in df.columns or 'Bid Doc' in df.columns:
        df = df.drop(columns=[col for col in ['b_id', 'Bid Doc'] if col in df.columns])

    csv_filename = build_csv_filename(state, city, label_override)
    csv_path = os.path.join(data_folder, csv_filename)
    df.to_csv(csv_path, index=False)
    print(f"Data saved to {csv_path}")
    return csv_path


def reconcile_bid_docs(records: list[dict], dest_folder: str) -> None:
    missing = 0
    yes_count = 0
    no_count = 0
    print(f"Reconciling {len(records)} records in folder.")
    if not os.path.exists(dest_folder):
        print(f"Warning: Destination folder {dest_folder} does not exist!")
        for record in records:
            record['Bid Doc'] = 'No'
        return
    for record in records:
        bid_no = record.get('Bid No') or ''
        safe_bid_no = sanitize_for_filename(bid_no)
        path = os.path.join(dest_folder, f"{safe_bid_no}.pdf")
        if os.path.exists(path) and os.path.getsize(path) > 0:
            record['Bid Doc'] = 'Yes'
            yes_count += 1
        else:
            record['Bid Doc'] = 'No'
            missing += 1
            no_count += 1
            print(f"Bid PDF missing for {bid_no}")
    print(f"Reconciliation complete: {yes_count} Yes, {no_count} No, {missing} missing files.")
    if missing:
        print(f"Bid PDF missing for {missing} record(s).")


def execute_scrape(
    session: requests.Session,
    csrf_token: str,
    user_agent: str,
    driver,
    download_dir: str,
    state: str,
    city: str,
    search_type: str = 'con',
    label_override: str | None = None,
    click_all_button: bool = False
) -> None:
    """Run the full scrape workflow for the provided parameters."""

    data: list[dict] = []
    ra_records: list[dict] = []
    existing_pdfs: set[str] = set()
    ra_folder = build_ra_destination(state, city)

    payload = {
        'searchType': search_type,
        'state_name_con': state,
        'city_name_con': city,
        'bidEndFromCon': '',
        'bidEndToCon': ''
    }

    try:
        if click_all_button:
            if click_view_all_button(driver):
                print("Clicked 'View All RAs/Bids' button.")
            else:
                print("Could not automatically click 'View All RAs/Bids'. Proceeding with API request.")

        total = fetch_bids(session, csrf_token, user_agent, payload, data)

        if total == 0 and search_type == 'all':
            print("No records returned for 'all' query. Retrying with consignee search.")
            payload['searchType'] = 'con'
            total = fetch_bids(session, csrf_token, user_agent, payload, data)

        print(f"Total extracted {len(data)} records via API.")
    except KeyboardInterrupt:
        print("Interrupted by user. Finalizing partial results.")
    except Exception as exc:
        print(f"Unexpected error during scraping: {exc}")
    finally:
        try:
            if data:
                download_bid_documents(session, user_agent, data, ra_folder)
        except KeyboardInterrupt:
            print("Download of bid PDFs interrupted by user.")
        except Exception as exc:
            print(f"Error while downloading bid PDFs: {exc}")

        try:
            ra_records = [record for record in data if record.get('RA available') == 'Yes']
            if ra_records:
                print(f"Preparing to download {len(ra_records)} RA document(s)...")
                existing_pdfs = set(glob.glob(os.path.join(download_dir, "*.pdf")))
                download_ra_documents(driver, ra_records)
        except KeyboardInterrupt:
            print("Download of RA documents interrupted by user.")
        except Exception as exc:
            print(f"Error while initiating RA downloads: {exc}")

        try:
            if ra_records:
                move_ra_pdfs(download_dir, ra_folder, ra_records, existing_pdfs)
        except Exception as exc:
            print(f"Error while organizing RA documents: {exc}")

        reconcile_bid_docs(data, ra_folder)

        try:
            csv_path = save_csv(data, state, city, label_override)
            if csv_path:
                # Run preprocessing
                preprocess_script = os.path.join(os.getcwd(), 'preprocessor.py')
                print("Running preprocessing...")
                result = subprocess.run([sys.executable, preprocess_script, csv_path], capture_output=True, text=True)
                if result.returncode == 0:
                    print("Preprocessing completed successfully.")
                else:
                    print(f"Preprocessing failed: {result.stderr}")
        except Exception as exc:
            print(f"Error while saving CSV: {exc}")

        driver.quit()
        print("Scraper shut down.")

# Set up Chrome options
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
download_dir = os.path.expanduser('~/Downloads')
options.add_experimental_option("prefs", {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True
})

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get("https://bidplus.gem.gov.in/advance-search")

# Wait for page to load
time.sleep(3)

# Get csrf token
try:
    csrf = driver.find_element(By.ID, "chash").get_attribute("value")
except:
    csrf = driver.execute_script("return document.getElementById('chash').value;")

# Create a requests session with cookies from selenium
session = requests.Session()
for cookie in driver.get_cookies():
    session.cookies.set(cookie['name'], cookie['value'])

# Get state list via API
user_agent = driver.execute_script("return navigator.userAgent;")
states: list[str] = []
state_list_available = True
try:
    response = session.post(
        'https://bidplus.gem.gov.in/state-list-adv',
        data={'csrf_bd_gem_nk': csrf},
        headers={'User-Agent': user_agent}
    )
    print(f"State list response status: {response.status_code}")
    states_data = response.json().get('data', [])
    states = [s['state_name'] for s in states_data]
except Exception as exc:
    state_list_available = False
    print(f"Error fetching states via API: {exc}")
    print("Falling back to manual selection...")

if not state_list_available:
    consignee_tab = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "location-tab"))
    )
    consignee_tab.click()
    time.sleep(2)

    print("Please select the state and optionally the city from the dropdowns.")
    print("Then click 'Search' button.")
    input("Press Enter after you've clicked search and results loaded...")

    state = (driver.execute_script("return document.getElementById('state_name_con').value;") or '').strip()
    city = (driver.execute_script("return document.getElementById('city_name_con').value;") or '').strip()

    all_mode = not state
    label_override = "All RAs/Bids" if all_mode else None
    search_type = 'all' if all_mode else 'con'

    print(f"Selected state: {state or 'ALL'}, city: {city or 'ALL'}")
    execute_scrape(
        session,
        csrf,
        user_agent,
        driver,
        download_dir,
        state,
        city,
        search_type=search_type,
        label_override=label_override,
        click_all_button=all_mode
    )
    sys.exit(0)

parser = argparse.ArgumentParser(description='Scrape GEM bid data.')
parser.add_argument('--state', type=str, help='State name (leave empty for all)')
parser.add_argument('--city', type=str, default='', help='City name (leave empty for all cities)')
args = parser.parse_args()

state = args.state
city = args.city if args.city else ''

if not state:
    all_mode = True
    label_override = "All RAs/Bids"
    search_type = 'all'
else:
    all_mode = False
    label_override = None
    search_type = 'con'

print(f"Selected state: {state or 'ALL'}, city: {city or 'ALL'}")

execute_scrape(
    session,
    csrf,
    user_agent,
    driver,
    download_dir,
    state,
    city,
    search_type=search_type,
    label_override=label_override,
    click_all_button=all_mode
)
