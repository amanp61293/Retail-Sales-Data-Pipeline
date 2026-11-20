
SELECT
    item_no,
    category_code,
    vendor_number,
    bottle_volume_ml,
    COUNT(*) AS record_count

FROM {{ ref('dim_product') }}

GROUP BY
    item_no,
    category_code,
    vendor_number,
    bottle_volume_ml

HAVING COUNT(*) > 1
