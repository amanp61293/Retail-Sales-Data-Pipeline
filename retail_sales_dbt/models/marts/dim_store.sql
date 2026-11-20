
WITH store_records AS (
    SELECT
        store_no,
        store_name,
        store_address,
        store_city,
        store_zip_code,
        county_fips_code,
        county_name,
        ordered_on
    FROM {{ ref('stg_liquor_sales') }}
),

latest_store_info AS (
    SELECT
        store_no,
        MAX_BY(store_name, ordered_on) AS store_name,
        MAX_BY(store_address, 
            CASE WHEN store_address IS NOT NULL 
                 THEN ordered_on END) AS store_address,
        MAX_BY(store_city,
            CASE WHEN store_city IS NOT NULL 
                 THEN ordered_on END) AS store_city,
        MAX_BY(store_zip_code,
            CASE WHEN store_zip_code IS NOT NULL 
                 THEN ordered_on END) AS store_zip_code,
        MAX_BY(county_fips_code,
            CASE WHEN county_fips_code IS NOT NULL 
                 THEN ordered_on END) AS county_fips_code,
        MAX_BY(county_name,
            CASE WHEN county_name IS NOT NULL 
                 THEN ordered_on END) AS county_name
    FROM store_records
    GROUP BY store_no
)

SELECT * FROM latest_store_info
