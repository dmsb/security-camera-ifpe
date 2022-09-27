
import cv2
import time
import logging
import securityConstants
from threading import Thread
import videoLocalLoader
from googleDriveIntegrator import service_account_google

def get_frames_to_store(cap, mac_address):
    
    fourcc = cv2.VideoWriter_fourcc('X','V','I','D')
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    current_seconds = time.time()
    file_location = securityConstants.RELATIVE_LOCAL_STORAGE_VIDEO_CAMERAS
    file_name = mac_address + '_' + str(current_seconds) + '.avi'
    out = cv2.VideoWriter(file_location + file_name, fourcc, 20, (frame_width, frame_height), True)

    while True:
        success, frame = cap.read()
        if success:
            try:
                if time.time() - current_seconds <= 60:
                    out.write(frame)
                else:
                    out.release()
                    service_acc_parameters = (file_location, file_name)
                    thread_to_upload_saved_video = Thread(target=service_account_google, args=(service_acc_parameters,))
                    thread_to_upload_saved_video.start()
                    get_frames_to_store(cap, mac_address)
            except Exception as e:
                logging.exception(e)
                print(e)
                break    
        else:
            break

def store_cameras_thread(cameraTuple):
    cap = videoLocalLoader.build_video_capture(cameraTuple[0])
    get_frames_to_store(cap, cameraTuple[1])

def store_cameras():
    camera_ips = videoLocalLoader.load_cameras()
    for camera in camera_ips:
        ip = camera[0]
        mac_address = camera[1].mac_address 
        cameraTuple = (ip, mac_address)
        new_thread_to_save_videos_in_background = Thread(target=store_cameras_thread, args=(cameraTuple,))
        new_thread_to_save_videos_in_background.start()
    
    #testando camera do notebook
    # cameraTuple = ('0', 'mac_address')
    # new_thread_to_save_videos_in_background = Thread(target=store_cameras_thread, args=(cameraTuple,))
    # new_thread_to_save_videos_in_background.start()
    #testando camera do notebook