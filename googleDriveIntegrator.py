import flask
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
from flask import request, render_template
import secrets
import string
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from flask_mongoengine import MongoEngine
from google.auth import credentials

from mongoMapper import google_token

app = flask.Flask(__name__, template_folder='./templates')

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

scheduler = BackgroundScheduler()

alphabet = string.ascii_letters + string.digits

while True:
    password = ''.join(secrets.choice(alphabet) for i in range(10))
    if (any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and sum(c.isdigit() for c in password) >= 3):
        break

app.secret_key = password

# Create the flow using the client secrets file from the Google API
# Console.

@app.route('/oauth2callback')
def oauth2callback():
    print(request.args)
    print('request.url ' + request.url)
    state = flask.session['state']
    print('state ' + state)

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'google-auth/client_secret_google_web.json',
        scopes=['https://www.googleapis.com/auth/drive.metadata.readonly'],
        state=state)

    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    # Tell the user to go to the authorization URL.
    authorization_response = flask.request.url
    print('authorization_response ' + authorization_response)
    cred = flow.fetch_token(authorization_response=authorization_response)
    print(cred)
    print(flow.credentials)
    return render_template('asdasd.html')
    
def google():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'google-auth/client_secret_google_web.json',
        scopes=['https://www.googleapis.com/auth/drive.metadata.readonly'])

    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    print('Please go to this URL: {}'.format(authorization_url))
    flask.session['state'] = state
    return flask.redirect(authorization_url)


API_SERVICE_NAME = 'drive'
API_VERSION = 'v2'

def oauth():
    scheduler.pause()
    
    last_token_saved = google_token.objects.order_by('-expiry').first()
    if(last_token_saved != None):
        last_token_saved = authenticate_google_from_local()

    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        'google-auth/client_secret_google_desktop.json',
        scopes=['https://www.googleapis.com/auth/drive.metadata.readonly'],
        state=last_token_saved.state)
    
    print(last_token_saved.expiry)
    print(last_token_saved.authorization_code)
    flow.fetch_token(code=last_token_saved.authorization_code)

    drive = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=flow.credentials)
    
    drive.files().list().execute()
    
    if(last_token_saved.expiry <= datetime.now()):
        print(last_token_saved)
    
    scheduler.resume()

def authenticate_google_from_local():
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        'google-auth/client_secret_google_desktop.json',
        scopes=['https://www.googleapis.com/auth/drive.metadata.readonly'])

    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    flow.run_local_server()
    
    flow.authorized_session()
    credentials = flow.credentials

    token = google_token( authorization_code=flow.oauth2session._client.code,
        token=credentials.token,
        refresh_token=credentials.refresh_token,
        expiry=credentials.expiry,
        token_uri=credentials.token_uri,
        client_id=credentials.client_id,
        client_secret=credentials.client_secret,
        scopes=credentials.scopes,
        state=state
    )
    token.save()
    return token

from google.oauth2 import service_account
from googleapiclient.discovery import build

def service_account_google():
    scheduler.pause()
    SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
    SERVICE_ACCOUNT_FILE = 'google-auth/google_service_account_private_key.json'

    credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    drive = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
    
    drive.files().list().execute()
    scheduler.resume()

scheduler.add_job(service_account_google, 'interval', seconds=3)
scheduler.start()

if __name__ == '__main__':
    # When running locally, disable OAuthlib's HTTPs verification.
    # ACTION ITEM for developers:
    #     When running in production *do not* leave this option enabled.
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    # Specify a hostname and port that are set as a valid redirect URI
    # for your API project in the Google API Console.
    app.run(debug=False, host='0.0.0.0')

    