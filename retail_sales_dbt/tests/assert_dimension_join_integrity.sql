
WITH fact_metrics AS (
    SELECT
        COUNT(*) AS row_count,
        SUM(sales_dollars) AS total_sales
    FROM {{ ref('fact_sales') }}
),

joined_metrics AS (
    SELECT
        COUNT(*) AS row_count,
        SUM(f.sales_dollars) AS total_sales,
        COUNT_IF(s.store_no IS NULL) AS unmatched_stores,
        COUNT_IF(p.product_key IS NULL) AS unmatched_products,
        COUNT_IF(d.date_key IS NULL) AS unmatched_dates
    FROM {{ ref('fact_sales') }} f

    LEFT JOIN {{ ref('dim_store') }} s
        ON f.store_no = s.store_no

    LEFT JOIN {{ ref('dim_product') }} p
        ON f.product_key = p.product_key

    LEFT JOIN {{ ref('dim_date') }} d
        ON f.date_key = d.date_key
)

SELECT *
FROM fact_metrics f
CROSS JOIN joined_metrics j
WHERE f.row_count <> j.row_count
   OR f.total_sales IS DISTINCT FROM j.total_sales
   OR j.unmatched_stores > 0
   OR j.unmatched_products > 0
   OR j.unmatched_dates > 0
