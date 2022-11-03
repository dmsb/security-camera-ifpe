from flask import current_app, url_for
from helpers import db
from flask_mailman import Mail
from itsdangerous import TimedJSONWebSignatureSerializer

def send_password_recovery_to_email(username):
    try:
        mail = Mail(current_app)
        user = db.get_user_by_username(username)
        if(user):
            mail = Mail(current_app)
            mail.content_subtype = 'html'
            mail.content_subtype = 'html'

            signatureSerializer = TimedJSONWebSignatureSerializer(current_app.secret_key, 60)
            token = signatureSerializer.dumps({'username': str(user['username'])}).decode('utf-8')
            mail.send_mail(
                subject='Patrimonio+Seguro: E-mail de redefinicao de senha',
                message='',
                html_message="<p>Link de redifinicao de senha: " + url_for('security_camera_api_v1.update_password_get',
                    _external = True, token=token, username=username) +  "</p>",
                recipient_list=[user['username']])
            return True
        return False
    except Exception as e:
        return False
