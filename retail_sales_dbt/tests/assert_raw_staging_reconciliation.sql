
WITH raw_metrics AS (
    SELECT
        COUNT(*) AS row_count,
        SUM(sales_dollars) AS total_sales,
        SUM(sales_bottles) AS total_bottles,
        SUM(sales_liters) AS total_liters,
        SUM(sales_gallons) AS total_gallons,
        COUNT_IF(category_code IS NULL) AS missing_categories,
        COUNT_IF(
            sales_bottles < 0
            OR sales_dollars < 0
            OR sales_liters < 0
        ) AS negative_records
    FROM {{ source('raw', 'liquor_sales') }}
),

staging_metrics AS (
    SELECT
        COUNT(*) AS row_count,
        SUM(sales_dollars) AS total_sales,
        SUM(sales_bottles) AS total_bottles,
        SUM(sales_liters) AS total_liters,
        SUM(sales_gallons) AS total_gallons,
        COUNT_IF(category_code IS NULL) AS missing_categories,
        COUNT_IF(
            sales_bottles < 0
            OR sales_dollars < 0
            OR sales_liters < 0
        ) AS negative_records
    FROM {{ ref('stg_liquor_sales') }}
)

SELECT *
FROM raw_metrics r
CROSS JOIN staging_metrics s
WHERE r.row_count = 0
   OR r.row_count <> s.row_count
   OR r.total_sales IS DISTINCT FROM s.total_sales
   OR r.total_bottles IS DISTINCT FROM s.total_bottles
   OR ABS(r.total_liters - s.total_liters) > 0.0001
   OR ABS(r.total_gallons - s.total_gallons) > 0.0001
   OR r.missing_categories IS DISTINCT FROM s.missing_categories
   OR r.negative_records IS DISTINCT FROM s.negative_records
