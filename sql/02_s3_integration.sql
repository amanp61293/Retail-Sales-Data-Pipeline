
-- Retail Sales Data Pipeline
-- Phase 3: AWS S3 Storage Integration

-- External storage integration
CREATE STORAGE INTEGRATION IF NOT EXISTS RETAIL_SALES_S3_INT
    TYPE = EXTERNAL_STAGE
    STORAGE_PROVIDER = 'S3'
    ENABLED = TRUE
    STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::202518311382:role/RetailSalesSnowflakeS3Role'
    STORAGE_ALLOWED_LOCATIONS = (
        's3://retail-sales-pipeline-2026-202518311382-us-east-2-an/raw/2026/'
    );

-- External S3 stage
CREATE STAGE IF NOT EXISTS RETAIL_SALES_DB.RAW.S3_SALES_STAGE
    URL = 's3://retail-sales-pipeline-2026-202518311382-us-east-2-an/raw/2026/'
    STORAGE_INTEGRATION = RETAIL_SALES_S3_INT
    FILE_FORMAT = (
        TYPE = CSV
        SKIP_HEADER = 1
        FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    );

-- Verify S3 connectivity
-- LIST @RETAIL_SALES_DB.RAW.S3_SALES_STAGE;
