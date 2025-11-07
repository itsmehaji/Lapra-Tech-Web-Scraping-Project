from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import pandas as pd
import os
import shutil
import time
import glob
import requests
import json
from typing import Any, Iterable
import re

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

def build_csv_filename(state: str | None, city: str | None) -> str:
    ts = time.strftime('%Y%m%d_%H%M%S', time.localtime())
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

# Set up Chrome options
options = webdriver.ChromeOptions()
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
try:
    response = session.post('https://bidplus.gem.gov.in/state-list-adv', 
                           data={'csrf_bd_gem_nk': csrf},
                           headers={'User-Agent': driver.execute_script("return navigator.userAgent;")})
    print(f"State list response status: {response.status_code}")
    states_data = response.json()['data']
    states = [s['state_name'] for s in states_data]
except Exception as e:
    print(f"Error fetching states via API: {e}")
    print("Falling back to manual selection...")
    # Select the consignee location tab
    consignee_tab = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "location-tab"))
    )
    consignee_tab.click()
    time.sleep(2)
    
    print("Please select the state and optionally the city from the dropdowns.")
    print("Then click 'Search' button.")
    input("Press Enter after you've clicked search and results loaded...")
    
    # Get values from the form
    state = driver.execute_script("return document.getElementById('state_name_con').value;")
    city = driver.execute_script("return document.getElementById('city_name_con').value;")
    print(f"Selected state: {state}, city: {city}")
    
    # Use API from here
    payload = {
        'searchType': 'con',
        'state_name_con': state,
        'city_name_con': city,
        'bidEndFromCon': '',
        'bidEndToCon': ''
    }
    
    data = []
    page = 1
    print("Fetching data via API...")
    while True:
        payload['page'] = page
        try:
            response = session.post('https://bidplus.gem.gov.in/search-bids', 
                                   data={'payload': json.dumps(payload), 'csrf_bd_gem_nk': csrf},
                                   headers={'User-Agent': driver.execute_script("return navigator.userAgent;")})
            if response.status_code != 200:
                break
            json_data = response.json()
            if 'response' not in json_data or 'response' not in json_data['response'] or 'docs' not in json_data['response']['response']:
                break
            docs = json_data['response']['response']['docs']
            if not docs:
                break
            for doc in docs:
                bid_no = doc['b_bid_number']
                items = doc['b_category_name'][0] if doc.get('b_category_name') else ''
                quantity = str(doc['b_total_quantity'])
                
                # Handle ministry name (can be list or string)
                min_name = doc.get('ba_official_details_minName', '')
                if isinstance(min_name, list):
                    min_name = min_name[0] if min_name else ''
                dept_name = doc.get('ba_official_details_deptName', '')
                if isinstance(dept_name, list):
                    dept_name = dept_name[0] if dept_name else ''
                deptAddr = (min_name + ' ' + dept_name).strip()
                
                # Handle dates using robust extraction (multiple possible keys/types)
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
                
                ra_available = 'Yes' if doc['b_bid_type'] == 2 and doc['b_eval_type'] != 0 else 'No'
                data.append({
                    'Bid No': bid_no,
                    'Items': items,
                    'Quantity': quantity,
                    'Department Name And Address': deptAddr,
                    'Start Date': start_date,
                    'End Date': end_date,
                    'RA available': ra_available,
                    'b_id': doc['b_id']
                })
            print(f"Page {page}: {len(docs)} records")
            page += 1
            if page > 1000:
                break
        except Exception as e:
            print(f"Error on page {page}: {e}")
            break
    
    print(f"Total extracted {len(data)} records via API.")
    
    # Skip to RA downloads and CSV saving
    # Now, for RA downloads
    ra_folder = os.path.join(os.getcwd(), "RAs")
    os.makedirs(ra_folder, exist_ok=True)

    for record in data:
        if record['RA available'] == 'Yes':
            b_id = record['b_id']
            ra_url = f"https://bidplus.gem.gov.in/list-ra-schedules/{b_id}"
            try:
                driver.get(ra_url)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                ra_links = driver.find_elements(By.PARTIAL_LINK_TEXT, "RA document")
                for link in ra_links:
                    link.click()
                    time.sleep(1)
                print(f"Downloaded RA for {record['Bid No']}")
            except Exception as e:
                print(f"Error downloading RA for {record['Bid No']}: {e}")

    # Move files
    time.sleep(10)
    downloaded_files = sorted(glob.glob(os.path.join(download_dir, "*.pdf")), key=os.path.getmtime)
    ra_records = [r for r in data if r['RA available'] == 'Yes']
    for i, file_path in enumerate(downloaded_files[-len(ra_records):]):
        if i < len(ra_records):
            bid_no = ra_records[i]['Bid No']
            safe_bid_no = bid_no.replace('/', '_').replace('\\', '_')
            new_name = f"{safe_bid_no}.pdf"
            try:
                shutil.move(file_path, os.path.join(ra_folder, new_name))
                print(f"Moved to RAs/{new_name}")
            except Exception as e:
                print(f"Error moving file: {e}")

    # Save to CSV with unique filename
    data_folder = os.path.join(os.getcwd(), "Data")
    os.makedirs(data_folder, exist_ok=True)
    df = pd.DataFrame(data)
    df = df.drop(columns=['b_id'])
    csv_filename = build_csv_filename(state, city)
    csv_path = os.path.join(data_folder, csv_filename)
    df.to_csv(csv_path, index=False)
    print(f"Data saved to {csv_path}")

    driver.quit()
    print("Scraping completed.")
    exit()

