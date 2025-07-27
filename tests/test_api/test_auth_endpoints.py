"""
Unit tests for authentication API endpoints.
Tests JWT authentication, user registration, login, and token management.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import json

from src.api.main import app
from src.database.models import User
from src.api.auth import create_token_pair, verify_token


class TestAuthEndpoints:
    """Test authentication API endpoints."""
    
    def test_user_registration(self, client, db_session):
        """Test user registration endpoint."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "hashed_password" not in data  # Should not expose password
        
        # Verify user was created in database
        user = db_session.query(User).filter(User.username == "newuser").first()
        assert user is not None
        assert user.is_active is True
        assert user.subscription_tier == "free"
    
    def test_user_registration_duplicate_username(self, client, test_user):
        """Test registration with duplicate username."""
        user_data = {
            "username": test_user.username,
            "email": "different@example.com",
            "password": "password123"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_user_registration_duplicate_email(self, client, test_user):
        """Test registration with duplicate email."""
        user_data = {
            "username": "differentuser",
            "email": test_user.email,
            "password": "password123"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_user_registration_invalid_data(self, client):
        """Test registration with invalid data."""
        # Test missing required fields
        response = client.post("/auth/register", json={})
        assert response.status_code == 422
        
        # Test invalid email format
        user_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "password123"
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 422
        
        # Test weak password
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "123"
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 422
    
    def test_user_login_success(self, client, test_user):
        """Test successful user login."""
        login_data = {
            "username": test_user.username,
            "password": "secret"
        }
        
        response = client.post("/auth/login-json", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        
        # Verify tokens are valid
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        
        assert verify_token(access_token, "access") == test_user.username
        assert verify_token(refresh_token, "refresh") == test_user.username
    
    def test_user_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials."""
        # Wrong password
        login_data = {
            "username": test_user.username,
            "password": "wrongpassword"
        }
        response = client.post("/auth/login-json", json=login_data)
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
        
        # Non-existent user
        login_data = {
            "username": "nonexistent",
            "password": "password"
        }
        response = client.post("/auth/login-json", json=login_data)
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    def test_user_login_inactive_user(self, client, db_session):
        """Test login with inactive user."""
        # Create inactive user
        inactive_user = User(
            username="inactive",
            email="inactive@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            is_active=False
        )
        db_session.add(inactive_user)
        db_session.commit()
        
        login_data = {
            "username": "inactive",
            "password": "secret"
        }
        
        response = client.post("/auth/login-json", json=login_data)
        
        assert response.status_code == 400
        assert "inactive" in response.json()["detail"].lower()
    
    def test_token_refresh(self, client, test_user):
        """Test token refresh functionality."""
        # First, login to get tokens
        login_data = {
            "username": test_user.username,
            "password": "secret"
        }
        login_response = client.post("/auth/login-json", json=login_data)
        tokens = login_response.json()
        
        # Use refresh token to get new access token
        refresh_data = {
            "refresh_token": tokens["refresh_token"]
        }
        
        response = client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        
        # Verify new tokens are different and valid
        new_access_token = data["access_token"]
        new_refresh_token = data["refresh_token"]
        
        assert new_access_token != tokens["access_token"]
        assert verify_token(new_access_token, "access") == test_user.username
        assert verify_token(new_refresh_token, "refresh") == test_user.username
    
    def test_token_refresh_invalid_token(self, client):
        """Test token refresh with invalid refresh token."""
        refresh_data = {
            "refresh_token": "invalid.token.here"
        }
        
        response = client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_token_refresh_access_token_used(self, client, test_user):
        """Test token refresh with access token instead of refresh token."""
        # Login to get tokens
        login_data = {
            "username": test_user.username,
            "password": "secret"
        }
        login_response = client.post("/auth/login-json", json=login_data)
        tokens = login_response.json()
        
        # Try to use access token for refresh (should fail)
        refresh_data = {
            "refresh_token": tokens["access_token"]
        }
        
        response = client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_get_current_user(self, client, auth_headers):
        """Test getting current user information."""
        response = client.get("/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert "subscription_tier" in data
        assert "is_active" in data
        assert "hashed_password" not in data  # Should not expose password
    
    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without authentication."""
        response = client.get("/auth/me")
        
        assert response.status_code == 401
        assert "not authenticated" in response.json()["detail"].lower()
    
    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_logout(self, client, auth_headers):
        """Test user logout."""
        response = client.post("/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "logged out" in data["message"].lower()


class TestTokenManagement:
    """Test JWT token creation and validation."""
    
    def test_create_token_pair(self):
        """Test token pair creation."""
        user_data = {"username": "testuser"}
        
        tokens = create_token_pair(user_data)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "expires_in" in tokens
        assert "token_type" in tokens
        
        # Verify tokens are different
        assert tokens["access_token"] != tokens["refresh_token"]
        
        # Verify token types
        access_username = verify_token(tokens["access_token"], "access")
        refresh_username = verify_token(tokens["refresh_token"], "refresh")
        
        assert access_username == "testuser"
        assert refresh_username == "testuser"
    
    def test_token_verification_success(self):
        """Test successful token verification."""
        user_data = {"username": "testuser"}
        tokens = create_token_pair(user_data)
        
        # Verify access token
        username = verify_token(tokens["access_token"], "access")
        assert username == "testuser"
        
        # Verify refresh token
        username = verify_token(tokens["refresh_token"], "refresh")
        assert username == "testuser"
    
    def test_token_verification_wrong_type(self):
        """Test token verification with wrong token type."""
        user_data = {"username": "testuser"}
        tokens = create_token_pair(user_data)
        
        # Try to verify access token as refresh token
        with pytest.raises(Exception):
            verify_token(tokens["access_token"], "refresh")
        
        # Try to verify refresh token as access token
        with pytest.raises(Exception):
            verify_token(tokens["refresh_token"], "access")
    
    def test_token_verification_invalid_token(self):
        """Test token verification with invalid token."""
        with pytest.raises(Exception):
            verify_token("invalid.token.here", "access")
        
        with pytest.raises(Exception):
            verify_token("", "access")
    
    def test_token_expiration(self):
        """Test token expiration handling."""
        # This test would require mocking time or creating expired tokens
        # For now, we'll test the structure
        user_data = {"username": "testuser"}
        tokens = create_token_pair(user_data)
        
        # Verify tokens have expiration info
        assert tokens["expires_in"] > 0
        assert isinstance(tokens["expires_in"], int)


class TestAuthenticationMiddleware:
    """Test authentication middleware and dependencies."""
    
    def test_protected_endpoint_with_valid_token(self, client, auth_headers):
        """Test accessing protected endpoint with valid token."""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
    
    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/auth/me")
        assert response.status_code == 401
    
    def test_protected_endpoint_with_malformed_header(self, client):
        """Test accessing protected endpoint with malformed auth header."""
        # Missing Bearer prefix
        headers = {"Authorization": "invalid_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401
        
        # Wrong format
        headers = {"Authorization": "Basic invalid_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_protected_endpoint_with_expired_token(self, client):
        """Test accessing protected endpoint with expired token."""
        # This would require creating an expired token
        # For now, we'll use an obviously invalid token
        headers = {"Authorization": "Bearer expired.token.here"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401


class TestPasswordSecurity:
    """Test password hashing and security."""
    
    def test_password_hashing_on_registration(self, client, db_session):
        """Test that passwords are properly hashed on registration."""
        user_data = {
            "username": "securitytest",
            "email": "security@example.com",
            "password": "plaintextpassword"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        
        # Check that password is hashed in database
        user = db_session.query(User).filter(User.username == "securitytest").first()
        assert user.hashed_password != "plaintextpassword"
        assert user.hashed_password.startswith("$2b$")  # bcrypt hash format
        assert len(user.hashed_password) > 50  # Hashed passwords are long
    
    def test_password_not_returned_in_responses(self, client, test_user):
        """Test that passwords are never returned in API responses."""
        # Registration response
        user_data = {
            "username": "nopasswordtest",
            "email": "nopassword@example.com",
            "password": "testpassword"
        }
        response = client.post("/auth/register", json=user_data)
        data = response.json()
        assert "password" not in data
        assert "hashed_password" not in data
        
        # Login response
        login_data = {
            "username": test_user.username,
            "password": "secret"
        }
        response = client.post("/auth/login-json", json=login_data)
        data = response.json()
        assert "password" not in data
        assert "hashed_password" not in data
        
        # User info response
        login_response = client.post("/auth/login-json", json=login_data)
        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        response = client.get("/auth/me", headers=headers)
        data = response.json()
        assert "password" not in data
        assert "hashed_password" not in data
