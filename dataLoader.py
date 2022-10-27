import configparser
import json
import os
import pymongo

def load_data(collection, file_data):
   result = None
   if isinstance(file_data, list):
      result = collection.insert_many(file_data) 
   else:
      result = collection.insert_one(file_data)
   print(collection, result)


def load_initial_data():
   config = configparser.ConfigParser()
   config.read(os.path.abspath(os.path.join(".ini")))


   client = pymongo.MongoClient(config['DEV']['DB_URI'])
   db = client["security-camera"]
   user_collection = db["user"]
   camera_collection = db["camera"]

   user_collection.delete_many({})
   camera_collection.delete_many({})

   with open('dataload/user.json') as file:
      load_data(user_collection, json.load(file))

   with open('dataload/camera.json') as file:
      load_data(camera_collection, json.load(file))


