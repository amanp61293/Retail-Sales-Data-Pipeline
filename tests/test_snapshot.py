
import csv
import hashlib
import importlib
import json
import zipfile
from unittest.mock import Mock

import pytest


@pytest.fixture
def snapshot(monkeypatch, tmp_path):
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")

    module = importlib.import_module("scripts.load_snapshot")

    raw_dir = tmp_path / "extracted"
    raw_dir.mkdir()

    monkeypatch.setattr(module, "RAW_DIR", raw_dir)
    monkeypatch.setattr(module, "ZIP_PATH", tmp_path / "data.zip")

    return module


def create_csv(snapshot, header=None, rows=None):
    path = snapshot.RAW_DIR / "part_0001.csv"

    if header is None:
        header = snapshot.COLUMNS

    if rows is None:
        rows = [["1"] * len(snapshot.COLUMNS)]

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(rows)

    with zipfile.ZipFile(snapshot.ZIP_PATH, "w") as archive:
        archive.write(path, arcname=path.name)

    return path


def batch_id(manifest):
    content = json.dumps(
        manifest,
        sort_keys=True,
        separators=(",", ":")
    )

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def test_valid_manifest(snapshot):
    path = create_csv(snapshot)
    manifest = snapshot.build_manifest()

    assert len(manifest) == 1
    assert manifest[0]["filename"] == path.name
    assert manifest[0]["row_count"] == 1
    assert manifest[0]["sha256"] == snapshot.sha256_file(path)


def test_missing_csv(snapshot):
    with pytest.raises(RuntimeError, match="No extracted"):
        snapshot.build_manifest()


def test_invalid_schema(snapshot):
    create_csv(snapshot, header=["invalid_column"])

    with pytest.raises(RuntimeError, match="Unexpected schema"):
        snapshot.build_manifest()


def test_malformed_row(snapshot):
    create_csv(snapshot, rows=[["1", "2"]])

    with pytest.raises(RuntimeError, match="Malformed row"):
        snapshot.build_manifest()


def test_empty_csv(snapshot):
    create_csv(snapshot, rows=[])

    with pytest.raises(RuntimeError, match="Empty CSV"):
        snapshot.build_manifest()


def test_archive_mismatch(snapshot):
    path = create_csv(snapshot)

    with path.open("a", encoding="utf-8") as file:
        file.write("unexpected data")

    with pytest.raises(RuntimeError, match="ZIP contents"):
        snapshot.build_manifest()


def test_repeatable_batch_id(snapshot):
    create_csv(snapshot)

    first = batch_id(snapshot.build_manifest())
    second = batch_id(snapshot.build_manifest())

    assert first == second


def test_changed_snapshot_id(snapshot):
    create_csv(snapshot)
    first = batch_id(snapshot.build_manifest())

    create_csv(
        snapshot,
        rows=[["2"] * len(snapshot.COLUMNS)]
    )

    second = batch_id(snapshot.build_manifest())

    assert first != second


def test_duplicate_rows_preserved(snapshot):
    row = ["1"] * len(snapshot.COLUMNS)

    create_csv(snapshot, rows=[row, row])

    manifest = snapshot.build_manifest()

    assert manifest[0]["row_count"] == 2


def test_s3_checksum_mismatch(snapshot, tmp_path):
    create_csv(snapshot)
    manifest = snapshot.build_manifest()

    s3 = Mock()

    def corrupted_download(bucket, key, filename):
        with open(filename, "wb") as file:
            file.write(b"corrupted data")

    s3.download_file.side_effect = corrupted_download

    with pytest.raises(RuntimeError, match="Checksum mismatch"):
        snapshot.download_snapshot(
            s3,
            manifest,
            "snapshots/test",
            tmp_path
        )


def test_existing_s3_object_mismatch(snapshot):
    create_csv(snapshot)
    manifest = snapshot.build_manifest()

    s3 = Mock()

    s3.head_object.return_value = {
        "Metadata": {"sha256": "incorrect-hash"},
        "ContentLength": manifest[0]["size_bytes"]
    }

    with pytest.raises(RuntimeError, match="Snapshot object mismatch"):
        snapshot.archive_snapshot(
            s3,
            manifest,
            "test-batch"
        )

    s3.upload_file.assert_not_called()
