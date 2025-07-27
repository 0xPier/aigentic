"""
Test configuration and fixtures for the AI consultancy platform.
Provides common test utilities, database fixtures, and mock objects.
"""

import pytest
import asyncio
from typing import Generator, Dict, Any
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from src.database.models import Base, User, Task, Feedback, AgentMemory
from src.database.connection import get_db
from src.core.config import settings
from src.api.main import app
from src.agents.base import AgentContext, AgentResult
from src.agents.memory_manager import memory_manager


# Test Database Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        is_active=True,
        subscription_tier="basic",
        monthly_task_count=5
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_task(db_session, test_user):
    """Create a test task."""
    task = Task(
        user_id=test_user.id,
        agent_name="research",
        task_type="research",
        query="Test research query",
        status="completed",
        priority="medium",
        created_at=datetime.now(),
        execution_time=15.5
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


@pytest.fixture
def test_feedback(db_session, test_user, test_task):
    """Create test feedback."""
    feedback = Feedback(
        user_id=test_user.id,
        task_id=test_task.id,
        rating=4,
        comments="Great job on the research!",
        feedback_type="quality"
    )
    db_session.add(feedback)
    db_session.commit()
    db_session.refresh(feedback)
    return feedback


@pytest.fixture
def test_memory(db_session):
    """Create test agent memory."""
    memory = AgentMemory(
        agent_name="research",
        memory_type="success",
        content={
            "execution_summary": {
                "task_type": "research",
                "execution_time": 12.3,
                "success": True,
                "summary": "Research completed successfully"
            }
        },
        context_tags=["research", "success", "web_search"],
        relevance_score=0.8,
        created_at=datetime.now()
    )
    db_session.add(memory)
    db_session.commit()
    db_session.refresh(memory)
    return memory


@pytest.fixture
def mock_agent_context():
    """Create a mock agent context for testing."""
    return AgentContext(
        user_id=1,
        task_id=1,
        query="Test query",
        task_type="research",
        priority="medium",
        project_id=None,
        previous_results=None,
        integrations={}
    )


@pytest.fixture
def mock_agent_result():
    """Create a mock agent result for testing."""
    return AgentResult(
        success=True,
        data={"result": "Test result"},
        summary="Test execution completed successfully",
        agent_name="test_agent",
        execution_time=10.5
    )


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    with patch('src.integrations.api_client.api_manager.openai') as mock_openai:
        mock_openai.chat_completion = AsyncMock(return_value={
            "success": True,
            "content": "Mock OpenAI response",
            "usage": {"total_tokens": 100}
        })
        mock_openai.image_generation = AsyncMock(return_value={
            "success": True,
            "images": ["https://example.com/image.png"]
        })
        yield mock_openai


@pytest.fixture
def mock_twitter_client():
    """Mock Twitter client for testing."""
    with patch('src.integrations.api_client.api_manager.twitter') as mock_twitter:
        mock_twitter.post_tweet = AsyncMock(return_value={
            "success": True,
            "tweet_id": "123456789",
            "url": "https://twitter.com/user/status/123456789"
        })
        mock_twitter.upload_media = AsyncMock(return_value={
            "success": True,
            "media_id": "media123"
        })
        yield mock_twitter


@pytest.fixture
def mock_telegram_client():
    """Mock Telegram client for testing."""
    with patch('src.integrations.api_client.api_manager.telegram') as mock_telegram:
        mock_telegram.send_message = AsyncMock(return_value={
            "success": True,
            "message_id": 123
        })
        mock_telegram.send_photo = AsyncMock(return_value={
            "success": True,
            "message_id": 124
        })
        yield mock_telegram


@pytest.fixture
def mock_web_search():
    """Mock web search functionality."""
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "RelatedTopics": [
                {
                    "Text": "Test search result",
                    "FirstURL": "https://example.com"
                }
            ]
        })
        mock_response.text = AsyncMock(return_value="<html><body>Test content</body></html>")
        mock_get.return_value.__aenter__.return_value = mock_response
        yield mock_get


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for API requests."""
    # Login to get access token
    login_data = {
        "username": test_user.username,
        "password": "secret"
    }
    response = client.post("/auth/login-json", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    return {"Authorization": f"Bearer {token_data['access_token']}"}


# Test Data Factories

def create_test_user_data(username: str = "testuser", email: str = "test@example.com") -> Dict[str, Any]:
    """Create test user data."""
    return {
        "username": username,
        "email": email,
        "password": "testpassword123",
        "subscription_tier": "basic"
    }


def create_test_task_data(agent_name: str = "research", query: str = "Test query") -> Dict[str, Any]:
    """Create test task data."""
    return {
        "agent_name": agent_name,
        "task_type": "research",
        "query": query,
        "priority": "medium",
        "parameters": {"test_param": "test_value"}
    }


def create_test_feedback_data(task_id: int, rating: int = 4) -> Dict[str, Any]:
    """Create test feedback data."""
    return {
        "task_id": task_id,
        "rating": rating,
        "comments": "Test feedback comments",
        "feedback_type": "quality"
    }


# Mock API Response Helpers

def mock_openai_response(content: str = "Mock response", success: bool = True) -> Dict[str, Any]:
    """Create mock OpenAI API response."""
    return {
        "success": success,
        "content": content,
        "usage": {"total_tokens": 100},
        "model": "gpt-4"
    }


def mock_twitter_response(tweet_id: str = "123456789", success: bool = True) -> Dict[str, Any]:
    """Create mock Twitter API response."""
    return {
        "success": success,
        "tweet_id": tweet_id,
        "url": f"https://twitter.com/user/status/{tweet_id}",
        "created_at": datetime.now().isoformat()
    }


def mock_telegram_response(message_id: int = 123, success: bool = True) -> Dict[str, Any]:
    """Create mock Telegram API response."""
    return {
        "success": success,
        "message_id": message_id,
        "chat_id": "@test_channel",
        "timestamp": datetime.now().isoformat()
    }


# Test Utilities

async def wait_for_async_task(task_func, timeout: int = 5):
    """Wait for an async task to complete with timeout."""
    try:
        return await asyncio.wait_for(task_func, timeout=timeout)
    except asyncio.TimeoutError:
        pytest.fail(f"Async task timed out after {timeout} seconds")


def assert_agent_result(result: AgentResult, expected_success: bool = True):
    """Assert agent result properties."""
    assert isinstance(result, AgentResult)
    assert result.success == expected_success
    assert isinstance(result.data, dict)
    assert isinstance(result.execution_time, (int, float))
    assert result.execution_time >= 0
    
    if expected_success:
        assert result.summary is not None
        assert len(result.summary) > 0
    else:
        assert result.error is not None


def assert_memory_stored(db_session, agent_name: str, memory_type: str):
    """Assert that memory was stored for an agent."""
    memory = db_session.query(AgentMemory).filter(
        AgentMemory.agent_name == agent_name,
        AgentMemory.memory_type == memory_type
    ).first()
    assert memory is not None
    assert memory.content is not None
    assert memory.relevance_score > 0


# Performance Testing Helpers

@pytest.fixture
def performance_timer():
    """Timer fixture for performance testing."""
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = datetime.now()
        
        def stop(self):
            self.end_time = datetime.now()
        
        @property
        def elapsed_seconds(self):
            if self.start_time and self.end_time:
                return (self.end_time - self.start_time).total_seconds()
            return None
    
    return Timer()


# Cleanup Helpers

@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Cleanup test files after each test."""
    yield
    # Cleanup any test files created during testing
    import os
    import glob
    
    test_files = glob.glob("test_*")
    test_files.extend(glob.glob("uploads/test_*"))
    
    for file_path in test_files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass  # Ignore cleanup errors
