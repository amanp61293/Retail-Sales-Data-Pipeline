
import hashlib
from pathlib import Path

import boto3

AWS_PROFILE = "retail-pipeline"
AWS_REGION = "us-east-2"
BUCKET_NAME = "retail-sales-pipeline-2026-202518311382-us-east-2-an"

DATA_DIR = Path("data/raw/extracted")


def calculate_checksum(file_path):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def verify_uploads():
    session = boto3.Session(
        profile_name=AWS_PROFILE,
        region_name=AWS_REGION
    )

    s3 = session.client("s3")

    csv_files = sorted(DATA_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError("No local CSV files found")

    for file in csv_files:
        s3_key = f"raw/2026/{file.name}"

        local_checksum = calculate_checksum(file)

        response = s3.get_object(
            Bucket=BUCKET_NAME,
            Key=s3_key
        )

        remote_hash = hashlib.sha256()

        try:
            for chunk in response["Body"].iter_chunks(
                chunk_size=1024 * 1024
            ):
                if chunk:
                    remote_hash.update(chunk)
        finally:
            response["Body"].close()

        if local_checksum != remote_hash.hexdigest():
            raise ValueError(
                f"Checksum mismatch: {file.name}"
            )

        print(f"Verified: {file.name}")

    print("\nAll S3 uploads verified successfully!")


if __name__ == "__main__":
    verify_uploads()
