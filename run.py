from factory import create_app

if __name__ == "__main__":
   app = create_app('DEV')
   app.run(debug=False, host='0.0.0.0', threaded=True)