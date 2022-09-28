
import cv2
import time
import securityConstants
from threading import Thread
import videoLocalLoader
from googleDriveIntegrator import upload_videos_to_google_drive

def __get_frames_to_store(cap, mac_address):
    
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
                if time.time() - current_seconds <= 600:
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
            print('Error getting frames to store')
            break

def __store_cameras_thread(cameraTuple):
    cap = videoLocalLoader.build_video_capture(cameraTuple[0])
    __get_frames_to_store(cap, cameraTuple[1])

def store_cameras():
    camera_ips = videoLocalLoader.load_cameras()
    for camera in camera_ips:
        ip = camera[0]
        mac_address = camera[1].mac_address 
        cameraTuple = (ip, mac_address)
        new_thread_to_save_videos_in_background = Thread(target=__store_cameras_thread, args=(cameraTuple,))
        new_thread_to_save_videos_in_background.start()
    
    #testando camera do notebook
    # cameraTuple = ('0', 'mac_address')
    # new_thread_to_save_videos_in_background = Thread(target=__store_cameras_thread, args=(cameraTuple,))
    # new_thread_to_save_videos_in_background.start()
    #testando camera do notebook