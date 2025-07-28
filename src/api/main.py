"""Main FastAPI application for the AI Consultancy Platform."""

import datetime
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn
import os

from src.core.config import settings
from src.database.connection import create_tables
# from src.api.routers import auth, users, projects, tasks, agents, feedback, integrations
from src.api.routers import auth, users, projects, integrations  # tasks, feedback temporarily disabled
# agents, tasks, feedback temporarily disabled for core functionality testing
from src.database.models import User
from src.database.connection import SessionLocal

# Import admin router conditionally for development
if settings.environment == 'development':
    from src.api.routers import admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("Starting up...")
    create_tables()
    
    # Seed admin user if not exists
    db = SessionLocal()
    try:
        if settings.environment == 'development':
            admin_user = db.query(User).filter(User.email == "admin@example.com").first()
            if not admin_user:
                from src.api.routers.auth import get_password_hash
                admin = User(
                    email="admin@example.com",
                    username="admin",
                    hashed_password=get_password_hash("admin123"),  # Changed from "admin" to "admin123"
                    full_name="Admin User",
                    is_active=True,
                    is_verified=True,
                    subscription_tier="enterprise",
                    subscription_status="active",
                    role="admin"
                )
                db.add(admin)
                db.commit()
                print("Admin user created.")
    finally:
        db.close()

    yield
    # Shutdown
    print("Shutting down...")
    pass


# Create FastAPI application
app = FastAPI(
    title="AI Consultancy Platform",
    description="Multi-agent AI platform for business automation and consultancy",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
allowed_origins = []
if settings.allowed_origins:
    allowed_origins = [origin.strip() for origin in settings.allowed_origins.split(",")]

# Add common development origins if not in production
if settings.environment == "development":
    if "http://localhost:3000" not in allowed_origins:
        allowed_origins.append("http://localhost:3000")
    if "http://127.0.0.1:3000" not in allowed_origins:
        allowed_origins.append("http://127.0.0.1:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
# app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
# app.include_router(agents.router, prefix="/api/agents", tags=["agents"]) # agents temporarily disabled for core functionality testing
# app.include_router(feedback.router, prefix="/api/feedback", tags=["feedback"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["integrations"])  # Uncommented to enable API key functionality

# Include admin router in development only
if settings.environment == 'development':
    app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Consultancy Platform API",
        "version": "1.0.0",
        "status": "active",
        "environment": settings.environment
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
