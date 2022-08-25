from securityCameraOnDemandLoad import app
from waitress import serve

if __name__ == '__main__':
   serve(app, listen='localhost:5001', url_scheme='https')