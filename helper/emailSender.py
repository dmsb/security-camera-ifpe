import configparser
import os
import smtplib
from email.message import EmailMessage

config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join(".ini")))

def send_password_recovery_to_email(user_email, current_password):
    
    msg = EmailMessage()
    msg['Subject'] = 'Email de recuperacao de senha Security Camera - IFPE'
    msg['From'] = config['GENERAL']['SERVER_EMAIL_ADDRESS']
    msg['To'] = user_email
    msg.set_content('Sua senha cadastrada: ' + current_password)

    # Send the email via our own SMTP server.
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(config['GENERAL']['SERVER_EMAIL_ADDRESS'], config['GENERAL']['SERVER_EMAIL_PASSWORD']) 
        smtp.send_message(msg)