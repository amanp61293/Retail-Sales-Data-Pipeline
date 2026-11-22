-- Retail Sales Data Pipeline
-- Read-only Snowflake diagnostics retained from exploratory worksheets.
-- Not required for normal GitHub Actions execution.
-- All metrics are dynamic; do not hardcode earlier snapshot counts.

USE WAREHOUSE RETAIL_SALES_WH;

-- 1. Raw dataset overview
SELECT
    COUNT(*) AS total_records,
    COUNT(DISTINCT invoice_id) AS unique_invoices,
    MIN(ordered_on) AS earliest_date,
    MAX(ordered_on) AS latest_date,
    COUNT_IF(category_code IS NULL) AS missing_categories,
    COUNT_IF(sales_bottles < 0 OR sales_dollars < 0 OR sales_liters < 0)
        AS negative_records,
    SUM(sales_dollars) AS total_net_sales
FROM RETAIL_SALES_DB.RAW.LIQUOR_SALES;

-- 2. Raw versus staging reconciliation
SELECT
    'RAW' AS layer,
    COUNT(*) AS row_count,
    SUM(sales_dollars) AS net_sales
FROM RETAIL_SALES_DB.RAW.LIQUOR_SALES
UNION ALL
SELECT
    'STAGING' AS layer,
    COUNT(*) AS row_count,
    SUM(sales_dollars) AS net_sales
FROM RETAIL_SALES_DB.STAGING.STG_LIQUOR_SALES;

-- 3. Fact and dimension join cardinality / missing dimension references
SELECT
    COUNT(*) AS joined_rows,
    SUM(f.sales_dollars) AS joined_net_sales,
    COUNT_IF(s.store_no IS NULL) AS missing_stores,
    COUNT_IF(p.product_key IS NULL) AS missing_products,
    COUNT_IF(d.date_key IS NULL) AS missing_dates
FROM RETAIL_SALES_DB.ANALYTICS.FACT_SALES AS f
LEFT JOIN RETAIL_SALES_DB.ANALYTICS.DIM_STORE AS s
    ON f.store_no = s.store_no
LEFT JOIN RETAIL_SALES_DB.ANALYTICS.DIM_PRODUCT AS p
    ON f.product_key = p.product_key
LEFT JOIN RETAIL_SALES_DB.ANALYTICS.DIM_DATE AS d
    ON f.date_key = d.date_key;

-- 4. Repeated invoice-product pairs: investigation only, not proof of errors
SELECT invoice_id, item_no, COUNT(*) AS occurrences
FROM RETAIL_SALES_DB.RAW.LIQUOR_SALES
GROUP BY invoice_id, item_no
HAVING COUNT(*) > 1
ORDER BY occurrences DESC
LIMIT 20;

-- 5. Fully identical raw records, including legitimate repetitions
SELECT HASH(*) AS row_hash, COUNT(*) AS occurrences
FROM RETAIL_SALES_DB.RAW.LIQUOR_SALES
GROUP BY HASH(*)
HAVING COUNT(*) > 1
ORDER BY occurrences DESC;

-- 6. Ingestion audit trail
SELECT batch_id, loaded_at, row_count, total_sales, data_hash
FROM RETAIL_SALES_DB.RAW.INGESTION_HISTORY
ORDER BY loaded_at DESC;

-- 7. Tableau reporting view reconciliation
SELECT
    COUNT(*) AS reporting_rows,
    SUM(transaction_lines) AS source_records,
    SUM(net_sales) AS net_sales,
    SUM(net_bottles) AS net_bottles,
    COUNT(DISTINCT store_no) AS active_stores,
    SUM(negative_records) AS negative_records
FROM RETAIL_SALES_DB.ANALYTICS.VW_TABLEAU_SALES;
