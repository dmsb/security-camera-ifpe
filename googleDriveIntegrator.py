from google.oauth2 import service_account
import requests
from google.auth.transport.requests import Request
import os
import json
import securityConstants

URL_GOOGLE_DRIVE = 'https://www.googleapis.com/upload/drive/v3/files'
URL_GOOGLE_DRIVE_CREATE = 'https://www.googleapis.com/drive/v3/files'

def read_in_chunks(file_object, CHUNK_SIZE):
    while True:
        data = file_object.read(CHUNK_SIZE)
        if not data:
            break
        yield data

def service_account_google(file_information):
    
    content_folder = file_information[0];
    content_name = file_information[1];

    SCOPES = ['https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = 'google-auth/google_service_account_private_key.json'

    credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    creds = credentials.with_subject(securityConstants.GOOGLE_DRIVE_SERVICE_ACCOUNT_EMAIL)
    request = Request()
    creds.refresh(request)

    data = {"name": content_name, 'parents': [securityConstants.GOOGLE_DRIVE_SECURITY_CAMERA_VIDEO_FOLDER_ID]}
    params = {"uploadType": "resumable",  "mimeType": "application/vnd.google-apps.video"}
    bearer_token = 'Bearer ' + creds.token
    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'X-Upload-Content-Type': 'application/octet-stream',
        'Authorization': bearer_token
    }
    google_file_create_response = requests.post(URL_GOOGLE_DRIVE_CREATE, 
        data=json.dumps(data, separators=(',', ':')), 
        headers=headers, 
        params=json.dumps(params, separators=(',', ':')))
    
    google_file_upload_id = json.loads(google_file_create_response.content)['id']
    
    google_drive_resumable_upload_id_response = requests.patch(URL_GOOGLE_DRIVE + '/' + google_file_upload_id, params=params, headers=headers)
    resumable_upload_id = google_drive_resumable_upload_id_response.headers['X-GUploader-UploadID']
    
    video_location = content_folder + content_name;
    file_object = open(video_location, "rb")
    index = 0
    offset = 0
    headers = {}
    params = {}

    content_size = os.stat(video_location).st_size 
    print(content_name, video_location, content_size)

    for chunk in read_in_chunks(file_object, 262144):
        
        offset = index + len(chunk)
        
        headers['Authorization'] = bearer_token
        headers['Content-Length'] = str(len(chunk))
        headers['Content-Range'] = 'bytes %s-%s/%s' % (index, offset - 1, content_size)

        params['upload_id'] = resumable_upload_id
        params['uploadType'] = 'resumable'
        params['mimeType'] = 'application/octet-stream'

        index = offset 

        try: 
            google_resumable_upload_response = requests.patch(URL_GOOGLE_DRIVE + '/' + google_file_upload_id, params=params, data=chunk, headers=headers)
            if(google_resumable_upload_response.status_code == 200):
                os.remove(video_location)
            elif(google_resumable_upload_response.status_code >= 400):
                print('Google Drive API Error: ' + google_resumable_upload_response.content)
            print('')
            print("google_resumable_upload_response: %s, Content-Range: %s" % (google_resumable_upload_response, headers['Content-Range'])) 
            print("google_resumable_upload_response: %s, Content-Length: %s" % (google_resumable_upload_response, headers['Content-Length']))
            print('--------------------------------------------------')
        except Exception as e:
            print(e)
        