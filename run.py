from src.appFactory import create_app
from dataload.dataLoader import load_initial_data

if __name__ == "__main__":
   app = create_app('DEV')
   load_initial_data()
   app.run(debug=True, host='0.0.0.0', threaded=True)