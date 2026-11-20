
SELECT
    p.category_code,
    CASE
        WHEN p.category_code IS NULL THEN 'Unknown'
        ELSE COALESCE(p.category_name, 'Unknown')
    END AS category_name,
    COUNT(DISTINCT p.item_no) AS unique_products,
    SUM(f.sales_bottles) AS total_bottles,
    SUM(f.sales_dollars) AS net_sales
FROM {{ ref('fact_sales') }} f
JOIN {{ ref('dim_product') }} p
    ON f.product_key = p.product_key
GROUP BY 1, 2
ORDER BY net_sales DESC;
