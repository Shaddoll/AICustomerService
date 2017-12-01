import base64
import boto3
import json
import time

expiration = 900
db = boto3.resource("dynamodb")
context_table = db.Table("Context")

def lambda_handler(event, context):
    for record in event['Records']:
        #Kinesis data is base64 encoded so decode here
        payload=base64.b64decode(record["kinesis"]["data"])
        print payload
        # verify payload
        try:
            context = json.loads(payload)
            userId = context["userId"]
            uuid = record["kinesis"]["sequenceNumber"]
            context_table.put_item(
                Item={
                    "userId": userId,
                    "uuid": uuid,
                    "ttl": long(time.time()) + expiration,
                    "eventType": "GENERAL",
                    "metadata": {
                        "title": context["title"],
                        "promptText": "You have a new assignment.",
                        "actions": [
                            {
                                "title": "Ignore",
                                "message": "I'm not going to do it now."
                            },
                            {
                                "title": "Accept",
                                "message": "I'm going to do it."
                            }
                        ]
                    }
                }
            )
        except:
            pass
            #return {"status": "error", "message": "Invalid data content."}
    return {"status": "success", "message": "OK!"}