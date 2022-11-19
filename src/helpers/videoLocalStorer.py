from datetime import datetime, timedelta
import threading
import cv2
import time
from src.flaskThread import CustomFlaskThread
from src.helpers import videoLocalLoader
from src.helpers.googleDriveIntegrator import upload_videos_to_google_drive
from configHelper import get_ini_config
from flask import current_app

TIME_PATTERN = '%d_%m_%Y__%H_%M_%S'

def __get_frames_to_store(video_capture, camera):
    
    RECORDING_TIME_IN_SECONDS = 60
    fourcc = cv2.VideoWriter_fourcc(*'avc1')

    frame_width = int(video_capture.get(3))
    frame_height = int(video_capture.get(4))
    
    file_location = get_ini_config()['GENERAL']['RELATIVE_LOCAL_STORAGE_VIDEO_CAMERAS']

    initial_time_to_video_label = datetime.now().strftime(TIME_PATTERN)
    finish_time_to_video_label = (datetime.now() + timedelta(seconds = RECORDING_TIME_IN_SECONDS)).strftime(TIME_PATTERN)

    file_name = camera['mac_address'] + '_' + initial_time_to_video_label + '_until_' + finish_time_to_video_label + '.mp4'

    video_writter = cv2.VideoWriter(file_location + file_name, fourcc, 20, (frame_width, frame_height))
    
    current_seconds = time.time()

    while True:
        success, frame = video_capture.read()
        if success:
            try:
                if time.time() - current_seconds <= RECORDING_TIME_IN_SECONDS:
                    video_writter.write(frame)
                else:
                    video_writter.release()
                    service_acc_parameters = (file_location, file_name)
                    CustomFlaskThread(name='camera_upload_' + camera['mac_address'], target=upload_videos_to_google_drive, args=(service_acc_parameters,)).start()
                    __get_frames_to_store(video_capture, camera)
            except Exception as e:
                current_app.logger.error('Error getting frames to store >> %s' % (camera['mac_address']))
                break    
        else:
            current_app.logger.error('Error reading frames to store >> %s' % (camera['mac_address']))
            break
    video_capture.release()
    video_writter.release()
    CustomFlaskThread(name='store_cameras', target=store_cameras).start()

def __store_cameras_thread(camera_tuple):
    camera_ip = camera_tuple[0]
    camera = camera_tuple[1]
    current_app.logger.info('google drive video store flow started to camera >> %s', camera['mac_address'])
    video_capture = videoLocalLoader.build_video_capture(camera, camera_ip)
    __get_frames_to_store(video_capture, camera)

def store_cameras():
    camera_ips_map = videoLocalLoader.load_cameras({'is_enabled':True}, {'_id':0})
    
    for camera_ip in camera_ips_map:
        ip = camera_ip[0]
        camera = camera_ip[1]  
        camera_tuple = (ip, camera)
        
        if not any(current_thread.name == 'camera_ip_' + ip for current_thread in threading.enumerate()):
            CustomFlaskThread(name='camera_ip_' + ip, target=__store_cameras_thread, args=(camera_tuple,)).start()