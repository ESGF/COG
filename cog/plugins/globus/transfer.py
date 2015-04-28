'''
Module to interact with Globus Online ("GO") data transfer services.

@author: Luca Cinquini
'''

from datetime import datetime, timedelta
from globusonline.transfer.api_client import Transfer
from globusonline.transfer.api_client import TransferAPIClient
import os

ACCESS_TOKEN_FILE = ".goauth-token.secret"
DOWNLOAD_SCRIPT = "download.py"

def generateGlobusDownloadScript(download_map):

    print "Generating script for downloading files: "
    print download_map

    # read script 'download.py' located in same directory as this module
    scriptFile = os.path.join(os.path.dirname(__file__), DOWNLOAD_SCRIPT)
    with open(scriptFile, 'r') as f:
        script = f.read().strip()
    script = script.replace('{}##GENDPOINTDICT##', str(download_map))

    return script
    

def get_access_token():
    '''Utility function to read an access_token for a client portal that is not registered with Globus Online.'''
    
    filepath = os.path.join(os.path.expanduser("~"), ACCESS_TOKEN_FILE)
    
    try:
        with open(filepath, 'r') as f:
            access_token = f.read().strip()
            return access_token
    except IOError:
        print "Access token file not found: %s" % filepath
        return None


def submiTransfer(username, access_token, source_endpoint, source_files, target_endpoint, target_directory):
    '''
    Method to submit a data transfer request to Globus Online.
    '''
    
    # instantiate GO client
    goapi_client = TransferAPIClient(username, goauth=access_token)
        
    # target_endpoint can be automatically activated using cached credentials
    code, reason, result = goapi_client.endpoint_autoactivate(target_endpoint, if_expires_in=600)
    print "Target Endpoint Activation: : %s (%s)" % (result["code"], result["message"])
        
    # obtain a submission id from Globus Online
    code, message, data = goapi_client.transfer_submission_id()
    submission_id = data["value"]
    print "Obtained transfer submission id: %s" % submission_id
    
    # maximum time for completing the transfer
    deadline = datetime.utcnow() + timedelta(days=10)
    
    # create a transfer request
    transfer_task = Transfer(submission_id, source_endpoint, target_endpoint, deadline)
    for source_file in source_files:
        source_directory, filename = os.path.split(source_file)
        target_file = os.path.join(target_directory, filename) 
        transfer_task.add_item(source_file, target_file)
    
    # submit the transfer request
    code, reason, data = goapi_client.transfer(transfer_task)
    task_id = data["task_id"]
    print "Submitted transfer task with id: %s" % task_id
    
    return task_id