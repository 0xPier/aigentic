"""
Unit tests for task execution API endpoints.
Tests task creation, execution, status tracking, and subscription limits.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import json

from src.api.main import app
from src.database.models import Task, User
from src.agents.base import AgentResult


class TestTaskEndpoints:
    """Test task execution API endpoints."""
    
    def test_create_task_success(self, client, auth_headers, db_session):
        """Test successful task creation."""
        task_data = {
            "agent_name": "research",
            "task_type": "research",
            "query": "Research artificial intelligence trends",
            "priority": "medium",
            "parameters": {"depth": "comprehensive"}
        }
        
        response = client.post("/tasks/", json=task_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["agent_name"] == "research"
        assert data["task_type"] == "research"
        assert data["query"] == "Research artificial intelligence trends"
        assert data["status"] == "pending"
        assert data["priority"] == "medium"
        assert "id" in data
        assert "created_at" in data
        
        # Verify task was created in database
        task = db_session.query(Task).filter(Task.id == data["id"]).first()
        assert task is not None
        assert task.status == "pending"
    
    def test_create_task_unauthorized(self, client):
        """Test task creation without authentication."""
        task_data = {
            "agent_name": "research",
            "task_type": "research",
            "query": "Test query"
        }
        
        response = client.post("/tasks/", json=task_data)
        
        assert response.status_code == 401
        assert "not authenticated" in response.json()["detail"].lower()
    
    def test_create_task_invalid_agent(self, client, auth_headers):
        """Test task creation with invalid agent name."""
        task_data = {
            "agent_name": "nonexistent_agent",
            "task_type": "research",
            "query": "Test query"
        }
        
        response = client.post("/tasks/", json=task_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "invalid agent" in response.json()["detail"].lower()
    
    def test_create_task_missing_fields(self, client, auth_headers):
        """Test task creation with missing required fields."""
        # Missing query
        task_data = {
            "agent_name": "research",
            "task_type": "research"
        }
        
        response = client.post("/tasks/", json=task_data, headers=auth_headers)
        
        assert response.status_code == 422
        
        # Missing agent_name
        task_data = {
            "task_type": "research",
            "query": "Test query"
        }
        
        response = client.post("/tasks/", json=task_data, headers=auth_headers)
        
        assert response.status_code == 422
    
    def test_execute_task_success(self, client, auth_headers, test_task, db_session):
        """Test successful task execution."""
        with patch('src.api.routers.tasks.orchestrator') as mock_orchestrator:
            # Mock successful execution
            mock_result = AgentResult(
                success=True,
                data={"research_results": "Comprehensive AI research completed"},
                summary="Research task completed successfully",
                agent_name="research",
                execution_time=15.5
            )
            mock_orchestrator.execute_task = AsyncMock(return_value=mock_result)
            
            response = client.post(f"/tasks/{test_task.id}/execute", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "research_results" in data["data"]
            assert data["summary"] == "Research task completed successfully"
            assert data["execution_time"] == 15.5
            
            # Verify task status was updated
            db_session.refresh(test_task)
            assert test_task.status == "completed"
            assert test_task.execution_time == 15.5
    
    def test_execute_task_failure(self, client, auth_headers, test_task, db_session):
        """Test task execution failure."""
        with patch('src.api.routers.tasks.orchestrator') as mock_orchestrator:
            # Mock failed execution
            mock_result = AgentResult(
                success=False,
                data={"error": "API connection failed"},
                summary="Task execution failed",
                agent_name="research",
                execution_time=5.0,
                error="Connection timeout"
            )
            mock_orchestrator.execute_task = AsyncMock(return_value=mock_result)
            
            response = client.post(f"/tasks/{test_task.id}/execute", headers=auth_headers)
            
            assert response.status_code == 200  # Still returns 200 but with failure data
            data = response.json()
            assert data["success"] is False
            assert "error" in data["data"]
            assert data["error"] == "Connection timeout"
            
            # Verify task status was updated
            db_session.refresh(test_task)
            assert test_task.status == "failed"
    
    def test_execute_task_subscription_limit(self, client, db_session, test_user):
        """Test task execution with subscription limit exceeded."""
        # Set user to have exceeded monthly limit
        test_user.monthly_task_count = 100  # Basic tier limit
        test_user.subscription_tier = "basic"
        db_session.commit()
        
        # Create task
        task = Task(
            user_id=test_user.id,
            agent_name="research",
            task_type="research",
            query="Test query",
            status="pending"
        )
        db_session.add(task)
        db_session.commit()
        
        # Get auth headers
        login_data = {"username": test_user.username, "password": "secret"}
        login_response = client.post("/auth/login-json", json=login_data)
        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        response = client.post(f"/tasks/{task.id}/execute", headers=headers)
        
        assert response.status_code == 402  # Payment Required
        assert "subscription limit" in response.json()["detail"].lower()
    
    def test_execute_nonexistent_task(self, client, auth_headers):
        """Test execution of non-existent task."""
        response = client.post("/tasks/99999/execute", headers=auth_headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_execute_task_not_owned(self, client, db_session):
        """Test execution of task not owned by user."""
        # Create another user and task
        other_user = User(
            username="otheruser",
            email="other@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()
        
        other_task = Task(
            user_id=other_user.id,
            agent_name="research",
            task_type="research",
            query="Other user's task",
            status="pending"
        )
        db_session.add(other_task)
        db_session.commit()
        
        # Try to execute with different user's auth
        login_data = {"username": "testuser", "password": "secret"}
        login_response = client.post("/auth/login-json", json=login_data)
        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        response = client.post(f"/tasks/{other_task.id}/execute", headers=headers)
        
        assert response.status_code == 404  # Should not find task for this user
    
    def test_get_user_tasks(self, client, auth_headers, test_task):
        """Test retrieving user's tasks."""
        response = client.get("/tasks/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Find our test task
        task_found = False
        for task in data:
            if task["id"] == test_task.id:
                task_found = True
                assert task["agent_name"] == test_task.agent_name
                assert task["query"] == test_task.query
                assert task["status"] == test_task.status
                break
        
        assert task_found
    
    def test_get_user_tasks_with_pagination(self, client, auth_headers, db_session, test_user):
        """Test task retrieval with pagination."""
        # Create multiple tasks
        for i in range(15):
            task = Task(
                user_id=test_user.id,
                agent_name="research",
                task_type="research",
                query=f"Test query {i}",
                status="completed"
            )
            db_session.add(task)
        db_session.commit()
        
        # Test pagination
        response = client.get("/tasks/?skip=0&limit=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
        
        # Test second page
        response = client.get("/tasks/?skip=10&limit=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5  # Should have remaining tasks
    
    def test_get_task_by_id(self, client, auth_headers, test_task):
        """Test retrieving specific task by ID."""
        response = client.get(f"/tasks/{test_task.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_task.id
        assert data["agent_name"] == test_task.agent_name
        assert data["query"] == test_task.query
        assert data["status"] == test_task.status
    
    def test_get_task_by_id_not_found(self, client, auth_headers):
        """Test retrieving non-existent task."""
        response = client.get("/tasks/99999", headers=auth_headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_task_by_id_not_owned(self, client, db_session):
        """Test retrieving task not owned by user."""
        # Create another user and task
        other_user = User(
            username="otheruser2",
            email="other2@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()
        
        other_task = Task(
            user_id=other_user.id,
            agent_name="research",
            task_type="research",
            query="Other user's task",
            status="pending"
        )
        db_session.add(other_task)
        db_session.commit()
        
        # Login as test user
        login_data = {"username": "testuser", "password": "secret"}
        login_response = client.post("/auth/login-json", json=login_data)
        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        response = client.get(f"/tasks/{other_task.id}", headers=headers)
        
        assert response.status_code == 404
    
    def test_update_task_status(self, client, auth_headers, test_task, db_session):
        """Test updating task status."""
        update_data = {
            "status": "in_progress"
        }
        
        response = client.patch(f"/tasks/{test_task.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        
        # Verify in database
        db_session.refresh(test_task)
        assert test_task.status == "in_progress"
    
    def test_update_task_invalid_status(self, client, auth_headers, test_task):
        """Test updating task with invalid status."""
        update_data = {
            "status": "invalid_status"
        }
        
        response = client.patch(f"/tasks/{test_task.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 422  # Validation error
    
    def test_delete_task(self, client, auth_headers, test_task, db_session):
        """Test task deletion."""
        task_id = test_task.id
        
        response = client.delete(f"/tasks/{task_id}", headers=auth_headers)
        
        assert response.status_code == 204
        
        # Verify task was deleted
        deleted_task = db_session.query(Task).filter(Task.id == task_id).first()
        assert deleted_task is None
    
    def test_delete_nonexistent_task(self, client, auth_headers):
        """Test deletion of non-existent task."""
        response = client.delete("/tasks/99999", headers=auth_headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestTaskFiltering:
    """Test task filtering and search functionality."""
    
    def test_filter_tasks_by_status(self, client, auth_headers, db_session, test_user):
        """Test filtering tasks by status."""
        # Create tasks with different statuses
        statuses = ["pending", "in_progress", "completed", "failed"]
        for status in statuses:
            task = Task(
                user_id=test_user.id,
                agent_name="research",
                task_type="research",
                query=f"Test query for {status}",
                status=status
            )
            db_session.add(task)
        db_session.commit()
        
        # Test filtering by completed status
        response = client.get("/tasks/?status=completed", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        for task in data:
            assert task["status"] == "completed"
    
    def test_filter_tasks_by_agent(self, client, auth_headers, db_session, test_user):
        """Test filtering tasks by agent name."""
        # Create tasks for different agents
        agents = ["research", "content", "social_media"]
        for agent in agents:
            task = Task(
                user_id=test_user.id,
                agent_name=agent,
                task_type=agent,
                query=f"Test query for {agent}",
                status="completed"
            )
            db_session.add(task)
        db_session.commit()
        
        # Test filtering by research agent
        response = client.get("/tasks/?agent_name=research", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        for task in data:
            assert task["agent_name"] == "research"
    
    def test_search_tasks_by_query(self, client, auth_headers, db_session, test_user):
        """Test searching tasks by query content."""
        # Create tasks with different queries
        queries = [
            "artificial intelligence research",
            "machine learning algorithms",
            "blockchain technology analysis"
        ]
        
        for query in queries:
            task = Task(
                user_id=test_user.id,
                agent_name="research",
                task_type="research",
                query=query,
                status="completed"
            )
            db_session.add(task)
        db_session.commit()
        
        # Test searching for "artificial intelligence"
        response = client.get("/tasks/?search=artificial intelligence", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Should find the AI research task
        found_ai_task = False
        for task in data:
            if "artificial intelligence" in task["query"].lower():
                found_ai_task = True
                break
        assert found_ai_task


class TestTaskPerformance:
    """Test task execution performance and monitoring."""
    
    def test_task_execution_timeout(self, client, auth_headers, test_task):
        """Test task execution timeout handling."""
        with patch('src.api.routers.tasks.orchestrator') as mock_orchestrator:
            # Mock timeout scenario
            mock_orchestrator.execute_task = AsyncMock(side_effect=asyncio.TimeoutError("Task timeout"))
            
            response = client.post(f"/tasks/{test_task.id}/execute", headers=auth_headers)
            
            assert response.status_code == 408  # Request Timeout
            assert "timeout" in response.json()["detail"].lower()
    
    def test_concurrent_task_execution(self, client, auth_headers, db_session, test_user):
        """Test handling of concurrent task executions."""
        # Create multiple tasks
        tasks = []
        for i in range(3):
            task = Task(
                user_id=test_user.id,
                agent_name="research",
                task_type="research",
                query=f"Concurrent test query {i}",
                status="pending"
            )
            db_session.add(task)
            tasks.append(task)
        db_session.commit()
        
        with patch('src.api.routers.tasks.orchestrator') as mock_orchestrator:
            # Mock successful execution with delay
            mock_result = AgentResult(
                success=True,
                data={"result": "concurrent execution"},
                summary="Concurrent task completed",
                agent_name="research",
                execution_time=2.0
            )
            mock_orchestrator.execute_task = AsyncMock(return_value=mock_result)
            
            # Execute tasks concurrently (simulate)
            responses = []
            for task in tasks:
                response = client.post(f"/tasks/{task.id}/execute", headers=auth_headers)
                responses.append(response)
            
            # All should succeed
            for response in responses:
                assert response.status_code == 200
                assert response.json()["success"] is True
    
    def test_task_execution_metrics(self, client, auth_headers, test_task, db_session):
        """Test task execution metrics tracking."""
        with patch('src.api.routers.tasks.orchestrator') as mock_orchestrator:
            mock_result = AgentResult(
                success=True,
                data={"metrics_test": "data"},
                summary="Metrics test completed",
                agent_name="research",
                execution_time=12.5
            )
            mock_orchestrator.execute_task = AsyncMock(return_value=mock_result)
            
            start_time = datetime.now()
            response = client.post(f"/tasks/{test_task.id}/execute", headers=auth_headers)
            end_time = datetime.now()
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify execution time is tracked
            assert data["execution_time"] == 12.5
            
            # Verify task was updated with metrics
            db_session.refresh(test_task)
            assert test_task.execution_time == 12.5
            assert test_task.completed_at is not None


class TestTaskIntegration:
    """Test task integration with other system components."""
    
    def test_task_with_feedback_integration(self, client, auth_headers, test_task, db_session):
        """Test task execution with feedback system integration."""
        with patch('src.api.routers.tasks.orchestrator') as mock_orchestrator:
            mock_result = AgentResult(
                success=True,
                data={"integration_test": "success"},
                summary="Integration test completed",
                agent_name="research",
                execution_time=10.0
            )
            mock_orchestrator.execute_task = AsyncMock(return_value=mock_result)
            
            # Execute task
            response = client.post(f"/tasks/{test_task.id}/execute", headers=auth_headers)
            assert response.status_code == 200
            
            # Create feedback for the task
            feedback_data = {
                "task_id": test_task.id,
                "rating": 5,
                "comments": "Excellent execution",
                "feedback_type": "quality"
            }
            
            feedback_response = client.post("/feedback/", json=feedback_data, headers=auth_headers)
            assert feedback_response.status_code == 201
            
            # Verify feedback was linked to task
            feedback = feedback_response.json()
            assert feedback["task_id"] == test_task.id
    
    def test_task_with_memory_integration(self, client, auth_headers, test_task):
        """Test task execution with memory system integration."""
        with patch('src.api.routers.tasks.orchestrator') as mock_orchestrator, \
             patch('src.agents.base.memory_manager') as mock_memory:
            
            # Mock memory operations
            mock_memory.retrieve_memories = AsyncMock(return_value=[])
            mock_memory.store_memory = AsyncMock(return_value=True)
            
            mock_result = AgentResult(
                success=True,
                data={"memory_integration": "success"},
                summary="Memory integration test completed",
                agent_name="research",
                execution_time=8.0
            )
            mock_orchestrator.execute_task = AsyncMock(return_value=mock_result)
            
            response = client.post(f"/tasks/{test_task.id}/execute", headers=auth_headers)
            
            assert response.status_code == 200
            assert response.json()["success"] is True
            
            # Verify memory operations were called during execution
            # (This would be verified through the agent's memory integration)
    
    def test_task_subscription_tier_features(self, client, db_session, test_user):
        """Test task features based on subscription tier."""
        # Test with different subscription tiers
        tiers = ["free", "basic", "pro", "enterprise"]
        
        for tier in tiers:
            test_user.subscription_tier = tier
            test_user.monthly_task_count = 0  # Reset count
            db_session.commit()
            
            # Login with updated user
            login_data = {"username": test_user.username, "password": "secret"}
            login_response = client.post("/auth/login-json", json=login_data)
            tokens = login_response.json()
            headers = {"Authorization": f"Bearer {tokens['access_token']}"}
            
            # Create and execute task
            task_data = {
                "agent_name": "research",
                "task_type": "research",
                "query": f"Test query for {tier} tier",
                "priority": "high" if tier in ["pro", "enterprise"] else "medium"
            }
            
            create_response = client.post("/tasks/", json=task_data, headers=headers)
            assert create_response.status_code == 201
            
            task_id = create_response.json()["id"]
            
            with patch('src.api.routers.tasks.orchestrator') as mock_orchestrator:
                mock_result = AgentResult(
                    success=True,
                    data={f"{tier}_feature": "enabled"},
                    summary=f"Task completed for {tier} tier",
                    agent_name="research",
                    execution_time=5.0
                )
                mock_orchestrator.execute_task = AsyncMock(return_value=mock_result)
                
                exec_response = client.post(f"/tasks/{task_id}/execute", headers=headers)
                assert exec_response.status_code == 200
