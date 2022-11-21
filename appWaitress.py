from src.helpers import videoLocalStorer
from src.flaskThread import CustomFlaskThread
from src.appFactory import create_app
from waitress import serve

app = create_app('PRD')

if __name__ == '__main__':
   with app.app_context():
      CustomFlaskThread(name='store_cameras', target=videoLocalStorer.store_cameras).start()
   serve(app, host='192.168.15.101', port='5001', url_scheme='http')