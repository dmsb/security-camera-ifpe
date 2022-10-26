from factory import create_app
from waitress import serve

if __name__ == '__main__':
   app = create_app('PRD')
   serve(app, host='192.168.15.101', port='5001', url_scheme='http')
   # serve(app, listen='localhost:5001', url_scheme='http')