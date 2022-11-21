from src.appFactory import create_app
from dataload.dataLoader import load_initial_data
from src.helpers import videoLocalStorer
from src.flaskThread import CustomFlaskThread

app = create_app('DEV')

if __name__ == "__main__":   
   load_initial_data()
   with app.app_context():
        CustomFlaskThread(name='store_cameras', target=videoLocalStorer.store_cameras).start()
   app.run(debug=False, host='0.0.0.0', threaded=True)