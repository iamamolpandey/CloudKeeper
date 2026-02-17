SELECT 

CASE 
    WHEN (product_servicecode IS NULL OR product_servicecode = '')
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

ROUND(SUM(line_item_unblended_cost),2) AS spneg_costs

FROM "db_name"."table_name" 
WHERE 

-- Only SavingsPlanNegation Choosen
line_item_line_item_type = 'SavingsPlanNegation'

-- Region filter (change if needed)
-- AND product_region_code = 'ap-south-1'

-- Only 2 accounts
-- AND line_item_usage_account_id IN (
--     '65**********',
--     '65**********'
-- )

AND DATE(at_timezone(line_item_usage_start_date,'UTC')) BETWEEN DATE '2026-01-01' AND DATE '2026-01-31'

group by 1;
