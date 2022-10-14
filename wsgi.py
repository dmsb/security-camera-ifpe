from securityCameraController import app
from waitress import serve

if __name__ == '__main__':
   serve(app, host='192.168.15.101', port='5001', url_scheme='hxttp')
   # serve(app, listen='localhost:5001', url_scheme='http')