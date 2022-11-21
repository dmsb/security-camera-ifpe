import re
import cv2
from flask import current_app
from src.helpers import db
import nmap

IP_VALIDATOR_REGEX  = "^((25[0-5]|(2[0-4]|1[0-9]|[1-9]|)[0-9])(\.(?!$)|$)){4}$"

def build_video_capture(camera, ip):
    ip_regex_check_result = re.search(IP_VALIDATOR_REGEX, ip)

    if ip_regex_check_result:
        if camera != None: 
            connection = (camera['network_stream_protocol']
                + '://'
                + camera['username']
                + ':'
                + camera['password']
                + '@'
                + ip
                + ':'
                + camera['port']
                + '/'
                + camera['compression_format'])
            return cv2.VideoCapture(connection)
        else:
            current_app.logger.warn('Nao foi encontrado uma camera ativa para o endereco mac informado >> %s' % (camera['mac_address']))
    else:
        current_app.logger.warn('IP invalido para operacao de captura de video da camera >> %s' % (ip))

def load_cameras(filter, query_fields):

    cameras = db.get_cameras_by_filter(filter, query_fields)

    scanner = nmap.PortScanner()
    scanner.scan(hosts='192.168.15.10-25', arguments='-sP')
    network_ips = scanner.all_hosts()
    cameras_map = []

    for camera in cameras:
        mac_adrress_camera = camera['mac_address'].upper()
        network_ip = None
        for network_map_item in network_ips:
            current_address = scanner[network_map_item]['addresses']
            if  'mac' in current_address and current_address['mac'] == mac_adrress_camera:
                network_ip = scanner[network_map_item]['addresses']['ipv4']
                cameras_map.append((network_ip, camera))
                break

    return cameras_map