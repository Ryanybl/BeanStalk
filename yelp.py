import json
import boto3
import logging
import requests
import time

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
dynamodb = boto3.client('dynamodb')



def getRestaurants():
    headers = {'Authorization' : 'Bearer 5ypin6mIj_0oTH9HwyKa3OVa2cmfAg52_MKbUZp9y6271dWQI7JogdUJ0bWo7v9lGRKcKdOUeObKXVInwNj4I_BPLrl5KjYt6ABtQd2BU4vBGIcEmHx1x9VtKlhlYXYx'}
    cuisineTypes = ['chinese', 'korean', 'american', 'mexican', 'japanese', 'indian', 'thai']

    for cuisineType in cuisineTypes:
        params = {
            "term": cuisineType + " restaurants",
            "location": "Manhattan",
            "limit": 50,
            "offset": 0
        }
        for i in range(0,200,50):
            params["offset"] = i
            response = requests.get("https://api.yelp.com/v3/businesses/search", headers=headers, params=params)
            res_json = response.json()
            logger.debug("returned response:" + str(res_json))
            uploadItems(res_json, cuisineType)

def uploadItems(data, cuisineType):
    for restaurant in data["businesses"]:
        logger.debug(restaurant)
        address = ""
        for a in ["address1","address2","address3"]:
            add = restaurant["location"][a]
            if add:
                address += add + " "
        address = address.strip()
        coordinates = str(restaurant["coordinates"]["latitude"]) + "," + str(restaurant["coordinates"]["longitude"])
        dynamodb.put_item(TableName='yelp-restaurants', Item={
            'business_id': {"S": restaurant["id"]},
            'name': {"S": restaurant["name"]},
            'address': {"S": address},
            'coordinates': {"S": coordinates},
            'review_count': {"N": str(restaurant["review_count"])},
            'rating': {"N": str(restaurant["rating"])},
            'zip_code': {"N": str(restaurant["location"]["zip_code"])},
            "city": {"S": restaurant["location"]["city"]},
            "cuisineType": {"S": cuisineType},
            "insertedAtTimestamp": {"N": str(time.time())}
        })




def lambda_handler(event, context):
    getRestaurants()
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
