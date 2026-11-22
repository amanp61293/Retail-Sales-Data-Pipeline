
WITH expected_fact AS (
    SELECT
        invoice_id,
        store_no,

        SHA2(CONCAT_WS('|',
            TO_VARCHAR(item_no),
            COALESCE(TO_VARCHAR(category_code), 'UNKNOWN'),
            TO_VARCHAR(vendor_number),
            TO_VARCHAR(bottle_volume_ml)
        ), 256) AS product_key,

        TO_NUMBER(
            TO_CHAR(ordered_on, 'YYYYMMDD')
        ) AS date_key,

        state_bottle_cost,
        state_bottle_retail,
        sales_bottles,
        sales_dollars,
        sales_liters,
        sales_gallons,
        COUNT(*) AS occurrence_count

    FROM {{ ref('stg_liquor_sales') }}
    GROUP BY ALL
),

actual_fact AS (
    SELECT
        invoice_id,
        store_no,
        product_key,
        date_key,
        state_bottle_cost,
        state_bottle_retail,
        sales_bottles,
        sales_dollars,
        sales_liters,
        sales_gallons,
        COUNT(*) AS occurrence_count

    FROM {{ ref('fact_sales') }}
    GROUP BY ALL
),

missing_records AS (
    SELECT * FROM expected_fact
    EXCEPT
    SELECT * FROM actual_fact
),

unexpected_records AS (
    SELECT * FROM actual_fact
    EXCEPT
    SELECT * FROM expected_fact
)

SELECT * FROM missing_records

UNION ALL

SELECT * FROM unexpected_records
