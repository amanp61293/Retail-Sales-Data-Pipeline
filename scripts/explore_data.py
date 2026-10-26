
import pandas as pd
from pathlib import Path

# Find all CSV files in the data folder
data_folder = Path("data")
csv_files = sorted(data_folder.glob("*.csv"))

# Read the first 1,000 rows from each file
dataframes = []

for file in csv_files:
    df = pd.read_csv(file, nrows=1000)
    dataframes.append(df)
    print(f"Loaded {file.name}: {len(df)} rows")

# Combine the data
df = pd.concat(dataframes, ignore_index=True)

print("\nCombined dataset shape:", df.shape)

print("\nColumn names:")
print(df.columns.tolist())

print("\nFirst 5 records:")
print(df.head())


# Examine column data types
print("\nData types:")
print(df.dtypes)

# Count missing values
print("\nMissing values per column:")
print(df.isnull().sum())

# Check for completely identical records
print("\nDuplicate rows:", df.duplicated().sum())

# Basic sales statistics
print("\nSales statistics:")
print(df[["sales_bottles", "sales_dollars", "sales_liters"]].describe())


# Find records containing negative sales values
negative_sales = df[
    (df["sales_bottles"] < 0) |
    (df["sales_dollars"] < 0) |
    (df["sales_liters"] < 0)
]

print("\nNumber of records with negative sales:")
print(len(negative_sales))

print("\nNegative sales records:")
print(
    negative_sales[
        [
            "invoice_id",
            "ordered_on",
            "store_no",
            "item_no",
            "sales_bottles",
            "sales_dollars",
            "sales_liters"
        ]
    ].to_string(index=False)
)

# Check whether invoice IDs repeat
print("\nUnique invoice IDs:", df["invoice_id"].nunique())

# Check for repeated invoice and product combinations
print(
    "Repeated invoice-product combinations:",
    df.duplicated(subset=["invoice_id", "item_no"]).sum()
)
