
import configparser
from datetime import datetime, timedelta
import os
import cv2
import time
from threading import Thread
from helper import videoLocalLoader
from helper.googleDriveIntegrator import upload_videos_to_google_drive
import logging

config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join(".ini")))

TIME_PATTERN = '%d_%m_%Y__%H_%M_%S'

def __get_frames_to_store(cap, camera):
    
    RECORDING_TIME_IN_SECONDS = 1600
    fourcc = cv2.VideoWriter_fourcc(*'avc1')

    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    
    file_location = config['GENERAL']['RELATIVE_LOCAL_STORAGE_VIDEO_CAMERAS']

    initial_time_to_video_label = datetime.now().strftime(TIME_PATTERN)
    finish_time_to_video_label = (datetime.now() + timedelta(seconds = RECORDING_TIME_IN_SECONDS)).strftime(TIME_PATTERN)

    file_name = camera['mac_address'] + '_' + initial_time_to_video_label + '_until_' + finish_time_to_video_label + '.mp4'

    out = cv2.VideoWriter(file_location + file_name, fourcc, 20, (frame_width, frame_height))
    
    current_seconds = time.time()

    while True:
        success, frame = cap.read()
        if success:
            try:
                if time.time() - current_seconds <= RECORDING_TIME_IN_SECONDS:
                    out.write(frame)
                else:
                    out.release()
                    service_acc_parameters = (file_location, file_name)
                    thread_to_upload_saved_video = Thread(target=upload_videos_to_google_drive, args=(service_acc_parameters,))
                    thread_to_upload_saved_video.start()
                    __get_frames_to_store(cap, camera)
            except Exception as e:
                print(e)
                break    
        else:
            logging.info('Error getting frames to store >> %s' % (camera['mac_address']))
            break

def __store_cameras_thread(camera_tuple):
    camera_ip = camera_tuple[0]
    camera = camera_tuple[1]
    cap = videoLocalLoader.build_video_capture(camera, camera_ip)
    __get_frames_to_store(cap, camera)

def store_cameras():
    camera_ips_map = videoLocalLoader.load_cameras()
    for camera_ip in camera_ips_map:
        ip = camera_ip[0]
        camera = camera_ip[1]  
        camera_tuple = (ip, camera)
        new_thread_to_save_videos_in_background = Thread(target=__store_cameras_thread, args=(camera_tuple,))
        new_thread_to_save_videos_in_background.start()