import os
from flask_mongoengine import MongoEngine
from flask import flash, Flask, request, Response, render_template, stream_with_context, redirect, url_for, session
from flask_bootstrap import Bootstrap5
from mongoMapper import User
import emailSender
import securityConstants
import securityCameraServices
import videoLocalStorer
import logging

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
        app.logger.info('%s logado com sucesso', connected_user.username)
        session['username'] = request.form['username']
        return redirect(url_for('cameras'))
    flash('Usuario ou senha invalidos', 'danger')
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
    user = User.objects(username=email).first()
    if user:
        app.logger.info('Enviado e-mail de recuperacao de senha para o usuario: %s', user.username)
        flash('Por favor, verifique na caixa de entrada o e-mail de recuperacao de senha.', 'success')
        emailSender.send_password_recovery_to_email(email, user.password)
        return redirect(url_for('login_get'))
    else:
        flash('E-mail nao encontrado.', 'warning')
        return redirect(url_for('password_recovery_get'))

@app.get('/cameras')
def cameras():
    if 'username' in session :
        cameras_matrix = securityCameraServices.build_camera_matrix()
        return render_template('cameras.html', cameras_matrix = cameras_matrix)
    return redirect(url_for('login_get'))

@app.route('/video_feed/<string:camera_mac_address>/<string:camera_ip>/<int:camera_matrix_size>')
def video_feed(camera_mac_address, camera_ip, camera_matrix_size):
    if 'username' in session:
        return Response(stream_with_context(securityCameraServices.generate_frames_to_view(camera_mac_address, camera_ip, camera_matrix_size)), mimetype='multipart/x-mixed-replace; boundary=frame')
    return redirect(url_for('login_get'))

if __name__ == '__main__':
    
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    log_level = logging.DEBUG
    
    for handler in app.logger.handlers:
        app.logger.removeHandler(handler)
    
    root = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(root, 'record.log')
    
    handler = logging.FileHandler(log_dir)
    handler.setLevel(log_level)

    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)
    
    app.run(debug=False, host='0.0.0.0', threaded=True)