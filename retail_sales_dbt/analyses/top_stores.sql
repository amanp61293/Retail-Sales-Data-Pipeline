
SELECT
    s.store_no,
    s.store_name,
    s.store_city,
    COUNT(DISTINCT f.invoice_id) AS total_invoices,
    SUM(f.sales_bottles) AS total_bottles,
    SUM(f.sales_dollars) AS net_sales
FROM {{ ref('fact_sales') }} f
JOIN {{ ref('dim_store') }} s
    ON f.store_no = s.store_no
GROUP BY
    s.store_no,
    s.store_name,
    s.store_city
ORDER BY net_sales DESC
LIMIT 10;
