"""Database models for the AI Consultancy Platform."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """User model for authentication and subscription management."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    subscription_tier = Column(String, default="free")  # free, basic, premium, enterprise
    subscription_status = Column(String, default="active")  # active, cancelled, expired
    role = Column(String, default="user")  # user, admin
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    projects = relationship("Project", back_populates="owner")
    tasks = relationship("Task", back_populates="user")
    feedback = relationship("Feedback", back_populates="user")


class Project(Base):
    """Project model for organizing user work."""
    
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="active")  # active, completed, archived
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project")


class Task(Base):
    """Task model for tracking agent work."""
    
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    query = Column(Text, nullable=False)  # Original user query
    task_type = Column(String)  # research, analysis, content_creation, etc.
    status = Column(String, default="pending")  # pending, in_progress, completed, failed
    priority = Column(String, default="medium")  # low, medium, high, urgent
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    assigned_agent = Column(String)  # Agent class name
    
    # Task execution details
    celery_task_id = Column(String)  # Celery task ID for async processing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    execution_time = Column(Float)  # Execution time in seconds
    
    # Results and outputs
    result_data = Column(JSON)  # Structured result data
    output_files = Column(JSON)  # List of generated file paths
    error_message = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")
    subtasks = relationship("SubTask", back_populates="parent_task")
    feedback = relationship("Feedback", back_populates="task")


class SubTask(Base):
    """SubTask model for agent delegation and orchestration."""
    
    __tablename__ = "subtasks"
    
    id = Column(Integer, primary_key=True, index=True)
    parent_task_id = Column(Integer, ForeignKey("tasks.id"))
    agent_name = Column(String, nullable=False)
    task_description = Column(Text, nullable=False)
    status = Column(String, default="pending")
    result_data = Column(JSON)
    execution_order = Column(Integer, default=0)
    dependencies = Column(JSON)  # List of subtask IDs this depends on
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    parent_task = relationship("Task", back_populates="subtasks")


class AgentMemory(Base):
    """Agent memory for learning and improvement."""
    
    __tablename__ = "agent_memory"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, nullable=False, index=True)
    memory_type = Column(String, nullable=False)  # conversation, feedback, learning
    content = Column(JSON, nullable=False)
    context_tags = Column(JSON)  # Tags for context retrieval
    relevance_score = Column(Float, default=1.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    accessed_at = Column(DateTime(timezone=True))
    access_count = Column(Integer, default=0)


class Feedback(Base):
    """User feedback for continuous improvement."""
    
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    task_id = Column(Integer, ForeignKey("tasks.id"))
    rating = Column(Integer)  # 1-5 star rating
    comment = Column(Text)
    feedback_type = Column(String)  # quality, speed, accuracy, usefulness
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="feedback")
    task = relationship("Task", back_populates="feedback")


class Integration(Base):
    """Third-party integrations and API configurations."""
    
    __tablename__ = "integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    integration_type = Column(String, nullable=False)  # twitter, telegram, crm, etc.
    configuration = Column(JSON, nullable=False)  # Encrypted API keys and settings
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Subscription(Base):
    """Subscription and billing information."""
    
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    stripe_subscription_id = Column(String, unique=True)
    plan_name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))
    
    # Usage tracking
    monthly_tasks_used = Column(Integer, default=0)
    monthly_tasks_limit = Column(Integer, default=10)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
