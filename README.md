# GEM Bid Scraper & Preprocessor

A tiny, focused toolchain to pull bid data from GeM (Government e‑Marketplace), save tidy CSVs, download Bid/RA PDFs, then clean and compare the results—all with a one‑click Streamlit UI or simple CLI.

---

## ✨ What you get
- Automated scrape by State/City (or ALL)
- CSV exports in `Data/` with timestamped names
- Bid and RA PDFs organized under `RAs/<STATE>/<CITY>/`
- Quick cleaning (dedupe by Bid No, friendlier dates) into `cleaned data/`
- Side‑by‑side comparison of raw vs cleaned
- Optional web app for a guided, friendly flow

---

## 🧭 Project structure (at a glance)
- `scraper.py` — Headless Chrome + API workflow, saves CSVs, downloads PDFs
- `preprocessor.py` — Cleans the CSV (de‑dupe, date touch‑ups)
- `compare_data.py` — Prints raw vs cleaned stats
- `web_app.py` — Streamlit UI to run scrape → preprocess → analyze
- `Data/` — Raw CSV outputs (timestamped)
- `cleaned data/` — Cleaned CSV outputs (timestamped)
- `RAs/` — RA and Bid PDFs organized by State/City

---

## ⚙️ Setup (Windows PowerShell)
1) Create a virtual env and install deps:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
```

2) Ensure Google Chrome is installed (the driver is auto‑managed).

---

## 🚀 Quick start
### Option A — Run the web app
```powershell
streamlit run web_app.py
```
Then pick your State/City and follow the buttons: Scrape → Preprocess → Analyze.

Outputs land here:
- Raw CSV: `Data/bids_<STATE>_<CITY>_<TIMESTAMP>.csv`
- Cleaned CSV: `cleaned data/bids_..._cleaned.csv`
- PDFs: `RAs/<STATE>/<CITY>/*.pdf`

---

## 📝 Notes & tips
- If GeM’s API blocks state/city lists, the scraper may prompt you to select them in the opened browser, then press Enter to continue.
- RA PDFs first download to your system `Downloads` and are then moved to `RAs/...` automatically.
- Filenames are sanitized (Windows‑safe) and timestamped to avoid clashes.

---

## 🧩 Troubleshooting
- "streamlit" not found → activate your venv and `pip install -r requirements.txt`.
- Chrome/driver issues → update Chrome; the driver is handled by `webdriver-manager`.
- Empty CSV → try running with a specific State/City, or re‑run later if GeM throttles.

---

Made with care for clarity and repeatability. If you need tweaks (extra columns, filters, or exports), you’re a small edit away in `scraper.py` and friends.

---

## ⭐ Like this project?

If this tool saved you time, please consider:

- Starring the repo to show support
- Sharing it with a teammate
- Opening an issue for ideas or bugs
- Sending a PR with improvements

Your support helps keep it maintained and improving. Thanks!


