
from mongoMapper import Camera
import subprocess
import re
import cv2

def build_video_capture(ip):
    ip_regex_check_result = re.search("^((25[0-5]|(2[0-4]|1[0-9]|[1-9]|)[0-9])(\.(?!$)|$)){4}$", ip)
        
    if ip_regex_check_result:
        rtsp_connetion = 'rtsp://admin:NUHIDF@'+ip+':554/H.264'
    else:
        rtsp_connetion = int(ip)
    return cv2.VideoCapture(rtsp_connetion)

def load_cameras():
    #resgatando todas as cameras do mongo
    cameras = Camera.objects().all()
    #resgatando todas as cameras do mongo

    #resgatando todos o mapa de ips/mac address identificados na rede local
    addresses = subprocess.check_output(['arp', '-a'])
    #resgatando todos o mapa de ips/mac address identificados na rede local

    #transformando o retorno dos ips numa estrutura facilmente iteravel
    network_adds = addresses.decode('windows-1252').splitlines()
    #transformando o retorno dos ips numa estrutura facilmente iteravel
    cameras_map = []
    #salvando na variavel global os ips das cameras para conexao
    for camera in cameras:
        for network_map_item in network_adds:
            if len(network_map_item) > 0 and network_map_item.split()[1] == camera.mac_address:
                cameras_map.append((network_map_item.split()[0], camera))
                break
    #salvando na variavel global os ips das cameras para conexao
    return cameras_map