#!/usr/bin/env python3
"""
Simple test script to verify authentication endpoints are working.
Run this with: python test_auth.py
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api"

def test_endpoints():
    """Test various authentication endpoints"""
    print("🧪 Testing Authentication Endpoints\n")
    
    # Test 1: Demo login
    print("1. Testing demo login...")
    try:
        response = requests.post(f"{BASE_URL}/admin/demo-login")
        if response.status_code == 200:
            data = response.json()
            print("✅ Demo login successful!")
            demo_token = data.get('access_token')
            print(f"   Access token: {demo_token[:20]}...")
        else:
            print(f"❌ Demo login failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Demo login error: {e}")
    
    print()
    
    # Test 2: Registration
    print("2. Testing user registration...")
    test_user = {
        "username": "testuser123",
        "email": "test123@example.com",
        "password": "securepassword123",
        "full_name": "Test User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=test_user)
        if response.status_code == 200:
            print("✅ Registration successful!")
            print(f"   User created: {response.json().get('username')}")
        elif response.status_code == 400:
            print("⚠️  User already exists (this is expected if running multiple times)")
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Registration error: {e}")
    
    print()
    
    # Test 3: Login with test user
    print("3. Testing login with test user...")
    try:
        login_data = {
            "username": test_user["username"],
            "password": test_user["password"]
        }
        response = requests.post(f"{BASE_URL}/auth/login-json", json=login_data)
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            user_token = data.get('access_token')
            print(f"   Access token: {user_token[:20]}...")
            
            # Test getting user info
            headers = {"Authorization": f"Bearer {user_token}"}
            me_response = requests.get(f"{BASE_URL}/users/me", headers=headers)
            if me_response.status_code == 200:
                user_info = me_response.json()
                print(f"   User info: {user_info.get('username')} ({user_info.get('email')})")
            else:
                print(f"   ⚠️  Could not get user info: {me_response.status_code}")
                
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Login error: {e}")
    
    print()
    
    # Test 4: Demo user login via standard login
    print("4. Testing demo user via standard login...")
    try:
        login_data = {"username": "demo", "password": "demo123"}
        response = requests.post(f"{BASE_URL}/auth/login-json", json=login_data)
        if response.status_code == 200:
            print("✅ Demo user login successful!")
        else:
            print(f"❌ Demo user login failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Demo user login error: {e}")

    print("\n🎯 Authentication Test Complete!")
    print("\nNext steps:")
    print("1. Start your frontend with: npm start")
    print("2. Visit http://localhost:3000/login")
    print("3. Try the 'Demo Login' button")
    print("4. Or register a new account")

if __name__ == "__main__":
    test_endpoints() 