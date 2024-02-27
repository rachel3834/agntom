import json
import requests
from os import path

def lco_api(request_group, credentials, end_point):
    """Function to communicate with various APIs of the LCO network.
    ur should be a user request in the form of a Python dictionary,
    while end_point is the URL string which
    should be concatenated to the observe portal path to complete the URL.
    Accepted end_points are:
        "requestgroups"
    Accepted methods are:
        POST
    """
    PORTAL_URL = 'https://observe.lco.global/api'

    jur = json.dumps(request_group)

    headers = {'Authorization': 'Token ' + credentials['lco_token']}

    if end_point[0:1] == '/':
        end_point = end_point[1:]
    if end_point[-1:] != '/':
        end_point = end_point+'/'
    url = path.join(PORTAL_URL,end_point)

    response = requests.post(url, headers=headers, json=request_group).json()

    return response

def load_lco_info(file_path):
    """Function to load a user's LCO API token and proposal ID code from a
    local file.  The contents of the file are expected to be JSON, of the form:
    {"submitter": <lco user ID>,
     "proposal_id": <proposal code>,
     "lco_token": <LCO token}
    """

    with open(file_path,'r') as f:
        credentials = json.load(f)

    return credentials
