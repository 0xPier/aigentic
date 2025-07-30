import datetime
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import os
import logging

from src.core.config import app_config
from src.database.connection import connect_to_mongo, close_mongo_connection, mongodb
from src.api.routers import users, projects, tasks, agents, integrations, dashboard
from src.api.routers import settings as settings_router  # Renamed to avoid conflict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting up AI Consultancy Platform...")
    await connect_to_mongo()
    logger.info("Connected to MongoDB.")

    yield
    # Shutdown
    logger.info("Shutting down...")
    await close_mongo_connection()


# Initialize FastAPI app with lifespan management
app = FastAPI(
    title="AI Consultancy Platform",
    description="A comprehensive platform for AI-powered consultancy services",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["integrations"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["settings"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI Consultancy Platform API",
        "version": "1.0.0",
        "status": "running",
        "environment": app_config.environment,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Test database connection (PyMongo async syntax)
        await mongodb.client.admin.command("ping")
        
        return {
            "status": "healthy",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": app_config.environment
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={"status": "unhealthy", "error": str(e)}
        )


if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if app_config.environment == "development" else False,
        log_level="info",
    )
