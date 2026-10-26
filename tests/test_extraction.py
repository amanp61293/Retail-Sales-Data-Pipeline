
import io
import zipfile

from scripts.extract_data import ZIP_FILE


def test_zip_file_exists():
    assert ZIP_FILE.exists()


def test_downloaded_archive_is_valid():
    assert zipfile.is_zipfile(ZIP_FILE)


def test_invalid_zip_is_rejected():
    invalid_file = io.BytesIO(b"This is not a ZIP archive")

    assert not zipfile.is_zipfile(invalid_file)
