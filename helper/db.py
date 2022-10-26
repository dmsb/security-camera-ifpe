from flask import current_app, g
from werkzeug.local import LocalProxy
from flask_pymongo import PyMongo
from cryptography.fernet import Fernet
from helper import private
import hashlib

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = PyMongo(current_app).db
    return db

db = LocalProxy(get_db)


def get_user_by_username(username):
    try:
        return db.user.find_one({"username" : username})
    except Exception as e:
        return e


def get_user_by_username_and_password(username, password):
    try:
        password_with_salt = password + private.SALT
        hashed_password = hashlib.sha256(password_with_salt.encode())
        return db.user.find_one({ "username": username, "password": hashed_password.hexdigest() })
    except Exception as e:
        return e

def get_camera_by_filter(filter):
    try:
        return db.camera.find_one(filter)
    except Exception as e:
        return e

def get_cameras_by_filter(filter):
    try:
        return list(db.camera.find(filter))
    except Exception as e:
        return e