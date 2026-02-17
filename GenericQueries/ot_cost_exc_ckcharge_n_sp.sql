--4. For all region get other services costs region wise, separate file per region = ot_costs
-- except ec2,s3,DataTransfer

SELECT 

-- if all service cost clubed togather  (remove grouped by in that case)  
'other_service' AS service,

-- each service wise cost    
-- CASE 
--     WHEN bill_billing_entity = 'AWS Marketplace'
--     THEN 'AWS Marketplace'
--     WHEN (product_servicecode IS NULL OR product_servicecode = '')
--     THEN line_item_product_code
--     ELSE product_servicecode
-- END AS service,

-- If need Daily Granularity
-- DATE(at_timezone(line_item_usage_start_date,'UTC')) AS usage_date,

-- If need Group By Name Tag
-- COALESCE(
--     NULLIF(resource_tags_user_name, ''),
--     'UNTAGGED'
-- ) AS tag_name,

ROUND(SUM(line_item_unblended_cost),2) AS ot_cost

FROM "db_name"."table_name"
WHERE 

COALESCE(
    NULLIF(product_servicecode, ''),
    line_item_product_code
) NOT IN ('AmazonS3', 'AmazonEC2', 'AWSDataTransfer','ComputeSavingsPlans','CKCharges')

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
