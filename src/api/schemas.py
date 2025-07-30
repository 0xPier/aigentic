"""Pydantic schemas for API request/response models."""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, EmailStr, validator
from bson import ObjectId


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
    id: str  # Changed from int to str to handle PyObjectId
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# User Settings schemas
class UserSettingsBase(BaseModel):
    llm_provider: Optional[str] = "openai"
    llm_api_key: Optional[str] = None
    llm_api_base: Optional[str] = None
    llm_model: Optional[str] = "gpt-3.5-turbo"
    theme: Optional[str] = "light"
    language: Optional[str] = "en"
    timezone: Optional[str] = "UTC"
    email_notifications: Optional[bool] = True
    task_completion_notifications: Optional[bool] = True
    project_updates_notifications: Optional[bool] = True
    auto_save_interval: Optional[int] = 30
    max_concurrent_tasks: Optional[int] = 3


class UserSettingsCreate(UserSettingsBase):
    pass


class UserSettingsUpdate(BaseModel):
    llm_provider: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_api_base: Optional[str] = None
    llm_model: Optional[str] = None
    theme: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    email_notifications: Optional[bool] = None
    task_completion_notifications: Optional[bool] = None
    project_updates_notifications: Optional[bool] = None
    auto_save_interval: Optional[int] = None
    max_concurrent_tasks: Optional[int] = None


class UserSettingsResponse(UserSettingsBase):
    id: str  # Changed from int to str to handle MongoDB ObjectId
    user_id: str  # Changed from int to str to handle MongoDB ObjectId
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


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
    id: str  # Changed from int to str to handle MongoDB ObjectId
    owner_id: str  # Changed from int to str to handle MongoDB ObjectId
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
    project_id: Optional[str] = None  # Changed from int to str


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None


class TaskResponse(TaskBase):
    id: str  # Changed from int to str to handle MongoDB ObjectId
    user_id: str  # Changed from int to str to handle MongoDB ObjectId
    project_id: Optional[str] = None  # Changed from int to str
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    result: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


# Task execution schemas
class TaskExecutionCreate(BaseModel):
    task_id: str  # Changed from int to str
    agent_name: str
    

class TaskExecutionUpdate(BaseModel):
    task_id: str  # Changed from int to str
    status: str
    result: Optional[Dict[str, Any]] = None


class TaskExecutionResponse(BaseModel):
    id: str  # Changed from int to str to handle MongoDB ObjectId
    user_id: str  # Changed from int to str to handle MongoDB ObjectId
    task_id: str  # Changed from int to str
    agent_name: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


# Agent Task Request
class AgentTaskRequest(BaseModel):
    query: str
    task_type: str
    project_id: Optional[str] = None  # Changed from int to str
    priority: str = "medium"
    context: Optional[Dict[str, Any]] = None


# Agent Task Response
class AgentTaskResponse(BaseModel):
    task_id: str  # Changed from int to str to handle MongoDB ObjectId
    status: str
    message: str
    estimated_completion: Optional[str] = None


# Feedback schemas
class FeedbackCreate(BaseModel):
    task_id: str  # Changed from int to str
    rating: int
    comment: Optional[str] = None
    feedback_type: str = "quality"


class FeedbackResponse(BaseModel):
    id: str  # Changed from int to str to handle MongoDB ObjectId
    user_id: str  # Changed from int to str to handle MongoDB ObjectId
    task_id: str  # Changed from int to str to handle MongoDB ObjectId
    rating: int
    comment: Optional[str]
    feedback_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Integration schemas
class IntegrationBase(BaseModel):
    name: str
    service_type: str
    config: Dict[str, Any]


class IntegrationCreate(IntegrationBase):
    pass


class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class IntegrationResponse(IntegrationBase):
    id: str  # Changed from int to str to handle MongoDB ObjectId
    user_id: str  # Changed from int to str to handle MongoDB ObjectId
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Agent schemas
class AgentBase(BaseModel):
    name: str
    agent_type: str
    config: Dict[str, Any]


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class AgentResponse(AgentBase):
    id: str  # Changed from int to str to handle MongoDB ObjectId
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Subscription schemas
class SubscriptionResponse(BaseModel):
    id: str  # Changed from int to str to handle MongoDB ObjectId
    user_id: str  # Changed from int to str to handle MongoDB ObjectId
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
    id: str  # Changed from int to str to handle MongoDB ObjectId
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
