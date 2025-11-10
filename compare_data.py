import pandas as pd
import os
import sys

# Get raw and cleaned CSV paths
if len(sys.argv) < 3:
    print("Usage: python compare_data.py <raw_csv_path> <cleaned_csv_path>")
    sys.exit(1)

raw_path = sys.argv[1]
cleaned_path = sys.argv[2]

if not os.path.exists(raw_path):
    print(f"Raw CSV not found: {raw_path}")
    sys.exit(1)
if not os.path.exists(cleaned_path):
    print(f"Cleaned CSV not found: {cleaned_path}")
    sys.exit(1)

# Load data
df_raw = pd.read_csv(raw_path)
df_cleaned = pd.read_csv(cleaned_path)

print("=== Comparative Analysis: Raw vs Cleaned Data ===\n")

# Basic stats
print(f"Raw Data Shape: {df_raw.shape}")
print(f"Cleaned Data Shape: {df_cleaned.shape}")
print(f"Rows Removed: {df_raw.shape[0] - df_cleaned.shape[0]}\n")

# Columns
print(f"Raw Columns: {list(df_raw.columns)}")
print(f"Cleaned Columns: {list(df_cleaned.columns)}\n")

# Unique Bid No
if 'Bid No' in df_raw.columns:
    print(f"Raw Unique 'Bid No': {df_raw['Bid No'].nunique()}")
    print(f"Cleaned Unique 'Bid No': {df_cleaned['Bid No'].nunique()}\n")

# Duplicates in raw
if 'Bid No' in df_raw.columns:
    dup_counts = df_raw['Bid No'].value_counts()
    duplicates = dup_counts[dup_counts > 1]
    print(f"Duplicate 'Bid No' in Raw Data: {len(duplicates)} unique values with duplicates")
    if not duplicates.empty:
        print("Top duplicates:")
        print(duplicates.head().to_string())
    print()

# RA available
if 'RA available' in df_raw.columns and 'RA available' in df_cleaned.columns:
    print("RA Available Distribution:")
    print("Raw:")
    print(df_raw['RA available'].value_counts())
    print("Cleaned:")
    print(df_cleaned['RA available'].value_counts())
    print()

# Date formats (sample)
if 'Start Date' in df_raw.columns and 'Start Date' in df_cleaned.columns:
    print("Sample Start Dates:")
    print(f"Raw: {df_raw['Start Date'].iloc[0] if not df_raw.empty else 'N/A'}")
    print(f"Cleaned: {df_cleaned['Start Date'].iloc[0] if not df_cleaned.empty else 'N/A'}")

print("\n=== Analysis Complete ===")