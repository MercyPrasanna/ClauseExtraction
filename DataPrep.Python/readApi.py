import os
import sys
import time
import json
import requests

def readApi(fl):

    #load OCR credentials
    with open('config.json','r') as config_file:
        config = json.load(config_file)

    endpoint = config['endpoint']
    subscription_key = config['apim-key']
    text_recognition_url = endpoint + "/vision/v3.1-preview.1/read/analyze"

    #Read file
    headers = {'Ocp-Apim-Subscription-Key': subscription_key,
            'Content-Type': 'application/octet-stream'}
    img_dat = open(fl, "rb").read()

    #post to OCR engine
    response = requests.post(
        text_recognition_url, headers=headers, data=img_dat)
    response.raise_for_status()


    #poll for results
    # Get the operation location (URL with an ID at the end) from the response
    ocr_txt = {}
    poll = True
    while (poll):
        response_final = requests.get(
            response.headers["Operation-Location"], headers=headers)
        ocr_txt = response_final.json()
        time.sleep(1)
        if ("analyzeResult" in ocr_txt):
            poll = False
        if ("status" in ocr_txt and ocr_txt['status'] == 'failed'):
            poll = False

    #send results
    return(ocr_txt)

#dat = readApi("../dataset/pdfs/_au_cases_act_ACAT_2020_117.pdf")
#print(dat)