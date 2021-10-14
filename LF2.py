import json
import boto3
import logging
import requests
import random
from boto3.dynamodb.conditions import Key


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
db = boto3.client('dynamodb')
sns = boto3.client('sns')

def lambda_handler(event, context):
    # TODO implement
    sqs_client = boto3.client("sqs", region_name="us-east-1")
    messages = sqs_client.receive_message(QueueUrl="https://sqs.us-east-1.amazonaws.com/685457686325/Q1", AttributeNames=['All'])
    logger.debug("messages : " + json.dumps(messages))
    
    if "Messages" not in messages:
        return {
        'statusCode': 200,
        'body': "No messages"
    }
    
    for data in messages["Messages"]:
        response = sqs_client.delete_message(
            QueueUrl='https://sqs.us-east-1.amazonaws.com/685457686325/Q1',
            ReceiptHandle=data["ReceiptHandle"]
        )
        
        data = json.loads(data["Body"])
        cuisineType = data["cuisineType"]
        partyNumber = data["partyNumber"]
        date = data["date"]
        time = data["reservationTime"]
        phoneNumber = data["phoneNumber"]
        
        
        
        searchRes = searchRestaurants(data)
        result_restaurants = getRestaurants(searchRes)
        msg = getMessage(cuisineType, partyNumber, date, time, result_restaurants)
        
        sendMsg(msg, phoneNumber)
    return {
        'statusCode': 200,
        'body': msg
    }

def searchRestaurants(data):
    host = "https://search-restaurants-os4i5xiyde3hwqpiuqaokxl7te.us-east-1.es.amazonaws.com"
    index = 'restaurants'
    logger.debug(data)
    cuisineType = data["cuisineType"]
    url = host + '/' + index + '/_search' + "?q=" + cuisineType
    headers = { "Content-Type": "application/json" }
    auth = ("ryan", "Lyb5739663!")
    response = requests.get(url, headers=headers, auth=auth)
    logger.debug(response.json())
    return response.json()

def sendMsg(msg, phoneNumber):
    if len(phoneNumber) == 10:
        phoneNumber = "+1" + phoneNumber
    elif len(phoneNumber) == 11:
        phoneNumber = "+" + phoneNumber
    sns.publish(
        PhoneNumber= str(phoneNumber),
        Message=msg
    )
    logger.debug("message to send: " + msg)

def getRestaurants(response):
    total = response["hits"]["total"]["value"]
    restaurants = response["hits"]["hits"][:3]
    res = []
    logger.debug(restaurants)
    for restaurant in restaurants:
        response = db.get_item(
            TableName='yelp-restaurants',
            Key={
                'business_id': {
                    'S': restaurant["_source"]["business_id"]
                }
            }
        )
        res.append(response)
    return res

def getMessage(cuisineType, partyNumber, date, time, data):
    msg = "Hello! Here are my " + cuisineType.capitalize() + " restaurant suggestions for " + str(partyNumber) + " people, for " + str(date) + " at " + str(time) + ": "
    for i in range(len(data)):
        item = data[i]["Item"]
        msg += str(i+1) + ". " + item["name"]["S"] + ", located at " + item["address"]["S"] + " "
    msg = msg.strip() + ". Enjoy your meal!”"
    return msg