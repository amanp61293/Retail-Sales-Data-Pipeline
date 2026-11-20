
SELECT
    d.year,
    d.month,
    d.month_name,
    COUNT(DISTINCT f.invoice_id) AS total_invoices,
    SUM(f.sales_bottles) AS total_bottles,
    SUM(f.sales_dollars) AS net_sales
FROM {{ ref('fact_sales') }} f
JOIN {{ ref('dim_date') }} d
    ON f.date_key = d.date_key
GROUP BY
    d.year,
    d.month,
    d.month_name
ORDER BY
    d.year,
    d.month
