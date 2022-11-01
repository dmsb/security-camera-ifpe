from flask import current_app, g
from werkzeug.local import LocalProxy
from flask_pymongo import PyMongo
import hashlib
from helpers.pythonAuxiliary import get_ini_config

config = get_ini_config()

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = PyMongo(current_app).db
    return db

db = LocalProxy(get_db)

def get_user_by_username(username):
    return db.user.find_one({"username" : username})


def get_user_by_username_and_password(username, password):
    password_with_salt = password + config['GENERAL']['SALT']
    hashed_password = hashlib.sha256(password_with_salt.encode())
    return db.user.find_one({ "username": username, "password": hashed_password.hexdigest() })

def get_camera_by_filter(filter):
    return db.camera.find_one(filter)

def get_cameras_by_filter(filter, fields):
    return list(db.camera.find(filter, fields))

def update_cameras_by_mac_address(camera):
    db.camera.update_one( { "mac_address": camera['mac_address'] },  { "$set": camera })