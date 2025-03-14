from pymongo import MongoClient

class MongoDB:
    def __init__(self, host='localhost', port=27017, db_name='telegram_bot_text_analysis'):
        self.client = MongoClient(host, port)
        self.db = self.client[db_name]

    def insert_post(self, post_data):
        posts_collection = self.db['posts']
        posts_collection.insert_one(post_data)

    def get_all_posts(self):
        posts_collection = self.db['posts']
        return posts_collection.find()
