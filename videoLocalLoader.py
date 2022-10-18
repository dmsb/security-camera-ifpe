
from mongoMapper import Camera
import subprocess
import re
import cv2
import logging

IP_VALIDATOR_REGEX  = "^((25[0-5]|(2[0-4]|1[0-9]|[1-9]|)[0-9])(\.(?!$)|$)){4}$"

def build_video_capture(camera_mac_address, ip):
    
    ip_regex_check_result = re.search(IP_VALIDATOR_REGEX, ip)

    if ip_regex_check_result:
        camera = Camera.objects(is_enabled=True, mac_address=camera_mac_address).first()
        if camera != None: 
            connection = (camera.network_stream_protocol
                + '://'
                + camera.username
                + ':'
                + camera.password
                + '@'
                + ip
                + ':'
                + camera.port
                + '/'
                + camera.compression_format)
            return cv2.VideoCapture(connection)
        else:
            logging.info('Nao foi encontrado uma camera ativa para o endereco mac informado >> %s' % (camera_mac_address))
    else:
        logging.info('IP invalido para operacao de captura de video da camera >> %s' % (ip))

def load_cameras():

    cameras = Camera.objects(is_enabled=True).only('_id', 'mac_address', 'department', 'location', 'brand', 'model', 'specific_location')
    
    addresses = subprocess.check_output(['arp', '-a'])
    network_adds = addresses.decode('windows-1252').splitlines()
    cameras_map = []

    for camera in cameras:
        for network_map_item in network_adds:
            if len(network_map_item) > 0 and network_map_item.split()[1] == camera.mac_address:
                cameras_map.append((network_map_item.split()[0], camera))
                break

    return cameras_map