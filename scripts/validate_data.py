
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/raw/extracted")

REQUIRED_COLUMNS = [
    "invoice_id",
    "ordered_on",
    "store_no",
    "item_no",
    "sales_bottles",
    "sales_dollars",
    "sales_liters",
]

NUMERIC_COLUMNS = [
    "store_no",
    "item_no",
    "sales_bottles",
    "sales_dollars",
    "sales_liters",
]


def validate_data():
    csv_files = sorted(DATA_DIR.rglob("*.csv"))

    if not csv_files:
        raise FileNotFoundError("No CSV files found.")

    total_rows = 0
    negative_rows = 0

    print(f"Found {len(csv_files)} CSV files.")

    for file in csv_files:
        file_rows = 0
        print(f"\nValidating: {file.name}")

        for chunk in pd.read_csv(file, chunksize=50000):
            missing_columns = set(REQUIRED_COLUMNS) - set(chunk.columns)

            if missing_columns:
                raise ValueError(
                    f"{file.name}: Missing columns: {missing_columns}"
                )

            if chunk[REQUIRED_COLUMNS].isnull().any().any():
                raise ValueError(
                    f"{file.name}: Missing required values"
                )

            pd.to_datetime(
                chunk["ordered_on"],
                format="%Y-%m-%d",
                errors="raise"
            )

            for column in NUMERIC_COLUMNS:
                numeric_values = pd.to_numeric(
                    chunk[column],
                    errors="raise"
                )

                if not numeric_values.notna().all():
                    raise ValueError(
                        f"{file.name}: Invalid values in {column}"
                    )

            negative_rows += (
                (chunk["sales_bottles"] < 0)
                | (chunk["sales_dollars"] < 0)
                | (chunk["sales_liters"] < 0)
            ).sum()

            file_rows += len(chunk)

        if file_rows == 0:
            raise ValueError(f"{file.name} is empty")

        total_rows += file_rows
        print(f"Validated {file_rows:,} rows.")

    print("\nValidation successful!")
    print(f"Total rows: {total_rows:,}")
    print(f"Negative sales records: {negative_rows:,}")


if __name__ == "__main__":
    validate_data()
