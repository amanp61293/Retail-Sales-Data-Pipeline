
SELECT
    p.item_no,
    p.product_description,
    p.bottle_volume_ml,
    SUM(f.sales_bottles) AS total_bottles,
    SUM(f.sales_dollars) AS net_sales
FROM {{ ref('fact_sales') }} f
JOIN {{ ref('dim_product') }} p
    ON f.product_key = p.product_key
GROUP BY
    p.item_no,
    p.product_description,
    p.bottle_volume_ml
ORDER BY net_sales DESC
LIMIT 10
