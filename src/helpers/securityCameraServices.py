import base64
import hashlib
from bson import ObjectId
import cv2
import math
from flask import current_app
from src.flaskThread import CustomFlaskThread
from src.helpers import videoLocalStorer
from src.helpers import videoLocalLoader
from src.helpers import db
from configHelper import get_ini_config
from itsdangerous import TimedJSONWebSignatureSerializer

def delete_camera_by_id(camera_id):
    try: 
        db.delete_camera({'_id': ObjectId(camera_id)})
        return True
    except Exception as e:
        current_app.logger.error('Error to delete camera >> %s >> %s' % (camera_id, e))
    return False


def update_user_password(form_request_user):
    try:
        signatureSerializer = TimedJSONWebSignatureSerializer(current_app.secret_key)
        username = signatureSerializer.loads(form_request_user['token'])['username']
        user = db.get_user_by_username(username)
        
        if user != None:
            config = get_ini_config()
            password_with_salt = form_request_user['password'] + config['GENERAL']['SALT']
            hashed_password = hashlib.sha256(password_with_salt.encode())
            user['password'] = hashed_password.hexdigest() 
            db.update_user_by_id(user)
            return True
    except Exception as e:
        current_app.logger.error('Error to update user password >> %s >> %s' % (form_request_user, e))
        return False

def __build_camera_from_form_data(form_request_camera):
    for field_entry in form_request_camera.keys():
        field_value_from_form = form_request_camera[field_entry]
        if field_value_from_form in ['true', 'false']:
            form_request_camera[field_entry] = field_value_from_form.lower().capitalize() == "True"
    return form_request_camera

def upsert_camera(form_request_camera):
    try:
        form_request_camera = __build_camera_from_form_data(form_request_camera)
        if form_request_camera['_id'] != None and ObjectId.is_valid(form_request_camera['_id']):
            form_request_camera['_id'] = ObjectId(form_request_camera['_id'])
        else:
            del form_request_camera['_id']
        db.upsert_cameras_by_id(form_request_camera)
        CustomFlaskThread(name='store_cameras', target=videoLocalStorer.store_cameras).start()
        return True
    except Exception as e:
        current_app.logger.error('Error to update camera >> %s >> %s' % (form_request_camera, e))
        return False

def generate_frames_to_view(camera, camera_ip, camera_matrix_size):
    cap = videoLocalLoader.build_video_capture(camera, camera_ip)
    return gen_frames_by_ip_to_view(cap, camera_matrix_size)

def generate_image_bytes(camera_matrix_size):
    cap = cv2.VideoCapture('src/static/img/disabled-camera.jpg')
    success, frame = cap.read()
    if success:
        try:
            resized_frame = resize_img_from_matriz_size(frame, camera_matrix_size)
            ret, buffer = cv2.imencode('.jpg', resized_frame)
            resized_frame = buffer.tobytes()
            resized_frame_text = base64.b64encode(buffer.tobytes()).decode('ASCII')
            cap.release()
            return 'data:image/jpeg;base64,' + resized_frame_text
        except Exception as e:
            current_app.logger.error('Error generating bytes to disabled camera image >> %s', e)
            cap.release()
    else:
        cap.release()
    
def build_camera_matrix():
    camera_ips = videoLocalLoader.load_cameras({}, {})
    return convert_1d_to_2d(camera_ips, get_cameras_matrix_size(camera_ips)) if camera_ips else None

def convert_1d_to_2d(l, cols):
    return [l[i:i + cols] for i in range(0, len(l), cols)]

def get_cameras_matrix_size(camera_ips):
    cameras_quantity = len(camera_ips)
    return math.ceil(math.sqrt(cameras_quantity))
    
def resize_img_from_matriz_size(frame, camera_matrix_size):
    height = int(720 / (camera_matrix_size * 1.5))
    width = int(1280 / (camera_matrix_size * 1.5))
    dim = (width, height)
    return cv2.resize(frame, dim, interpolation = cv2.INTER_AREA)

def gen_frames_by_ip_to_view(cap, camera_matrix_size):
    while True:
        success, frame = cap.read()
        if success:
            try:
                resized_frame = resize_img_from_matriz_size(frame, camera_matrix_size)
                ret, buffer = cv2.imencode('.jpg', resized_frame)
                resized_frame = buffer.tobytes()
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + resized_frame + b'\r\n')
            except Exception as e:
                current_app.logger.error('Error sending frames to view >> %s', e)
                cap.release()
                pass    
        else:
            current_app.logger.error('Error reading frames to view >> %s', e)
            cap.release()
            return None