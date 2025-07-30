from pymongo import AsyncMongoClient
from src.core.config import app_config

class MongoDB:
    client: AsyncMongoClient = None
    database = None

mongodb = MongoDB()

async def connect_to_mongo():
    mongodb.client = AsyncMongoClient(app_config.database_url)
    mongodb.database = mongodb.client.get_database()
    print("Connected to MongoDB.")

async def close_mongo_connection():
    mongodb.client.close()
    print("Disconnected from MongoDB.")
