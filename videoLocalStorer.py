
from datetime import datetime, timedelta
import cv2
import time
import securityConstants
from threading import Thread
import videoLocalLoader
from googleDriveIntegrator import upload_videos_to_google_drive
import logging

def __get_frames_to_store(cap, mac_address):
    
    RECORDING_TIME_IN_SECONDS = 3600

    fourcc = cv2.VideoWriter_fourcc('X','V','I','D')

    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    
    file_location = securityConstants.RELATIVE_LOCAL_STORAGE_VIDEO_CAMERAS

    initial_time_to_video_label = datetime.now().strftime('%d_%m_%Y__%H_%M_%S')
    finish_time_to_video_label = (datetime.now() + timedelta(seconds = RECORDING_TIME_IN_SECONDS)).strftime('%d_%m_%Y__%H_%M_%S')

    file_name = mac_address + '_' + initial_time_to_video_label + '_until_' + finish_time_to_video_label + '.avi'

    out = cv2.VideoWriter(file_location + file_name, fourcc, 20, (frame_width, frame_height), True)
    
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
                    __get_frames_to_store(cap, mac_address)
            except Exception as e:
                print(e)
                break    
        else:
            logging.info('Error getting frames to store >> %s' % (mac_address))
            break

def __store_cameras_thread(cameraTuple):
    camera_ip = cameraTuple[0]
    camera_mac_address = cameraTuple[1]
    cap = videoLocalLoader.build_video_capture(camera_mac_address, camera_ip)
    __get_frames_to_store(cap, cameraTuple[1])

def store_cameras():
    camera_ips = videoLocalLoader.load_cameras()
    for camera in camera_ips:
        ip = camera[0]
        mac_address = camera[1].mac_address 
        cameraTuple = (ip, mac_address)
        new_thread_to_save_videos_in_background = Thread(target=__store_cameras_thread, args=(cameraTuple,))
        new_thread_to_save_videos_in_background.start()