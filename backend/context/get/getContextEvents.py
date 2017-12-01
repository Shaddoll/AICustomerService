import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
import datetime
import logging

db = boto3.resource("dynamodb")
context_table = db.Table("Context")
expiration = 900

def handler(event, context):
    print(event)
    try:
        userId = event["userId"]
        response = context_table.query(
            KeyConditionExpression=Key('userId').eq(userId)
        )
        events = []
        for item in response['Items']:
            timestamp = datetime.datetime.fromtimestamp(item['ttl'] - expiration).strftime('%Y-%m-%d %H:%M:%S')
            evt = {
                "uuid": item["uuid"],
                "userId": item["userId"],
                "eventType": item["eventType"],
                "metadata": item["metadata"],
                "timestamp": timestamp
            }
            events.append(evt)
        return {"events": events}
    except:
        return {"code": 500, "message": "Error!", "field": "Unknown."}

def logging_handler(event, context):
    import logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.info('Event{}'.format(event))
    logger.info('Context{}'.format(context))
    return 'Hello World!'