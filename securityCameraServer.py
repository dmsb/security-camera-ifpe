import json
from flask_mongoengine import MongoEngine
from flask import Flask, request, Response, render_template, stream_with_context, redirect, url_for, session
import cv2
import logging
import subprocess
import re
from flask_bootstrap import Bootstrap5
import math
from mongoMapper import Camera, User
import string
import secrets
import time
from threading import Thread
from emailSender import send_password_recovery_to_email
from google.oauth2 import service_account
import requests
from google.auth.transport.requests import Request
import os
import securityConstants

#instatiate flask app
app = Flask(__name__, template_folder='./templates')
#instatiate flask app

#Set the secret key to some random bytes
alphabet = string.ascii_letters + string.digits

while True:
    password = ''.join(secrets.choice(alphabet) for i in range(10))
    if (any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and sum(c.isdigit() for c in password) >= 3):
        break

app.secret_key = password
#Set the secret key to some random bytes

#configurando bootstrap
bootstrap = Bootstrap5(app)
#configurando bootstrap

#configurando mongo
db = MongoEngine()
app.config["MONGODB_SETTINGS"] = [
    {
        "db": securityConstants.MONGO_DATABASE_NAME,
        "host": securityConstants.MONGO_DATABASE_HOST,
        "port": securityConstants.MONGO_DATABASE_PORT,
        "username": securityConstants.MONGO_DATABASE_USERNAME,
        "password": securityConstants.MONGO_DATABASE_PASSWORD,
        "alias": "default"
    }
]
db.init_app(app)
#configurando mongo

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
        

def load_cameras():
    #resgatando todas as cameras do mongo
    cameras = Camera.objects().all()
    #resgatando todas as cameras do mongo

    #resgatando todos o mapa de ips/mac address identificados na rede local
    addresses = subprocess.check_output(['arp', '-a'])
    #resgatando todos o mapa de ips/mac address identificados na rede local

    #transformando o retorno dos ips numa estrutura facilmente iteravel
    network_adds = addresses.decode('windows-1252').splitlines()
    #transformando o retorno dos ips numa estrutura facilmente iteravel
    cameras_map = []
    #salvando na variavel global os ips das cameras para conexao
    for camera in cameras:
        for network_map_item in network_adds:
            if len(network_map_item) > 0 and network_map_item.split()[1] == camera.mac_address:
                cameras_map.append((network_map_item.split()[0], camera))
                break
    #salvando na variavel global os ips das cameras para conexao
    return cameras_map


def convert_1d_to_2d(l, cols):
    return [l[i:i + cols] for i in range(0, len(l), cols)]

def get_cameras_matrix_size(camera_ips):
    cameras_quantity = len(camera_ips)
    return math.ceil(math.sqrt(cameras_quantity))
    
def resize_img_from_matriz_size(frame, camera_matrix_size):
    width = int(frame.shape[1] / camera_matrix_size)
    height = int(frame.shape[0] / camera_matrix_size)
    dim = (width, height)
    return cv2.resize(frame, dim, interpolation = cv2.INTER_AREA)

def build_video_capture(ip):
    ip_regex_check_result = re.search("^((25[0-5]|(2[0-4]|1[0-9]|[1-9]|)[0-9])(\.(?!$)|$)){4}$", ip)
        
    if ip_regex_check_result:
        rtsp_connetion = 'rtsp://admin:NUHIDF@'+ip+':554/H.264'
    else:
        rtsp_connetion = int(ip)
    return cv2.VideoCapture(rtsp_connetion)

def gen_frames_by_ip_to_view(cap, camera_matrix_size):
    while True:
        success, frame = cap.read()
        if success:
            try:
                resized_frame = resize_img_from_matriz_size(frame, camera_matrix_size)
                ret, buffer = cv2.imencode('.jpg', resized_frame)
                resized_frame = buffer.tobytes()
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + resized_frame + b'\r\n')
            except Exception as e:
                logging.exception(e)
                print(e)
                pass    
        else:
            pass

# recording camera locally
def get_frames_to_store(cap, mac_address):
    
    fourcc = cv2.VideoWriter_fourcc('X','V','I','D')
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    current_seconds = time.time()
    file_location = securityConstants.RELATIVE_LOCAL_STORAGE_VIDEO_CAMERAS
    file_name = mac_address + '_' + str(current_seconds) + '.avi'
    out = cv2.VideoWriter(file_location + file_name, fourcc, 20, (frame_width, frame_height), True)

    while True:
        success, frame = cap.read()
        if success:
            try:
                if time.time() - current_seconds <= 60:
                    out.write(frame)
                else:
                    out.release()
                    service_acc_parameters = (file_location, file_name)
                    thread_to_upload_saved_video = Thread(target=service_account_google, args=(service_acc_parameters,))
                    thread_to_upload_saved_video.start()
                    get_frames_to_store(cap, mac_address)
            except Exception as e:
                logging.exception(e)
                print(e)
                break    
        else:
            break

def store_cameras_thread(cameraTuple):
    cap = build_video_capture(cameraTuple[0])
    get_frames_to_store(cap, cameraTuple[1])

def store_cameras():
    camera_ips = load_cameras()
    for camera in camera_ips:
        ip = camera[0]
        mac_address = camera[1].mac_address 
        cameraTuple = (ip, mac_address)
        new_thread_to_save_videos_in_background = Thread(target=store_cameras_thread, args=(cameraTuple,))
        new_thread_to_save_videos_in_background.start()
    
    #testando camera do notebook
    # cameraTuple = ('0', 'mac_address')
    # new_thread_to_save_videos_in_background = Thread(target=store_cameras_thread, args=(cameraTuple,))
    # new_thread_to_save_videos_in_background.start()
    #testando camera do notebook

store_cameras()
# recording camera locally

@app.route('/')
def index():
    return redirect(url_for('login_get'))

@app.get('/login')
def login_get():
    if 'username' in session :
        return redirect(url_for('cameras'))
    return render_template('login.html')

@app.post('/login')
def login_post():
    username = request.form['username']
    password = request.form['password']
    connected_user = User.objects(username=username, password=password).first()
    if connected_user :
        session['username'] = request.form['username']
        return redirect(url_for('cameras'))
    return redirect(url_for('login_get'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login_get'))

@app.get('/password_recovery_get')
def password_recovery_get():
    return render_template('passwordRecovery.html')

@app.post('/password_recovery_post')
def password_recovery_post():
    email = request.form['email']
    connected_user = User.objects(username=email).first()
    send_password_recovery_to_email(email, connected_user.password)
    return redirect(url_for('login_get'))

@app.get('/cameras')
def cameras():
    if 'username' in session :
        camera_ips = load_cameras()

        #usando para testes
        camera_ips.append('0')
        #usando para testes
        
        cameras_matrix = convert_1d_to_2d(camera_ips, get_cameras_matrix_size(camera_ips))
        print(cameras_matrix)
        
        return render_template('cameras.html', cameras_matrix = cameras_matrix)
    return redirect(url_for('login_get'))

@app.route('/video_feed/<string:camera_ip>/<int:camera_matrix_size>')
def video_feed(camera_ip, camera_matrix_size):
    if 'username' in session:
        print(camera_matrix_size)
        cap = build_video_capture(camera_ip)
        return Response(stream_with_context(gen_frames_by_ip_to_view(cap, camera_matrix_size)), mimetype='multipart/x-mixed-replace; boundary=frame')
    return redirect(url_for('login_get'))

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', threaded=True)