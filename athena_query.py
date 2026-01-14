#!/usr/bin/env python3
import boto3
import pandas as pd
import time
from datetime import datetime, timedelta

DATABASE = ''
TABLE = ''
WORKGROUP = 'primary'
Athena_OUTPUT_LOCATION = ''  # Replace with your S3 bucket
DAYS_BACK = 13
TAG_COLUMN = 'resource_tags_user_name'
REGION = 'us-east-1'
OUTPUT_FILE = 'Last9_-_All-Report-Cost-Explorer.xlsx'
TEST_DATE = None  # Set to None to use yesterday's date

def generate_query(database, table, tag_column, days_back, test_date):
    try:
        if test_date:
            ref_date = datetime.strptime(test_date, '%Y-%m-%d').date()
            dates = [(ref_date - timedelta(days=d)).strftime('%Y-%m-%d') for d in range(days_back)]
            case_stmts = [f"SUM(CASE WHEN usage_date = DATE '{d}' THEN line_item_unblended_cost ELSE 0 END) AS day_{i}" 
                          for i, d in enumerate(dates)]
            date_filter = f"BETWEEN DATE '{dates[-1]}' AND DATE '{dates[0]}'"
        else:
            case_stmts = [f"SUM(CASE WHEN usage_date = current_date - INTERVAL '{d+1}' DAY THEN line_item_unblended_cost ELSE 0 END) AS day_{d}" 
                          for d in range(days_back)]
            date_filter = f">= current_date - INTERVAL '{days_back}' DAY AND CAST(line_item_usage_start_date AS DATE) < current_date"
        
        return f"""
SELECT {tag_column}, {', '.join(case_stmts)}
FROM (
    SELECT 
        CONCAT(COALESCE(NULLIF(TRIM({tag_column}), ''), 'UnTagged'), ' ($)') AS {tag_column},
        CAST(line_item_usage_start_date AS DATE) AS usage_date,
        line_item_unblended_cost
    FROM "{database}"."{table}"
    WHERE product_product_family in ('Load Balancer','Load Balancer-Application','Load Balancer-Network')
      AND CAST(line_item_usage_start_date AS DATE) {date_filter}
) t
GROUP BY {tag_column}
ORDER BY {tag_column}"""
    except Exception as e:
        raise Exception(f"Query generation failed: {e}")


def run_query(query, database, region):
    try:
        athena = boto3.client('athena', region_name=region)
    except Exception as e:
        raise Exception(f"AWS connection failed. Check credentials: {e}")
    
    try:
        response = athena.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': database, 'Catalog': 'AwsDataCatalog'},
            WorkGroup=WORKGROUP,
            ResultConfiguration = { 'OutputLocation': Athena_OUTPUT_LOCATION } # Replace with your S3 bucket
        )
        query_id = response['QueryExecutionId']
    except athena.exceptions.InvalidRequestException as e:
        raise Exception(f"Invalid query or database '{database}' not found: {e}")
    except Exception as e:
        raise Exception(f"Failed to start query: {e}")
    
    try:
        while True:
            status = athena.get_query_execution(QueryExecutionId=query_id)
            state = status['QueryExecution']['Status']['State']
            if state == 'SUCCEEDED':
                break
            elif state in ['FAILED', 'CANCELLED']:
                reason = status['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
                raise Exception(f"Query {state}: {reason}")
            time.sleep(2)
    except Exception as e:
        if 'Query' not in str(e):
            raise Exception(f"Query execution check failed: {e}")
        raise
    
    try:
        results, columns, next_token = [], None, None
        while True:
            params = {'QueryExecutionId': query_id, 'MaxResults': 1000}
            if next_token:
                params['NextToken'] = next_token
            response = athena.get_query_results(**params)
            
            if not columns:
                columns = [c['Name'] for c in response['ResultSet']['ResultSetMetadata']['ColumnInfo']]
            
            start = 1 if not results else 0
            results.extend([[f.get('VarCharValue', '') for f in r['Data']] 
                           for r in response['ResultSet']['Rows'][start:]])
            
            next_token = response.get('NextToken')
            if not next_token:
                break
        
        return pd.DataFrame(results, columns=columns)
    except Exception as e:
        raise Exception(f"Failed to fetch query results: {e}")


def format_and_export(df, days_back, test_date, output_file):
    try:
        ref_date = (datetime.strptime(test_date, '%Y-%m-%d').date() if test_date 
                    else datetime.now().date() - timedelta(days=1))
        
        date_cols = {f'day_{d}': (ref_date - timedelta(days=d)).strftime('%d %b %Y') 
                     for d in range(days_back)}
        df = df.rename(columns=date_cols)
        
        df[df.columns[0]] = df[df.columns[0]].replace('', 'UNTAGGED').fillna('UNTAGGED')
        for col in df.columns[1:]:
            df[col] = pd.to_numeric(df[col], errors='coerce').round(2)
        df = df.rename(columns={df.columns[0]: 'TAGS'})
        
        df['Total'] = df.iloc[:, 1:].sum(axis=1).round(2)
        df = df.sort_values('Total', ascending=False).reset_index(drop=True)
        
        cols = ['TAGS'] + list(reversed(df.columns[1:-1].tolist())) + ['Total']
        df = df[cols]
        
        totals_row = ['Total Cost ($)'] + df.iloc[:, 1:-1].sum().round(2).tolist() + [df['Total'].sum().round(2)]
        df.loc[len(df)] = totals_row
    except Exception as e:
        raise Exception(f"Data formatting failed: {e}")
    
    try:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Cost Report', index=False)
            ws = writer.sheets['Cost Report']
            
            for idx in range(1, len(df.columns) + 1):
                ws.column_dimensions[chr(64 + idx)].width = 20
            
            from openpyxl.styles import Font
            for col in range(1, len(df.columns) + 1):
                ws.cell(row=len(df) + 1, column=col).font = Font(bold=True)
            ws.cell(row=1, column=len(df.columns)).font = Font(bold=True)
    except PermissionError:
        raise Exception(f"Cannot write to '{output_file}'. File may be open in Excel. Close it and try again.")
    except Exception as e:
        raise Exception(f"Excel export failed: {e}")
    
    return df


def main():
    if DAYS_BACK < 1:
        raise Exception(f"DAYS_BACK must be >= 1, got {DAYS_BACK}")
    
    query = generate_query(DATABASE, TABLE, TAG_COLUMN, DAYS_BACK, TEST_DATE)
    print(query)
    df = run_query(query, DATABASE, REGION)
    
    if df.empty:
        raise Exception(f"No data found for product in database '{DATABASE}.{TABLE}'")
    
    df = format_and_export(df, DAYS_BACK, TEST_DATE, OUTPUT_FILE)
    print(f"{OUTPUT_FILE}: {len(df)} rows, {len(df.columns)} columns")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Cancelled")
        exit(1)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
