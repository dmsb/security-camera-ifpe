from flask_mongoengine import MongoEngine
from flask import Flask, request, Response, render_template, stream_with_context, redirect, url_for, session
from flask_bootstrap import Bootstrap5
from mongoMapper import User
import emailSender
import securityConstants
import securityCameraServices
import videoLocalStorer

#instatiate flask app
app = Flask(__name__, template_folder='./templates')
#instatiate flask app

app.secret_key = securityCameraServices.generate_secret_key()
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

videoLocalStorer.store_cameras()

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
    emailSender.send_password_recovery_to_email(email, connected_user.password)
    return redirect(url_for('login_get'))

@app.get('/cameras')
def cameras():
    if 'username' in session :
        cameras_matrix = securityCameraServices.build_camera_matrix()
        return render_template('cameras.html', cameras_matrix = cameras_matrix)
    return redirect(url_for('login_get'))

@app.route('/video_feed/<string:camera_ip>/<int:camera_matrix_size>')
def video_feed(camera_ip, camera_matrix_size):
    if 'username' in session:
        return Response(stream_with_context(securityCameraServices.generate_frames_to_view(camera_ip, camera_matrix_size)), mimetype='multipart/x-mixed-replace; boundary=frame')
    return redirect(url_for('login_get'))

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', threaded=True)