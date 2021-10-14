import boto3
import datetime
import dateutil.parser
import json
import logging
import math
import os
import re
import time

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def get_slots(intent_request):
    return intent_request['currentIntent']['slots']

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }

def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }
    return response

def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }

def lambda_handler(event, context):
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('Event received:{}'.format(event))
    
    intent_name = event['currentIntent']['name']
    session_attributes = event["sesstion_attributes"] if "sesstion_attributes" in event  else {}
    if intent_name == 'DininSuggestionsIntent':
        return dining_suggestion_intent(event)
    else:
        return delegate(session_attributes, event['currentIntent']['slots'])
    
    return dispatch(event)

def dining_suggestion_intent(intent_request):
    city = get_slots(intent_request)["city"]
    cuisineType = get_slots(intent_request)["cuisineType"]
    partyNumber = get_slots(intent_request)["partyNumber"]
    date = get_slots(intent_request)["date"]
    reservationTime = get_slots(intent_request)["reservationTime"]
    phoneNumber = get_slots(intent_request)["phoneNumber"]
    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':
        slots = get_slots(intent_request)

        validation_result = validate_dining_suggestion(city, cuisineType, partyNumber, date, reservationTime, phoneNumber)

        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])

        if intent_request['sessionAttributes'] is not None:
            output_session_attributes = intent_request['sessionAttributes']
        else:
            output_session_attributes = {}

        return delegate(output_session_attributes, get_slots(intent_request))

    phoneNumber = clean_phone(phoneNumber)
    msg = {
        "cuisineType": cuisineType,
        "city": city,
        "phoneNumber": phoneNumber,
        "partyNumber": partyNumber,
        "date": date,
        "reservationTime": reservationTime
    }

    sqs_client = boto3.client("sqs", region_name="us-east-1")
    response = sqs_client.send_message(
        QueueUrl="https://sqs.us-east-1.amazonaws.com/685457686325/Q1",
        MessageBody=json.dumps(msg))

    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Thank you! You will recieve suggestion shortly'})

def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False

def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')

def clean_phone(phoneNumber):
    phoneNumber = re.sub(r'[^0-9]', "", phoneNumber)
    return phoneNumber
def isvalid_phone(phoneNumber):
    if len(phoneNumber) > 11:
        return False
    if len(phoneNumber) == 11 and phoneNumber[0] != '1':
        return False
    if len(phoneNumber) != 10:
        return False
    return True

def validate_dining_suggestion(city, cuisineType, num_people, date, reservationTime, phoneNumber):
    cities = ['new york', 'manhattan']
    if city is not None and city.lower() not in cities:
        return build_validation_result(False,
                                       'city',
                                       'We currently do not support {} as a valid destination. Can you try a different city?'.format(city))

    cuisineTypes = ['chinese', 'korean', 'american', 'mexican', 'japanese', 'indian', 'thai']
    if cuisineType is not None and cuisineType.lower() not in cuisineTypes:
        return build_validation_result(False,
                                       'cuisineType',
                                       '{} cuisineType not available. Please try another.'.format(cuisineType))

    if num_people is not None:
        num_people = int(num_people)
        if num_people > 20 or num_people < 1:
            return build_validation_result(False,
                                           'partyNumber',
                                           'Maximum 20 people allowed. Try again')

    if date is not None:
        if not isvalid_date(date):
            return build_validation_result(False, 'date',
                                           'I did not understand that, what date would you like to book?')
        if datetime.datetime.strptime(date, '%Y-%m-%d').date() < datetime.date.today():
            return build_validation_result(False, 'date',
                                           'Reservations must be scheduled for future only.  Can you try a different '
                                           'date?')

    if reservationTime is not None:
        if len(reservationTime) != 5:
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'reservationTime', None)

        hour, minute = reservationTime.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)

        date = datetime.datetime.strptime(date, "%Y-%m-%d").replace(hour=hour,minute=minute)
        if date < datetime.datetime.now():
            return build_validation_result(False, 'reservationTime',
                                           'Reservations must be scheduled for future only.  Can you try a different '
                                           'time?')

    if phoneNumber is not None:
        phoneNumber = clean_phone(phoneNumber)
        if not isvalid_phone(phoneNumber):
            return build_validation_result(False, 'phoneNumber','Invalid phone number')

    return build_validation_result(True, None, None)