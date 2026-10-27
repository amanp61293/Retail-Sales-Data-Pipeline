
from pathlib import Path

import boto3

AWS_PROFILE = "retail-pipeline"
AWS_REGION = "us-east-2"
BUCKET_NAME = "retail-sales-pipeline-2026-202518311382-us-east-2-an"


def upload_file(file_path, s3_key):
    file_path = Path(file_path)

    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    session = boto3.Session(
        profile_name=AWS_PROFILE,
        region_name=AWS_REGION
    )

    s3 = session.client("s3")

    s3.upload_file(
        str(file_path),
        BUCKET_NAME,
        s3_key
    )

    print(f"Successfully uploaded: {file_path.name}")
    print(f"S3 location: s3://{BUCKET_NAME}/{s3_key}")



if __name__ == "__main__":
    data_folder = Path("data/raw/extracted")

    csv_files = sorted(data_folder.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError("No CSV files found to upload")

    print(f"Found {len(csv_files)} CSV files.")

    for file in csv_files:
        s3_key = f"raw/2026/{file.name}"

        upload_file(file, s3_key)

    print("\nAll files uploaded successfully!")

