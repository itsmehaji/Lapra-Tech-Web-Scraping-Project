import pandas as pd
import os
import sys

# Get CSV path from command line argument
if len(sys.argv) < 2:
    print("Usage: python preprocess_andaman.py <csv_path>")
    sys.exit(1)
csv_path = sys.argv[1]

if not os.path.exists(csv_path):
    print(f"File not found: {csv_path}")
    sys.exit(1)

df = pd.read_csv(csv_path)

print("Original data shape:", df.shape)
print("Columns:", df.columns.tolist())

# Remove duplicates based on 'Bid No'
df_clean = df.drop_duplicates(subset=['Bid No']).copy()
print("After removing duplicates shape:", df_clean.shape)

# Check for missing values
print("Missing values per column:")
print(df_clean.isnull().sum())

# Convert date columns to date and time with space separator
df_clean.loc[:, 'Start Date'] = df_clean['Start Date'].str.replace('T', ' ')
df_clean.loc[:, 'End Date'] = df_clean['End Date'].str.replace('T', ' ')

# Fill any missing dates or other columns if needed (none here)
# df_clean.fillna({'Quantity': 0}, inplace=True)  # Example

# Save the cleaned data
cleaned_data_dir = os.path.join(os.getcwd(), 'cleaned data')
os.makedirs(cleaned_data_dir, exist_ok=True)
base_name = os.path.basename(csv_path).replace('.csv', '_cleaned.csv')
output_path = os.path.join(cleaned_data_dir, base_name)
df_clean.to_csv(output_path, index=False)
print("Cleaned data saved successfully.")

# Basic statistics
print("RA available distribution:")
print(df_clean['RA available'].value_counts())
if 'Bid Doc' in df_clean.columns:
    print("Bid Doc distribution:")
    print(df_clean['Bid Doc'].value_counts())
else:
    print("Bid Doc column not present.")