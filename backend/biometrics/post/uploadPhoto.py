import base64
import boto3
import uuid

s3 = boto3.resource("s3")
bucket = s3.Bucket("ai-customer-group6-photos")
db = boto3.resource("dynamodb")
table = db.Table("Photos")

def lambda_handler(event, context):
    # TODO implement
    logging_handler(event, context)
    responseCode = 500
    #response = {"status": responseCode, "message": message}
    photo = None
    userId = None
    if event.has_key("userId"):
        userId = event["userId"]
    else:
        message = "UserId not provided."
        code = 500
        response = {"code": code, "message": message, "fields": "userId"}
        return response
    try:
        photo = base64.b64decode(event["base64Image"])
    except:
        message = "photo binary invalid."
        code = 500
        response = {"code": code, "message": message, "fields": "base64Image"}
        return response
    key = "{}.png".format(uuid.uuid4())
    try:
        bucket.put_object(Key=key, Body=photo)
        table.update_item(Key={"userId": userId}, 
            UpdateExpression="set #photos=list_append(if_not_exists(#photos, :empty_list), :file)",
            ExpressionAttributeNames={'#photos': "photos"},
            ExpressionAttributeValues={':file': [key], ':empty_list': []},
            ReturnValues="UPDATED_NEW")
    except:
        message = "photo storation failed."
        code = 500
        response = {"code": code, "message": message, "fields": ""}
        return response
    status = "200 OK"
    response = {"status": status, "message": "Success!"}
    return response
    
    
def logging_handler(event, context):
    import logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.info('Event{}'.format(event))
    logger.info('Context{}'.format(context))
    return 'Hello World!'