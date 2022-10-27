import configparser
from json import JSONEncoder
import logging
import os
import secrets
import string
from flask import Flask
from flask.json import JSONEncoder
from flask_cors import CORS
from bson import json_util, ObjectId
from datetime import datetime
from flask_bootstrap import Bootstrap5
from blueprints.securityCameraBlueprint import security_camera_api_v1
from helpers import videoLocalStorer

bootstrap = Bootstrap5()

class MongoJsonEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(obj, ObjectId):
            return str(obj)
        return json_util.default(obj, json_util.CANONICAL_JSON_OPTIONS)

def generate_secret_key():
    alphabet = string.ascii_letters + string.digits

    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(10))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and sum(c.isdigit() for c in password) >= 3):
            return password
            
def create_app(envirovment):

    APP_DIR = os.path.abspath(os.path.dirname(__file__))
    TEMPLATE_FOLDER = os.path.join(APP_DIR, 'blueprints\\templates')

    #instatiate flask app
    app = Flask(__name__, template_folder=TEMPLATE_FOLDER)
    #instatiate flask app
    
    CORS(app)
    app.json_encoder = MongoJsonEncoder
    app.register_blueprint(security_camera_api_v1)

    #Set the secret key to some random bytes
    app.secret_key = generate_secret_key()
    #Set the secret key to some random bytes

    config = configparser.ConfigParser()
    config.read(os.path.abspath(os.path.join(".ini")))

    #log configuration
    app.config['DEBUG'] = True
    log_level = logging.DEBUG

    for handler in app.logger.handlers:
        app.logger.removeHandler(handler)

    root = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(root, config[envirovment]['LOG_FILE_NAME'])

    handler = logging.FileHandler(log_dir)
    handler.setLevel(log_level)

    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)
    #log configuration

    #mongodb configuration
    app.config["MONGO_URI"] = config[envirovment]['DB_URI']
    #mongodb configuration
    
    bootstrap.init_app(app)
    with app.app_context():
      videoLocalStorer.store_cameras()

    return app

   