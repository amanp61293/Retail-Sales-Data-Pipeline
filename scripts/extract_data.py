
import logging
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

import requests

URL = "https://idh-be.iowa.gov/api/v1/datasets/1263/rows.csv"

OUTPUT_DIR = Path("data/raw")
ZIP_FILE = OUTPUT_DIR / "iowa_liquor_sales_2026.zip"
EXTRACT_DIR = OUTPUT_DIR / "extracted"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/csv",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def download_data():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    temporary_zip = ZIP_FILE.with_suffix(".zip.tmp")
    temporary_extract = None

    try:
        logger.info("Starting dataset download...")

        with requests.get(
            URL,
            headers=HEADERS,
            stream=True,
            timeout=(30, 120),
        ) as response:
            response.raise_for_status()

            with open(temporary_zip, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        file.write(chunk)

        if not zipfile.is_zipfile(temporary_zip):
            raise ValueError("Downloaded file is not a ZIP archive")

        with zipfile.ZipFile(temporary_zip) as archive:
            if archive.testzip() is not None:
                raise ValueError("ZIP archive failed integrity check")

            csv_files = [
                member for member in archive.infolist()
                if member.filename.lower().endswith(".csv")
                and not member.is_dir()
            ]

            if not csv_files:
                raise ValueError("ZIP archive contains no CSV files")

            temporary_extract = Path(
                tempfile.mkdtemp(prefix="liquor_extract_", dir=OUTPUT_DIR)
            )

            for member in csv_files:
                # Avoid extracting untrusted paths or nested directories
                name = Path(member.filename.replace("\\", "/"))
                if name.is_absolute() or ".." in name.parts:
                    raise ValueError("Unsafe ZIP member path")

                destination = temporary_extract / name.name

                if destination.exists():
                    raise ValueError("Duplicate CSV filename")

                with archive.open(member) as source:
                    with open(destination, "wb") as target:
                        shutil.copyfileobj(source, target)

        # Publish files only after successful download and extraction
        os.replace(temporary_zip, ZIP_FILE)

        if EXTRACT_DIR.exists():
            shutil.rmtree(EXTRACT_DIR)

        temporary_extract.rename(EXTRACT_DIR)
        temporary_extract = None

        logger.info("Download and extraction successful")
        logger.info("Extracted %d CSV files", len(csv_files))

    except Exception:
        logger.exception("Data extraction failed")
        raise

    finally:
        temporary_zip.unlink(missing_ok=True)

        if temporary_extract is not None:
            shutil.rmtree(temporary_extract, ignore_errors=True)


if __name__ == "__main__":
    download_data()
