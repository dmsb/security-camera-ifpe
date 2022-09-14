from flask_mongoengine import MongoEngine
from flask import Flask, request, Response, render_template, stream_with_context, redirect, url_for
import cv2
import logging
import subprocess
import re
from flask_bootstrap import Bootstrap5
import math
from mongoMapper import Camera, User
import string
import secrets
from flask import session
import time
from threading import Thread

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
        "db": "security-camera",
        "host": "mongodb://localhost/security-camera",
        "port": 27017,
        "username": "admin-ifpe",
        "password": "admin-ifpe",
        "alias": "default"
    }
]
db.init_app(app)
#configurando mongo

camera_ips = []

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

def gen_frames(ip, request_type):
    gen_frames(ip, None, request_type)

# generate frame by frame from camera
def gen_frames(ip, mac_address, request_type): 

    ip_regex_check_result = re.search("^((25[0-5]|(2[0-4]|1[0-9]|[1-9]|)[0-9])(\.(?!$)|$)){4}$", ip)
    
    if ip_regex_check_result:
        rtsp_connetion = 'rtsp://admin:NUHIDF@'+ip+':554/H.264'
    else:
        rtsp_connetion = int(ip)
    
    cap = cv2.VideoCapture(rtsp_connetion)
    if request_type == 'store':
        get_frames_to_store(cap, mac_address)
    else:
        get_frames_to_view(cap)


def get_frames_to_store(cap, mac_address):
    
    fourcc = cv2.VideoWriter_fourcc('X','V','I','D')
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    current_seconds = time.time()
    out = cv2.VideoWriter(mac_address + '_' + str(current_seconds) + '.avi', fourcc, 20, (frame_width,frame_height), True)

    while True:
        success, frame = cap.read()
        if success:
            try:
                if time.time() - current_seconds <= 15:
                    out.write(frame)
                else:
                    out.release()
                    get_frames_to_store(cap, mac_address)
            except Exception as e:
                logging.exception(e)
                print(e)
                break    
        else:
            break

def store_cameras():
    for camera_to_store in load_cameras():
        gen_frames(camera_to_store[0], camera_to_store[1].mac_address, 'store')

new_thread_to_save_videos_in_background = Thread(target=store_cameras)
new_thread_to_save_videos_in_background.start()

def get_frames_to_view(cap):
    while True:
        success, frame = cap.read()
        if success:
            try:
                resized_frame = resize_img_from_matriz_size(get_cameras_matrix_size(), frame)
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
def resize_img_from_matriz_size(camera_matrix_size, frame):
    width = int(frame.shape[1] / camera_matrix_size)
    height = int(frame.shape[0] / camera_matrix_size)
    dim = (width, height)
    return cv2.resize(frame, dim, interpolation = cv2.INTER_AREA)
    
def convert_1d_to_2d(l, cols):
    return [l[i:i + cols] for i in range(0, len(l), cols)]

def get_cameras_matrix_size():
    cameras_quantity = len(camera_ips)
    return math.ceil(math.sqrt(cameras_quantity))

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

@app.get('/cameras')
def cameras():
    if 'username' in session :
        camera_ips = load_cameras()

        #usando para testes
        camera_ips.append('0')
        #usando para testes
        
        cameras_matrix = convert_1d_to_2d(camera_ips, get_cameras_matrix_size())
        return render_template('cameras.html', cameras_matrix = cameras_matrix, camera_ips = camera_ips)
    return redirect(url_for('login_get'))

@app.route('/video_feed/<string:ip>')
def video_feed(ip):
    if 'username' in session:
        return Response(stream_with_context(gen_frames(ip,'view')), mimetype='multipart/x-mixed-replace; boundary=frame')
    return redirect(url_for('login_get'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', threaded=True)