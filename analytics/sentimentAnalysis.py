import json
import boto3
import urllib.parse
import requests
from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_understanding_v1 import Features, SentimentOptions

s3 = boto3.resource("s3")
bucket_name = 'ai-customer-group6-photos'

def lambda_handler(event, context):
    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    try:
        # response = s3.get_object(Bucket=bucket, Key=key)
        content_object = s3.Object(bucket, key)
        file_content = content_object.get()['Body'].read().decode('utf-8')
        json_content = json.loads(file_content)
        print(json_content)
        content = json_content['messages']
        userid = json_content['userId']
    except Exception as e:
        print(e)

    #get user utterances, whose index is even in content
    user_utterances = ""
    for i in range(len(content)):
        if (i % 2 == 0):
            user_utterances = user_utterances + content[i] + " "

    print(user_utterances)

    nlu = NaturalLanguageUnderstandingV1(
        username="931cc3a6-d39a-40bd-8f7f-6c175d080c99",
        password="mc8LTve2zPIh",
        version="2017-02-27")
    
    response = nlu.analyze(
        # url="www.wsj.com/news/markets",
        #  text="I'm unhappy with that",
        text = user_utterances,
        features=Features(sentiment=SentimentOptions())
            # Sentiment options
    )
    
    #event['Records'][0]['s3']['object']['key'] : file name
    # file_name = event['Records'][0]['s3']['object']['key'].split('.')[0]
    data = {'uid': userid, 'label':response['sentiment']['document']['label'], 'score':response['sentiment']['document']['score']}
    print(data)
    r = requests.post("http://160.39.139.216:3000/sentiment", data)
    print(r)