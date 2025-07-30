#!/usr/bin/env python3
"""
Script to create an admin user for the AI Consultancy Platform.
Run this after setting up the database to create your first admin user.
"""

import logging
from pymongo import MongoClient
from passlib.context import CryptContext
from src.core.config import app_config
from src.database.models import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin_user(email: str, username: str, password: str, full_name: str):
    """Create an admin user in the database."""
    try:
        # Connect to MongoDB
        client = MongoClient(app_config.database_url)
        db = client.get_default_database()
        users_collection = db["users"]
        
        # Check if user already exists
        existing_user = users_collection.find_one({"email": email})
        if existing_user:
            logger.error(f"User with email {email} already exists!")
            return
        
        # Hash password
        hashed_password = pwd_context.hash(password)
        
        # Create user document
        user_data = {
            "email": email,
            "username": username,
            "full_name": full_name,
            "hashed_password": hashed_password,
            "is_active": True,
            "is_admin": True,
            "created_at": None,  # Will be set by the model
            "updated_at": None   # Will be set by the model
        }
        
        # Insert user
        result = users_collection.insert_one(user_data)
        
        if result.inserted_id:
            logger.info(f"Admin user created successfully!")
            logger.info(f"User ID: {result.inserted_id}")
            logger.info(f"Email: {email}")
            logger.info(f"Username: {username}")
        else:
            logger.error("Failed to create admin user")
            
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    print("=== AI Consultancy Platform - Admin User Creation ===\n")
    
    # Get user input
    email = input("Enter admin email: ").strip()
    username = input("Enter admin username: ").strip()
    full_name = input("Enter admin full name: ").strip()
    password = input("Enter admin password: ").strip()
    
    if not all([email, username, full_name, password]):
        logger.error("All fields are required!")
        exit(1)
    
    create_admin_user(email, username, password, full_name)
