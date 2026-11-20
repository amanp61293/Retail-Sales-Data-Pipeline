
WITH staging_metrics AS (
    SELECT
        COUNT(*) AS row_count,
        SUM(sales_dollars) AS total_sales,
        SUM(sales_bottles) AS total_bottles,
        SUM(sales_liters) AS total_liters,
        SUM(sales_gallons) AS total_gallons,
        COUNT_IF(
            sales_bottles < 0
            OR sales_dollars < 0
            OR sales_liters < 0
        ) AS negative_records
    FROM {{ ref('stg_liquor_sales') }}
),

fact_metrics AS (
    SELECT
        COUNT(*) AS row_count,
        SUM(sales_dollars) AS total_sales,
        SUM(sales_bottles) AS total_bottles,
        SUM(sales_liters) AS total_liters,
        SUM(sales_gallons) AS total_gallons,
        COUNT_IF(
            sales_bottles < 0
            OR sales_dollars < 0
            OR sales_liters < 0
        ) AS negative_records
    FROM {{ ref('fact_sales') }}
)

SELECT *
FROM staging_metrics s
CROSS JOIN fact_metrics f
WHERE s.row_count = 0
   OR s.row_count <> f.row_count
   OR s.total_sales IS DISTINCT FROM f.total_sales
   OR s.total_bottles IS DISTINCT FROM f.total_bottles
   OR ABS(s.total_liters - f.total_liters) > 0.0001
   OR ABS(s.total_gallons - f.total_gallons) > 0.0001
   OR s.negative_records IS DISTINCT FROM f.negative_records
