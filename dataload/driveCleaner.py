import configparser
import os
from google.oauth2 import service_account
import requests
from google.auth.transport.requests import Request
import json
from googleapiclient.discovery import build

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

result = requests.get('https://www.googleapis.com/drive/v3/files',
   headers=headers, 
   params=json.dumps(params, separators=(',', ':')))

service = build('drive', 'v3', credentials=credentialsWithSuject)
folders_response = service.files().list(q="'security-camera-ifpe@security-camera-363502.iam.gserviceaccount.com' in owners").execute()
print(folders_response)

for folder in folders_response['files']:
   result = service.files().delete(fileId=folder['id'])
   print(result)
   result.execute()