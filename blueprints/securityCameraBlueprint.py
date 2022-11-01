import os
from flask import Blueprint, flash, g, jsonify, make_response, request, Response, render_template, send_from_directory, stream_with_context, redirect, url_for, session
from helpers import emailSender
from helpers import securityCameraServices
from helpers import db
from flask import current_app
from flask_cors import CORS

security_camera_api_v1 = Blueprint('security_camera_api_v1', __name__ )
CORS(security_camera_api_v1)

@security_camera_api_v1.route('/')
def index():
    return redirect(url_for('security_camera_api_v1.login_get'))

@security_camera_api_v1.get('/login')
def login_get():
    if 'username' in session :
        return redirect(url_for('security_camera_api_v1.cameras'))
    return render_template('login.html')

@security_camera_api_v1.post('/login')
def login_post():
    username = request.form['username']
    password = request.form['password']
    connected_user = db.get_user_by_username_and_password(username, password)
    if connected_user :
        current_app.logger.info('%s logado com sucesso', connected_user['username'])
        session['username'] = request.form['username']
        return redirect(url_for('security_camera_api_v1.cameras'))
    flash('Usuario ou senha invalidos', 'danger')
    return redirect(url_for('security_camera_api_v1.login_get'))

@security_camera_api_v1.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('security_camera_api_v1.login_get'))

@security_camera_api_v1.get('/password_recovery_get')
def password_recovery_get():
    return render_template('passwordRecovery.html')

@security_camera_api_v1.post('/password_recovery_post')
def password_recovery_post():
    username = request.form['email']
    user = db.get_user_by_username(username)
    if user:
        current_app.logger.info('Enviado e-mail de recuperacao de senha para o usuario: %s', user['username'])
        flash('Por favor, verifique na caixa de entrada o e-mail de recuperacao de senha.', 'success')
        emailSender.send_password_recovery_to_email(username, user['password'])
        return redirect(url_for('security_camera_api_v1.login_get'))
    else:
        flash('E-mail nao encontrado.', 'warning')
        return redirect(url_for('security_camera_api_v1.password_recovery_get'))

@security_camera_api_v1.get('/cameras')
def cameras():
    if 'username' in session :
        cameras_matrix = securityCameraServices.build_camera_matrix()
        if cameras_matrix == None: 
            return render_template('cameras.html', message = 'Nao ha cameras ativas no momento.')
        else: 
            return render_template('cameras.html', cameras_matrix = cameras_matrix)
    return redirect(url_for('security_camera_api_v1.login_get'))

@security_camera_api_v1.route('/video_feed/<string:camera_mac_address>/<string:camera_ip>/<int:camera_matrix_size>')
def video_feed(camera_mac_address, camera_ip, camera_matrix_size):
    if 'username' in session:
        camera = db.get_camera_by_filter({'is_enabled':True, 'mac_address':camera_mac_address})
        if camera != None :
            return Response(stream_with_context(securityCameraServices.generate_frames_to_view(camera, camera_ip, camera_matrix_size)), mimetype='multipart/x-mixed-replace; boundary=frame')
    return redirect(url_for('security_camera_api_v1.login_get'))

@security_camera_api_v1.route('/disabled_camera/<int:camera_matrix_size>')
def disaled_camera(camera_matrix_size):
    if 'username' in session:
        return securityCameraServices.generate_image_bytes(camera_matrix_size)
    return redirect(url_for('security_camera_api_v1.login_get'))

@security_camera_api_v1.post('/update_camera')
def update_camera():
    if 'username' in session:
        securityCameraServices.update_camera(request.form.to_dict())
        return redirect(url_for('security_camera_api_v1.cameras'))
    return redirect(url_for('security_camera_api_v1.login_get'))