
import boto3

AWS_PROFILE = "retail-pipeline"
AWS_REGION = "us-east-2"

BUCKET_NAME = "retail-sales-pipeline-2026-202518311382-us-east-2-an"


def test_connection():
    # Use existing AWS CLI credentials
    session = boto3.Session(
        profile_name=AWS_PROFILE,
        region_name=AWS_REGION
    )

    s3 = session.client("s3")

    # Check whether the bucket exists and is accessible
    s3.head_bucket(Bucket=BUCKET_NAME)

    print("Successfully connected to AWS S3!")
    print(f"Bucket: {BUCKET_NAME}")
    print(f"Region: {AWS_REGION}")


if __name__ == "__main__":
    test_connection()
