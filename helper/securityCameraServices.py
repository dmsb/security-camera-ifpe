import cv2
import logging
import math
from helper import videoLocalLoader
from helper import db

def generate_frames_to_view(camara_mac_address, camera_ip, camera_matrix_size):
    camera = db.get_camera_by_filter({'is_enabled':True, 'mac_address':camara_mac_address})
    cap = videoLocalLoader.build_video_capture(camera, camera_ip)
    return gen_frames_by_ip_to_view(cap, camera_matrix_size)

def build_camera_matrix():
    camera_ips = videoLocalLoader.load_cameras()
    return convert_1d_to_2d(camera_ips, get_cameras_matrix_size(camera_ips)) if camera_ips else None

def convert_1d_to_2d(l, cols):
    return [l[i:i + cols] for i in range(0, len(l), cols)]

def get_cameras_matrix_size(camera_ips):
    cameras_quantity = len(camera_ips)
    return math.ceil(math.sqrt(cameras_quantity))
    
def resize_img_from_matriz_size(frame, camera_matrix_size):
    height = int(frame.shape[0] / (camera_matrix_size * 1.5))
    width = int(frame.shape[1] / (camera_matrix_size * 1.5))
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
                logging.error('Error getting frames to store >> %s', e)
                logging.exception(e)
                print(e)
                pass    
        else:
            pass