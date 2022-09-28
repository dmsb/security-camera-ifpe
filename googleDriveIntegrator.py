from google.oauth2 import service_account
import requests
from google.auth.transport.requests import Request
import os
import json
import securityConstants

URL_GOOGLE_DRIVE = 'https://www.googleapis.com/upload/drive/v3/files'
URL_GOOGLE_DRIVE_CREATE = 'https://www.googleapis.com/drive/v3/files'

def __read_in_chunks(file_object, CHUNK_SIZE):
    while True:
        data = file_object.read(CHUNK_SIZE)
        if not data:
            break
        yield data

def __upload_chunkeds_file_to_google_drive(video_location, bearer_token, resumable_upload_id, google_file_upload_id):

    file_object = open(video_location, "rb")
    index = 0
    offset = 0
    headers = {}
    params = {}

    content_size = os.stat(video_location).st_size 

    is_completed_upload = False
    for chunk in __read_in_chunks(file_object, 262144):
        
        offset = index + len(chunk)
        
        headers['Authorization'] = bearer_token
        headers['Accept'] = 'application/json'
        headers['Content-Length'] = str(len(chunk))
        headers['Content-Range'] = 'bytes %s-%s/%s' % (index, offset - 1, content_size)

        params['upload_id'] = resumable_upload_id
        params['uploadType'] = 'resumable'
        params['mimeType'] = 'application/octet-stream'

        index = offset 

        try: 
            google_resumable_upload_response = requests.patch(URL_GOOGLE_DRIVE + '/' + google_file_upload_id, params=params, data=chunk, headers=headers)
            
            if(google_resumable_upload_response.status_code >= 400):
                print('Google Drive API Error: ' + google_resumable_upload_response.content.decode("utf-8") )

            is_completed_upload = google_resumable_upload_response.status_code == 200

            print('')
            print("google_resumable_upload_response: %s, Content-Range: %s" % (google_resumable_upload_response, headers['Content-Range'])) 
            print("google_resumable_upload_response: %s, Content-Length: %s" % (google_resumable_upload_response, headers['Content-Length']))
            print('--------------------------------------------------')

        except Exception as e:
            print('Google Drive Upload Error: ' + video_location)
            print(e)
    try:
        file_object.close()
        if (is_completed_upload):
            os.remove(video_location)
    except Exception as e:
        print('Error in close file: ' + video_location)
        print(e)

def __create_file_to_video_in_google_drive(file_name, bearer_token):
    data = {"name": file_name, 'parents': [securityConstants.GOOGLE_DRIVE_SECURITY_CAMERA_VIDEO_FOLDER_ID]}
    params = {"uploadType": "resumable",  "mimeType": "application/vnd.google-apps.video"}
    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Accept': 'application/json',
        'X-Upload-Content-Type': 'application/octet-stream',
        'Authorization': bearer_token
    }
    return requests.post(URL_GOOGLE_DRIVE_CREATE, 
        data=json.dumps(data, separators=(',', ':')), 
        headers=headers, 
        params=json.dumps(params, separators=(',', ':')))

def __create_resumable_file_upload_id_from_google_drive(google_file_upload_id, bearer_token):

    params = {"uploadType": "resumable",  "mimeType": "application/vnd.google-apps.video"}
    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Accept': 'application/json',
        'X-Upload-Content-Type': 'application/octet-stream',
        'Authorization': bearer_token
    }

    google_drive_resumable_upload_id_response = requests.patch(URL_GOOGLE_DRIVE + '/' + google_file_upload_id, params=params, headers=headers)
    return  google_drive_resumable_upload_id_response.headers['X-GUploader-UploadID']
    

def upload_videos_to_google_drive(file_information):
    
    file_folder = file_information[0];
    file_name = file_information[1];

    SCOPES = ['https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = 'google-auth/google_service_account_private_key.json'

    credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    credentialsWithSuject = credentials.with_subject(securityConstants.GOOGLE_DRIVE_SERVICE_ACCOUNT_EMAIL)
    request = Request()
    credentialsWithSuject.refresh(request)
    bearer_token = 'Bearer ' + credentialsWithSuject.token

    google_file_create_response = __create_file_to_video_in_google_drive(file_name, bearer_token)
    
    google_file_upload_id = json.loads(google_file_create_response.content)['id']
    resumable_upload_id = __create_resumable_file_upload_id_from_google_drive(google_file_upload_id, bearer_token)
    video_location = file_folder + file_name

    __upload_chunkeds_file_to_google_drive(video_location, bearer_token, resumable_upload_id, google_file_upload_id)
    
        