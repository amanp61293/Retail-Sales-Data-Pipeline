
-- Retail Sales Data Pipeline
-- Phase 3: Raw Data Loading

-- Select our compute warehouse
USE WAREHOUSE RETAIL_SALES_WH;

-- Internal stage for CSV files
CREATE STAGE IF NOT EXISTS RETAIL_SALES_DB.RAW.LOCAL_SALES_STAGE
    FILE_FORMAT = (
        TYPE = CSV
        SKIP_HEADER = 1
        FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    );

-- Raw sales table
CREATE TABLE IF NOT EXISTS RETAIL_SALES_DB.RAW.LIQUOR_SALES (
    invoice_id VARCHAR(50),
    ordered_on DATE,
    store_no NUMBER(10,0),
    store_name VARCHAR(255),
    store_address VARCHAR(255),
    store_city VARCHAR(100),
    store_zip_code VARCHAR(10),
    county_fips_code VARCHAR(10),
    county_name VARCHAR(100),
    category_code NUMBER(10,0),
    category_name VARCHAR(255),
    vendor_number NUMBER(10,0),
    vendor_name VARCHAR(255),
    item_no NUMBER(10,0),
    im_desc VARCHAR(255),
    pack NUMBER(10,0),
    bottle_volume_ml NUMBER(10,0),
    state_bottle_cost NUMBER(12,2),
    state_bottle_retail NUMBER(12,2),
    sales_bottles NUMBER(10,0),
    sales_dollars NUMBER(14,2),
    sales_liters FLOAT,
    sales_gallons FLOAT
);

-- Load CSV files into the raw table
-- Requires files to be uploaded to LOCAL_SALES_STAGE first
COPY INTO RETAIL_SALES_DB.RAW.LIQUOR_SALES
FROM @RETAIL_SALES_DB.RAW.LOCAL_SALES_STAGE
FILE_FORMAT = (
    TYPE = CSV
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    DATE_FORMAT = 'YYYY-MM-DD'
    EMPTY_FIELD_AS_NULL = TRUE
    NULL_IF = ('')
)
PATTERN = '.*[.]csv'
ON_ERROR = ABORT_STATEMENT;

-- Verify loaded records
SELECT COUNT(*) AS total_records
FROM RETAIL_SALES_DB.RAW.LIQUOR_SALES;
