
USE ROLE RETAIL_PIPELINE_ROLE;
USE WAREHOUSE RETAIL_SALES_WH;

CREATE OR REPLACE VIEW
RETAIL_SALES_DB.ANALYTICS.VW_TABLEAU_SALES AS

SELECT
    DATE_TRUNC('MONTH', d.date_day)::DATE AS sales_month,
    s.store_no,
    s.store_name,
    COALESCE(s.store_city, 'Unknown') AS city,
    COALESCE(s.county_name, 'Unknown') AS county,
    'Iowa' AS state,
    'United States' AS country,
    COALESCE(
        TO_VARCHAR(p.category_code), 'UNKNOWN'
    ) AS category_code,
    CASE
        WHEN p.category_code IS NULL THEN 'Unknown'
        ELSE COALESCE(p.category_name, 'Unknown')
    END AS category_name,

    COUNT(*) AS transaction_lines,
    SUM(f.sales_dollars) AS net_sales,
    SUM(f.sales_bottles) AS net_bottles,
    SUM(f.sales_liters) AS net_liters,
    SUM(f.sales_gallons) AS net_gallons,

    SUM(
        CASE WHEN f.sales_dollars > 0
        THEN f.sales_dollars ELSE 0 END
    ) AS positive_sales,

    SUM(
        CASE WHEN f.sales_dollars < 0
        THEN f.sales_dollars ELSE 0 END
    ) AS negative_sales,

    COUNT_IF(
        f.sales_bottles < 0
        OR f.sales_dollars < 0
        OR f.sales_liters < 0
    ) AS negative_records

FROM RETAIL_SALES_DB.ANALYTICS.FACT_SALES f

JOIN RETAIL_SALES_DB.ANALYTICS.DIM_STORE s
    ON f.store_no = s.store_no

JOIN RETAIL_SALES_DB.ANALYTICS.DIM_PRODUCT p
    ON f.product_key = p.product_key

JOIN RETAIL_SALES_DB.ANALYTICS.DIM_DATE d
    ON f.date_key = d.date_key

GROUP BY ALL;
