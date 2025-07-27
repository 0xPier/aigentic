#!/usr/bin/env python3
"""Script to verify database setup and create admin user if needed."""

import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.connection import SessionLocal, create_tables
from src.database.models import User
from src.api.auth import get_password_hash
from src.core.config import settings

def check_and_create_admin():
    """Check if admin user exists, create if not."""
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            print("Creating admin user...")
            admin_user = User(
                username="admin",
                email="admin@example.com",
                full_name="Admin User",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_verified=True,
                role="admin",
                subscription_tier="enterprise"
            )
            db.add(admin_user)
            db.commit()
            print("Admin user created successfully!")
            print("Username: admin")
            print("Password: admin123")
        else:
            print("Admin user already exists.")
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Checking database setup...")
    create_tables()
    print("Database tables created/verified.")
    
    print("Checking admin user...")
    check_and_create_admin()
