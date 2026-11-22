
import csv
import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path

import boto3
import snowflake.connector
from botocore.exceptions import ClientError


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "extracted"
ZIP_PATH = ROOT / "data" / "raw" / "iowa_liquor_sales_2026.zip"

BUCKET = os.environ["S3_BUCKET_NAME"]

RAW_TABLE = "RETAIL_SALES_DB.RAW.LIQUOR_SALES"
CANDIDATE = "RETAIL_SALES_DB.RAW.SNAPSHOT_CANDIDATE"
STAGE = "RETAIL_SALES_DB.RAW.SNAPSHOT_LOAD_STAGE"
AUDIT = "RETAIL_SALES_DB.RAW.INGESTION_HISTORY"

COLUMNS = """
invoice_id ordered_on store_no store_name store_address
store_city store_zip_code county_fips_code county_name
category_code category_name vendor_number vendor_name
item_no im_desc pack bottle_volume_ml state_bottle_cost
state_bottle_retail sales_bottles sales_dollars sales_liters
sales_gallons
""".split()


def sha256_file(path):
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def build_manifest():
    files = sorted(RAW_DIR.glob("*.csv"))

    if not files:
        raise RuntimeError("No extracted CSV files found")

    with zipfile.ZipFile(ZIP_PATH) as archive:
        expected = {
            Path(member.filename).name: member.file_size
            for member in archive.infolist()
            if member.filename.lower().endswith(".csv")
        }

    actual = {file.name: file.stat().st_size for file in files}

    if actual != expected:
        raise RuntimeError("Extracted files do not match ZIP contents")

    manifest = []

    for path in files:
        with path.open(
            encoding="utf-8-sig", newline=""
        ) as file:
            reader = csv.reader(file, strict=True)
            header = next(reader)

            if header != COLUMNS:
                raise RuntimeError(
                    f"Unexpected schema in {path.name}"
                )

            rows = 0

            for row in reader:
                if len(row) != len(COLUMNS):
                    raise RuntimeError(
                        f"Malformed row in {path.name}"
                    )
                rows += 1

        if rows == 0:
            raise RuntimeError(f"Empty CSV: {path.name}")

        manifest.append({
            "filename": path.name,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "row_count": rows
        })

    return manifest


def get_s3_client():
    profile = os.getenv("AWS_PROFILE")

    session = boto3.Session(
        profile_name=profile,
        region_name="us-east-2"
    )

    return session.client("s3")


def archive_snapshot(s3, manifest, batch_id):
    prefix = f"snapshots/2026/{batch_id}"

    for entry in manifest:
        filename = entry["filename"]
        key = f"{prefix}/{filename}"
        path = RAW_DIR / filename

        try:
            response = s3.head_object(
                Bucket=BUCKET,
                Key=key
            )

        except ClientError as error:
            code = error.response["Error"]["Code"]

            if code not in {"404", "NoSuchKey", "NotFound"}:
                raise

            s3.upload_file(
                str(path),
                BUCKET,
                key,
                ExtraArgs={
                    "Metadata": {
                        "sha256": entry["sha256"]
                    }
                }
            )

            print(f"Archived: {filename}")

        else:
            if (
                response["Metadata"].get("sha256")
                != entry["sha256"]
                or response["ContentLength"]
                != entry["size_bytes"]
            ):
                raise RuntimeError(
                    f"Snapshot object mismatch: {filename}"
                )

            print(f"Already archived: {filename}")

    return prefix


def download_snapshot(s3, manifest, prefix, directory):
    paths = []

    for entry in manifest:
        filename = entry["filename"]
        path = directory / filename

        s3.download_file(
            BUCKET,
            f"{prefix}/{filename}",
            str(path)
        )

        if sha256_file(path) != entry["sha256"]:
            raise RuntimeError(
                f"Checksum mismatch: {filename}"
            )

        paths.append(path)
        print(f"Verified S3 download: {filename}")

    return paths


def connect_snowflake():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        role=os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        warehouse="RETAIL_SALES_WH",
        database="RETAIL_SALES_DB",
        schema="RAW",
        authenticator="SNOWFLAKE_JWT",
        private_key_file=os.environ["SNOWFLAKE_KEY_PATH"],
        private_key_file_pwd=os.environ["DBT_KEY_PASSPHRASE"],
        autocommit=True
    )


def get_metrics(cursor, table):
    cursor.execute(f"""
        SELECT
            COUNT(*),
            SUM(sales_dollars),
            COALESCE(COUNT_IF(category_code IS NULL), 0),
            COALESCE(COUNT_IF(
                sales_bottles < 0
                OR sales_dollars < 0
                OR sales_liters < 0
            ), 0),
            HASH_AGG(*)
        FROM {table}
    """)

    return cursor.fetchone()


