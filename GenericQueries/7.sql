--7. Get global services where region code == global - this will have Savings Plan and CK Discounts = sp_and_discount_costs

SELECT 

CASE 
    WHEN bill_billing_entity = 'AWS Marketplace'
    THEN 'AWS Marketplace'
    WHEN (product_servicecode IS NULL OR product_servicecode = '')
    THEN line_item_product_code
    ELSE product_servicecode
END AS service,

-- to ensure region is global (if region column is NULL)
-- product_region_code, "product_from_region_code", "product_to_region_code",

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

-- Region filter (Set to Global)
product_region_code is NULL

-- Only 2 accounts
-- AND line_item_usage_account_id IN (
--     '65**********',
--     '65**********'
-- )

AND DATE(at_timezone(line_item_usage_start_date,'UTC')) BETWEEN DATE '2026-01-01' AND DATE '2026-01-31'

GROUP BY 1
;