print("Available states:")
for s in states:
    print(s)

state = input("Enter the exact state name: ").strip()

city = ''
if state:
    # Get city list
    response = session.post('https://bidplus.gem.gov.in/city-list-adv', 
                           data={'state_name': state, 'csrf_bd_gem_nk': csrf},
                           headers={'User-Agent': driver.execute_script("return navigator.userAgent;")})
    cities_data = response.json()['data']
    if cities_data:
        cities = [c['city_name'] for c in cities_data if c['city_name']]
        print("Available cities:")
        for c in cities:
            print(c)
        city = input("Enter the exact city name (leave blank for all cities): ").strip()

print(f"Selected state: {state}, city: {city}")

# Now, use API to get all data
payload = {
    'searchType': 'con',
    'state_name_con': state,
    'city_name_con': city,
    'bidEndFromCon': '',
    'bidEndToCon': ''
}

data = []
page = 1
print("Fetching data via API...")
while True:
    payload['page'] = page
    response = session.post('https://bidplus.gem.gov.in/search-bids', 
                           data={'payload': json.dumps(payload), 'csrf_bd_gem_nk': csrf},
                           headers={'User-Agent': driver.execute_script("return navigator.userAgent;")})
    if response.status_code != 200:
        break
    try:
        json_data = response.json()
    except:
        break
    if 'response' not in json_data or 'response' not in json_data['response'] or 'docs' not in json_data['response']['response']:
        break
    docs = json_data['response']['response']['docs']
    if not docs:
        break
    for doc in docs:
        bid_no = doc['b_bid_number']
        items = doc['b_category_name'][0] if doc.get('b_category_name') else ''
        quantity = str(doc['b_total_quantity'])
        
        # Handle ministry name (can be list or string)
        min_name = doc.get('ba_official_details_minName', '')
        if isinstance(min_name, list):
            min_name = min_name[0] if min_name else ''
        dept_name = doc.get('ba_official_details_deptName', '')
        if isinstance(dept_name, list):
            dept_name = dept_name[0] if dept_name else ''
        deptAddr = (min_name + ' ' + dept_name).strip()
        
        # Handle dates using robust extraction (multiple possible keys/types)
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

        if not start_date or not end_date:
            # One-time debug print to help discover actual keys if dates missing
            if 'DATE_DEBUG_PRINTED' not in globals():
                print("[DEBUG] Date fields missing. Available keys in first problematic doc:")
                print(sorted(list(doc.keys())))
                globals()['DATE_DEBUG_PRINTED'] = True
        
        ra_available = 'Yes' if doc['b_bid_type'] == 2 and doc['b_eval_type'] != 0 else 'No'
        data.append({
            'Bid No': bid_no,
            'Items': items,
            'Quantity': quantity,
            'Department Name And Address': deptAddr,
            'Start Date': start_date,
            'End Date': end_date,
            'RA available': ra_available,
            'b_id': doc['b_id']
        })
    print(f"Page {page}: {len(docs)} records")
    page += 1
    if page > 1000:
        break

print(f"Total extracted {len(data)} records via API.")

# Now, for RA downloads
ra_folder = os.path.join(os.getcwd(), "RAs")
os.makedirs(ra_folder, exist_ok=True)

for record in data:
    if record['RA available'] == 'Yes':
        b_id = record['b_id']
        ra_url = f"https://bidplus.gem.gov.in/list-ra-schedules/{b_id}"
        try:
            driver.get(ra_url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            ra_links = driver.find_elements(By.PARTIAL_LINK_TEXT, "RA document")
            for link in ra_links:
                link.click()
                time.sleep(1)
            print(f"Downloaded RA for {record['Bid No']}")
        except Exception as e:
            print(f"Error downloading RA for {record['Bid No']}: {e}")

# Move files
time.sleep(10)
downloaded_files = sorted(glob.glob(os.path.join(download_dir, "*.pdf")), key=os.path.getmtime)
ra_records = [r for r in data if r['RA available'] == 'Yes']
for i, file_path in enumerate(downloaded_files[-len(ra_records):]):
    if i < len(ra_records):
        bid_no = ra_records[i]['Bid No']
        safe_bid_no = bid_no.replace('/', '_').replace('\\', '_')
        new_name = f"{safe_bid_no}.pdf"
        try:
            shutil.move(file_path, os.path.join(ra_folder, new_name))
            print(f"Moved to RAs/{new_name}")
        except Exception as e:
            print(f"Error moving file: {e}")

# Save to CSV with unique filename
data_folder = os.path.join(os.getcwd(), "Data")
os.makedirs(data_folder, exist_ok=True)
df = pd.DataFrame(data)
df = df.drop(columns=['b_id'])
csv_filename = build_csv_filename(state, city)
csv_path = os.path.join(data_folder, csv_filename)
df.to_csv(csv_path, index=False)
print(f"Data saved to {csv_path}")

driver.quit()
print("Scraping completed.")