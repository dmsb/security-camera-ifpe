from flask_mongoengine import MongoEngine
from flask import Flask, request, Response, render_template, stream_with_context, redirect, url_for
import cv2
import logging
import subprocess
import re
from flask_bootstrap import Bootstrap5
import math

from mongoMapper import Camera, User

#instatiate flask app
app = Flask(__name__, template_folder='./templates')

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

matrix = math.sqrt(17)
print(matrix)
print(math.ceil(matrix))

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

    while True:
        success, frame = cap.read()
        if success:
            try:
                #ret, buffer = cv2.imencode('.jpg', cv2.flip(frame,1))
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                logging.exception(e)
                print(e)
                pass    
        else:
            pass

@app.route('/')
def index():
    return redirect(url_for('login_get'))

@app.get('/login')
def login_get():
    return render_template('login.html')

@app.post('/login')
def login_post():
    username = request.form['username']
    password = request.form['password']
    connected_user = User.objects(username=username, password=password).first()
    if connected_user :
        return redirect(url_for('cameras'))
    else :
        return redirect(url_for('login_get'))

@app.get('/cameras')
def cameras():
    return render_template('indexOnDemandLoad.html', len = len(cameraIps), cameraIps = cameraIps)

@app.route('/video_feed/<string:ip>')
def video_feed(ip):
    return Response(stream_with_context(gen_frames(ip)), mimetype='multipart/x-mixed-replace; boundary=frame')
        
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')