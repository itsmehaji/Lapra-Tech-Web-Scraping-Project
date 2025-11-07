# GEM Bidplus Web Scraper

## 📌 Project Overview

An efficient, production-ready web scraper for extracting bid information from the **Government e-Marketplace (GeM) Bidplus** platform ([https://bidplus.gem.gov.in/advance-search]). 

This project was developed as part of the **LapraTech Internship** under the Web Scraping/Automation Engineer position.

### ✨ Key Features

- **⚡ High-Performance API-Based Extraction**: Hybrid architecture using Selenium + REST API for lightning-fast data retrieval (seconds vs hours)
- **📊 Comprehensive Data Extraction**: Captures 8 critical bid fields including dates, items, departments, and RA availability
- **🗂️ Intelligent File Management**: Auto-generates unique CSV filenames with state/city/timestamp to prevent data loss
- **📄 Automated Document Downloads**: Retrieves and organizes RA (Rate Analysis) documents with proper naming
- **🛡️ Robust Error Handling**: Defensive type checking for inconsistent API responses
- **🌍 State/City Filtering**: Interactive selection with fallback to manual browser-based input
- **💾 Clean Data Output**: Well-structured CSV files ready for analysis

---

## 🎯 Assignment Requirements

✅ Extract bid data with 8 columns:
- Bid Number
- Items (full descriptions)
- Quantity
- Department Name and Address
- Start Date
- End Date
- RA Available

✅ Handle state/city filtering via "search by consignee location"

✅ Download RA documents when available and rename with bid numbers

✅ **Performance**: Fast, accurate, user-friendly, and efficient (completes in seconds to minutes)

✅ Multi-page data extraction (handles pagination automatically)

---

## 🏗️ Architecture

### Hybrid Approach (Selenium + API)

```
┌─────────────────┐
│  Selenium Init  │ → Load page, extract CSRF token, transfer cookies
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   API Calls     │ → Fast state/city lists + bid data extraction
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  RA Downloads   │ → Selenium navigates to RA pages, clicks download links
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  File Handling  │ → Move/rename PDFs, save CSV with unique filename
└─────────────────┘
```

### Why This Architecture?

- **Initial Approach**: Pure Selenium with pagination → ❌ 4.5 hours execution time
- **Optimized Solution**: API for data + Selenium for RA downloads → ✅ Seconds to minutes
- **Fallback Mechanism**: If API fails, gracefully degrades to manual browser selection

---

## 🚀 Setup & Installation

### Prerequisites

- **Python**: 3.7 or higher
- **Chrome Browser**: Latest version installed
- **Internet Connection**: Required for accessing GeM portal

### Installation Steps

1. **Clone/Download the project**
   ```bash
   cd "https://github.com/itsmehaji/Lapra-Tech-Web-Scraping-Project"
   ```

2. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Verify installation**
   ```powershell
   python -c "import selenium, pandas, requests; print('All dependencies installed!')"
   ```

---

## 📖 Usage

### Quick Start

#### Option 1: Using Python directly
```powershell
python scraper.py
```

### Interactive Workflow

1. **Script launches Chrome** and loads the GeM Bidplus page
2. **Select State**: Enter exact state name from the displayed list (e.g., `GOA`)
3. **Select City** (optional): Enter city name or press Enter to select all cities in the state
4. **Automatic Extraction**: Script fetches all bid data via API with progress updates
5. **RA Document Downloads**: Automatically retrieves and organizes PDF documents
6. **Output**: Check the `Data/` folder for your CSV file

### Example Session

```
Available states:
ANDHRA PRADESH
GOA
MAHARASHTRA
...

Enter the exact state name: GOA

Available cities:
North Goa
SOUTH GOA

Enter the exact city name (leave blank for all cities): North Goa

Selected state: GOA, city: North Goa
Fetching data via API...
Page 1: 10 records
Page 2: 10 records
Page 3: 7 records
Total extracted 27 records via API.

Downloaded RA for GEM/2024/B/1234567
...

Data saved to Data\bids_GOA_North_Goa_20251108_143022.csv
Scraping completed.
```

---

## 📁 Project Structure

```
Intern Assignment/
│
├── scraper.py              # Main scraper script
├── requirements.txt        # Python dependencies
├── run.bat                # Windows batch launcher
├── README.md              # This file
│
├── Data/                  # CSV output folder
│   ├── bids_GOA_North_Goa_20251108_143022.csv
│   ├── bids_MAHARASHTRA_MUMBAI_20251108_150315.csv
│   └── ...
│
└── RAs/                   # RA documents folder
    ├── GEM_2024_B_1234567.pdf
    ├── GEM_2024_B_7654321.pdf
    └── ...
```

---

## 🔧 Technical Details

### Technologies Used

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.13.5 | Core scripting language |
| Selenium | 4.38.0 | Browser automation & RA downloads |
| Pandas | 2.x | CSV generation & data handling |
| Requests | 2.x | API communication |
| WebDriver Manager | 4.0.2 | Auto Chrome driver setup |

### API Endpoints

The script interfaces with GeM's public API:

- **State List**: `POST /state-list-adv`
- **City List**: `POST /city-list-adv`
- **Bid Search**: `POST /search-bids`
- **RA Schedules**: `GET /list-ra-schedules/{bid_id}`

### Data Extraction Logic

#### Robust Date Parsing
```python
# Handles mixed types: list, int, string, or null
- Tries numeric keys: final_start_date_sort, b_bid_start_date_js, etc.
- Falls back to string keys: b_bid_start_date, start_date
- Heuristic scan: searches all keys containing 'date' and 'start'/'end'
- Converts epoch milliseconds/seconds to formatted date strings
```

#### CSV Filename Convention
```
bids_{STATE}_{CITY}_{YYYYMMDD_HHMMSS}.csv

Examples:
- bids_GOA_North_Goa_20251108_143022.csv
- bids_DELHI_ALL_20251108_150000.csv
- bids_ALL_20251108_160000.csv (when no state/city selected)
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. **ImportError: No module named 'pandas' / 'requests'**
```powershell
pip install -r requirements.txt
```

#### 2. **Chrome driver issues**
- WebDriver Manager auto-downloads the correct driver
- If issues persist, update Chrome to the latest version

#### 3. **API returns empty results**
- Verify state/city names are exact matches (case-sensitive)
- Check internet connection
- Try a different state/city combination

#### 4. **Dates showing as empty in CSV**
- Enable debug mode (script will print available field names)
- The robust extractor tries multiple field variations
- Contact support with the debug output if persistent

#### 5. **RA documents not downloading**
- Ensure Chrome allows automatic downloads
- Check `~/Downloads` folder for partial downloads
- Verify sufficient disk space

#### 6. **TypeError: unsupported operand**
- Latest version includes defensive type checking
- Update to the newest scraper.py version

---

## 📊 Output Format

### CSV Columns

| Column | Description | Example |
|--------|-------------|---------|
| Bid No | Unique bid identifier | GEM/2024/B/1234567 |
| Items | Full item description | Desktop Computers - Intel Core i5 |
| Quantity | Total quantity | 50 |
| Department Name And Address | Ministry + Department | Ministry of Defence Indian Army |
| Start Date | Bid start date/time | 05-11-2024 10:00 AM |
| End Date | Bid end date/time | 15-11-2024 05:00 PM |
| RA available | RA document availability | Yes / No |

---

## 🎓 Development Notes

### Performance Optimization Journey

1. **Initial Implementation**: Full Selenium automation
   - ⏱️ 4.5 hours for complete extraction
   - ❌ Too slow for production use

2. **API Discovery**: Analyzed network traffic
   - ✅ Found public API endpoints
   - ✅ Extracted CSRF token for authentication

3. **Hybrid Architecture**: Best of both worlds
   - ⚡ API for fast data extraction (seconds)
   - 🌐 Selenium for RA downloads (requires browser interaction)
   - 📈 99% performance improvement

### Challenges Overcome

- **Inconsistent API Response Types**: Fields returned as list, string, int, or null
  - Solution: Defensive `isinstance()` checks with type normalization

- **Date Field Variability**: Multiple possible field names across records
  - Solution: Multi-key fallback extraction with heuristic scanning

- **File Overwrite Issue**: Single CSV filename caused data loss
  - Solution: Dynamic filenames with state/city/timestamp

- **RA Download Timing**: Race conditions in file download detection
  - Solution: Sleep delays + file count validation (future: stabilization polling)

---

## 🔮 Future Enhancements

- [ ] Headless Chrome mode for server deployment
- [ ] Progress bar for multi-page extraction
- [ ] Excel (.xlsx) output option
- [ ] Email notification on completion
- [ ] Configurable filters (date range, department, etc.)
- [ ] Database integration (SQLite/MySQL)
- [ ] Multi-threaded RA downloads
- [ ] Download stabilization (wait for file size to stop changing)
- [ ] Retry logic for failed API calls
- [ ] Command-line arguments for non-interactive mode

---

## 📄 License

This project was created as part of the LapraTech internship.

---

## 👤 Author

**Mohammad**  
Web Scraping/Automation Engineer Candidate  
LapraTech Internship Program

---

## 🙏 Acknowledgments

- **LapraTech**: For the opportunity and challenge
- **Government e-Marketplace (GeM)**: For the public API access
- **Python Community**: For excellent libraries (Selenium, Pandas, Requests)

---

## 📞 Support

For issues or questions:
1. Check the **Troubleshooting** section above
2. Review error messages in console output
3. Verify all dependencies are installed
4. Contact LapraTech technical team

---

**Last Updated**: November 8, 2025  
**Version**: 2.0 (Hybrid API Architecture)
