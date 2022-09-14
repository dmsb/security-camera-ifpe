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

#resgatando todas as cameras do mongo
cameras = Camera.objects().all()
#resgatando todas as cameras do mongo

#resgatando todos o mapa de ips/mac address identificados na rede local
addresses = subprocess.check_output(['arp', '-a'])
#resgatando todos o mapa de ips/mac address identificados na rede local

#transformando o retorno dos ips numa estrutura facilmente iteravel
networkAdds = addresses.decode('windows-1252').splitlines()
#transformando o retorno dos ips numa estrutura facilmente iteravel

#salvando na variavel global os ips das cameras para conexao
cameraIps = ['0']
for camera in cameras:
    for networkMapItem in networkAdds :
        if len(networkMapItem) > 0 and networkMapItem.split()[1] == camera.macAddress :
            cameraIps.append(networkMapItem.split()[0])
            break
#salvando na variavel global os ips das cameras para conexao

# generate frame by frame from camera
def gen_frames(ip): 

    ipRegexCheckResult = re.search("^((25[0-5]|(2[0-4]|1[0-9]|[1-9]|)[0-9])(\.(?!$)|$)){4}$", ip)
    
    print(ipRegexCheckResult)
    
    if ipRegexCheckResult:
        rtspConnetion = 'rtsp://admin:NUHIDF@'+ip+':554/H.264'
    else:
        rtspConnetion = int(ip)
    
    print(rtspConnetion)
    
    cap = cv2.VideoCapture(rtspConnetion)

    cameras_quantity = len(cameraIps)
    camera_matrix_size = math.ceil(math.sqrt(cameras_quantity))

    while True:
        success, frame = cap.read()
        if success:
            try:
                resized_frame = resize_img_from_matriz_size(camera_matrix_size, frame)
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
        
        cameras_quantity = len(cameraIps)
        camera_matrix_size = math.ceil(math.sqrt(cameras_quantity))
        cameras_matrix = convert_1d_to_2d(cameraIps, camera_matrix_size)

        return render_template('cameras.html', cameras_matrix = cameras_matrix, cameraIps = cameraIps)
    return redirect(url_for('login_get'))

@app.route('/video_feed/<string:ip>')
def video_feed(ip):
    if 'username' in session:
        return Response(stream_with_context(gen_frames(ip)), mimetype='multipart/x-mixed-replace; boundary=frame')
    return redirect(url_for('login_get'))
         
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')