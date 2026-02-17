--3. For all region get S3 costs on a daily basis, separate file per region = s3_costs

SELECT 

product_servicecode, 

-- If need Daily Granularity
-- DATE(at_timezone(line_item_usage_start_date,'UTC')) AS usage_date,

-- If need Group By Name Tag
-- COALESCE(
--     NULLIF(resource_tags_user_name, ''),
--     'UNTAGGED'
-- ) AS tag_name,

ROUND(SUM(line_item_unblended_cost),2) AS cost

FROM "db_name"."table_name"
WHERE 

product_servicecode = 'AmazonS3'

-- Region filter (change if needed)
-- AND product_region_code = 'ap-south-1'

-- Only 2 accounts
-- AND line_item_usage_account_id IN (
--     '65**********',
--     '65**********'
-- )

AND DATE(at_timezone(line_item_usage_start_date,'UTC')) BETWEEN DATE '2026-01-01' AND DATE '2026-01-31'

GROUP BY 1
;
