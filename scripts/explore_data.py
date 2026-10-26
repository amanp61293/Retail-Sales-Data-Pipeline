
import requests
import zipfile
from pathlib import Path

URL = "https://idh-be.iowa.gov/api/v1/datasets/1263/rows.csv"

OUTPUT_DIR = Path("data/raw")
ZIP_FILE = OUTPUT_DIR / "iowa_liquor_sales_2026.zip"
EXTRACT_DIR = OUTPUT_DIR / "extracted"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/csv",
}


def download_data():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Starting dataset download...")

    with requests.get(
        URL,
        headers=HEADERS,
        stream=True,
        timeout=(30, 120)
    ) as response:
        response.raise_for_status()

        with open(ZIP_FILE, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)

    print("Download complete.")

    # Verify that the downloaded file is a ZIP archive
    if not zipfile.is_zipfile(ZIP_FILE):
        raise ValueError("Downloaded file is not a valid ZIP archive")

    # Extract the CSV files
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(ZIP_FILE, "r") as archive:
        csv_files = [
            name for name in archive.namelist()
            if name.lower().endswith(".csv")
        ]

        if not csv_files:
            raise ValueError("ZIP archive contains no CSV files")

        archive.extractall(EXTRACT_DIR)

    print(f"Extracted {len(csv_files)} CSV files.")
    print(f"Files saved to: {EXTRACT_DIR}")


if __name__ == "__main__":
    download_data()
