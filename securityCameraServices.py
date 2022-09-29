import cv2
import logging
import math
import string
import secrets
import videoLocalLoader

def generate_frames_to_view(camara_mac_address, camera_ip, camera_matrix_size):
    cap = videoLocalLoader.build_video_capture(camara_mac_address, camera_ip)
    return gen_frames_by_ip_to_view(cap, camera_matrix_size)

def build_camera_matrix():
    camera_ips = videoLocalLoader.load_cameras()
    return convert_1d_to_2d(camera_ips, get_cameras_matrix_size(camera_ips))

def generate_secret_key():
    alphabet = string.ascii_letters + string.digits

    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(10))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and sum(c.isdigit() for c in password) >= 3):
            return password

def convert_1d_to_2d(l, cols):
    return [l[i:i + cols] for i in range(0, len(l), cols)]

def get_cameras_matrix_size(camera_ips):
    cameras_quantity = len(camera_ips)
    return math.ceil(math.sqrt(cameras_quantity))
    
def resize_img_from_matriz_size(frame, camera_matrix_size):
    width = int(frame.shape[1] / camera_matrix_size)
    height = int(frame.shape[0] / camera_matrix_size)
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
                logging.exception(e)
                print(e)
                pass    
        else:
            pass