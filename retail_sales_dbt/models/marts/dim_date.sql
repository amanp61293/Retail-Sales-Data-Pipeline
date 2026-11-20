
WITH dates AS (
    SELECT DISTINCT
        ordered_on AS date_day
    FROM {{ ref('stg_liquor_sales') }}
    WHERE ordered_on IS NOT NULL
)

SELECT
    TO_NUMBER(TO_CHAR(date_day, 'YYYYMMDD')) AS date_key,
    date_day,
    YEAR(date_day) AS year,
    QUARTER(date_day) AS quarter,
    MONTH(date_day) AS month,
    MONTHNAME(date_day) AS month_name,
    DAY(date_day) AS day_of_month,
    DAYOFWEEKISO(date_day) AS day_of_week,
    DAYNAME(date_day) AS day_name,
    WEEKISO(date_day) AS week_of_year,
    DAYOFWEEKISO(date_day) IN (6, 7) AS is_weekend
FROM dates
