import streamlit as st
import subprocess
import os
import glob
import pandas as pd
import requests
from bs4 import BeautifulSoup

@st.cache_data
def get_cities(state):
    if state == 'ALL':
        return ['ALL']
    
    with st.spinner(f"Fetching cities for {state}..."):
        session = requests.Session()
        response = session.get("https://bidplus.gem.gov.in/advance-search")
        
        if response.status_code != 200:
            return ['ALL']
        
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_element = soup.find('input', {'id': 'chash'})
        if not csrf_element:
            return ['ALL']
        csrf = csrf_element.get('value')
        
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        response = session.post(
            'https://bidplus.gem.gov.in/city-list-adv',
            data={'state_name': state, 'csrf_bd_gem_nk': csrf},
            headers={'User-Agent': user_agent}
        )
        
        if response.status_code == 200:
            cities_data = response.json().get('data', [])
            cities = ['ALL'] + [c['city_name'] for c in cities_data if c.get('city_name')]
            return cities
        else:
            return ['ALL']

st.title("GEM Bid Scraper & Preprocessor")
st.markdown("A user-friendly interface for scraping and processing GEM bid data.")

# Expanded hardcoded states list
states = [
    'ALL', 'ANDAMAN & NICOBAR', 'ANDHRA PRADESH', 'ARUNACHAL PRADESH', 'ASSAM', 'BIHAR', 'CHANDIGARH', 'CHHATTISGARH',
    'DADRA & NAGAR HAVELI', 'DAMAN & DIU', 'DELHI', 'GOA', 'GUJARAT', 'HARYANA', 'HIMACHAL PRADESH', 'JAMMU & KASHMIR',
    'JHARKHAND', 'KARNATAKA', 'KERALA', 'LAKSHADWEEP', 'MADHYA PRADESH', 'MAHARASHTRA', 'MANIPUR', 'MEGHALAYA',
    'MIZORAM', 'NAGALAND', 'ODISHA', 'PUDUCHERRY', 'PUNJAB', 'RAJASTHAN', 'SIKKIM', 'TAMIL NADU', 'TELANGANA',
    'TRIPURA', 'UTTAR PRADESH', 'UTTARAKHAND', 'WEST BENGAL'
]

# City options based on state (fetched dynamically)
# Removed hardcoded city_dict

start_button = st.button("🚀 Start Scraping Process")

if start_button or 'started' in st.session_state:
    st.session_state['started'] = True

    st.subheader("Select Location")
    col1, col2 = st.columns(2)
    with col1:
        state = st.selectbox("Select State", states, key='state')
    with col2:
        city_options = get_cities(state)
        city = st.selectbox("Select City", city_options)

    run_button = st.button("🔍 Run Scraper", help="Start scraping bid data for the selected location.")

    if run_button:
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text("Initializing scraper...")

        with st.spinner("Scraping data... Please wait."):
            progress_bar.progress(10)
            status_text.text("Setting up browser and session...")

            cmd = ['python', 'scraper.py']
            if state != 'ALL':
                cmd.extend(['--state', state])
            if city != 'ALL':
                cmd.extend(['--city', city])

            progress_bar.progress(30)
            status_text.text("Fetching bid data...")

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())

            progress_bar.progress(70)
            status_text.text("Processing and downloading files...")

            # Simulate progress
            import time
            time.sleep(2)  # Simulate time for downloads

            progress_bar.progress(100)
            status_text.text("Scraping completed!")

        if result.returncode == 0:
            st.success("✅ Scraping completed successfully!")

            # Display key outputs
            with st.expander("Scraper Details"):
                st.code(result.stdout[-1000:], language='text')  # Last 1000 chars

            # Find the latest raw CSV
            data_files = glob.glob('Data/*.csv')
            if data_files:
                latest_raw = max(data_files, key=os.path.getctime)
                st.session_state['raw_csv'] = latest_raw
                st.info(f"📄 Raw data saved: `{os.path.basename(latest_raw)}` ({len(pd.read_csv(latest_raw))} records)")
            else:
                st.error("No CSV found in Data folder.")
        else:
            st.error("❌ Scraping failed.")
            st.code(result.stderr, language='text')

if 'raw_csv' in st.session_state:
    st.subheader("Preprocessing")
    preprocess_button = st.button("🧹 Start Preprocessing", help="Clean and deduplicate the scraped data.")

    if preprocess_button:
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text("Starting preprocessing...")

        with st.spinner("Preprocessing data..."):
            progress_bar.progress(20)
            status_text.text("Removing duplicates and formatting dates...")

            cmd = ['python', 'preprocessor.py', st.session_state['raw_csv']]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())

            progress_bar.progress(80)
            status_text.text("Saving cleaned data...")

            progress_bar.progress(100)
            status_text.text("Preprocessing completed!")

        if result.returncode == 0:
            st.success("✅ Preprocessing completed successfully!")

            with st.expander("Preprocessing Details"):
                st.code(result.stdout, language='text')

            # Find the latest cleaned CSV
            cleaned_files = glob.glob('cleaned data/*.csv')
            if cleaned_files:
                latest_cleaned = max(cleaned_files, key=os.path.getctime)
                st.session_state['cleaned_csv'] = latest_cleaned
                st.info(f"📄 Cleaned data saved: `{os.path.basename(latest_cleaned)}` ({len(pd.read_csv(latest_cleaned))} records)")
            else:
                st.error("No cleaned CSV found.")
        else:
            st.error("❌ Preprocessing failed.")
            st.code(result.stderr, language='text')

if 'cleaned_csv' in st.session_state and 'raw_csv' in st.session_state:
    st.subheader("Data Analysis")
    analyze_button = st.button("📊 Analyze Data", help="Compare raw and cleaned data.")

    if analyze_button:
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text("Analyzing data...")

        with st.spinner("Running comparative analysis..."):
            progress_bar.progress(50)

            cmd = ['python', 'compare_data.py', st.session_state['raw_csv'], st.session_state['cleaned_csv']]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())

            progress_bar.progress(100)
            status_text.text("Analysis completed!")

        if result.returncode == 0:
            st.success("✅ Analysis completed!")

            # Parse and display analysis nicely
            analysis_text = result.stdout
            lines = analysis_text.split('\n')

            st.subheader("📈 Comparative Analysis Summary")
            for line in lines:
                if 'Raw Data Shape:' in line:
                    st.metric("Raw Records", line.split(':')[1].strip().split()[0])
                elif 'Cleaned Data Shape:' in line:
                    st.metric("Cleaned Records", line.split(':')[1].strip().split()[0])
                elif 'Rows Removed:' in line:
                    st.metric("Duplicates Removed", line.split(':')[1].strip())
                elif 'Unique' in line and 'Bid No' in line:
                    st.write(f"**{line}**")

            with st.expander("Full Analysis Details"):
                st.code(analysis_text, language='text')
        else:
            st.error("❌ Analysis failed.")
            st.code(result.stderr, language='text')