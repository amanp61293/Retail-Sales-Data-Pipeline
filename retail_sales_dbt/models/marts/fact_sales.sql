
SELECT
    invoice_id,
    store_no,

    SHA2(CONCAT_WS('|',
        TO_VARCHAR(item_no),
        COALESCE(TO_VARCHAR(category_code), 'UNKNOWN'),
        TO_VARCHAR(vendor_number),
        TO_VARCHAR(bottle_volume_ml)
    ), 256) AS product_key,

    TO_NUMBER(TO_CHAR(ordered_on, 'YYYYMMDD')) AS date_key,

    state_bottle_cost,
    state_bottle_retail,
    sales_bottles,
    sales_dollars,
    sales_liters,
    sales_gallons

FROM {{ ref('stg_liquor_sales') }}
