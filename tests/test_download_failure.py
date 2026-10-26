
from pathlib import Path
from unittest.mock import patch

import pytest
import requests

from scripts import extract_data


def test_download_failure_preserves_existing_data(tmp_path, monkeypatch):
    # Redirect output to a temporary testing directory
    monkeypatch.setattr(extract_data, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(
        extract_data, "ZIP_FILE", tmp_path / "sales.zip"
    )
    monkeypatch.setattr(
        extract_data, "EXTRACT_DIR", tmp_path / "extracted"
    )

    # Simulate an existing successful download
    existing_zip = tmp_path / "sales.zip"
    existing_zip.write_bytes(b"previous download")

    existing_folder = tmp_path / "extracted"
    existing_folder.mkdir()
    (existing_folder / "previous.csv").write_text("existing data")

    # Simulate a network failure
    with patch(
        "scripts.extract_data.requests.get",
        side_effect=requests.ConnectionError("Network unavailable")
    ):
        with pytest.raises(requests.ConnectionError):
            extract_data.download_data()

    # Existing data must remain unchanged
    assert existing_zip.read_bytes() == b"previous download"
    assert (existing_folder / "previous.csv").read_text() == "existing data"

    # Temporary download must be cleaned up
    assert not (tmp_path / "sales.zip.tmp").exists()
