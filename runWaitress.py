from src.helpers import videoLocalStorer
from src.flaskThread import CustomFlaskThread
from src.appFactory import create_app
from waitress import serve

if __name__ == '__main__':
   app = create_app('PRD')
   with app.app_context():
      CustomFlaskThread(name='store_cameras', target=videoLocalStorer.store_cameras).start()
   serve(app, host='192.168.15.101', port='5001', url_scheme='http')
   # serve(app, listen='localhost:5001', url_scheme='http')