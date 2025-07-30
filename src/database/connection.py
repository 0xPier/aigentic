import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from src.core.config import app_config

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

mongodb = MongoDB()

async def connect_to_mongo():
    """Create database connection"""
    mongodb.client = AsyncIOMotorClient(app_config.database_url)
    mongodb.database = mongodb.client.get_default_database()
    logger.info("Connected to MongoDB.")

async def close_mongo_connection():
    """Close database connection"""
    if mongodb.client:
        mongodb.client.close()
        logger.info("Disconnected from MongoDB.")
