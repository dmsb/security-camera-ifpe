import configparser
import os
from google.oauth2 import service_account
import requests
from google.auth.transport.requests import Request
import json
from googleapiclient.discovery import build
from threading import Thread

def delete_drive_file(service, folder):
   result = service.files().delete(fileId=folder['id'])
   result.execute()
   print(result)

def start_files_deletion(service, pageToken=None):
   drive_response = service.files().list(
      q="'security-camera-ifpe@security-camera-363502.iam.gserviceaccount.com' in owners",
      pageToken=pageToken).execute()

   for folder in drive_response['files']:
      delete_drive_file(service, folder)
      # Thread(target=delete_drive_file, args=(service, folder,)).start()
   
   if (hasattr(drive_response, 'nextPageToken') and drive_response['nextPageToken']):
      start_files_deletion(service, drive_response['nextPageToken'])
      # Thread(target=start_files_deletion, args=(service, drive_response['nextPageToken'],)).start()


def clear_drive():

   config = configparser.ConfigParser()
   config.read(os.path.abspath(os.path.join(".ini")))

   DRIVE_SCOPE = ['https://www.googleapis.com/auth/drive']
   SERVICE_ACCOUNT_FILE = 'google-auth/google_service_account_private_key.json'

   credentials = service_account.Credentials.from_service_account_file(
         SERVICE_ACCOUNT_FILE, scopes=DRIVE_SCOPE)

   credentialsWithSuject = credentials.with_subject(config['GENERAL']['GOOGLE_DRIVE_SERVICE_ACCOUNT_EMAIL'])
   request = Request()
   credentialsWithSuject.refresh(request)
   bearer_token = 'Bearer ' + credentialsWithSuject.token

   params = {"fields": "*"}
   headers = { 'Authorization': bearer_token }

   resultA = requests.get('https://www.googleapis.com/drive/v3/about?fields=*',
      headers=headers, 
      params=json.dumps(params, separators=(',', ':')))

   print(json.loads(resultA.text)['storageQuota'])

   service = build('drive', 'v3', credentials=credentialsWithSuject)
   start_files_deletion(service)

clear_drive()