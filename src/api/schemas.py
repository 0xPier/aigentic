"""Pydantic schemas for API request/response models."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    subscription_tier: Optional[str] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    subscription_tier: str
    subscription_status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Authentication schemas
class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    expires_in: Optional[int] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# Project schemas
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Task schemas
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    query: str
    task_type: Optional[str] = None
    priority: str = "medium"


class TaskCreate(TaskBase):
    project_id: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None


class TaskResponse(TaskBase):
    id: int
    user_id: int
    project_id: Optional[int]
    status: str
    assigned_agent: Optional[str]
    celery_task_id: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    execution_time: Optional[float]
    result_data: Optional[Dict[str, Any]]
    output_files: Optional[List[str]]
    error_message: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Agent Task Request
class AgentTaskRequest(BaseModel):
    query: str
    task_type: str
    project_id: Optional[int] = None
    priority: str = "medium"
    context: Optional[Dict[str, Any]] = None


# Agent Task Response
class AgentTaskResponse(BaseModel):
    task_id: int
    status: str
    message: str
    estimated_completion: Optional[str] = None


# Feedback schemas
class FeedbackCreate(BaseModel):
    task_id: int
    rating: int
    comment: Optional[str] = None
    feedback_type: str = "quality"


class FeedbackResponse(BaseModel):
    id: int
    user_id: int
    task_id: int
    rating: int
    comment: Optional[str]
    feedback_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Integration schemas
class IntegrationCreate(BaseModel):
    integration_type: str
    configuration: Dict[str, Any]


class IntegrationUpdate(BaseModel):
    configuration: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class IntegrationResponse(BaseModel):
    id: int
    user_id: int
    integration_type: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Subscription schemas
class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    plan_name: str
    status: str
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    monthly_tasks_used: int
    monthly_tasks_limit: int
    
    class Config:
        from_attributes = True


# Agent Memory schemas
class AgentMemoryCreate(BaseModel):
    agent_name: str
    memory_type: str
    content: Dict[str, Any]
    context_tags: Optional[List[str]] = None
    relevance_score: float = 1.0


class AgentMemoryResponse(BaseModel):
    id: int
    agent_name: str
    memory_type: str
    content: Dict[str, Any]
    context_tags: Optional[List[str]]
    relevance_score: float
    created_at: datetime
    accessed_at: Optional[datetime]
    access_count: int
    
    class Config:
        from_attributes = True


# Dashboard Analytics
class DashboardStats(BaseModel):
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    failed_tasks: int
    average_execution_time: float
    tasks_this_month: int
    monthly_limit: int
    subscription_tier: str


# File Upload Response
class FileUploadResponse(BaseModel):
    filename: str
    file_path: str
    file_size: int
    upload_time: datetime


# Error Response
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
