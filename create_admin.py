#!/usr/bin/env python3
"""
Script to create an admin user for the AI Consultancy Platform.
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to the Python path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

from src.core.config import settings
from src.database.connection import SessionLocal
from src.database.models import User
from src.api.routers.auth import get_password_hash


def create_admin(email: str, username: str, password: str, full_name: str = "Admin User"):
    """
    Creates an admin user in the database.
    """
    db = SessionLocal()
    try:
        # Check if user with the same email or username already exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()

        if existing_user:
            print(f"Error: User with email '{email}' or username '{username}' already exists.")
            return

        # Create new admin user
        admin_user = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            is_active=True,
            is_verified=True,
            subscription_tier="enterprise",
            subscription_status="active",
            role="admin"  # Assign admin role
        )

        db.add(admin_user)
        db.commit()

        print(f"Admin user '{username}' created successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a new admin user.")
    parser.add_argument("--email", required=True, help="Admin's email address.")
    parser.add_argument("--username", required=True, help="Admin's username.")
    parser.add_argument("--password", required=True, help="Admin's password.")
    parser.add_argument("--full-name", default="Admin User", help="Admin's full name.")
    
    args = parser.parse_args()
    
    create_admin(
        email=args.email,
        username=args.username,
        password=args.password,
        full_name=args.full_name
    )
