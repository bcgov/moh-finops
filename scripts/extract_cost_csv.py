import json
import boto3
from datetime import datetime, timedelta
 
# Initialize AWS clients
 
ce_client = boto3.client('ce')  # Cost Explorer client
s3_client = boto3.client('s3')  # S3 client
 
def lambda_handler(event, context):
 
    # Define the S3 bucket where the report will be stored
    s3_bucket_name = 'ec2-dropbox-44'
 
    # Define the time range for the CUR (last 24 hours)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)
 
    # Format the date as YYYY-MM-DD
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
 
    # Name of the CUR report file
    report_filename = f'aws_cur_report_by_service_{start_date_str}_{end_date_str}.json'
 
    try:
        # Fetch the cost and usage data from AWS Cost Explorer, grouped by service
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date_str,
                'End': end_date_str
            },
            Granularity='DAILY',  # or 'HOURLY' for hourly granularity
            Metrics=['BlendedCost', 'UnblendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
 
        # Prepare the data to include service names and costs
 
        report_data = []
 
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                service_name = group['Keys'][0]
                cost_amount = group['Metrics']['BlendedCost']['Amount']
                report_data.append({
                    'service': service_name,
                    'cost_amount': float(cost_amount),
                    'start_date': start_date_str,
                    'end_date': end_date_str
                })
 
        # Upload the formatted data to S3 as a JSON file
 
        s3_client.put_object(
            Bucket=s3_bucket_name,
            Key=f'CUR/{report_filename}',
            Body=json.dumps(report_data, indent=4),
            ContentType='application/json'
        )
        print(f"Successfully uploaded report to s3://{s3_bucket_name}/CUR/{report_filename}")
        return {
            'statusCode': 200,
            'body': json.dumps('Report successfully exported to S3')
        }

    except Exception as e:
        print(f"Error exporting report: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error exporting report')
        }