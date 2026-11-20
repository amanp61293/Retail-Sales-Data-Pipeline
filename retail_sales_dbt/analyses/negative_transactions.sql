SELECT
    d.year,
    d.month,
    d.month_name,
    COUNT(*) AS negative_records,
    SUM(f.sales_bottles) AS net_bottles,
    SUM(f.sales_dollars) AS net_sales
FROM {{ ref('fact_sales') }} f
JOIN {{ ref('dim_date') }} d
    ON f.date_key = d.date_key
WHERE f.sales_bottles < 0
    OR f.sales_dollars < 0
    OR f.sales_liters < 0
GROUP BY 1, 2, 3
ORDER BY 1, 2