
SELECT

CASE WHEN (product_servicecode IS NULL OR product_servicecode = '')
    THEN line_item_product_code
    ELSE product_servicecode
END AS service,

-- If need Daily Granularity
-- DATE(at_timezone(line_item_usage_start_date,'UTC')) AS usage_date,

-- If need Group By Name Tag
-- COALESCE(
--     NULLIF(resource_tags_user_name, ''),
--     'UNTAGGED'
-- ) AS tag_name,

-- Columns for debugging, can be removed
-- line_item_product_code, 
-- product_usagetype, 
-- product_operation, 
-- line_item_line_item_type,

-- Unblended Cost upto two decimal place
ROUND(SUM(line_item_unblended_cost),2) AS cost

FROM "db_name"."table_name" 
WHERE

COALESCE(
        NULLIF(product_servicecode, ''),
        line_item_product_code
    ) = 'AmazonEC2'

-- Explicit exclusions (extra safety)
AND COALESCE(
    NULLIF(product_servicecode, ''),
    line_item_product_code
) NOT IN ('AWSDataTransfer', 'AmazonVPC')

-- Region filter (change if needed)
-- AND product_region_code = 'ap-south-1'

-- Only 2 accounts
-- AND line_item_usage_account_id IN (
--     '65**********',
--     '65**********'
-- )

-- for EBS
-- AND (line_item_operation LIKE 'CreateVolume%' OR line_item_operation = 'CreateSnapshot')

-- for NatGatway
-- AND line_item_operation LIKE '%NatGateway'

-- for EC2 Running Hour
-- AND line_item_operation LIKE 'RunInstance%'

AND line_item_line_item_type != 'SavingsPlanNegation'
AND DATE(at_timezone(line_item_usage_start_date,'UTC')) BETWEEN DATE '2026-01-01' AND DATE '2026-01-31'
Group By 1;