def load_snapshot(paths, manifest, batch_id):
    expected_rows = sum(
        entry["row_count"] for entry in manifest
    )

    connection = connect_snowflake()
    cursor = connection.cursor()

    try:
        cursor.execute(f"""
            CREATE TEMPORARY STAGE {STAGE}
        """)

        cursor.execute(f"""
            CREATE TEMPORARY TABLE {CANDIDATE}
            LIKE {RAW_TABLE}
        """)

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {AUDIT} (
                batch_id VARCHAR(64),
                loaded_at TIMESTAMP_LTZ,
                row_count NUMBER,
                total_sales NUMBER(38, 2),
                data_hash NUMBER,
                manifest VARIANT
            )
        """)

        for path in paths:
            with path.open("rb") as stream:
                cursor.execute(
                    f"PUT 'file://{path.name}' @{STAGE} "
                    "AUTO_COMPRESS=TRUE OVERWRITE=FALSE",
                    file_stream=stream
                )

                result = cursor.fetchall()

                if not result or any(
                    row[6] != "UPLOADED" for row in result
                ):
                    raise RuntimeError(
                        f"Stage upload failed: {path.name}"
                    )

            print(f"Staged: {path.name}")

        cursor.execute(f"""
            COPY INTO {CANDIDATE}
            FROM @{STAGE}
            FILE_FORMAT = (
                TYPE = CSV
                SKIP_HEADER = 1
                FIELD_OPTIONALLY_ENCLOSED_BY = '"'
                DATE_FORMAT = 'YYYY-MM-DD'
                EMPTY_FIELD_AS_NULL = TRUE
                NULL_IF = ('')
                ERROR_ON_COLUMN_COUNT_MISMATCH = TRUE
            )
            ON_ERROR = ABORT_STATEMENT
        """)

        results = cursor.fetchall()

        if len(results) != len(manifest):
            raise RuntimeError("Unexpected loaded file count")

        if any(row[1] != "LOADED" for row in results):
            raise RuntimeError("One or more files failed to load")

        loaded_rows = sum(int(row[3]) for row in results)

        if loaded_rows != expected_rows:
            raise RuntimeError("COPY row count mismatch")

        cursor.execute(f"""
            SELECT COUNT(*)
            FROM {CANDIDATE}
            WHERE invoice_id IS NULL
               OR TRIM(invoice_id) = ''
               OR ordered_on IS NULL
               OR store_no IS NULL
               OR item_no IS NULL
               OR vendor_number IS NULL
               OR bottle_volume_ml IS NULL
               OR sales_bottles IS NULL
               OR sales_dollars IS NULL
               OR sales_liters IS NULL
        """)

        if cursor.fetchone()[0] != 0:
            raise RuntimeError("Candidate contains invalid records")

        candidate_metrics = get_metrics(cursor, CANDIDATE)

        if candidate_metrics[0] != expected_rows:
            raise RuntimeError("Candidate row count mismatch")

        print(f"Candidate validated: {candidate_metrics}")

        cursor.execute("BEGIN")

        try:
            cursor.execute(f"""
                INSERT OVERWRITE INTO {RAW_TABLE}
                SELECT * FROM {CANDIDATE}
            """)

            published_metrics = get_metrics(cursor, RAW_TABLE)

            if published_metrics != candidate_metrics:
                raise RuntimeError("Published data mismatch")

            cursor.execute(f"""
                INSERT INTO {AUDIT}
                SELECT
                    %s,
                    CURRENT_TIMESTAMP(),
                    %s,
                    %s,
                    %s,
                    PARSE_JSON(%s)
            """, (
                batch_id,
                published_metrics[0],
                published_metrics[1],
                published_metrics[4],
                json.dumps(manifest)
            ))

            cursor.execute("COMMIT")

        except Exception:
            cursor.execute("ROLLBACK")
            raise

        print("Snapshot published successfully")
        print(f"Rows: {published_metrics[0]:,}")
        print(f"Sales: ${published_metrics[1]:,.2f}")
        print(f"Missing categories: {published_metrics[2]}")
        print(f"Negative records: {published_metrics[3]}")
        print(f"Data hash: {published_metrics[4]}")

    finally:
        cursor.close()
        connection.close()


def main():
    manifest = build_manifest()

    manifest_json = json.dumps(
        manifest,
        sort_keys=True,
        separators=(",", ":")
    )

    batch_id = hashlib.sha256(
        manifest_json.encode("utf-8")
    ).hexdigest()

    print(f"Batch ID: {batch_id}")
    print(f"Files: {len(manifest)}")

    s3 = get_s3_client()
    prefix = archive_snapshot(s3, manifest, batch_id)

    with tempfile.TemporaryDirectory() as directory:
        paths = download_snapshot(
            s3, manifest, prefix, Path(directory)
        )

        s3.put_object(
            Bucket=BUCKET,
            Key=f"{prefix}/manifest.json",
            Body=manifest_json.encode("utf-8"),
            ContentType="application/json"
        )

        load_snapshot(paths, manifest, batch_id)


if __name__ == "__main__":
    main()
