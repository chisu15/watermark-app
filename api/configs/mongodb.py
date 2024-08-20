from pymongo import MongoClient
import os

class MongoDB:
    def __init__(self):
        self.client = MongoClient(os.getenv('DATABASE_HOST'))
        self.db = self.client[os.getenv('DATABASE_NAME')]
        
    # def connect(self):
    #     return self.client.connect()
    def run(self, *args, **kwargs):
        return self.client.run(*args,)
    def get_collection(self, collection_name):
        print("Connect Succsess!")
        return self.db[collection_name]
