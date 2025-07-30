from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, Field, field_validator
from pydantic_core import core_schema

from bson import ObjectId

# Custom type for PyObjectId
class PyObjectId(ObjectId):
    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.no_info_plain_validator_function(cls.validate),
            ]),
            serialization=core_schema.to_string_ser_schema(),
        )

# User Model
class User(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    @field_validator('id', mode='before')
    @classmethod
    def convert_objectid_to_str(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# UserSettings Model
class UserSettings(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: PyObjectId
    llm_provider: str = "openai"
    llm_api_key: Optional[str] = None
    llm_api_base: Optional[str] = None
    llm_model: str = "gpt-3.5-turbo"
    theme: str = "light"
    language: str = "en"
    timezone: str = "UTC"
    email_notifications: bool = True
    task_completion_notifications: bool = True
    project_updates_notifications: bool = True
    auto_save_interval: int = 30
    max_concurrent_tasks: int = 3
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Project Model
class Project(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    description: Optional[str] = None
    owner_id: PyObjectId
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Task Model
class Task(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    title: str
    description: Optional[str] = None
    query: str
    task_type: Optional[str] = None
    status: str = "pending"
    priority: str = "medium"
    user_id: PyObjectId
    project_id: Optional[PyObjectId] = None
    assigned_agent: Optional[str] = None
    celery_task_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    result_data: Optional[dict] = None
    output_files: Optional[List[str]] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# SubTask Model
class SubTask(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    parent_task_id: PyObjectId
    agent_name: str
    task_description: str
    status: str = "pending"
    result_data: Optional[dict] = None
    execution_order: int = 0
    dependencies: Optional[List[PyObjectId]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# AgentMemory Model
class AgentMemory(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    agent_name: str
    memory_type: str
    content: dict
    context_tags: Optional[List[str]] = None
    relevance_score: float = 1.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    accessed_at: Optional[datetime] = None
    access_count: int = 0

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Feedback Model
class Feedback(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: PyObjectId
    task_id: PyObjectId
    rating: Optional[int] = None
    comment: Optional[str] = None
    feedback_type: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Integration Model
class Integration(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: PyObjectId
    integration_type: str
    configuration: dict
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Subscription Model
class Subscription(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: PyObjectId
    stripe_subscription_id: Optional[str] = None
    tier: str
    is_active: bool = False
    status: str
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    monthly_tasks_used: int = 0
    monthly_tasks_limit: int = 10
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}