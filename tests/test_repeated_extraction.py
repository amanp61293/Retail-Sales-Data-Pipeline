
import io
import zipfile
from unittest.mock import Mock, patch

from scripts import extract_data


def test_repeated_extraction(tmp_path, monkeypatch):
    monkeypatch.setattr(extract_data, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(extract_data, "ZIP_FILE", tmp_path / "sales.zip")
    monkeypatch.setattr(extract_data, "EXTRACT_DIR", tmp_path / "extracted")

    # Create a small ZIP archive
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("part_0001.csv", "id,amount\n1,100\n")
        archive.writestr("part_0002.csv", "id,amount\n2,200\n")

    zip_bytes = buffer.getvalue()

    def mock_response():
        response = Mock()
        response.raise_for_status.return_value = None
        response.iter_content.return_value = [zip_bytes]
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=None)
        return response

    with patch(
        "scripts.extract_data.requests.get",
        side_effect=lambda *args, **kwargs: mock_response()
    ):
        # First extraction
        extract_data.download_data()

        # Add a file that should not survive the next extraction
        (tmp_path / "extracted" / "outdated.csv").write_text("old")

        # Second extraction
        extract_data.download_data()

    extracted_files = sorted(
        file.name for file in (tmp_path / "extracted").glob("*.csv")
    )

    assert extracted_files == ["part_0001.csv", "part_0002.csv"]

    assert (
        tmp_path / "extracted" / "part_0001.csv"
    ).read_text() == "id,amount\n1,100\n"

    assert not (tmp_path / "sales.zip.tmp").exists()
