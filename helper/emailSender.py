import smtplib
from email.message import EmailMessage
from helper.private import SERVER_EMAIL_ADDRESS, SERVER_EMAIL_PASSWORD

def send_password_recovery_to_email(user_email, current_password):
    msg = EmailMessage()
    msg['Subject'] = 'Email de recuperacao de senha Security Camera - IFPE'
    msg['From'] = SERVER_EMAIL_ADDRESS
    msg['To'] = user_email
    msg.set_content('Sua senha cadastrada: ' + current_password)

    # Send the email via our own SMTP server.
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SERVER_EMAIL_ADDRESS, SERVER_EMAIL_PASSWORD) 
        smtp.send_message(msg)