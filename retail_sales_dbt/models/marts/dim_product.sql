
WITH product_records AS (
    SELECT
        item_no,
        product_description,
        category_code,
        category_name,
        vendor_number,
        vendor_name,
        bottle_volume_ml,
        pack,
        ordered_on
    FROM {{ ref('stg_liquor_sales') }}
),

ranked_products AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY
                item_no,
                category_code,
                vendor_number,
                bottle_volume_ml
            ORDER BY
                ordered_on DESC,
                product_description,
                category_name,
                vendor_name,
                pack
        ) AS row_num
    FROM product_records
)

SELECT
    SHA2(CONCAT_WS('|',
        TO_VARCHAR(item_no),
        COALESCE(TO_VARCHAR(category_code), 'UNKNOWN'),
        TO_VARCHAR(vendor_number),
        TO_VARCHAR(bottle_volume_ml)
    ), 256) AS product_key,
    item_no,
    product_description,
    category_code,
    category_name,
    vendor_number,
    vendor_name,
    bottle_volume_ml,
    pack
FROM ranked_products
WHERE row_num = 1
