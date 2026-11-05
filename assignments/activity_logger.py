import boto3
import os
from datetime import datetime, timezone
from botocore.exceptions import ClientError, BotoCoreError

def log_activity(user_id, action, details=None, ip_address=None):
    """
    Records an audit log entry in Amazon DynamoDB 'ActivityLogs' table.
    Schema:
      - partition key: user_id (String)
      - sort key: event_time (String ISO8601)
      - action (String)
      - details (String or Map)
      - ip_address (String)
    
    Safe & resilient: If DynamoDB is unavailable or not yet created, logs safely
    to standard output without disrupting the user journey.
    """
    table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'ActivityLogs')
    aws_region = os.environ.get('AWS_REGION', 'eu-north-1')
    event_time = datetime.now(timezone.utc).isoformat()

    item = {
        'user_id': str(user_id),
        'event_time': event_time,
        'action': str(action),
        'details': str(details or ''),
    }
    if ip_address:
        item['ip_address'] = str(ip_address)

    # If AWS credentials or instance metadata are present, log to DynamoDB
    try:
        dynamodb = boto3.resource('dynamodb', region_name=aws_region)
        table = dynamodb.Table(table_name)
        table.put_item(Item=item)
        print(f"[ActivityLog - DynamoDB] {action} logged for user_id={user_id}")
    except (ClientError, BotoCoreError, Exception) as e:
        # Fallback graceful logger
        print(f"[ActivityLog - Fallback] (DynamoDB unreachable: {e}) | Event: {action} | user_id={user_id} | time={event_time}")
