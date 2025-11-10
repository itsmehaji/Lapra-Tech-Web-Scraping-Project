# 📊 GEM Bid Scraper & Preprocessor  
*A simple and efficient toolkit to extract and clean bid data from the Government e-Marketplace (GeM).*

---

## ✨ Overview  
This project automates the process of collecting bid details from the GeM portal and neatly organizes the data for analysis.  
No more manual downloads or messy spreadsheets — everything is structured and ready to use.

---

## ✅ Prerequisites  
Make sure the following are available on your system before running the project:

| Requirement | Description |
|------------|-------------|
| 🐍 Python (Latest Version) | Ensure Python is installed and added to PATH |
| 🌐 Google Chrome Installed | Used for automated browsing and PDF handling |
| 📶 Stable Internet Connection | Required for fetching data from GeM website |

---

## ✅ Features  
- Scrape bid data by **State / City** or scrape **all** available data  
- Save raw data in `Data/` with timestamped filenames  
- Download and arrange Bid/RA PDFs in `RAs/<STATE>/<CITY>/`  
- Clean and preprocess CSVs into `cleaned data/`  
- Compare raw vs cleaned datasets using `compare_data.py`  
- Optional **Streamlit** UI for an intuitive, click-based workflow

---

## 📂 Project Structure  
- scraper.py → Scrapes bid data and downloads PDFs
- preprocessor.py → Cleans and formats the raw CSV files
- compare_data.py → Summarizes differences between raw and cleaned data
- web_app.py → Streamlit UI for scraping and preprocessing
- Data/ → Raw CSV outputs
- cleaned data/ → Cleaned and deduplicated CSV outputs
- RAs/ → Organized folder of downloaded PDFs

---

## ⚙️ Installation  
```bash
pip install -r requirements.txt
```

## 🚀 How to Use
Run the Streamlit Web App:
```
streamlit run web_app.py
```
Select State / City

Click → Scrape

Click → Preprocess

Click → Analyze

Processed files will appear in the corresponding directories.

##💡 Tips
# If GeM limits API access, the scraper may switch to browser mode — select State/City manually and press Enter.

- PDFs first download to your Downloads folder and are then automatically moved to RAs/.

## 🔧 Troubleshooting
# Issue	Solution
- streamlit command not found	Re-activate environment & run pip install -r requirements.txt
- Chrome/Driver mismatch errors	Update Chrome; webdriver-manager handles the driver
- CSV output is empty	Try filtering by State/City; GeM may be throttling bulk scraping

## 🤝 Contributions
- Fork the repo
- Improve or optimize scripts
- Submit Issues or PRs

## ⭐ Star the repo if this helped you!

## 🛠️ Built For
# Automation • Procurement Analytics • Data Extraction • Quick Workflows

Happy Scraping! 🚀
