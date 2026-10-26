
import io
import zipfile
from unittest.mock import Mock, patch

from scripts import extract_data


def test_successful_extraction(tmp_path, monkeypatch):
    # Use temporary paths instead of real project data
    monkeypatch.setattr(extract_data, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(
        extract_data, "ZIP_FILE", tmp_path / "sales.zip"
    )
    monkeypatch.setattr(
        extract_data, "EXTRACT_DIR", tmp_path / "extracted"
    )

    # Create a ZIP archive in memory
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as archive:
        archive.writestr(
            "part_0001.csv",
            "invoice_id,sales_dollars\nINV-001,100\n"
        )
        archive.writestr(
            "part_0002.csv",
            "invoice_id,sales_dollars\nINV-002,200\n"
        )

    zip_bytes = zip_buffer.getvalue()

    # Simulate a successful HTTP response
    response = Mock()
    response.raise_for_status.return_value = None
    response.iter_content.return_value = [zip_bytes]
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=None)

    with patch(
        "scripts.extract_data.requests.get",
        return_value=response
    ):
        extract_data.download_data()

    # Verify the downloaded archive
    assert (tmp_path / "sales.zip").exists()

    # Verify both CSV files were extracted
    assert (tmp_path / "extracted/part_0001.csv").exists()
    assert (tmp_path / "extracted/part_0002.csv").exists()

    # Verify extracted content
    content = (
        tmp_path / "extracted/part_0001.csv"
    ).read_text()

    assert "INV-001,100" in content

    # No temporary download should remain
    assert not (tmp_path / "sales.zip.tmp").exists()
