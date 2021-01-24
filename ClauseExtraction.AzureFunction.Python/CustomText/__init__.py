import logging
import azure.functions as func
import json
import os
import requests
from time import sleep

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        body = json.dumps(req.get_json())
    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )
    
    if body:
        result = compose_response(body)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )


def compose_response(json_data):
    values = json.loads(json_data)['values']
    
    # Prepare the Output before the loop
    results = {}
    results["values"] = []
    
    for value in values:
        output_record = transform_value(value)
        if output_record != None:
            results["values"].append(output_record)
    return json.dumps(results, ensure_ascii=False)

## Perform an operation on a record
def transform_value(value):
    print("##########################################")
    print(value)
    try:
        recordId = value['recordId']
    except AssertionError  as error:
        return None

    # Validate the inputs
    try:         
        assert ('data' in value), "'data' field is required."
        data = value['data']        
        assert ('text' in data), "'text' field is required in 'data' object."
    except AssertionError  as error:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "Error:" + error.args[0] }   ]       
            })

    try:                
        # Core Skill to call Custom Text

        msg = value['data']['text']

        if len(msg) > 25000:
            msg = msg[:25000]

        luis_location = os.environ.get("luis_location")
        luis_api_key = os.environ.get("luis_api_key")
        luis_app_id = os.environ.get("luis_app_id")
        luis_app_slot = os.environ.get("luis_app_slot")

        luis_endpoint_base = f"https://{luis_location}.cognitiveservices.azure.com/luis/prediction/v4.0-preview/documents/apps/{luis_app_id}/slots/{luis_app_slot}/"

        # Return object
        data = {}
        
        luis_extractors = os.environ.get('luis_extractors').split(',') if os.environ.get('luis_extractors') != "" else None

        if luis_extractors != None:
            for ext in luis_extractors:
                data[ext] = []
        
        luis_classifiers = os.environ.get('luis_classifiers').split(',') if os.environ.get('luis_classifiers') != "" else None
        
        if luis_classifiers != None:
            data['class'] = list()
                

        if luis_classifiers != None or luis_extractors != None:            
            results = luis_process(msg, luis_endpoint_base, luis_api_key)
            print("#######################################################")
            print(results)
        
        if luis_extractors != None:
            for key, value in results['prediction']['extractors'].items():
                if key in luis_extractors:
                    data[key] += value

        if luis_classifiers != None:
            for value in results['prediction']['positiveClassifiers']:
                data['class'].append(value)
    

    except ValueError as e:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": f"Could not complete operation for record: {recordId} with error: {str(e)}" }   ]       
            })

    return ({
            "recordId": recordId,
            "data" : data
            })


def luis_process(text, luis_endpoint_base, luis_api_key):
    if text == None:
        return None
    operation_id = luis_start_processing(text, luis_endpoint_base, luis_api_key)
    if luis_check_processing(operation_id, luis_endpoint_base, luis_api_key) == "succeeded":
        return luis_get_result(operation_id, luis_endpoint_base, luis_api_key)
    else:
        return None
        
def luis_start_processing(text, luis_endpoint_base, luis_api_key):
    headers = {
        "Ocp-Apim-Subscription-Key" : luis_api_key,
        "Content-Type" : "application/json"
    }

    data = {
    "query": text
    }

    luis_endpoint_start_processing = f"{luis_endpoint_base}/predictText?log=true&%24expand=classifier%2Cextractor"

    response = requests.post(luis_endpoint_start_processing, data=json.dumps(data), headers=headers)
    return response.json()['operationId']

def luis_check_processing(operation_id, luis_endpoint_base, luis_api_key):
    headers = {
        "Ocp-Apim-Subscription-Key" : luis_api_key
    }

    luis_endpoint_check_result = f"{luis_endpoint_base}/operations/{operation_id}/predictText/status"

    response = requests.get(luis_endpoint_check_result, headers = headers)
    
    while response.json()['status'] not in ('succeeded', 'failed'):
        sleep(1)
        response = requests.get(luis_endpoint_check_result, headers = headers)

    return response.json()['status']

def luis_get_result(operation_id, luis_endpoint_base, luis_api_key):
    headers = {
        "Ocp-Apim-Subscription-Key" : luis_api_key
    }
    luis_endpoint_get_result = f"{luis_endpoint_base}/operations/{operation_id}/predictText"

    return requests.get(luis_endpoint_get_result, headers=headers).json()
    