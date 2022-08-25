from flask import Flask, Response, render_template, stream_with_context
import cv2
import logging
import subprocess
import re
from flask_bootstrap import Bootstrap5

#instatiate flask app  
app = Flask(__name__, template_folder='./templates')

bootstrap = Bootstrap5(app)

#metodo para resgatar os ips das cameras de seguranca. (deve-se ser consultado do banco)
addresses = subprocess.check_output(['arp', '-a'])

networkAdds = addresses.decode('windows-1252').splitlines()
cameraIps = ['0']
for networkMapItem in networkAdds :
    if len(networkMapItem) > 0 and networkMapItem.split()[1] == '60-23-a4-b4-1b-8f':
        cameraIps.append(networkMapItem.split()[0])

def gen_frames(ip):  # generate frame by frame from camera

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
    return render_template('indexOnDemandLoad.html', len = len(cameraIps), cameraIps = cameraIps)

@app.route('/video_feed/<string:ip>')
def video_feed(ip):
    return Response(stream_with_context(gen_frames(ip)), mimetype='multipart/x-mixed-replace; boundary=frame')
        
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')