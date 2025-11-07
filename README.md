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
