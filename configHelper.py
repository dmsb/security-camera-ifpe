import configparser
import os

def get_ini_config():
    config = configparser.ConfigParser()
    config.read(os.path.abspath(os.path.join(".ini")))
    return config