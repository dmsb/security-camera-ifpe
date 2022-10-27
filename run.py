from appFactory import create_app
from dataLoader import load_initial_data

if __name__ == "__main__":
   load_initial_data()
   app = create_app('DEV')
   app.run(debug=False, host='0.0.0.0', threaded=True)