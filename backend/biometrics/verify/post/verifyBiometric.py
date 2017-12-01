import base64
import boto3
import uuid
import time

s3 = boto3.resource("s3")
bucket_name = 'ai-customer-group6-photos'
bucket = s3.Bucket(bucket_name)
db = boto3.resource("dynamodb")
photos_table = db.Table("Photos")
tokens_table = db.Table("Tokens")
rek = boto3.client('rekognition')

def lambda_handler(event, context):
    logging_handler(event, context)

    # check user and get a photo from S3
    userId = None
    if event.has_key("userId"):
        userId = event["userId"]
        #userId = '123'
        try:
            db_response = photos_table.get_item(Key={"userId": userId})
            target_path = db_response['Item']['photos'][0]
        except:
            code = 403
            message = 'User photo not found'
            response = {"code": code, "message": message, "fields": "userId"}
            return response
    else:
        message = "UserId not provided."
        code = 500
        response = {"code": code, "message": message, "fields": "userId"}
        return response
    
    # get photo from event
    photo = None
    try:
        photo = base64.b64decode(event["base64Image"])
    except:
        message = "photo binary invalid."
        code = 500
        response = {"code": code, "message": message, "fields": "base64Image"}
        return response
    
    # store the photo into S3
    key = "{}.png".format(uuid.uuid4())
    try:
        bucket.put_object(Key=key, Body=photo)
    except:
        message = "photo storation failed."
        code = 500
        response = {"code": code, "message": message, "fields": ""}
        return response
    
    # compare faces
    rek_response = rek.compare_faces(SimilarityThreshold=70,
                                    SourceImage={'S3Object':{'Bucket':bucket_name,'Name':key}},
                                    TargetImage={'S3Object':{'Bucket':bucket_name,'Name':target_path}})
    if len(rek_response['FaceMatches']) > 0:
        code = 200
        tokenId = "{}".format(uuid.uuid4())
        expiration = 100
        response = {'code': code, 'tokenId': tokenId, 'expiration': expiration}
        photos_table.update_item(Key={"userId": userId}, 
                                UpdateExpression="set #photos=list_append(if_not_exists(#photos, :empty_list), :file)",
                                ExpressionAttributeNames={'#photos': "photos"},
                                ExpressionAttributeValues={':file': [key], ':empty_list': []},
                                ReturnValues="UPDATED_NEW")
        tokens_table.put_item(Item={
                                        "userId": userId,
                                        "tokenId": tokenId,
                                        "ttl": long(time.time()) + expiration
                                    })
    else:
        code = 500
        message = 'Face not matched'
        response = {"code": code, "message": message, "fields": ""}
    
    return response
    
    
def logging_handler(event, context):
    import logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.info('Event{}'.format(event))
    logger.info('Context{}'.format(context))
    return 'Hello World!'